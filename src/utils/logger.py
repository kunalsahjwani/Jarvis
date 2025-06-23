# src/utils/logger.py - Simple Interview-Appropriate Logger
"""
Simple logging configuration for Steve Connect
Basic file logging with timestamps - focused on functionality over infrastructure
"""

import logging
import os
from datetime import datetime

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Simple log file with date
LOG_FILE = f"{datetime.now().strftime('%Y_%m_%d')}.log"
LOG_FILE_PATH = os.path.join("logs", LOG_FILE)

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()  # Also log to console for development
    ]
)

def get_logger(name: str) -> logging.Logger:
    """Get a simple logger for the given module"""
    return logging.getLogger(name)