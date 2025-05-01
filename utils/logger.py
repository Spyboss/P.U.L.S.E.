"""
Structured logging utilities for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides consistent logging across the application using structlog
"""

import os
import logging
import sys
from datetime import datetime
import traceback
import structlog
from functools import lru_cache

# Set up default log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# Default log file
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "pulse.log")

def ensure_log_directory_exists():
    """Ensure the log directory exists"""
    os.makedirs(LOG_DIR, exist_ok=True)

def configure_structlog():
    """Configure structlog with standard processors"""
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

def configure_file_logging(log_level=logging.INFO, log_file=DEFAULT_LOG_FILE):
    """Configure file-based logging for the application"""
    # Ensure the log directory exists
    ensure_log_directory_exists()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Create file handler with rotation
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console gets INFO and above

        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        return True
    except Exception as e:
        print(f"Error configuring logging: {str(e)}")
        traceback.print_exc()
        return False

def setup_logger(log_level=logging.INFO):
    """
    Set up the application logger with structlog

    Args:
        log_level: Logging level (default: INFO)

    Returns:
        bool: True if setup was successful
    """
    try:
        # Configure structlog
        configure_structlog()

        # Configure file logging
        configure_file_logging(log_level)

        # Create a sample log entry to verify configuration
        logger = structlog.get_logger("pulse")
        logger.info("Logging initialized",
            level=logging.getLevelName(log_level),
            log_file=DEFAULT_LOG_FILE)

        return True
    except Exception as e:
        print(f"Error setting up logger: {str(e)}")
        traceback.print_exc()
        return False

@lru_cache(maxsize=32)
def get_logger(name="pulse"):
    """
    Get a logger instance with the given name

    Args:
        name: Logger name for component identification

    Returns:
        structlog.BoundLogger: A configured logger instance
    """
    return structlog.get_logger(name)

class PulseLogger:
    """
    Centralized logger for P.U.L.S.E. using structlog
    Provides structured logging with JSON output and no duplicates
    """

    def __init__(self, name, log_level=None, log_file=None, console_output=True):
        """Initialize the structured logger with specified name."""
        # We ignore log_file and console_output as structlog is configured globally
        self.logger = structlog.get_logger(name)
        self.name = name

    def debug(self, message, *args, **kwargs):
        """Log a debug message with structured context."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """Log an info message with structured context."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """Log a warning message with structured context."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, exc_info=False, **kwargs):
        """Log an error message with structured context and optional exception info."""
        if exc_info:
            kwargs['exc_info'] = True
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, exc_info=True, **kwargs):
        """Log a critical message with structured context and exception info."""
        if exc_info:
            kwargs['exc_info'] = True
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        """Log an exception with structured context and traceback."""
        self.logger.exception(message, *args, **kwargs)

    @staticmethod
    def format_error(e):
        """Format an exception for logging and user display."""
        error_type = type(e).__name__
        error_msg = str(e)
        tb_str = traceback.format_exc()
        return f"{error_type}: {error_msg}\n{tb_str}"

# Create a default logger instance
default_logger = PulseLogger("PULSE")