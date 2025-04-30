"""
Unified logging system for P.U.L.S.E.
Provides a single, consistent logging interface with deduplication
"""

import os
import sys
import time
import logging
import traceback
import structlog
from datetime import datetime
from logging.handlers import RotatingFileHandler
from functools import lru_cache

# Set up default log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Default log file
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "pulse.log")

# Global log cache to prevent duplicate messages
_log_cache = {}
_LOG_CACHE_TTL = 30  # seconds
_LOG_CACHE_COUNTS = {}  # Track counts of repeated messages

def configure_logging(log_level=logging.INFO, log_file=DEFAULT_LOG_FILE, console_output=True):
    """
    Configure the unified logging system
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Log file path (default: logs/pulse.log)
        console_output: Whether to output logs to console (default: True)
        
    Returns:
        bool: True if setup was successful
    """
    try:
        # Ensure the log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create file handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(name)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Create console handler if requested
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)  # Console gets INFO and above
            console_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s')
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Configure structlog
        structlog.configure(
            processors=[
                # Add timestamps to each log entry
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                # Add log level to each log entry
                structlog.processors.add_log_level,
                # Format exceptions in a readable way
                structlog.processors.format_exc_info,
                # Add source file and line numbers for debugging
                structlog.processors.StackInfoRenderer(),
                # Format as JSON for easier parsing
                structlog.processors.JSONRenderer()
            ],
            # Configure logger factory (where logs are sent)
            logger_factory=structlog.stdlib.LoggerFactory(),
            # Attach context to loggers
            wrapper_class=structlog.stdlib.BoundLogger,
            # Use dict for context
            context_class=dict,
            # Set default log level to INFO
            cache_logger_on_first_use=True,
        )
        
        # Create a sample log entry to verify configuration
        logger = structlog.get_logger("unified_logger")
        logger.info("Unified logging system initialized", 
            level=logging.getLevelName(log_level), 
            log_file=log_file)
        
        return True
    except Exception as e:
        print(f"Error configuring unified logging: {str(e)}")
        traceback.print_exc()
        return False

class UnifiedLogger:
    """
    Unified logger for P.U.L.S.E. with deduplication
    """
    
    def __init__(self, name, log_level=None):
        """
        Initialize the unified logger
        
        Args:
            name: Logger name
            log_level: Optional log level override
        """
        self.name = name
        self.logger = structlog.get_logger(name)
        
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
    
    def debug(self, message, *args, **kwargs):
        """Log a debug message with structured context."""
        if self._should_log(message, "DEBUG"):
            self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """Log an info message with structured context."""
        if self._should_log(message, "INFO"):
            self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Log a warning message with structured context."""
        if self._should_log(message, "WARNING"):
            self.logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, exc_info=False, **kwargs):
        """Log an error message with structured context and optional exception info."""
        if self._should_log(message, "ERROR"):
            if exc_info:
                kwargs['exc_info'] = True
            self.logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, exc_info=True, **kwargs):
        """Log a critical message with structured context and exception info."""
        if self._should_log(message, "CRITICAL"):
            if exc_info:
                kwargs['exc_info'] = True
            self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        """Log an exception with structured context and traceback."""
        if self._should_log(message, "ERROR"):
            self.logger.exception(message, *args, **kwargs)

@lru_cache(maxsize=32)
def get_logger(name="pulse"):
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name for component identification
        
    Returns:
        UnifiedLogger: A configured logger instance
    """
    return UnifiedLogger(name)

# Initialize logging when the module is imported
configure_logging()
