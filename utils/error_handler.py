"""
Comprehensive Error Handling Framework for P.U.L.S.E.
Provides centralized error handling, logging, and recovery
"""

import os
import sys
import traceback
import asyncio
import functools
import structlog
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Union, Callable, Type, Awaitable, Tuple, TypeVar

from utils.error_taxonomy import (
    ErrorInfo, ErrorCategory, ErrorType, ErrorSource, ErrorSeverity,
    classify_exception, classify_error_dict, RetryStrategy
)
from utils.retry import retry, retry_async, retry_sync, RetryResult
from utils.circuit_breaker import CircuitBreaker, circuit_breaker, get_circuit_breaker, create_circuit_breaker

# Import telemetry if available
try:
    from utils.telemetry import get_telemetry
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

# Logger
logger = structlog.get_logger("error_handler")

# Type variables
T = TypeVar('T')

# Global error registry for tracking error patterns
_error_registry: Dict[str, Dict[str, Any]] = {}

# Error handler configuration
ERROR_HANDLER_CONFIG = {
    "log_all_errors": False,  # Changed from True to reduce log noise
    "track_error_patterns": True,
    "max_tracked_errors": 500,  # Reduced from 1000
    "error_aggregation_window": 3600,  # 1 hour
    "notify_on_critical": True,
    "error_notification_cooldown": 600,  # Increased from 300 to 600 (10 minutes)
    "error_notification_threshold": 10,  # Increased from 5 to 10
    "suppress_repetitive_errors": True,  # Suppress repetitive errors
    "repetitive_error_cooldown": 300,  # Increased from 60 to 300 (5 minutes)
    "suppress_dns_timeout_errors": True,  # Suppress DNS timeout errors
    "suppress_connection_errors": True,  # Suppress connection errors
    "suppress_mongodb_errors": True,  # Added to suppress MongoDB connection errors
    "log_suppressed_errors_count": True,  # Log count of suppressed errors instead of each one
}

# Last notification timestamps to prevent notification spam
_last_notification_times: Dict[str, float] = {}

