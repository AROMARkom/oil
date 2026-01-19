"""
Configuration management for WTI Oil Trading Bot
"""
import os
import yaml
from typing import Dict, Any
from pathlib import Path


class Config:
    """Configuration manager for the trading bot"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            # Default to config/config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation)
        
        Args:
            key: Configuration key (e.g., 'risk.max_risk_per_trade')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def symbol(self) -> str:
        """Get trading symbol"""
        return self.get('symbol', 'WTI')
    
    @property
    def timeframe(self) -> str:
        """Get trading timeframe"""
        return self.get('timeframe', 'M15')
    
    @property
    def max_risk_per_trade(self) -> float:
        """Get max risk per trade"""
        return self.get('risk.max_risk_per_trade', 0.02)
    
    @property
    def atr_period(self) -> int:
        """Get ATR period"""
        return self.get('risk.atr_period', 14)
    
    @property
    def stop_loss_atr_multiple(self) -> float:
        """Get stop loss ATR multiple"""
        return self.get('risk.stop_loss_atr_multiple', 2.0)
    
    @property
    def magic_number(self) -> int:
        """Get MetaTrader magic number"""
        return self.get('metatrader.magic_number', 987654)
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
