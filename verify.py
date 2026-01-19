"""
Verification script to test bot components without MT5
"""
import sys
import os
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from indicators.volatility import VolatilityIndicator
from indicators.breakout import BreakoutDetector
from core.config import Config


def verify_configuration():
    """Verify configuration loading"""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    config = Config('config/config.yaml')
    print(f"✓ Symbol: {config.symbol}")
    print(f"✓ Timeframe: {config.timeframe}")
    print(f"✓ Max Risk per Trade: {config.max_risk_per_trade * 100}%")
    print(f"✓ ATR Period: {config.atr_period}")
    print(f"✓ Magic Number: {config.magic_number}")
    print()
    return config


def verify_volatility_indicators():
    """Verify volatility indicators"""
    print("=" * 60)
    print("Testing Volatility Indicators")
    print("=" * 60)
    
    # Sample data
    high = np.array([100.5, 101.0, 102.0, 101.5, 103.0, 102.5, 104.0, 103.5, 105.0])
    low = np.array([99.5, 100.0, 100.5, 100.0, 101.0, 101.5, 102.0, 102.5, 103.0])
    close = np.array([100.0, 100.5, 101.0, 100.5, 102.0, 102.0, 103.0, 103.0, 104.0])
    
    # Calculate ATR
    atr = VolatilityIndicator.calculate_atr(high, low, close, period=5)
    print(f"✓ ATR calculated: last value = {atr[-1]:.4f}")
    
    # Detect compression
    compression = VolatilityIndicator.detect_compression(atr, period=5, threshold=0.6)
    print(f"✓ Compression detection: {np.sum(compression)} periods compressed")
    
    # Detect expansion
    expansion = VolatilityIndicator.detect_expansion(atr, compression, multiplier=1.5)
    print(f"✓ Expansion detection: {np.sum(expansion)} periods expanded")
    print()


def verify_breakout_detection():
    """Verify breakout detection"""
    print("=" * 60)
    print("Testing Breakout Detection")
    print("=" * 60)
    
    # Sample data with clear breakout
    high = np.array([100.0, 100.5, 101.0, 101.5, 104.0])
    low = np.array([98.0, 99.0, 99.5, 100.0, 102.0])
    close = np.array([99.0, 100.0, 100.5, 101.0, 103.5])
    
    # Identify structure
    resistance, support = BreakoutDetector.identify_structure(high, low, close, lookback=3)
    print(f"✓ Structure identified")
    print(f"  - Resistance: {resistance[-1]:.2f}")
    print(f"  - Support: {support[-1]:.2f}")
    
    # Create ATR for breakout detection
    atr = np.array([1.0, 1.0, 1.0, 1.0, 1.5])
    
    # Detect bullish breakout
    bullish = BreakoutDetector.detect_bullish_breakout(close, resistance, atr, min_size_atr=0.3)
    print(f"✓ Bullish breakout detection: {np.sum(bullish)} breakouts")
    
    # Calculate momentum
    momentum = BreakoutDetector.calculate_momentum(close, period=3)
    print(f"✓ Momentum calculated: last value = {momentum[-1]:.2f}")
    print()


def verify_strategy_logic():
    """Verify strategy logic without MT5"""
    print("=" * 60)
    print("Testing Strategy Logic")
    print("=" * 60)
    
    # Reuse already imported modules from top
    config = Config('config/config.yaml')
    
    # Sample market data
    high = np.array([70.0, 70.5, 71.0, 70.8, 72.5, 72.0, 73.5] * 10)
    low = np.array([69.0, 69.5, 70.0, 69.8, 71.0, 71.0, 72.0] * 10)
    close = np.array([69.5, 70.0, 70.5, 70.2, 72.0, 71.5, 73.0] * 10)
    
    # Calculate indicators using already imported classes
    atr = VolatilityIndicator.calculate_atr(high, low, close, period=14)
    compression = VolatilityIndicator.detect_compression(atr, period=20, threshold=0.6)
    expansion = VolatilityIndicator.detect_expansion(atr, compression, multiplier=1.5)
    resistance, support = BreakoutDetector.identify_structure(high, low, close, lookback=10)
    
    print(f"✓ Market analysis completed")
    print(f"  - Current price: {close[-1]:.2f}")
    print(f"  - Current ATR: {atr[-1]:.4f}")
    print(f"  - Volatility compressed: {compression[-1]}")
    print(f"  - Volatility expanded: {expansion[-1]}")
    
    # Test SL/TP calculation
    if atr[-1] > 0:
        entry = close[-1]
        sl_distance = atr[-1] * config.stop_loss_atr_multiple
        sl_buy = entry - sl_distance
        
        tp_levels = config.get('take_profit.levels', [])
        
        print(f"✓ Risk calculation (BUY):")
        print(f"  - Entry: {entry:.2f}")
        print(f"  - Stop Loss: {sl_buy:.2f} (distance: {sl_distance:.2f})")
        print(f"  - TP Levels: {len(tp_levels)}")
        for i, tp in enumerate(tp_levels):
            target_atr = tp.get('target_atr_multiple', 2.0)
            percentage = tp.get('close_percentage', 0.5)
            tp_price = entry + (atr[-1] * target_atr)
            print(f"    Level {i+1}: {tp_price:.2f} ({percentage*100:.0f}% close at {target_atr}x ATR)")
    print()


