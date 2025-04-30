"""
Enhanced logging system for P.U.L.S.E.
Provides deduplication and centralized logging
"""

import logging
import os
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Configure base logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Global log cache to prevent duplicate messages
_log_cache = {}
_LOG_CACHE_TTL = 30  # seconds - increased to prevent initialization duplicates
_LOG_CACHE_COUNTS = {}  # Track counts of repeated messages

class PulseLogger:
    """Enhanced logger for P.U.L.S.E. with deduplication"""

    def __init__(self, name, log_file=None):
        """
        Initialize the logger

        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.name = name
        self.logger = logging.getLogger(name)

        # Only configure if not already configured
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler (if specified)
            if log_file:
                file_path = os.path.join(LOG_DIR, log_file)
            else:
                file_path = os.path.join(LOG_DIR, f"{name.lower().replace(' ', '_')}.log")

            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(name)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def _should_log(self, message, level):
        """
        Check if a message should be logged (deduplication)

        Args:
            message: Log message
            level: Log level

        Returns:
            True if the message should be logged, False otherwise
        """
        # Create a unique key for this logger, message and level
        cache_key = f"{self.name}:{level}:{message}"

        # Check if the message was recently logged
        current_time = time.time()
        if cache_key in _log_cache:
            last_time, count = _log_cache[cache_key]

            # If the message was logged recently, update the count and skip
            if current_time - last_time < _LOG_CACHE_TTL:
                _log_cache[cache_key] = (last_time, count + 1)
                _LOG_CACHE_COUNTS[cache_key] = count + 1

                # For initialization messages, use a longer TTL to prevent duplicates
                if "initialized" in message.lower():
                    return False

                # For other messages, log once every 10 occurrences as a summary
                if count % 10 == 0:
                    self.logger.info(f"Message repeated {count} times: {message}")

                return False

        # Update the cache and log the message
        _log_cache[cache_key] = (current_time, 1)
        _LOG_CACHE_COUNTS[cache_key] = 1

        # Clean up old cache entries
        current_time = time.time()
        for key in list(_log_cache.keys()):
            if current_time - _log_cache[key][0] > _LOG_CACHE_TTL:
                # Log a summary for frequently repeated messages before removing
                if key in _LOG_CACHE_COUNTS and _LOG_CACHE_COUNTS[key] > 5:
                    count = _LOG_CACHE_COUNTS[key]
                    msg = key.split(":", 2)[2]  # Extract the message part
                    self.logger.info(f"Summary: Message repeated {count} times: {msg}")

                # Remove from caches
                del _log_cache[key]
                if key in _LOG_CACHE_COUNTS:
                    del _LOG_CACHE_COUNTS[key]

        return True

    def debug(self, message):
        """Log a debug message"""
        if self._should_log(message, "DEBUG"):
            self.logger.debug(message)

    def info(self, message):
        """Log an info message"""
        if self._should_log(message, "INFO"):
            self.logger.info(message)

    def warning(self, message):
        """Log a warning message"""
        if self._should_log(message, "WARNING"):
            self.logger.warning(message)

    def error(self, message):
        """Log an error message"""
        if self._should_log(message, "ERROR"):
            self.logger.error(message)

    def critical(self, message):
        """Log a critical message"""
        if self._should_log(message, "CRITICAL"):
            self.logger.critical(message)

def get_logger(name):
    """
    Get a logger instance

    Args:
        name: Logger name

    Returns:
        PulseLogger instance
    """
    return PulseLogger(name)
