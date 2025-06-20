# ABOUTME: Logging configuration for different environments with structured formatting
# ABOUTME: Handles log levels, formatters, and output destinations for development and production

import logging
import sys
from typing import Dict, Any
from config import settings

def setup_logging() -> None:
    """Configure logging based on environment settings."""
    
    # Log format for different environments
    if settings.ENVIRONMENT == "production":
        # JSON-like format for production (easier for log aggregation)
        log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    else:
        # More detailed format for development
        log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Reduce noise from external libraries in development
    if settings.ENVIRONMENT == "development":
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)