class ErrorHandler:
    """
    Comprehensive error handler for P.U.L.S.E.
    """

    def __init__(self):
        """Initialize error handler"""
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, List[float]] = {}
        self.last_cleanup = time.time()

    def handle_exception(
        self,
        exception: Exception,
        operation: Optional[str] = None,
        source: ErrorSource = ErrorSource.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        notify: bool = False,
        reraise: bool = True
    ) -> ErrorInfo:
        """
        Handle an exception

        Args:
            exception: The exception to handle
            operation: The operation being performed when the exception occurred
            source: The source of the exception
            context: Additional context information
            notify: Whether to send a notification for this error
            reraise: Whether to re-raise the exception after handling

        Returns:
            ErrorInfo object with classification

        Raises:
            The original exception if reraise is True
        """
        # Classify the exception
        error_info = classify_exception(
            exception=exception,
            operation=operation,
            source=source,
            context=context
        )

        # Set timestamp
        error_info.timestamp = datetime.now()

        # Log the error
        self._log_error(error_info)

        # Track error pattern
        if ERROR_HANDLER_CONFIG["track_error_patterns"]:
            self._track_error(error_info)

        # Send notification if requested
        if notify or (ERROR_HANDLER_CONFIG["notify_on_critical"] and
                     error_info.severity == ErrorSeverity.CRITICAL):
            self._send_notification(error_info)

        # Record in telemetry if available
        if TELEMETRY_AVAILABLE:
            telemetry = get_telemetry()
            telemetry.record_error(
                error_type=error_info.error_type,
                attributes={
                    "source": error_info.source,
                    "category": error_info.category,
                    "severity": error_info.severity,
                    "operation": operation or "unknown"
                }
            )

        # Periodically clean up old error records
        self._cleanup_old_errors()

        # Re-raise the exception if requested
        if reraise:
            raise exception

        return error_info

    def handle_error(
        self,
        error_dict: Dict[str, Any],
        notify: bool = False
    ) -> ErrorInfo:
        """
        Handle an error dictionary

        Args:
            error_dict: The error dictionary to handle
            notify: Whether to send a notification for this error

        Returns:
            ErrorInfo object with classification
        """
        # Classify the error dictionary
        error_info = classify_error_dict(error_dict)

        # Set timestamp
        error_info.timestamp = datetime.now()

        # Log the error
        self._log_error(error_info)

        # Track error pattern
        if ERROR_HANDLER_CONFIG["track_error_patterns"]:
            self._track_error(error_info)

        # Send notification if requested
        if notify or (ERROR_HANDLER_CONFIG["notify_on_critical"] and
                     error_info.severity == ErrorSeverity.CRITICAL):
            self._send_notification(error_info)

        # Record in telemetry if available
        if TELEMETRY_AVAILABLE:
            telemetry = get_telemetry()
            telemetry.record_error(
                error_type=error_info.error_type,
                attributes={
                    "source": error_info.source,
                    "category": error_info.category,
                    "severity": error_info.severity,
                    "operation": error_info.operation or "unknown"
                }
            )

        # Periodically clean up old error records
        self._cleanup_old_errors()

        return error_info

    def _log_error(self, error_info: ErrorInfo):
        """
        Log an error with appropriate severity

        Args:
            error_info: The error information to log
        """
        if not ERROR_HANDLER_CONFIG["log_all_errors"]:
            return

        # Check if we should suppress this error
        if ERROR_HANDLER_CONFIG["suppress_repetitive_errors"]:
            # Create a key for this error type
            error_key = f"{error_info.source}:{error_info.category}:{error_info.error_type}"

            # Check if we've logged this error recently
            current_time = time.time()
            if error_key in _last_notification_times:
                time_since_last = current_time - _last_notification_times[error_key]
                if time_since_last < ERROR_HANDLER_CONFIG["repetitive_error_cooldown"]:
                    # Too soon to log another error of this type
                    return

            # Update last notification time
            _last_notification_times[error_key] = current_time

        # Check if this is a DNS timeout error that should be suppressed
        if ERROR_HANDLER_CONFIG["suppress_dns_timeout_errors"]:
            if "DNS operation timed out" in error_info.message or "resolution lifetime expired" in error_info.message:
                # Only log at debug level instead of error
                logger.debug(f"Suppressed DNS timeout error: {error_info.message[:50]}...")
                return

        # Check if this is a MongoDB error that should be suppressed
        if ERROR_HANDLER_CONFIG.get("suppress_mongodb_errors", False):
            if any(term in error_info.message for term in ["MongoDB", "mongodb", "mongo"]):
                # Only log once per minute
                current_time = time.time()
                error_key = f"mongodb_{error_info.source}_{error_info.error_type}"

                if error_key in _last_notification_times:
                    last_time = _last_notification_times[error_key]
                    if current_time - last_time < ERROR_HANDLER_CONFIG.get("repetitive_error_cooldown", 300):
                        return

                _last_notification_times[error_key] = current_time
                logger.warning(f"MongoDB error: {error_info.message[:50]}...")
                return

        # Check if this is a connection error that should be suppressed
        if ERROR_HANDLER_CONFIG["suppress_connection_errors"]:
            connection_error_patterns = [
                "connection refused",
                "connection error",
                "connection timeout",
                "connection reset",
                "failed to connect",
                "connection closed",
                "not connected",
                "server selection timeout"
            ]

            for pattern in connection_error_patterns:
                if pattern in error_info.message.lower():
                    # Only log at debug level instead of error
                    logger.debug(f"Suppressed connection error: {error_info.message[:100]}...")
                    return

        # Log with appropriate severity
        error_info.log()

    def _track_error(self, error_info: ErrorInfo):
        """
        Track error patterns

        Args:
            error_info: The error information to track
        """
        # Create a key for this error type
        error_key = f"{error_info.source}:{error_info.category}:{error_info.error_type}"

        # Update error counts
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
            self.error_timestamps[error_key] = []

        self.error_counts[error_key] += 1
        self.error_timestamps[error_key].append(time.time())

        # Limit the number of timestamps we store
        if len(self.error_timestamps[error_key]) > ERROR_HANDLER_CONFIG["max_tracked_errors"]:
            self.error_timestamps[error_key] = self.error_timestamps[error_key][-ERROR_HANDLER_CONFIG["max_tracked_errors"]:]

        # Update global error registry
        if error_key not in _error_registry:
            _error_registry[error_key] = {
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "source": error_info.source,
                "category": error_info.category,
                "error_type": error_info.error_type,
                "examples": []
            }

        _error_registry[error_key]["count"] += 1
        _error_registry[error_key]["last_seen"] = datetime.now().isoformat()

        # Store example errors (limited to 10)
        if len(_error_registry[error_key]["examples"]) < 10:
            example = {
                "message": error_info.message,
                "timestamp": datetime.now().isoformat()
            }

            if error_info.operation:
                example["operation"] = error_info.operation

            if error_info.status_code:
                example["status_code"] = error_info.status_code

            _error_registry[error_key]["examples"].append(example)

    def _send_notification(self, error_info: ErrorInfo):
        """
        Send a notification for an error

        Args:
            error_info: The error information to notify about
        """
        # Create a key for this error type
        error_key = f"{error_info.source}:{error_info.category}:{error_info.error_type}"

        # Check if we've sent a notification for this error type recently
        current_time = time.time()
        if error_key in _last_notification_times:
            time_since_last = current_time - _last_notification_times[error_key]
            if time_since_last < ERROR_HANDLER_CONFIG["error_notification_cooldown"]:
                # Too soon to send another notification
                return

        # Check if we've seen this error enough times to warrant a notification
        if error_key in self.error_counts:
            # Count recent occurrences (within the last hour)
            recent_count = sum(1 for ts in self.error_timestamps[error_key]
                             if current_time - ts < ERROR_HANDLER_CONFIG["error_aggregation_window"])

            if recent_count < ERROR_HANDLER_CONFIG["error_notification_threshold"]:
                # Not enough occurrences to warrant a notification
                return

        # Update last notification time
        _last_notification_times[error_key] = current_time

        # Log notification
        logger.warning(f"Error notification for {error_key}",
                      error_info=error_info.to_dict(),
                      recent_count=self.error_counts.get(error_key, 0))

        # TODO: Implement actual notification mechanism (email, Slack, etc.)

    def _cleanup_old_errors(self):
        """Clean up old error records"""
        current_time = time.time()

        # Only clean up periodically
        if current_time - self.last_cleanup < 3600:  # 1 hour
            return

        self.last_cleanup = current_time

        # Clean up old timestamps
        for error_key in list(self.error_timestamps.keys()):
            # Keep only timestamps within the aggregation window
            self.error_timestamps[error_key] = [
                ts for ts in self.error_timestamps[error_key]
                if current_time - ts < ERROR_HANDLER_CONFIG["error_aggregation_window"]
            ]

            # If no timestamps remain, remove the error key
            if not self.error_timestamps[error_key]:
                del self.error_timestamps[error_key]
                if error_key in self.error_counts:
                    del self.error_counts[error_key]

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics

        Returns:
            Dictionary with error statistics
        """
        current_time = time.time()

        # Calculate statistics for each error type
        stats = {}
        for error_key, timestamps in self.error_timestamps.items():
            # Count recent occurrences (within the last hour)
            recent_count = sum(1 for ts in timestamps
                             if current_time - ts < ERROR_HANDLER_CONFIG["error_aggregation_window"])

            # Calculate frequency (errors per hour)
            if timestamps:
                oldest_timestamp = min(timestamps)
                newest_timestamp = max(timestamps)
                time_span_hours = (newest_timestamp - oldest_timestamp) / 3600

                if time_span_hours > 0:
                    frequency = len(timestamps) / time_span_hours
                else:
                    frequency = 0
            else:
                frequency = 0

            # Add to stats
            stats[error_key] = {
                "total_count": self.error_counts.get(error_key, 0),
                "recent_count": recent_count,
                "frequency_per_hour": frequency
            }

        return stats


# Global error handler instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance

    Returns:
        ErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_exception(
    exception: Exception,
    operation: Optional[str] = None,
    source: ErrorSource = ErrorSource.UNKNOWN,
    context: Optional[Dict[str, Any]] = None,
    notify: bool = False,
    reraise: bool = True
) -> ErrorInfo:
    """
    Handle an exception using the global error handler

    Args:
        exception: The exception to handle
        operation: The operation being performed when the exception occurred
        source: The source of the exception
        context: Additional context information
        notify: Whether to send a notification for this error
        reraise: Whether to re-raise the exception after handling

    Returns:
        ErrorInfo object with classification

    Raises:
        The original exception if reraise is True
    """
    return get_error_handler().handle_exception(
        exception=exception,
        operation=operation,
        source=source,
        context=context,
        notify=notify,
        reraise=reraise
    )


def handle_error(
    error_dict: Dict[str, Any],
    notify: bool = False
) -> ErrorInfo:
    """
    Handle an error dictionary using the global error handler

    Args:
        error_dict: The error dictionary to handle
        notify: Whether to send a notification for this error

    Returns:
        ErrorInfo object with classification
    """
    return get_error_handler().handle_error(
        error_dict=error_dict,
        notify=notify
    )


def get_error_stats() -> Dict[str, Any]:
    """
    Get error statistics from the global error handler

    Returns:
        Dictionary with error statistics
    """
    return get_error_handler().get_error_stats()


class ErrorHandlerDecorator:
    """
    Decorator for handling exceptions in functions
    """

    def __init__(
        self,
        operation: Optional[str] = None,
        source: ErrorSource = ErrorSource.UNKNOWN,
        notify: bool = False,
        reraise: bool = True,
        with_context: bool = True
    ):
        """
        Initialize error handler decorator

        Args:
            operation: The operation being performed
            source: The source of the operation
            notify: Whether to send a notification for errors
            reraise: Whether to re-raise exceptions after handling
            with_context: Whether to include function arguments in error context
        """
        self.operation = operation
        self.source = source
        self.notify = notify
        self.reraise = reraise
        self.with_context = with_context

    def __call__(self, func):
        """
        Decorate the function

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """
        # Use function name if operation not provided
        operation = self.operation or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create context from function arguments if requested
                context = None
                if self.with_context:
                    context = self._create_context(func, args, kwargs)

                # Handle the exception
                handle_exception(
                    exception=e,
                    operation=operation,
                    source=self.source,
                    context=context,
                    notify=self.notify,
                    reraise=self.reraise
                )

                # If we get here, reraise must be False
                return None

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Create context from function arguments if requested
                context = None
                if self.with_context:
                    context = self._create_context(func, args, kwargs)

                # Handle the exception
                handle_exception(
                    exception=e,
                    operation=operation,
                    source=self.source,
                    context=context,
                    notify=self.notify,
                    reraise=self.reraise
                )

                # If we get here, reraise must be False
                return None

        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def _create_context(self, func, args, kwargs) -> Dict[str, Any]:
        """
        Create context dictionary from function arguments

        Args:
            func: The function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Context dictionary
        """
        context = {}

        # Add keyword arguments
        for key, value in kwargs.items():
            # Only include simple types
            if isinstance(value, (str, int, float, bool, type(None))):
                context[f"arg_{key}"] = value

        # Try to add positional arguments using function signature
        try:
            import inspect
            signature = inspect.signature(func)
            parameters = list(signature.parameters.keys())

            for i, arg in enumerate(args):
                if i < len(parameters):
                    param_name = parameters[i]
                    # Only include simple types
                    if isinstance(arg, (str, int, float, bool, type(None))):
                        context[f"arg_{param_name}"] = arg
        except Exception:
            # Ignore errors in getting function signature
            pass

        return context


def with_error_handling(
    operation: Optional[str] = None,
    source: ErrorSource = ErrorSource.UNKNOWN,
    notify: bool = False,
    reraise: bool = True,
    with_context: bool = True
):
    """
    Decorator for handling exceptions in functions

    Args:
        operation: The operation being performed
        source: The source of the operation
        notify: Whether to send a notification for errors
        reraise: Whether to re-raise exceptions after handling
        with_context: Whether to include function arguments in error context

    Returns:
        Decorated function
    """
    return ErrorHandlerDecorator(
        operation=operation,
        source=source,
        notify=notify,
        reraise=reraise,
        with_context=with_context
    )


class ResilientFunction:
    """
    Decorator for making functions resilient with retry and circuit breaker
    """

    def __init__(
        self,
        operation: Optional[str] = None,
        source: ErrorSource = ErrorSource.UNKNOWN,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_strategy: RetryStrategy = RetryStrategy.JITTERED_BACKOFF,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        with_circuit_breaker: bool = True,
        with_retry: bool = True,
        with_error_handling: bool = True,
        notify_on_failure: bool = False,
        circuit_breaker_name: Optional[str] = None
    ):
        """
        Initialize resilient function decorator

        Args:
            operation: The operation being performed
            source: The source of the operation
            max_retries: Maximum number of retries
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            retry_strategy: Strategy for calculating retry delays
            failure_threshold: Number of consecutive failures before opening circuit
            reset_timeout: Time in seconds before attempting to close circuit
            with_circuit_breaker: Whether to use circuit breaker
            with_retry: Whether to use retry mechanism
            with_error_handling: Whether to use error handling
            notify_on_failure: Whether to send a notification on failure
            circuit_breaker_name: Name for the circuit breaker
        """
        self.operation = operation
        self.source = source
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_strategy = retry_strategy
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.with_circuit_breaker = with_circuit_breaker
        self.with_retry = with_retry
        self.with_error_handling = with_error_handling
        self.notify_on_failure = notify_on_failure
        self.circuit_breaker_name = circuit_breaker_name

    def __call__(self, func):
        """
        Decorate the function

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """
        # Use function name if operation not provided
        operation = self.operation or f"{func.__module__}.{func.__name__}"

        # Use function name for circuit breaker if not provided
        circuit_breaker_name = self.circuit_breaker_name or f"{func.__module__}.{func.__name__}"

        # Get or create circuit breaker
        cb = get_circuit_breaker(circuit_breaker_name)
        if cb is None and self.with_circuit_breaker:
            cb = create_circuit_breaker(
                name=circuit_breaker_name,
                failure_threshold=self.failure_threshold,
                reset_timeout=self.reset_timeout
            )

        # Define the decorated function
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # Apply circuit breaker if enabled
                if self.with_circuit_breaker and cb is not None:
                    # Apply retry if enabled
                    if self.with_retry:
                        result, value = await retry_async(
                            func=lambda: cb.execute_async(func, *args, **kwargs),
                            max_retries=self.max_retries,
                            base_delay=self.base_delay,
                            max_delay=self.max_delay,
                            retry_strategy=self.retry_strategy
                        )

                        if result == RetryResult.SUCCESS:
                            return value
                        else:
                            # Handle the exception
                            if self.with_error_handling:
                                handle_exception(
                                    exception=value,
                                    operation=operation,
                                    source=self.source,
                                    notify=self.notify_on_failure,
                                    reraise=True
                                )
                            raise value
                    else:
                        # No retry, just circuit breaker
                        return await cb.execute_async(func, *args, **kwargs)
                else:
                    # No circuit breaker
                    if self.with_retry:
                        # Apply retry
                        result, value = await retry_async(
                            func=func,
                            max_retries=self.max_retries,
                            base_delay=self.base_delay,
                            max_delay=self.max_delay,
                            retry_strategy=self.retry_strategy,
                            *args, **kwargs
                        )

                        if result == RetryResult.SUCCESS:
                            return value
                        else:
                            # Handle the exception
                            if self.with_error_handling:
                                handle_exception(
                                    exception=value,
                                    operation=operation,
                                    source=self.source,
                                    notify=self.notify_on_failure,
                                    reraise=True
                                )
                            raise value
                    else:
                        # No retry, no circuit breaker
                        return await func(*args, **kwargs)
            except Exception as e:
                # Handle the exception
                if self.with_error_handling:
                    handle_exception(
                        exception=e,
                        operation=operation,
                        source=self.source,
                        notify=self.notify_on_failure,
                        reraise=True
                    )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                # Apply circuit breaker if enabled
                if self.with_circuit_breaker and cb is not None:
                    # Apply retry if enabled
                    if self.with_retry:
                        result, value = retry_sync(
                            func=lambda: cb.execute(func, *args, **kwargs),
                            max_retries=self.max_retries,
                            base_delay=self.base_delay,
                            max_delay=self.max_delay,
                            retry_strategy=self.retry_strategy
                        )

                        if result == RetryResult.SUCCESS:
                            return value
                        else:
                            # Handle the exception
                            if self.with_error_handling:
                                handle_exception(
                                    exception=value,
                                    operation=operation,
                                    source=self.source,
                                    notify=self.notify_on_failure,
                                    reraise=True
                                )
                            raise value
                    else:
                        # No retry, just circuit breaker
                        return cb.execute(func, *args, **kwargs)
                else:
                    # No circuit breaker
                    if self.with_retry:
                        # Apply retry
                        result, value = retry_sync(
                            func=func,
                            max_retries=self.max_retries,
                            base_delay=self.base_delay,
                            max_delay=self.max_delay,
                            retry_strategy=self.retry_strategy,
                            *args, **kwargs
                        )

                        if result == RetryResult.SUCCESS:
                            return value
                        else:
                            # Handle the exception
                            if self.with_error_handling:
                                handle_exception(
                                    exception=value,
                                    operation=operation,
                                    source=self.source,
                                    notify=self.notify_on_failure,
                                    reraise=True
                                )
                            raise value
                    else:
                        # No retry, no circuit breaker
                        return func(*args, **kwargs)
            except Exception as e:
                # Handle the exception
                if self.with_error_handling:
                    handle_exception(
                        exception=e,
                        operation=operation,
                        source=self.source,
                        notify=self.notify_on_failure,
                        reraise=True
                    )
                raise

        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


def resilient(
    operation: Optional[str] = None,
    source: ErrorSource = ErrorSource.UNKNOWN,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_strategy: RetryStrategy = RetryStrategy.JITTERED_BACKOFF,
    failure_threshold: int = 5,
    reset_timeout: float = 60.0,
    with_circuit_breaker: bool = True,
    with_retry: bool = True,
    with_error_handling: bool = True,
    notify_on_failure: bool = False,
    circuit_breaker_name: Optional[str] = None
):
    """
    Decorator for making functions resilient with retry and circuit breaker

    Args:
        operation: The operation being performed
        source: The source of the operation
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_strategy: Strategy for calculating retry delays
        failure_threshold: Number of consecutive failures before opening circuit
        reset_timeout: Time in seconds before attempting to close circuit
        with_circuit_breaker: Whether to use circuit breaker
        with_retry: Whether to use retry mechanism
        with_error_handling: Whether to use error handling
        notify_on_failure: Whether to send a notification on failure
        circuit_breaker_name: Name for the circuit breaker

    Returns:
        Decorated function
    """
    return ResilientFunction(
        operation=operation,
        source=source,
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        retry_strategy=retry_strategy,
        failure_threshold=failure_threshold,
        reset_timeout=reset_timeout,
        with_circuit_breaker=with_circuit_breaker,
        with_retry=with_retry,
        with_error_handling=with_error_handling,
        notify_on_failure=notify_on_failure,
        circuit_breaker_name=circuit_breaker_name
    )
