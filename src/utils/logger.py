"""
Logging utilities for the trading bot
"""
import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = 'TradingBot', level: str = 'INFO', 
                log_file: str = None, console: bool = True) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        console: Enable console output
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger
