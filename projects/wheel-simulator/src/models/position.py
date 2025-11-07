"""Position and portfolio management"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional
from enum import Enum


class PositionStatus(Enum):
    """Status of an options position"""
    OPEN = "open"
    EXPIRED_WORTHLESS = "expired_worthless"
    ASSIGNED = "assigned"
    CALLED_AWAY = "called_away"
    CLOSED = "closed"


@dataclass
class OptionsPosition:
    """Represents an options position"""
    symbol: str
    option_type: Literal['call', 'put']
    strike: float
    expiration: datetime
    premium_received: float
    contracts: int
    entry_date: datetime
    status: PositionStatus = PositionStatus.OPEN
    exit_date: Optional[datetime] = None
    stock_price_at_entry: float = 0.0
    stock_price_at_exit: float = 0.0
    
    def days_to_expiration(self, current_date: datetime) -> int:
        """Calculate days remaining to expiration"""
        if current_date >= self.expiration:
            return 0
        return (self.expiration - current_date).days
    
    def total_premium(self) -> float:
        """Total premium received for this position"""
        return self.premium_received * self.contracts * 100
    
    def is_expired(self, current_date: datetime) -> bool:
        """Check if position has expired"""
        return current_date >= self.expiration


@dataclass
class StockPosition:
    """Represents a stock position"""
    symbol: str
    shares: int
    cost_basis: float
    acquisition_date: datetime
    assigned_from_put: bool = False
    
    def total_cost(self) -> float:
        """Total cost of position"""
        return self.shares * self.cost_basis
    
    def current_value(self, current_price: float) -> float:
        """Current value of position"""
        return self.shares * current_price
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Unrealized profit/loss"""
        return self.current_value(current_price) - self.total_cost()


class Portfolio:
    """Manages the entire portfolio of positions"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.stock_positions: dict[str, StockPosition] = {}
        self.options_positions: list[OptionsPosition] = []
        self.closed_positions: list[OptionsPosition] = []
        self.transaction_history: list[dict] = []
        
    def add_cash(self, amount: float, description: str = ""):
        """Add cash to portfolio"""
        self.cash += amount
        self.transaction_history.append({
            'type': 'cash_in',
            'amount': amount,
            'description': description,
            'timestamp': datetime.now()
        })
    
    def remove_cash(self, amount: float, description: str = ""):
        """Remove cash from portfolio"""
        if amount > self.cash:
            raise ValueError(f"Insufficient cash: ${self.cash:.2f} available, ${amount:.2f} required")
        self.cash -= amount
        self.transaction_history.append({
            'type': 'cash_out',
            'amount': amount,
            'description': description,
            'timestamp': datetime.now()
        })
    
    def sell_put(self, position: OptionsPosition):
        """Sell a cash-secured put"""
        required_cash = position.strike * position.contracts * 100
        if required_cash > self.cash:
            raise ValueError(f"Insufficient cash for cash-secured put: ${self.cash:.2f} available, ${required_cash:.2f} required")
        
        # Cash is secured but not removed yet
        premium = position.total_premium()
        self.add_cash(premium, f"Premium from selling {position.contracts} {position.symbol} put(s)")
        self.options_positions.append(position)
        
    def sell_call(self, position: OptionsPosition):
        """Sell a covered call"""
        # Check if we have the shares
        stock_pos = self.stock_positions.get(position.symbol)
        if not stock_pos or stock_pos.shares < position.contracts * 100:
            raise ValueError(f"Insufficient shares to sell covered call: need {position.contracts * 100}, have {stock_pos.shares if stock_pos else 0}")
        
        premium = position.total_premium()
        self.add_cash(premium, f"Premium from selling {position.contracts} {position.symbol} call(s)")
        self.options_positions.append(position)
    
    def assign_put(self, position: OptionsPosition, stock_price: float, current_date: datetime):
        """Handle put assignment - we buy the stock"""
        cost = position.strike * position.contracts * 100
        shares = position.contracts * 100
        
        # Remove cash to buy stock
        self.remove_cash(cost, f"Put assigned: bought {shares} shares of {position.symbol}")
        
        # Add stock position
        stock_pos = StockPosition(
            symbol=position.symbol,
            shares=shares,
            cost_basis=position.strike,
            acquisition_date=current_date,
            assigned_from_put=True
        )
        self.stock_positions[position.symbol] = stock_pos
        
        # Update position status
        position.status = PositionStatus.ASSIGNED
        position.exit_date = current_date
        position.stock_price_at_exit = stock_price
        self.closed_positions.append(position)
        self.options_positions.remove(position)
    
    def assign_call(self, position: OptionsPosition, stock_price: float, current_date: datetime):
        """Handle call assignment - our stock is called away"""
        proceeds = position.strike * position.contracts * 100
        shares = position.contracts * 100
        
        # Remove stock position
        stock_pos = self.stock_positions.get(position.symbol)
        if stock_pos:
            if stock_pos.shares == shares:
                del self.stock_positions[position.symbol]
            else:
                stock_pos.shares -= shares
        
        # Add cash from sale
        self.add_cash(proceeds, f"Call assigned: sold {shares} shares of {position.symbol}")
        
        # Update position status
        position.status = PositionStatus.CALLED_AWAY
        position.exit_date = current_date
        position.stock_price_at_exit = stock_price
        self.closed_positions.append(position)
        self.options_positions.remove(position)
    
    def expire_worthless(self, position: OptionsPosition, current_date: datetime):
        """Handle option expiring worthless (good for us as sellers)"""
        position.status = PositionStatus.EXPIRED_WORTHLESS
        position.exit_date = current_date
        self.closed_positions.append(position)
        self.options_positions.remove(position)
    
    def get_total_value(self, current_prices: dict[str, float]) -> float:
        """Calculate total portfolio value"""
        stock_value = sum(
            pos.current_value(current_prices.get(symbol, 0))
            for symbol, pos in self.stock_positions.items()
        )
        return self.cash + stock_value
    
    def get_total_premium_collected(self) -> float:
        """Calculate total premium collected from all positions"""
        open_premium = sum(pos.total_premium() for pos in self.options_positions)
        closed_premium = sum(pos.total_premium() for pos in self.closed_positions)
        return open_premium + closed_premium
