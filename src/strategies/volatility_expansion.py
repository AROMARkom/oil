"""
Volatility Expansion Strategy for WTI Oil Trading
"""
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

from ..indicators.volatility import VolatilityIndicator
from ..indicators.breakout import BreakoutDetector
from ..core.config import Config


class VolatilityExpansionStrategy:
    """
    Volatility expansion and structural breakout strategy
    
    Strategy Logic:
    1. Identify volatility compression (low ATR relative to average)
    2. Wait for volatility expansion (ATR increase)
    3. Confirm with structural breakout (support/resistance)
    4. Enter trade in breakout direction
    5. Manage risk with ATR-based stops
    """
    
    def __init__(self, config: Config):
        """
        Initialize strategy
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.volatility_indicator = VolatilityIndicator()
        self.breakout_detector = BreakoutDetector()
        
        # Strategy parameters
        self.compression_period = config.get('strategy.volatility.compression_period', 20)
        self.compression_threshold = config.get('strategy.volatility.compression_threshold', 0.6)
        self.expansion_multiplier = config.get('strategy.volatility.expansion_multiplier', 1.5)
        self.breakout_lookback = config.get('strategy.breakout.lookback_period', 10)
        self.min_breakout_size = config.get('strategy.breakout.min_breakout_size', 0.3)
        self.atr_period = config.get('risk.atr_period', 14)
    
    def analyze(self, high: np.ndarray, low: np.ndarray, close: np.ndarray,
                open_price: np.ndarray, volume: np.ndarray = None) -> Dict:
        """
        Analyze market conditions and generate signals
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            open_price: Open prices
            volume: Volume data (optional)
            
        Returns:
            Dictionary with analysis results and signals
        """
        # Calculate ATR
        atr = self.volatility_indicator.calculate_atr(high, low, close, self.atr_period)
        
        # Detect volatility compression
        compression = self.volatility_indicator.detect_compression(
            atr, self.compression_period, self.compression_threshold
        )
        
        # Detect volatility expansion
        expansion = self.volatility_indicator.detect_expansion(
            atr, compression, self.expansion_multiplier
        )
        
        # Identify market structure
        resistance, support = self.breakout_detector.identify_structure(
            high, low, close, self.breakout_lookback
        )
        
        # Detect breakouts
        bullish_breakout = self.breakout_detector.detect_bullish_breakout(
            close, resistance, atr, self.min_breakout_size
        )
        
        bearish_breakout = self.breakout_detector.detect_bearish_breakout(
            close, support, atr, self.min_breakout_size
        )
        
        # Calculate momentum
        momentum = self.breakout_detector.calculate_momentum(close, 10)
        
        # Generate signals
        buy_signal = self._generate_buy_signal(
            expansion, bullish_breakout, momentum, close
        )
        
        sell_signal = self._generate_sell_signal(
            expansion, bearish_breakout, momentum, close
        )
        
        return {
            'atr': atr,
            'compression': compression,
            'expansion': expansion,
            'resistance': resistance,
            'support': support,
            'bullish_breakout': bullish_breakout,
            'bearish_breakout': bearish_breakout,
            'momentum': momentum,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'current_price': close[-1] if len(close) > 0 else 0,
            'current_atr': atr[-1] if len(atr) > 0 else 0
        }
    
    def _generate_buy_signal(self, expansion: np.ndarray, bullish_breakout: np.ndarray,
                            momentum: np.ndarray, close: np.ndarray) -> bool:
        """
        Generate buy signal based on strategy conditions
        
        Args:
            expansion: Volatility expansion indicators
            bullish_breakout: Bullish breakout indicators
            momentum: Momentum values
            close: Close prices
            
        Returns:
            True if buy signal is generated
        """
        if len(close) < 2:
            return False
        
        # Current bar conditions
        current_expansion = expansion[-1]
        current_breakout = bullish_breakout[-1]
        current_momentum = momentum[-1]
        
        # Buy signal: Expansion + Bullish breakout + Positive momentum
        if current_expansion and current_breakout and current_momentum > 0:
            return True
        
        return False
    
    def _generate_sell_signal(self, expansion: np.ndarray, bearish_breakout: np.ndarray,
                             momentum: np.ndarray, close: np.ndarray) -> bool:
        """
        Generate sell signal based on strategy conditions
        
        Args:
            expansion: Volatility expansion indicators
            bearish_breakout: Bearish breakout indicators
            momentum: Momentum values
            close: Close prices
            
        Returns:
            True if sell signal is generated
        """
        if len(close) < 2:
            return False
        
        # Current bar conditions
        current_expansion = expansion[-1]
        current_breakout = bearish_breakout[-1]
        current_momentum = momentum[-1]
        
        # Sell signal: Expansion + Bearish breakout + Negative momentum
        if current_expansion and current_breakout and current_momentum < 0:
            return True
        
        return False
    
    def calculate_entry_price(self, signal_type: str, current_price: float) -> float:
        """
        Calculate entry price for the trade
        
        Args:
            signal_type: 'BUY' or 'SELL'
            current_price: Current market price
            
        Returns:
            Entry price
        """
        # For market orders, entry is current price
        return current_price
    
    def calculate_stop_loss(self, entry_price: float, signal_type: str, 
                           atr: float) -> float:
        """
        Calculate stop loss based on ATR
        
        Args:
            entry_price: Entry price
            signal_type: 'BUY' or 'SELL'
            atr: Current ATR value
            
        Returns:
            Stop loss price
        """
        sl_distance = atr * self.config.stop_loss_atr_multiple
        
        if signal_type == 'BUY':
            return entry_price - sl_distance
        else:  # SELL
            return entry_price + sl_distance
    
    def calculate_take_profit_levels(self, entry_price: float, signal_type: str,
                                    atr: float) -> list:
        """
        Calculate multiple take profit levels
        
        Args:
            entry_price: Entry price
            signal_type: 'BUY' or 'SELL'
            atr: Current ATR value
            
        Returns:
            List of (price, percentage) tuples
        """
        tp_levels = []
        tp_config = self.config.get('take_profit.levels', [])
        
        for level in tp_config:
            target_atr = level.get('target_atr_multiple', 2.0)
            percentage = level.get('close_percentage', 0.5)
            
            tp_distance = atr * target_atr
            
            if signal_type == 'BUY':
                tp_price = entry_price + tp_distance
            else:  # SELL
                tp_price = entry_price - tp_distance
            
            tp_levels.append({
                'price': tp_price,
                'percentage': percentage,
                'atr_multiple': target_atr
            })
        
        return tp_levels