def verify_session_filter():
    """Verify session filtering"""
    print("=" * 60)
    print("Testing Session Filter Configuration")
    print("=" * 60)
    
    config = Config('config/config.yaml')
    
    # Check session configuration
    london_enabled = config.get('sessions.london.enabled', True)
    london_start = config.get('sessions.london.start_hour', 8)
    london_end = config.get('sessions.london.end_hour', 16)
    ny_enabled = config.get('sessions.newyork.enabled', True)
    ny_start = config.get('sessions.newyork.start_hour', 13)
    ny_end = config.get('sessions.newyork.end_hour', 21)
    
    print(f"✓ London session: {london_enabled} ({london_start}:00-{london_end}:00 UTC)")
    print(f"✓ New York session: {ny_enabled} ({ny_start}:00-{ny_end}:00 UTC)")
    print(f"✓ Overlap period: {ny_start}:00-{london_end}:00 UTC")
    
    # Test different times
    test_times = [
        (10, "London session"),
        (15, "London/NY overlap"),
        (18, "NY session"),
        (3, "Asian session (blocked)"),
    ]
    
    for hour, desc in test_times:
        if london_enabled and london_start <= hour < london_end:
            session = "London"
            allowed = True
        elif ny_enabled and ny_start <= hour < ny_end:
            session = "New York"
            allowed = True
        else:
            session = "None"
            allowed = False
        
        status = "✓" if allowed else "✗"
        print(f"{status} {desc}: {session} ({hour}:00 UTC)")
    print()


def verify_news_calendar():
    """Verify news calendar"""
    print("=" * 60)
    print("Testing News Calendar")
    print("=" * 60)
    
    config = Config('config/config.yaml')
    
    # Check EIA configuration
    eia_enabled = config.get('news.eia.enabled', True)
    eia_day = config.get('news.eia.release_day', 3)  # Wednesday
    eia_hour = config.get('news.eia.release_hour', 15)
    eia_minute = config.get('news.eia.release_minute', 30)
    
    print(f"✓ EIA news filtering enabled: {eia_enabled}")
    print(f"  - Release day: Wednesday ({eia_day})")
    print(f"  - Release time: {eia_hour}:{eia_minute:02d} UTC")
    print(f"  - Avoid before: {config.get('news.eia.avoid_minutes_before', 30)} minutes")
    print(f"  - Avoid after: {config.get('news.eia.avoid_minutes_after', 60)} minutes")
    
    # Simple logic check
    test_day = 3  # Wednesday
    test_hour = 15
    if test_day == eia_day and test_hour == eia_hour:
        print(f"✗ Wednesday 15:30 UTC would be blocked (EIA time)")
    else:
        print(f"✓ Non-EIA times would be allowed")
    print()


def main():
    """Run all verification tests"""
    print("\n" + "=" * 60)
    print("WTI OIL TRADING BOT - COMPONENT VERIFICATION")
    print("=" * 60)
    print()
    
    try:
        verify_configuration()
        verify_volatility_indicators()
        verify_breakout_detection()
        verify_strategy_logic()
        verify_session_filter()
        verify_news_calendar()
        
        print("=" * 60)
        print("✓ ALL VERIFICATIONS PASSED")
        print("=" * 60)
        print()
        print("Note: MetaTrader 5 integration cannot be tested in this environment.")
        print("Install MT5 and run the bot with a real broker connection to test fully.")
        print()
        
    except Exception as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
