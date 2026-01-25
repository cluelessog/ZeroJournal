"""
Centralized logging utility for ZeroJournal
Replaces print() statements with proper logging
"""
import logging
import sys
from pathlib import Path


def setup_logger(name: str = "zerojournal", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name (default: "zerojournal")
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '[%(levelname)s] %(name)s: %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Create default logger instance
logger = setup_logger()
