"""
Reddit Radar - Logging Configuration
===================================

Centralized logging setup for the Reddit Radar application.

Author: Rohan Nair
Date: 20250910
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logger(name: str, 
                 log_file: Optional[str] = None, 
                 level: str = 'INFO',
                 max_bytes: int = 10_000_000,  # 10MB
                 backup_count: int = 5) -> logging.Logger:
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        log_file: Path to log file (optional)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_default_logger() -> logging.Logger:
    """
    Get default logger for Reddit Radar application
    
    Returns:
        Default configured logger
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/reddit_radar.log')
    
    return setup_logger('reddit_radar', log_file, log_level)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger


def log_execution_time(func):
    """
    Decorator to log function execution time
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that logs execution time
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = setup_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    
    return wrapper


def setup_root_logger(level: str = 'WARNING') -> None:
    """
    Configure root logger to avoid spam from third-party libraries
    
    Args:
        level: Root logging level
    """
    logging.basicConfig(level=getattr(logging, level.upper()))
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('prawcore').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


# Initialize root logger when module is imported
setup_root_logger()


if __name__ == "__main__":
    # Test logging setup
    test_logger = setup_logger('test', 'logs/test.log', 'DEBUG')
    
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    
    print("Logging test complete - check logs/test.log")