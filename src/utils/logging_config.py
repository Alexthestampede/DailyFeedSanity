"""
Logging configuration for RSS Feed Processor
"""
import logging
import os
from datetime import datetime
from ..config import LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def setup_logging(debug=False):
    """
    Setup logging to both file and console.

    Args:
        debug: If True, set log level to DEBUG

    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Set log level
    level = logging.DEBUG if debug else getattr(logging, LOG_LEVEL)

    # Create logger
    logger = logging.getLogger('rss_processor')
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_filename = os.path.join(LOG_DIR, f"rss_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Log file: {log_filename}")

    return logger


def get_logger(name):
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f'rss_processor.{name}')
