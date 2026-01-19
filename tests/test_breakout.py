"""
Unit tests for BreakoutDetector
"""
import numpy as np
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from indicators.breakout import BreakoutDetector


class TestBreakoutDetector:
    """Test cases for BreakoutDetector"""
    
    def test_identify_structure(self):
        """Test structure identification"""
        high = np.array([100.0, 101.0, 102.0, 101.5, 103.0, 102.5, 104.0])
        low = np.array([98.0, 99.0, 100.0, 99.5, 101.0, 100.5, 102.0])
        close = np.array([99.0, 100.0, 101.0, 100.5, 102.0, 101.5, 103.0])
        
        resistance, support = BreakoutDetector.identify_structure(
            high, low, close, lookback=3
        )
        
        assert len(resistance) == len(high)
        assert len(support) == len(low)
        # Resistance should be >= support
        assert np.all(resistance >= support)
    
    def test_detect_bullish_breakout(self):
        """Test bullish breakout detection"""
        close = np.array([100.0, 100.5, 101.0, 101.5, 103.0])
        resistance = np.array([101.5, 101.5, 101.5, 101.5, 101.5])
        atr = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        
        breakouts = BreakoutDetector.detect_bullish_breakout(
            close, resistance, atr, min_size_atr=0.3
        )
        
        assert isinstance(breakouts, np.ndarray)
        assert len(breakouts) == len(close)
        # Last candle should show breakout
        assert breakouts[-1]
    
    def test_detect_bearish_breakout(self):
        """Test bearish breakout detection"""
        close = np.array([100.0, 99.5, 99.0, 98.5, 97.0])
        support = np.array([98.5, 98.5, 98.5, 98.5, 98.5])
        atr = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        
        breakouts = BreakoutDetector.detect_bearish_breakout(
            close, support, atr, min_size_atr=0.3
        )
        
        assert isinstance(breakouts, np.ndarray)
        assert len(breakouts) == len(close)
        # Should detect bearish breakout
        assert breakouts[-1]
    
    def test_calculate_momentum(self):
        """Test momentum calculation"""
        close = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
        
        momentum = BreakoutDetector.calculate_momentum(close, period=3)
        
        assert len(momentum) == len(close)
        # Positive momentum for uptrend
        assert momentum[-1] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
