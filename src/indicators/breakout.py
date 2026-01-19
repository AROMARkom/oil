"""
Breakout detection and structural analysis
"""
import numpy as np
from typing import Optional, Tuple


class BreakoutDetector:
    """Detect structural breakouts in price action"""
    
    @staticmethod
    def identify_structure(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                          lookback: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Identify support and resistance levels
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            lookback: Lookback period
            
        Returns:
            Tuple of (resistance levels, support levels)
        """
        resistance = np.zeros_like(high)
        support = np.zeros_like(low)
        
        for i in range(lookback, len(high)):
            window_high = high[i-lookback:i]
            window_low = low[i-lookback:i]
            
            resistance[i] = np.max(window_high)
            support[i] = np.min(window_low)
        
        return resistance, support
    
    @staticmethod
    def detect_bullish_breakout(close: np.ndarray, resistance: np.ndarray,
                               atr: np.ndarray, min_size_atr: float = 0.3) -> np.ndarray:
        """
        Detect bullish breakouts above resistance
        
        Args:
            close: Close prices
            resistance: Resistance levels
            atr: ATR values
            min_size_atr: Minimum breakout size in ATR multiples
            
        Returns:
            Boolean array indicating bullish breakouts
        """
        breakouts = np.zeros(len(close), dtype=bool)
        
        for i in range(1, len(close)):
            if resistance[i-1] > 0 and close[i-1] < resistance[i-1]:
                # Current close breaks above previous resistance
                if close[i] > resistance[i-1]:
                    breakout_size = close[i] - resistance[i-1]
                    if atr[i] > 0:
                        size_atr_multiple = breakout_size / atr[i]
                        breakouts[i] = size_atr_multiple >= min_size_atr
        
        return breakouts
    
    @staticmethod
    def detect_bearish_breakout(close: np.ndarray, support: np.ndarray,
                               atr: np.ndarray, min_size_atr: float = 0.3) -> np.ndarray:
        """
        Detect bearish breakouts below support
        
        Args:
            close: Close prices
            support: Support levels
            atr: ATR values
            min_size_atr: Minimum breakout size in ATR multiples
            
        Returns:
            Boolean array indicating bearish breakouts
        """
        breakouts = np.zeros(len(close), dtype=bool)
        
        for i in range(1, len(close)):
            if support[i-1] > 0 and close[i-1] > support[i-1]:
                # Current close breaks below previous support
                if close[i] < support[i-1]:
                    breakout_size = support[i-1] - close[i]
                    if atr[i] > 0:
                        size_atr_multiple = breakout_size / atr[i]
                        breakouts[i] = size_atr_multiple >= min_size_atr
        
        return breakouts
    
    @staticmethod
    def calculate_momentum(close: np.ndarray, period: int = 10) -> np.ndarray:
        """
        Calculate price momentum
        
        Args:
            close: Close prices
            period: Momentum period
            
        Returns:
            Momentum values
        """
        momentum = np.zeros_like(close)
        
        for i in range(period, len(close)):
            momentum[i] = close[i] - close[i-period]
        
        return momentum
