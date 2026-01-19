"""
Profit management with partial take profit and trailing stop
"""
from typing import Dict, List, Optional
import logging

from ..core.config import Config


class ProfitManager:
    """
    Manage profit taking with partial closes and trailing stops
    """
    
    def __init__(self, config: Config):
        """
        Initialize profit manager
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Take profit configuration
        self.tp_enabled = config.get('take_profit.enabled', True)
        self.tp_levels = config.get('take_profit.levels', [])
        
        # Trailing stop configuration
        self.trailing_enabled = config.get('take_profit.trailing_stop.enabled', True)
        self.trail_activation = config.get('take_profit.trailing_stop.activation_atr_multiple', 2.5)
        self.trail_distance = config.get('take_profit.trailing_stop.trail_atr_multiple', 1.5)
        
        # Track TP levels hit for each position
        self.position_tp_status = {}  # {ticket: {'levels_hit': [0, 1], 'trailing_active': False}}
    
    def initialize_position(self, ticket: int):
        """
        Initialize tracking for a new position
        
        Args:
            ticket: Position ticket number
        """
        self.position_tp_status[ticket] = {
            'levels_hit': [],
            'trailing_active': False,
            'highest_profit_atr': 0.0
        }
    
    def check_partial_tp(self, ticket: int, entry_price: float, current_price: float,
                        position_type: str, atr: float, initial_volume: float) -> List[Dict]:
        """
        Check if any TP levels should be executed
        
        Args:
            ticket: Position ticket
            entry_price: Entry price
            current_price: Current market price
            position_type: 'BUY' or 'SELL'
            atr: Current ATR value
            initial_volume: Initial position size
            
        Returns:
            List of TP actions to execute
        """
        if not self.tp_enabled or ticket not in self.position_tp_status:
            return []
        
        actions = []
        status = self.position_tp_status[ticket]
        
        # Calculate current profit in ATR multiples
        if position_type == 'BUY':
            profit_points = current_price - entry_price
        else:  # SELL
            profit_points = entry_price - current_price
        
        if atr <= 0:
            return []
        
        profit_atr = profit_points / atr
        
        # Update highest profit
        if profit_atr > status['highest_profit_atr']:
            status['highest_profit_atr'] = profit_atr
        
        # Check each TP level
        for i, level in enumerate(self.tp_levels):
            if i in status['levels_hit']:
                continue  # Already hit this level
            
            target_atr = level.get('target_atr_multiple', 2.0)
            percentage = level.get('close_percentage', 0.5)
            
            # Check if TP level reached
            if profit_atr >= target_atr:
                close_volume = initial_volume * percentage
                
                actions.append({
                    'action': 'partial_close',
                    'ticket': ticket,
                    'volume': close_volume,
                    'level': i,
                    'reason': f'TP level {i+1} hit ({target_atr}x ATR)'
                })
                
                status['levels_hit'].append(i)
                self.logger.info(f"Position {ticket}: TP level {i+1} reached at {profit_atr:.2f}x ATR")
        
        return actions
    
    def check_trailing_stop(self, ticket: int, entry_price: float, current_price: float,
                           position_type: str, current_sl: float, atr: float) -> Optional[Dict]:
        """
        Check and update trailing stop
        
        Args:
            ticket: Position ticket
            entry_price: Entry price
            current_price: Current market price
            position_type: 'BUY' or 'SELL'
            current_sl: Current stop loss
            atr: Current ATR value
            
        Returns:
            Trailing stop action or None
        """
        if not self.trailing_enabled or ticket not in self.position_tp_status:
            return None
        
        status = self.position_tp_status[ticket]
        
        # Calculate current profit in ATR multiples
        if position_type == 'BUY':
            profit_points = current_price - entry_price
        else:  # SELL
            profit_points = entry_price - current_price
        
        if atr <= 0:
            return None
        
        profit_atr = profit_points / atr
        
        # Activate trailing stop if profit threshold reached
        if not status['trailing_active'] and profit_atr >= self.trail_activation:
            status['trailing_active'] = True
            self.logger.info(f"Position {ticket}: Trailing stop activated at {profit_atr:.2f}x ATR")
        
        # Update trailing stop if active
        if status['trailing_active']:
            trail_distance_points = atr * self.trail_distance
            
            if position_type == 'BUY':
                new_sl = current_price - trail_distance_points
                # Only move SL up, never down
                if new_sl > current_sl:
                    return {
                        'action': 'modify_sl',
                        'ticket': ticket,
                        'new_sl': new_sl,
                        'reason': f'Trailing stop update (trail at {self.trail_distance}x ATR)'
                    }
            else:  # SELL
                new_sl = current_price + trail_distance_points
                # Only move SL down, never up
                if new_sl < current_sl or current_sl == 0:
                    return {
                        'action': 'modify_sl',
                        'ticket': ticket,
                        'new_sl': new_sl,
                        'reason': f'Trailing stop update (trail at {self.trail_distance}x ATR)'
                    }
        
        return None
    
    def remove_position(self, ticket: int):
        """
        Remove position from tracking
        
        Args:
            ticket: Position ticket
        """
        if ticket in self.position_tp_status:
            del self.position_tp_status[ticket]
    
    def get_position_status(self, ticket: int) -> Optional[Dict]:
        """
        Get position profit management status
        
        Args:
            ticket: Position ticket
            
        Returns:
            Status dictionary or None
        """
        return self.position_tp_status.get(ticket)
    
    def calculate_remaining_volume(self, ticket: int, initial_volume: float) -> float:
        """
        Calculate remaining volume after partial closes
        
        Args:
            ticket: Position ticket
            initial_volume: Initial position size
            
        Returns:
            Remaining volume
        """
        if ticket not in self.position_tp_status:
            return initial_volume
        
        status = self.position_tp_status[ticket]
        total_closed_pct = 0.0
        
        for level_idx in status['levels_hit']:
            if level_idx < len(self.tp_levels):
                percentage = self.tp_levels[level_idx].get('close_percentage', 0.0)
                total_closed_pct += percentage
        
        remaining_pct = 1.0 - total_closed_pct
        return initial_volume * remaining_pct
