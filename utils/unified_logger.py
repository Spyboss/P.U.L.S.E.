"""
Unified logging system for P.U.L.S.E.
Provides a single, consistent logging interface with deduplication and OpenTelemetry integration
"""

import os
import sys
import time
import logging
import traceback
import structlog
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from functools import lru_cache

# Import OpenTelemetry modules with fallback to dummy implementations
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

# Set up default log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Default log file
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "pulse.log")

# Global log cache to prevent duplicate messages
_log_cache = {}
_LOG_CACHE_TTL = 60  # seconds - increased to prevent more duplicates
_LOG_CACHE_COUNTS = {}  # Track counts of repeated messages
_STARTUP_MESSAGES = set()  # Track startup messages to prevent duplicates

# Generate a unique instance ID for this process
INSTANCE_ID = str(uuid.uuid4())[:8]

def configure_logging(log_level=logging.INFO, log_file=DEFAULT_LOG_FILE, console_output=True, enable_telemetry=False):
    """
    Configure the unified logging system with OpenTelemetry integration

    Args:
        log_level: Logging level (default: INFO)
        log_file: Log file path (default: logs/pulse.log)
        console_output: Whether to output logs to console (default: True)
        enable_telemetry: Whether to enable OpenTelemetry (default: False)

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
            console_handler.setLevel(logging.WARNING)  # Console only gets WARNING and above
            console_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s')
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # Initialize OpenTelemetry if available and enabled
        if OPENTELEMETRY_AVAILABLE and enable_telemetry:
            _init_opentelemetry()

        # Define structlog processors
        processors = [
            # Add instance ID to each log entry
            _add_instance_id,
            # Add timestamps to each log entry
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            # Add log level to each log entry
            structlog.processors.add_log_level,
            # Format exceptions in a readable way
            structlog.processors.format_exc_info,
            # Add source file and line numbers for debugging
            structlog.processors.StackInfoRenderer(),
        ]

        # Add OpenTelemetry processor if available and enabled
        if OPENTELEMETRY_AVAILABLE and enable_telemetry:
            processors.append(_opentelemetry_processor)

        # Add JSON renderer as the final processor
        processors.append(structlog.processors.JSONRenderer())

        # Configure structlog
        structlog.configure(
            processors=processors,
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
            log_file=log_file,
            telemetry_enabled=OPENTELEMETRY_AVAILABLE and enable_telemetry)

        return True
    except Exception as e:
        print(f"Error configuring unified logging: {str(e)}")
        traceback.print_exc()
        return False

def _add_instance_id(logger, method_name, event_dict):
    """Add instance ID to the log entry"""
    event_dict["instance_id"] = INSTANCE_ID
    return event_dict

def _opentelemetry_processor(logger, method_name, event_dict):
    """Add OpenTelemetry trace context to the log entry"""
    if not OPENTELEMETRY_AVAILABLE:
        return event_dict

    # Get current span context
    span_context = trace.get_current_span().get_span_context()

    # Add trace and span IDs if available
    if span_context.is_valid:
        event_dict["trace_id"] = format(span_context.trace_id, "032x")
        event_dict["span_id"] = format(span_context.span_id, "016x")

    return event_dict

def _init_opentelemetry():
    """Initialize OpenTelemetry"""
    if not OPENTELEMETRY_AVAILABLE:
        return

    # Create resource with service info
    resource = Resource.create({
        "service.name": "pulse",
        "service.instance.id": INSTANCE_ID,
        "deployment.environment": os.environ.get("PULSE_ENVIRONMENT", "development")
    })

    # Create and set tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Add console exporter for development
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    tracer_provider.add_span_processor(console_processor)

    # Add OTLP exporter if configured
    otlp_endpoint = os.environ.get("PULSE_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        tracer_provider.add_span_processor(otlp_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)

class UnifiedLogger:
    """
    Unified logger for P.U.L.S.E. with deduplication and OpenTelemetry integration
    """

    def __init__(self, name, log_level=None):
        """
        Initialize the unified logger

        Args:
            name: Logger name
            log_level: Optional log level override (not used, kept for backward compatibility)
        """
        self.name = name
        self.logger = structlog.get_logger(name)

        # Create OpenTelemetry tracer if available
        self.tracer = None
        if OPENTELEMETRY_AVAILABLE:
            try:
                self.tracer = trace.get_tracer(name)
            except Exception:
                # Ignore errors in getting tracer
                pass

    def _should_log(self, message, level):
        """
        Check if a message should be logged (deduplication)

        Args:
            message: Log message
            level: Log level

        Returns:
            True if the message should be logged, False otherwise
        """
        # Skip common startup messages that tend to be duplicated
        lower_msg = message.lower()

        # Aggressively filter initialization and startup messages
        if any(keyword in lower_msg for keyword in [
            "initialized",
            "initialization",
            "starting",
            "started",
            "connected to",
            "optimized",
            "created or verified",
            "loaded",
            "configured"
        ]):
            # Create a unique key for this logger, message and level
            startup_key = f"{self.name}:{message}"

            # If we've seen this startup message before, skip it
            if startup_key in _STARTUP_MESSAGES:
                return False

            # Otherwise, mark it as seen and allow it once
            _STARTUP_MESSAGES.add(startup_key)

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

                # For error messages, log once every 5 occurrences as a summary
                if level in ["ERROR", "WARNING"] and count % 5 == 0:
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

    def _create_span(self, level, message, kwargs):
        """
        Create an OpenTelemetry span for the log message if telemetry is available

        Args:
            level: Log level
            message: Log message
            kwargs: Additional context

        Returns:
            Span or None
        """
        if not OPENTELEMETRY_AVAILABLE or self.tracer is None:
            return None

        try:
            # Only create spans for warnings, errors, and critical logs
            if level not in ["WARNING", "ERROR", "CRITICAL"]:
                return None

            # Create a span for the log message
            span = self.tracer.start_span(
                name=f"log.{level.lower()}",
                attributes={
                    "log.message": message,
                    "log.level": level,
                    "log.logger": self.name,
                    # Add additional attributes from kwargs (only simple types)
                    **{f"log.context.{k}": v for k, v in kwargs.items()
                       if isinstance(v, (str, int, float, bool, type(None)))}
                }
            )

            return span
        except Exception:
            # Ignore errors in creating span
            return None

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
            # Create span for warning
            span = self._create_span("WARNING", message, kwargs)

            try:
                self.logger.warning(message, *args, **kwargs)
            finally:
                # End span if created
                if span:
                    span.end()

    def error(self, message, *args, exc_info=False, **kwargs):
        """Log an error message with structured context and optional exception info."""
        if self._should_log(message, "ERROR"):
            # Create span for error
            span = self._create_span("ERROR", message, kwargs)

            try:
                if exc_info:
                    kwargs['exc_info'] = True

                    # Record exception in span if available
                    if span and 'exc_info' in kwargs and kwargs['exc_info'] is not True:
                        span.record_exception(kwargs['exc_info'])

                self.logger.error(message, *args, **kwargs)
            finally:
                # End span if created
                if span:
                    span.end()

    def critical(self, message, *args, exc_info=True, **kwargs):
        """Log a critical message with structured context and exception info."""
        if self._should_log(message, "CRITICAL"):
            # Create span for critical error
            span = self._create_span("CRITICAL", message, kwargs)

            try:
                if exc_info:
                    kwargs['exc_info'] = True

                    # Record exception in span if available
                    if span and 'exc_info' in kwargs and kwargs['exc_info'] is not True:
                        span.record_exception(kwargs['exc_info'])

                self.logger.critical(message, *args, **kwargs)
            finally:
                # End span if created
                if span:
                    span.end()

    def exception(self, message, *args, **kwargs):
        """Log an exception with structured context and traceback."""
        if self._should_log(message, "ERROR"):
            # Create span for exception
            span = self._create_span("ERROR", message, kwargs)

            try:
                self.logger.exception(message, *args, **kwargs)
            finally:
                # End span if created
                if span:
                    span.end()

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
