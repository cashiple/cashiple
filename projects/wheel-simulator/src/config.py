"""Configuration settings for the Wheel Strategy Simulator"""

# Stock symbols to track
STOCKS = ['AAPL', 'MSFT', 'JNJ', 'KO', 'XOM', 'V', 'GOOG', 'AXP', 'WMT', 'PG']

# Historical data period (1.5 years)
YEARS_OF_DATA = 1.5

# Trading parameters
INITIAL_CAPITAL = 100000  # Starting cash
RISK_FREE_RATE = 0.045    # Current risk-free rate (approximate)

# Options parameters
DAYS_TO_EXPIRATION = [7, 14, 30, 45]  # Available expiration cycles
CONTRACT_SIZE = 100  # Shares per contract

# Display settings
DISPLAY_PRECISION = 2
