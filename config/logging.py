"""
Logging configuration for Mini Video Factory

Provides structured logging for application monitoring and debugging.
"""

import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(app):
    """
    Configure logging for the Flask application
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.environ.get('LOG_DIR', './logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set logging level from environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for application logs
    app_log_file = os.path.join(log_dir, 'app.log')
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for error logs
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    
    # Set app logger level
    app.logger.setLevel(numeric_level)
    
    # Configure specific loggers
    configure_component_loggers()
    
    app.logger.info(f"Logging configured - Level: {log_level}, Directory: {log_dir}")

def configure_component_loggers():
    """Configure logging for specific application components"""
    
    # Video processing logger
    processing_logger = logging.getLogger('video_processing')
    processing_logger.setLevel(logging.INFO)
    
    # Authentication logger
    auth_logger = logging.getLogger('authentication')
    auth_logger.setLevel(logging.INFO)
    
    # Storage logger
    storage_logger = logging.getLogger('storage')
    storage_logger.setLevel(logging.INFO)
    
    # Suppress verbose third-party logs
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def get_logger(name):
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)