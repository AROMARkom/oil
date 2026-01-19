# Quick Start Guide - WTI Oil Trading Bot

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AROMARkom/oil.git
   cd oil
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install MetaTrader 5:**
   - Download MT5 from your broker
   - Log in to your trading account
   - Keep MT5 running during bot operation

## Configuration

Edit `config/config.yaml` to customize your bot:

```yaml
# Key settings to adjust
risk:
  max_risk_per_trade: 0.02    # 2% risk per trade
  max_daily_drawdown: 0.05    # 5% daily limit
  max_total_drawdown: 0.15    # 15% total limit

sessions:
  london:
    enabled: true              # Trade during London session
  newyork:
    enabled: true              # Trade during NY session
```

## Running the Bot

### Option 1: Using the example script
```bash
python example.py
```

### Option 2: Using Python directly
```python
from src.trading_bot import WTIOilTradingBot

bot = WTIOilTradingBot()
if bot.connect_mt5():
    bot.run(check_interval=60)  # Check every 60 seconds
```

### Option 3: With login credentials
```python
bot = WTIOilTradingBot()
bot.connect_mt5(
    login=12345678,           # Your MT5 account number
    password="your_password",
    server="YourBroker-Demo"
)
bot.run()
```

## Verification

Test components without MT5:
```bash
python verify.py
```

Run unit tests:
```bash
pytest tests/ -v
```

## Important Settings

### Risk Management
- **Position Sizing**: Automatically calculated based on 2% risk per trade
- **Stop Loss**: 2.0x ATR from entry price
- **Daily Drawdown**: Trading stops at 5% daily loss
- **Total Drawdown**: Trading stops at 15% total drawdown from peak

### Take Profit Levels
1. **Level 1**: 50% position closed at 2.0x ATR profit
2. **Level 2**: 30% position closed at 3.5x ATR profit
3. **Level 3**: 20% position closed at 5.0x ATR profit

### Trailing Stop
- Activates after 2.5x ATR profit
- Trails at 1.5x ATR distance

### Trading Hours (UTC)
- **London**: 8:00 - 16:00
- **New York**: 13:00 - 21:00
- **Best**: 13:00 - 16:00 (overlap)

### News Avoidance
- **EIA Report**: Wednesday 15:30 UTC
- Avoidance window: 30 min before, 60 min after

## Strategy Logic

The bot uses a **Volatility Expansion + Structural Breakout** strategy:

1. **Compression Detection**: Identifies low volatility periods (ATR < 60% of 20-period average)
2. **Expansion Trigger**: Waits for ATR to increase 1.5x from compressed level
3. **Structure Analysis**: Identifies support/resistance from last 10 candles
4. **Breakout Confirmation**: Enters when price breaks structure by >0.3x ATR
5. **Momentum Filter**: Requires positive/negative momentum for buy/sell

## Monitoring

Bot logs are saved to `logs/trading_bot.log`:
- Signal generation
- Trade execution
- Position management
- Risk statistics (hourly)

Check logs:
```bash
tail -f logs/trading_bot.log
```

## Safety Features

1. **Session Filter**: Only trades during active market hours
2. **News Filter**: Avoids EIA petroleum reports
3. **Risk Controls**: Daily and total drawdown limits
4. **ATR-based Sizing**: Dynamic position sizing
5. **Partial Profits**: Locks in profits progressively
6. **Trailing Stops**: Protects running profits

## Troubleshooting

### "MetaTrader5 module not found"
Install MT5 package:
```bash
pip install MetaTrader5
```

### "Failed to connect to MT5"
- Ensure MT5 is installed and running
- Check that you're logged into your account
- Verify terminal is not minimized to tray

### "No signals generated"
- Check session filter (must be London or NY hours)
- Verify no EIA news period (Wednesday 15:00-16:30 UTC)
- Check drawdown limits not exceeded
- Ensure sufficient volatility in market

### "Position size too small"
- Check account balance
- Review risk settings in config
- Verify symbol specifications in MT5

## Best Practices

1. **Start with Demo**: Test thoroughly on demo account
2. **Monitor Regularly**: Check bot operation and logs
3. **Review Performance**: Analyze trades weekly
4. **Adjust Parameters**: Fine-tune based on results
5. **Risk Management**: Never risk more than 2% per trade
6. **Backup Config**: Save your configuration settings

## Support

- Check logs: `logs/trading_bot.log`
- Review config: `config/config.yaml`
- Run tests: `pytest tests/`
- Verify setup: `python verify.py`

## Disclaimer

This bot is for educational purposes. Trading involves risk. Always test on demo accounts before live trading. Past performance does not guarantee future results.
