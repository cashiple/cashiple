"""Fetch and manage historical market data"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from .. import config


class DataFetcher:
    """Fetches and caches historical stock data"""
    
    def __init__(self):
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
    def fetch_historical_data(self, symbols: List[str], years: int = 3) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            years: Number of years of historical data
            
        Returns:
            Dictionary mapping symbol to DataFrame with OHLCV data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        print(f"Fetching {years} years of historical data for {len(symbols)} stocks...")
        
        for symbol in symbols:
            try:
                print(f"  Downloading {symbol}...", end=' ')
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                if not df.empty:
                    self.data_cache[symbol] = df
                    print(f"âœ“ ({len(df)} days)")
                else:
                    print(f"âœ— (no data)")
                    
            except Exception as e:
                print(f"âœ— (error: {e})")
                
        print(f"\nSuccessfully loaded data for {len(self.data_cache)} stocks")
        return self.data_cache
    
    def get_data(self, symbol: str) -> pd.DataFrame:
        """Get cached data for a symbol"""
        return self.data_cache.get(symbol, pd.DataFrame())
    
    def get_price_at_date(self, symbol: str, date: datetime) -> float:
        """Get closing price for a symbol on a specific date"""
        df = self.get_data(symbol)
        if df.empty:
            return 0.0
            
        # Find the closest date (in case of holidays/weekends)
        idx = df.index.get_indexer([date], method='nearest')[0]
        price = df.iloc[idx]['Close']
        
        # Handle NaN values
        if pd.isna(price):
            return 0.0
            
        return float(price)
    
    def calculate_historical_volatility(self, symbol: str, date: datetime, window: int = 30) -> float:
        """
        Calculate historical volatility (annualized) for a symbol
        
        Args:
            symbol: Stock symbol
            date: Date for calculation
            window: Number of days to look back
            
        Returns:
            Annualized volatility (standard deviation of returns)
        """
        df = self.get_data(symbol)
        if df.empty:
            return 0.30  # Default volatility
            
        # Get data up to the specified date
        historical = df[df.index <= date].tail(window + 1)
        
        if len(historical) < 2:
            return 0.30
            
        # Calculate daily returns
        returns = historical['Close'].pct_change().dropna()
        
        # Annualize volatility (252 trading days per year)
        volatility = returns.std() * (252 ** 0.5)
        
        return float(volatility)
    
    def get_available_dates(self, symbol: str) -> List[datetime]:
        """Get list of available trading dates for a symbol"""
        df = self.get_data(symbol)
        if df.empty:
            return []
        return df.index.tolist()


if __name__ == "__main__":
    # Test the data fetcher
    fetcher = DataFetcher()
    data = fetcher.fetch_historical_data(config.STOCKS, config.YEARS_OF_DATA)
    
    # Display summary
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    for symbol, df in data.items():
        if not df.empty:
            vol = fetcher.calculate_historical_volatility(symbol, df.index[-1])
            print(f"{symbol:6s}: {len(df):4d} days  |  Current: ${df['Close'].iloc[-1]:.2f}  |  Vol: {vol:.1%}")
