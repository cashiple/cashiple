"""Black-Scholes option pricing model"""

import numpy as np
from scipy.stats import norm
from typing import Literal


class BlackScholes:
    """Calculate option prices using Black-Scholes model"""
    
    @staticmethod
    def calculate_d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 parameter"""
        return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def calculate_d2(d1: float, sigma: float, T: float) -> float:
        """Calculate d2 parameter"""
        return d1 - sigma * np.sqrt(T)
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate call option price
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            
        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)
            
        d1 = BlackScholes.calculate_d1(S, K, T, r, sigma)
        d2 = BlackScholes.calculate_d2(d1, sigma, T)
        
        call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return max(call, 0)
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate put option price
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            
        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)
            
        d1 = BlackScholes.calculate_d1(S, K, T, r, sigma)
        d2 = BlackScholes.calculate_d2(d1, sigma, T)
        
        put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return max(put, 0)
    
    @staticmethod
    def option_price(S: float, K: float, T: float, r: float, sigma: float, 
                    option_type: Literal['call', 'put']) -> float:
        """
        Calculate option price for either call or put
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            option_type: 'call' or 'put'
            
        Returns:
            Option price
        """
        if option_type == 'call':
            return BlackScholes.call_price(S, K, T, r, sigma)
        else:
            return BlackScholes.put_price(S, K, T, r, sigma)


def generate_strike_prices(stock_price: float, num_strikes: int = 5, 
                          spacing_pct: float = 0.025) -> list:
    """
    Generate strike prices around current stock price
    
    Args:
        stock_price: Current stock price
        num_strikes: Number of strikes to generate on each side
        spacing_pct: Spacing between strikes as percentage
        
    Returns:
        List of strike prices
    """
    strikes = []
    for i in range(-num_strikes, num_strikes + 1):
        strike = stock_price * (1 + i * spacing_pct)
        # Round to nearest 0.50 or 1.00 depending on price
        if strike < 50:
            strike = round(strike * 2) / 2
        else:
            strike = round(strike)
        strikes.append(strike)
    
    return sorted(set(strikes))


if __name__ == "__main__":
    # Test Black-Scholes calculations
    print("Black-Scholes Option Pricing Test")
    print("="*60)
    
    # Example: AAPL at $180, 30 days to expiration, 30% volatility
    S = 180.0
    r = 0.045
    sigma = 0.30
    T = 30 / 365
    
    strikes = generate_strike_prices(S, num_strikes=3)
    
    print(f"\nStock Price: ${S:.2f}")
    print(f"Volatility: {sigma:.1%}")
    print(f"Time to Expiration: {30} days")
    print(f"Risk-free Rate: {r:.1%}")
    print("\n" + "="*60)
    print(f"{'Strike':<10} {'Call Price':<15} {'Put Price':<15}")
    print("="*60)
    
    for K in strikes:
        call = BlackScholes.call_price(S, K, T, r, sigma)
        put = BlackScholes.put_price(S, K, T, r, sigma)
        print(f"${K:<9.2f} ${call:<14.2f} ${put:<14.2f}")
