"""
Logging configuration for RAG Chatbot Application
Provides structured logging with file and console handlers
"""
import logging
import os
from datetime import datetime

def setup_logger(name, log_file=None, level=None):
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Log level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create default application logger
app_logger = setup_logger('rag_chatbot', log_file='logs/app.log')
