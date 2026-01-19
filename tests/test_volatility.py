"""
Unit tests for VolatilityIndicator
"""
import numpy as np
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from indicators.volatility import VolatilityIndicator


class TestVolatilityIndicator:
    """Test cases for VolatilityIndicator"""
    
    def test_calculate_atr_basic(self):
        """Test basic ATR calculation"""
        # Simple test data
        high = np.array([100.5, 101.0, 102.0, 101.5, 103.0])
        low = np.array([99.5, 100.0, 100.5, 100.0, 101.0])
        close = np.array([100.0, 100.5, 101.0, 100.5, 102.0])
        
        atr = VolatilityIndicator.calculate_atr(high, low, close, period=3)
        
        # ATR should be positive
        assert np.all(atr >= 0)
        # Should have same length as input
        assert len(atr) == len(high)
    
    def test_detect_compression(self):
        """Test volatility compression detection"""
        # Create ATR array with compression period
        atr = np.array([2.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0])
        
        compression = VolatilityIndicator.detect_compression(
            atr, period=5, threshold=0.6
        )
        
        # Should detect compression in later periods
        assert isinstance(compression, np.ndarray)
        assert len(compression) == len(atr)
        assert compression[-1]  # Last value should be compressed
    
    def test_detect_expansion(self):
        """Test volatility expansion detection"""
        # Create compression array
        compression = np.array([False, False, True, True, False, False])
        atr = np.array([2.0, 2.0, 1.0, 1.0, 2.5, 3.0])
        
        expansion = VolatilityIndicator.detect_expansion(
            atr, compression, multiplier=1.5
        )
        
        assert isinstance(expansion, np.ndarray)
        assert len(expansion) == len(atr)
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        close = np.array([100.0, 101.0, 102.0, 101.5, 103.0, 102.5, 104.0])
        
        upper, middle, lower = VolatilityIndicator.calculate_bollinger_bands(
            close, period=3, std_dev=2.0
        )
        
        # Bands should bracket the middle
        assert np.all(upper >= middle)
        assert np.all(middle >= lower)
        assert len(upper) == len(close)
    
    def test_calculate_band_width(self):
        """Test Bollinger Band width calculation"""
        upper = np.array([105.0, 106.0, 107.0])
        middle = np.array([100.0, 101.0, 102.0])
        lower = np.array([95.0, 96.0, 97.0])
        
        width = VolatilityIndicator.calculate_band_width(upper, lower, middle)
        
        assert np.all(width > 0)
        assert len(width) == len(upper)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
