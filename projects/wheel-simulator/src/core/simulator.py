"""Main wheel strategy simulator"""

from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
from tabulate import tabulate

from .data_fetcher import DataFetcher
from ..models.black_scholes import BlackScholes, generate_strike_prices
from ..models.position import Portfolio, OptionsPosition, PositionStatus, StockPosition
from .. import config


class WheelSimulator:
    """Simulates wheel strategy trading with historical data"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.portfolio = Portfolio(config.INITIAL_CAPITAL)
        self.current_date: Optional[datetime] = None
        self.trading_dates: List[datetime] = []
        self.current_date_index = 0
        
    def initialize(self):
        """Load historical data and prepare for simulation"""
        print("\n" + "="*70)
        print("WHEEL STRATEGY SIMULATOR - INITIALIZATION")
        print("="*70)
        
        # Fetch data
        self.data_fetcher.fetch_historical_data(config.STOCKS, config.YEARS_OF_DATA)
        
        # Get trading dates (use first stock as reference)
        first_symbol = config.STOCKS[0]
        self.trading_dates = self.data_fetcher.get_available_dates(first_symbol)
        
        if not self.trading_dates:
            raise ValueError("No trading dates available")
        
        self.current_date = self.trading_dates[0]
        self.current_date_index = 0
        
        print(f"\nâœ“ Loaded {len(self.trading_dates)} trading days")
        print(f"âœ“ Date range: {self.trading_dates[0].date()} to {self.trading_dates[-1].date()}")
        print(f"âœ“ Starting capital: ${config.INITIAL_CAPITAL:,.2f}")
        
    def advance_day(self, days: int = 1) -> bool:
        """
        Advance the simulation by a number of days
        
        Returns:
            Tuple of (success: bool, expired_events: list)
        """
        self.current_date_index += days
        if self.current_date_index >= len(self.trading_dates):
            self.current_date_index = len(self.trading_dates) - 1
            return False, []
        
        self.current_date = self.trading_dates[self.current_date_index]
        
        # Check for expirations and get events
        expired_events = self._process_expirations()
        
        return True, expired_events
    
    def _process_expirations(self):
        """Check and process any expired options"""
        expired_events = []
        
        for position in list(self.portfolio.options_positions):
            if position.is_expired(self.current_date):
                stock_price = self.data_fetcher.get_price_at_date(position.symbol, self.current_date)
                
                if position.option_type == 'put':
                    # Put expires ITM if stock price < strike
                    if stock_price < position.strike:
                        print(f"\nâš  PUT ASSIGNED: {position.symbol} @ ${position.strike:.2f} (stock at ${stock_price:.2f})")
                        self.portfolio.assign_put(position, stock_price, self.current_date)
                        expired_events.append({
                            'type': 'put_assigned',
                            'symbol': position.symbol,
                            'strike': position.strike,
                            'shares': position.contracts * 100,
                            'total_cost': position.strike * position.contracts * 100,
                            'stock_price': stock_price
                        })
                    else:
                        print(f"\nâœ“ Put expired worthless: {position.symbol} ${position.strike:.2f}")
                        self.portfolio.expire_worthless(position, self.current_date)
                        expired_events.append({
                            'type': 'expired_worthless',
                            'symbol': position.symbol,
                            'strike': position.strike,
                            'option_type': 'PUT',
                            'premium_kept': position.total_premium(),
                            'stock_price': stock_price
                        })
                        
                elif position.option_type == 'call':
                    # Call expires ITM if stock price > strike
                    if stock_price > position.strike:
                        print(f"\nâš  CALL ASSIGNED: {position.symbol} @ ${position.strike:.2f} (stock at ${stock_price:.2f})")
                        self.portfolio.assign_call(position, stock_price, self.current_date)
                        expired_events.append({
                            'type': 'call_assigned',
                            'symbol': position.symbol,
                            'strike': position.strike,
                            'shares': position.contracts * 100,
                            'total_proceeds': position.strike * position.contracts * 100,
                            'stock_price': stock_price
                        })
                    else:
                        print(f"\nâœ“ Call expired worthless: {position.symbol} ${position.strike:.2f}")
                        self.portfolio.expire_worthless(position, self.current_date)
                        expired_events.append({
                            'type': 'expired_worthless',
                            'symbol': position.symbol,
                            'strike': position.strike,
                            'option_type': 'CALL',
                            'premium_kept': position.total_premium(),
                            'stock_price': stock_price
                        })
        
        return expired_events
    
    def get_current_prices(self) -> dict[str, float]:
        """Get current prices for all stocks"""
        prices = {}
        for symbol in config.STOCKS:
            price = self.data_fetcher.get_price_at_date(symbol, self.current_date)
            # Ensure we have a valid price
            if price is None or price <= 0:
                price = 0.0
            prices[symbol] = float(price)
        return prices
    
    def get_option_chain(self, symbol: str, days_to_expiration: int = 30, 
                        num_strikes: int = 5) -> pd.DataFrame:
        """
        Generate option chain for a symbol
        
        Args:
            symbol: Stock symbol
            days_to_expiration: Days until expiration
            num_strikes: Number of strikes above/below current price
            
        Returns:
            DataFrame with calls and puts
        """
        stock_price = self.data_fetcher.get_price_at_date(symbol, self.current_date)
        volatility = self.data_fetcher.calculate_historical_volatility(symbol, self.current_date)
        
        strikes = generate_strike_prices(stock_price, num_strikes)
        T = days_to_expiration / 365
        r = config.RISK_FREE_RATE
        
        chain_data = []
        for strike in strikes:
            call_price = BlackScholes.call_price(stock_price, strike, T, r, volatility)
            put_price = BlackScholes.put_price(stock_price, strike, T, r, volatility)
            
            chain_data.append({
                'Strike': strike,
                'Call Premium': round(call_price, 2),
                'Put Premium': round(put_price, 2),
                'Call Premium (%)': round(call_price / stock_price * 100, 2),
                'Put Premium (%)': round(put_price / stock_price * 100, 2)
            })
        
        df = pd.DataFrame(chain_data)
        return df
    
    def sell_put_option(self, symbol: str, strike: float, days_to_expiration: int, 
                       contracts: int = 1) -> bool:
        """
        Sell a cash-secured put option
        
        Returns:
            True if successful, False otherwise
        """
        stock_price = self.data_fetcher.get_price_at_date(symbol, self.current_date)
        volatility = self.data_fetcher.calculate_historical_volatility(symbol, self.current_date)
        
        T = days_to_expiration / 365
        premium = BlackScholes.put_price(stock_price, strike, T, config.RISK_FREE_RATE, volatility)
        
        # Calculate expiration using trading days, not calendar days
        future_index = min(self.current_date_index + days_to_expiration, len(self.trading_dates) - 1)
        expiration = self.trading_dates[future_index]
        
        position = OptionsPosition(
            symbol=symbol,
            option_type='put',
            strike=strike,
            expiration=expiration,
            premium_received=premium,
            contracts=contracts,
            entry_date=self.current_date,
            stock_price_at_entry=stock_price
        )
        
        try:
            self.portfolio.sell_put(position)
            print(f"\nâœ“ SOLD PUT: {contracts} {symbol} ${strike:.2f} put @ ${premium:.2f}")
            print(f"  Premium collected: ${position.total_premium():.2f}")
            print(f"  Expiration: {expiration.date()} ({days_to_expiration} days)")
            return True
        except ValueError as e:
            print(f"\nâœ— ERROR: {e}")
            return False
    
    def sell_call_option(self, symbol: str, strike: float, days_to_expiration: int,
                        contracts: int = 1) -> bool:
        """
        Sell a covered call option
        
        Returns:
            True if successful, False otherwise
        """
        stock_price = self.data_fetcher.get_price_at_date(symbol, self.current_date)
        volatility = self.data_fetcher.calculate_historical_volatility(symbol, self.current_date)
        
        T = days_to_expiration / 365
        premium = BlackScholes.call_price(stock_price, strike, T, config.RISK_FREE_RATE, volatility)
        
        # Calculate expiration using trading days, not calendar days
        future_index = min(self.current_date_index + days_to_expiration, len(self.trading_dates) - 1)
        expiration = self.trading_dates[future_index]
        
        position = OptionsPosition(
            symbol=symbol,
            option_type='call',
            strike=strike,
            expiration=expiration,
            premium_received=premium,
            contracts=contracts,
            entry_date=self.current_date,
            stock_price_at_entry=stock_price
        )
        
        try:
            self.portfolio.sell_call(position)
            print(f"\nâœ“ SOLD CALL: {contracts} {symbol} ${strike:.2f} call @ ${premium:.2f}")
            print(f"  Premium collected: ${position.total_premium():.2f}")
            print(f"  Expiration: {expiration.date()} ({days_to_expiration} days)")
            return True
        except ValueError as e:
            print(f"\nâœ— ERROR: {e}")
            return False
    
    def display_status(self):
        """Display current portfolio status"""
        print("\n" + "="*70)
        print(f"PORTFOLIO STATUS - {self.current_date.date()}")
        print("="*70)
        
        current_prices = self.get_current_prices()
        total_value = self.portfolio.get_total_value(current_prices)
        total_return = (total_value - self.portfolio.initial_capital) / self.portfolio.initial_capital * 100
        
        print(f"\nCash: ${self.portfolio.cash:,.2f}")
        print(f"Total Portfolio Value: ${total_value:,.2f}")
        print(f"Total Return: {total_return:+.2f}%")
        print(f"Total Premium Collected: ${self.portfolio.get_total_premium_collected():,.2f}")
        
        # Stock positions
        if self.portfolio.stock_positions:
            print("\n" + "-"*70)
            print("STOCK POSITIONS")
            print("-"*70)
            stock_data = []
            for symbol, pos in self.portfolio.stock_positions.items():
                current_price = current_prices.get(symbol, 0)
                pnl = pos.unrealized_pnl(current_price)
                pnl_pct = (pnl / pos.total_cost()) * 100 if pos.total_cost() > 0 else 0
                
                stock_data.append([
                    symbol,
                    pos.shares,
                    f"${pos.cost_basis:.2f}",
                    f"${current_price:.2f}",
                    f"${pos.current_value(current_price):,.2f}",
                    f"${pnl:+,.2f} ({pnl_pct:+.1f}%)"
                ])
            
            print(tabulate(stock_data, 
                          headers=['Symbol', 'Shares', 'Cost Basis', 'Current', 'Value', 'P&L'],
                          tablefmt='simple'))
        
        # Open options positions
        if self.portfolio.options_positions:
            print("\n" + "-"*70)
            print("OPEN OPTIONS POSITIONS")
            print("-"*70)
            options_data = []
            for pos in self.portfolio.options_positions:
                dte = pos.days_to_expiration(self.current_date)
                options_data.append([
                    pos.symbol,
                    pos.option_type.upper(),
                    f"${pos.strike:.2f}",
                    pos.contracts,
                    f"${pos.premium_received:.2f}",
                    f"${pos.total_premium():.2f}",
                    f"{dte} days"
                ])
            
            print(tabulate(options_data,
                          headers=['Symbol', 'Type', 'Strike', 'Contracts', 'Premium', 'Total', 'DTE'],
                          tablefmt='simple'))
    
    def display_market_overview(self):
        """Display overview of all stocks"""
        print("\n" + "="*70)
        print(f"MARKET OVERVIEW - {self.current_date.date()}")
        print("="*70)
        
        market_data = []
        for symbol in config.STOCKS:
            price = self.data_fetcher.get_price_at_date(symbol, self.current_date)
            vol = self.data_fetcher.calculate_historical_volatility(symbol, self.current_date)
            
            # Check if we have position
            has_stock = symbol in self.portfolio.stock_positions
            has_option = any(pos.symbol == symbol for pos in self.portfolio.options_positions)
            status = ""
            if has_stock:
                status += "ðŸ“ˆ "
            if has_option:
                status += "ðŸ“‹ "
            
            market_data.append([
                symbol,
                f"${price:.2f}",
                f"{vol:.1%}",
                status
            ])
        
        print(tabulate(market_data,
                      headers=['Symbol', 'Price', 'IV (30d)', 'Position'],
                      tablefmt='simple'))


if __name__ == "__main__":
    # Test the simulator
    sim = WheelSimulator()
    sim.initialize()
    sim.display_market_overview()
    sim.display_status()
