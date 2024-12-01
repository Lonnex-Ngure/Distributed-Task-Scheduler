# src/utils/logger.py

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file='app.log', level=logging.INFO):
    """Configure and return a logger instance with both file and console handlers"""
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and configure file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Create and configure logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger('distributed_scheduler')