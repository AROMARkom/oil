"""
Example usage of WTI Oil Trading Bot
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.trading_bot import WTIOilTradingBot


def main():
    """
    Example: How to use the WTI Oil Trading Bot
    """
    print("=" * 60)
    print("WTI Oil Trading Bot - Example")
    print("=" * 60)
    
    # Create bot instance with default configuration
    bot = WTIOilTradingBot()
    
    # Option 1: Connect to MT5 (assumes MT5 is already logged in)
    print("\nConnecting to MetaTrader 5...")
    if bot.connect_mt5():
        print("✓ Connected successfully")
        
        # Run the bot
        # check_interval: how often to check for signals (in seconds)
        print("\nStarting trading bot...")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        bot.run(check_interval=60)  # Check every 60 seconds
    else:
        print("✗ Failed to connect to MetaTrader 5")
        print("\nMake sure:")
        print("1. MetaTrader 5 is installed")
        print("2. You are logged into your account")
        print("3. MT5 terminal is running")
    
    # Option 2: Connect with credentials (if needed)
    # login = 12345678  # Your MT5 account number
    # password = "your_password"
    # server = "YourBroker-Demo"
    # 
    # if bot.connect_mt5(login, password, server):
    #     bot.run(check_interval=60)


if __name__ == "__main__":
    main()
