"""
Volatility indicators and analysis for trading bot
"""
import numpy as np
from typing import List, Tuple


class VolatilityIndicator:
    """Calculate volatility-based indicators"""
    
    @staticmethod
    def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                      period: int = 14) -> np.ndarray:
        """
        Calculate Average True Range (ATR)
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            ATR values
        """
        # True Range calculation
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Set first value to high - low
        tr[0] = high[0] - low[0]
        
        # Calculate ATR using EMA
        atr = np.zeros_like(tr)
        atr[period-1] = np.mean(tr[:period])
        
        multiplier = 1.0 / period
        for i in range(period, len(tr)):
            atr[i] = atr[i-1] + multiplier * (tr[i] - atr[i-1])
        
        return atr
    
    @staticmethod
    def detect_compression(atr: np.ndarray, period: int = 20, 
                          threshold: float = 0.6) -> np.ndarray:
        """
        Detect volatility compression
        
        Args:
            atr: ATR values
            period: Lookback period
            threshold: Compression threshold (ratio to period average)
            
        Returns:
            Boolean array indicating compression
        """
        compression = np.zeros(len(atr), dtype=bool)
        
        for i in range(period, len(atr)):
            period_avg = np.mean(atr[i-period:i])
            if period_avg > 0:
                ratio = atr[i] / period_avg
                compression[i] = ratio < threshold
        
        return compression
    
    @staticmethod
    def detect_expansion(atr: np.ndarray, compression: np.ndarray,
                        multiplier: float = 1.5) -> np.ndarray:
        """
        Detect volatility expansion after compression
        
        Args:
            atr: ATR values
            compression: Compression indicators
            multiplier: Expansion multiplier
            
        Returns:
            Boolean array indicating expansion
        """
        expansion = np.zeros(len(atr), dtype=bool)
        
        for i in range(1, len(atr)):
            if compression[i-1] and not compression[i]:
                # Check if ATR expanded significantly
                if atr[i-1] > 0:
                    expansion_ratio = atr[i] / atr[i-1]
                    expansion[i] = expansion_ratio >= multiplier
        
        return expansion
    
    @staticmethod
    def calculate_bollinger_bands(close: np.ndarray, period: int = 20,
                                 std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Bollinger Bands
        
        Args:
            close: Close prices
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper band, middle band, lower band)
        """
        middle = np.zeros_like(close)
        upper = np.zeros_like(close)
        lower = np.zeros_like(close)
        
        for i in range(period-1, len(close)):
            window = close[i-period+1:i+1]
            middle[i] = np.mean(window)
            std = np.std(window)
            upper[i] = middle[i] + std_dev * std
            lower[i] = middle[i] - std_dev * std
        
        return upper, middle, lower
    
    @staticmethod
    def calculate_band_width(upper: np.ndarray, lower: np.ndarray,
                            middle: np.ndarray) -> np.ndarray:
        """
        Calculate Bollinger Band width
        
        Args:
            upper: Upper band
            lower: Lower band
            middle: Middle band
            
        Returns:
            Band width percentage
        """
        width = np.zeros_like(upper)
        
        for i in range(len(upper)):
            if middle[i] > 0:
                width[i] = (upper[i] - lower[i]) / middle[i]
        
        return width
