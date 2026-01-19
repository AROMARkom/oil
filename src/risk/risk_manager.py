"""
Risk management module for trading bot
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import numpy as np

from ..core.config import Config


class RiskManager:
    """
    Risk management system with ATR-based position sizing and drawdown control
    """
    
    def __init__(self, config: Config):
        """
        Initialize risk manager
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.max_risk_per_trade = config.get('risk.max_risk_per_trade', 0.02)
        self.max_daily_drawdown = config.get('risk.max_daily_drawdown', 0.05)
        self.max_total_drawdown = config.get('risk.max_total_drawdown', 0.15)
        
        # Track daily performance
        self.daily_pnl = 0.0
        self.daily_start_balance = 0.0
        self.current_date = None
        
        # Track total performance
        self.initial_balance = 0.0
        self.peak_balance = 0.0
    
    def calculate_position_size(self, account_balance: float, entry_price: float,
                               stop_loss: float, symbol_info: Dict) -> float:
        """
        Calculate position size based on risk per trade
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            symbol_info: Symbol information (point, contract_size, etc.)
            
        Returns:
            Position size in lots
        """
        # Calculate risk amount in account currency
        risk_amount = account_balance * self.max_risk_per_trade
        
        # Calculate price difference (pips/points)
        price_diff = abs(entry_price - stop_loss)
        
        # Get contract specifications
        point = symbol_info.get('point', 0.01)
        contract_size = symbol_info.get('contract_size', 100)
        
        # Calculate position size
        # risk_amount = position_size * contract_size * price_diff
        if price_diff > 0:
            position_size = risk_amount / (contract_size * price_diff)
        else:
            position_size = 0.01  # Minimum position
        
        # Apply minimum and maximum limits
        min_lot = symbol_info.get('min_lot', 0.01)
        max_lot = symbol_info.get('max_lot', 100.0)
        lot_step = symbol_info.get('lot_step', 0.01)
        
        # Round to lot step
        position_size = round(position_size / lot_step) * lot_step
        
        # Enforce limits
        position_size = max(min_lot, min(position_size, max_lot))
        
        return position_size
    
    def check_daily_drawdown(self, account_balance: float, current_date: datetime) -> bool:
        """
        Check if daily drawdown limit is exceeded
        
        Args:
            account_balance: Current account balance
            current_date: Current date
            
        Returns:
            True if trading is allowed, False if daily limit exceeded
        """
        # Reset daily tracking on new day
        if self.current_date is None or self.current_date.date() != current_date.date():
            self.current_date = current_date
            self.daily_start_balance = account_balance
            self.daily_pnl = 0.0
        
        # Calculate daily drawdown
        daily_drawdown = (self.daily_start_balance - account_balance) / self.daily_start_balance
        
        if daily_drawdown >= self.max_daily_drawdown:
            return False  # Daily limit exceeded
        
        return True
    
    def check_total_drawdown(self, account_balance: float) -> bool:
        """
        Check if total drawdown limit is exceeded
        
        Args:
            account_balance: Current account balance
            
        Returns:
            True if trading is allowed, False if total limit exceeded
        """
        # Initialize peak balance
        if self.initial_balance == 0.0:
            self.initial_balance = account_balance
            self.peak_balance = account_balance
        
        # Update peak balance
        if account_balance > self.peak_balance:
            self.peak_balance = account_balance
        
        # Calculate total drawdown from peak
        total_drawdown = (self.peak_balance - account_balance) / self.peak_balance
        
        if total_drawdown >= self.max_total_drawdown:
            return False  # Total limit exceeded
        
        return True
    
    def can_trade(self, account_balance: float, current_date: datetime) -> Dict:
        """
        Check if trading is allowed based on all risk controls
        
        Args:
            account_balance: Current account balance
            current_date: Current date
            
        Returns:
            Dictionary with trading permission and reason
        """
        # Check daily drawdown
        if not self.check_daily_drawdown(account_balance, current_date):
            return {
                'allowed': False,
                'reason': 'Daily drawdown limit exceeded'
            }
        
        # Check total drawdown
        if not self.check_total_drawdown(account_balance):
            return {
                'allowed': False,
                'reason': 'Total drawdown limit exceeded'
            }
        
        return {
            'allowed': True,
            'reason': 'All risk checks passed'
        }
    
    def update_daily_pnl(self, pnl: float):
        """
        Update daily P&L tracking
        
        Args:
            pnl: Profit/Loss from closed trade
        """
        self.daily_pnl += pnl
    
    def get_statistics(self, account_balance: float) -> Dict:
        """
        Get current risk statistics
        
        Args:
            account_balance: Current account balance
            
        Returns:
            Dictionary with risk statistics
        """
        daily_dd = 0.0
        if self.daily_start_balance > 0:
            daily_dd = (self.daily_start_balance - account_balance) / self.daily_start_balance
        
        total_dd = 0.0
        if self.peak_balance > 0:
            total_dd = (self.peak_balance - account_balance) / self.peak_balance
        
        return {
            'daily_drawdown': daily_dd,
            'daily_drawdown_limit': self.max_daily_drawdown,
            'total_drawdown': total_dd,
            'total_drawdown_limit': self.max_total_drawdown,
            'daily_pnl': self.daily_pnl,
            'peak_balance': self.peak_balance,
            'current_balance': account_balance
        }
