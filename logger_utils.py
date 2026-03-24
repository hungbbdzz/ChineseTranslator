# -*- coding: utf-8 -*-
"""
Logging utility module for Chinese Translator
Provides centralized logging configuration for the application
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Log file path
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'translator.log')

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a logger with both file and console handlers.
    
    Args:
        name: Name of the logger (usually __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10MB max, 5 backup files)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails, continue with console only
        print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)
    
    # Console handler (only for ERROR and above to avoid spam)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        Logger instance
    """
    return setup_logger(name)


def set_log_level(level: int) -> None:
    """
    Set log level for all existing loggers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    for logger in logging.getLogger().root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)


# Convenience function for quick logging
log = get_logger(__name__)
