"""
WTI Oil Trading Bot

Systematic trading bot for WTI Crude Oil CFD
Strategy: Volatility Expansion + Structural Breakout
"""

__version__ = '1.0.0'
__author__ = 'Trading Bot Team'

from .trading_bot import WTIOilTradingBot

__all__ = ['WTIOilTradingBot']
