"""Structured logging system with console output and rotating file handlers."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys

def setup_logger(name: str = "stock_agent", log_file: str = "data/logs/stock_agent.log", level: str = "INFO") -> logging.Logger:
    """Configures and returns a logger instance with rotating file and console handlers.
    
    Args:
        name: Logger name.
        log_file: Path to log file.
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        logging.Logger instance.
    """
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if logger is already set up
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating File Handler (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Primary logger instance for the application
logger = setup_logger()
