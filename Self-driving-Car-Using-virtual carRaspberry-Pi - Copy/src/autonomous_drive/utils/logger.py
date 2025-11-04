"""
Centralized Logging System
Provides consistent logging across all modules
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class VehicleLogger:
    """
    Centralized logger for the autonomous vehicle system.
    Provides both file and console logging with rotation support.
    """
    
    _loggers = {}
    
    @staticmethod
    def get_logger(name: str, log_level: str = 'INFO') -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name (str): Logger name (typically __name__)
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            logging.Logger: Configured logger instance
        """
        if name in VehicleLogger._loggers:
            return VehicleLogger._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level))
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # File handler with rotation
        log_file = f'logs/vehicle_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        VehicleLogger._loggers[name] = logger
        return logger


# Convenience function for quick access
def get_logger(name: str, log_level: str = 'INFO') -> logging.Logger:
    """
    Convenience function to get a logger.
    
    Args:
        name (str): Logger name
        log_level (str): Logging level
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return VehicleLogger.get_logger(name, log_level)

