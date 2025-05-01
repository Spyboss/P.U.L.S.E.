"""
Circuit Breaker Pattern for P.U.L.S.E.
Prevents cascading failures by failing fast when a service is unavailable
"""

import time
import asyncio
import functools
import structlog
from enum import Enum
from typing import Callable, TypeVar, Any, Optional, Dict, List, Union, Awaitable, Type, Tuple
from datetime import datetime, timedelta
import threading

from utils.error_taxonomy import ErrorInfo, classify_exception, ErrorSeverity

# Logger
logger = structlog.get_logger("circuit_breaker")

# Type variables
T = TypeVar('T')

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation, requests are allowed
    OPEN = "open"           # Circuit is open, requests fail fast
    HALF_OPEN = "half_open" # Testing if service is available again


class CircuitBreakerError(Exception):
    """Exception raised when circuit is open"""
    def __init__(self, service: str, opened_at: datetime, failure_count: int, last_exception: Optional[Exception] = None):
        self.service = service
        self.opened_at = opened_at
        self.failure_count = failure_count
        self.last_exception = last_exception
        
        # Calculate how long the circuit has been open
        open_duration = datetime.now() - opened_at
        
        message = (
            f"Circuit breaker for {service} is open. "
            f"Circuit opened {open_duration.total_seconds():.1f} seconds ago "
            f"after {failure_count} consecutive failures."
        )
        
        if last_exception:
            message += f" Last error: {str(last_exception)}"
            
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker implementation
    
    The circuit breaker pattern prevents cascading failures by failing fast
    when a service is unavailable. It has three states:
    
    1. CLOSED: Normal operation, requests are allowed
    2. OPEN: Circuit is open, requests fail fast without calling the service
    3. HALF_OPEN: Testing if service is available again
    
    When in the CLOSED state, if the failure threshold is reached, the circuit
    opens and moves to the OPEN state. When in the OPEN state, after the reset
    timeout expires, the circuit moves to the HALF_OPEN state and allows a
    single request through. If that request succeeds, the circuit closes again.
    If it fails, the circuit opens again and the reset timeout is increased.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        timeout_multiplier: float = 2.0,
        max_timeout: float = 300.0,
        exclude_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Name of the service protected by this circuit breaker
            failure_threshold: Number of consecutive failures before opening circuit
            reset_timeout: Time in seconds before attempting to close circuit
            timeout_multiplier: Factor to increase timeout by on each failure
            max_timeout: Maximum timeout in seconds
            exclude_exceptions: List of exception types that should not count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.timeout_multiplier = timeout_multiplier
        self.max_timeout = max_timeout
        self.exclude_exceptions = exclude_exceptions or []
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.opened_at = None
        self.current_timeout = reset_timeout
        self.last_exception = None
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        logger.info(f"Circuit breaker initialized for {name}",
                   failure_threshold=failure_threshold,
                   reset_timeout=reset_timeout)
    
    def _record_success(self):
        """Record a successful operation"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                # If we were testing the service and it succeeded, close the circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.current_timeout = self.reset_timeout  # Reset timeout
                logger.info(f"Circuit closed for {self.name} after successful test")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    def _record_failure(self, exception: Exception):
        """
        Record a failed operation
        
        Args:
            exception: The exception that occurred
        """
        # Check if this exception type should be excluded
        if any(isinstance(exception, exc_type) for exc_type in self.exclude_exceptions):
            return
        
        with self.lock:
            self.last_exception = exception
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.CLOSED:
                # Increment failure count
                self.failure_count += 1
                
                # Check if we've reached the threshold
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.now()
                    logger.warning(f"Circuit opened for {self.name} after {self.failure_count} consecutive failures",
                                  last_error=str(exception),
                                  exception_type=type(exception).__name__)
            
            elif self.state == CircuitState.HALF_OPEN:
                # If we were testing the service and it failed, open the circuit again
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()
                
                # Increase timeout, but cap at max_timeout
                self.current_timeout = min(self.current_timeout * self.timeout_multiplier, self.max_timeout)
                
                logger.warning(f"Circuit reopened for {self.name} after failed test",
                              last_error=str(exception),
                              exception_type=type(exception).__name__,
                              next_retry_in=self.current_timeout)
    
    def _check_state(self):
        """
        Check the current state of the circuit breaker
        
        Returns:
            True if the request should be allowed, False if it should be blocked
        
        Raises:
            CircuitBreakerError: If the circuit is open
        """
        with self.lock:
            if self.state == CircuitState.CLOSED:
                # Circuit is closed, allow the request
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if the reset timeout has expired
                if self.opened_at and (datetime.now() - self.opened_at).total_seconds() >= self.current_timeout:
                    # Timeout expired, move to half-open state
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit half-open for {self.name}, testing service availability")
                    return True
                else:
                    # Circuit is open and timeout hasn't expired, fail fast
                    raise CircuitBreakerError(
                        service=self.name,
                        opened_at=self.opened_at,
                        failure_count=self.failure_count,
                        last_exception=self.last_exception
                    )
            
            elif self.state == CircuitState.HALF_OPEN:
                # Only allow one request through in half-open state
                # If multiple requests come in while in half-open state,
                # only the first one is allowed through
                raise CircuitBreakerError(
                    service=self.name,
                    opened_at=self.opened_at,
                    failure_count=self.failure_count,
                    last_exception=self.last_exception
                )
    
    def execute(self, func, *args, **kwargs):
        """
        Execute a function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the function
        """
        # Check if the circuit allows this request
        self._check_state()
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Record success
            self._record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            self._record_failure(e)
            
            # Re-raise the exception
            raise
    
    async def execute_async(self, func, *args, **kwargs):
        """
        Execute an async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the function
        """
        # Check if the circuit allows this request
        self._check_state()
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Record success
            self._record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            self._record_failure(e)
            
            # Re-raise the exception
            raise
    
    def reset(self):
        """Reset the circuit breaker to closed state"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.opened_at = None
            self.current_timeout = self.reset_timeout
            self.last_exception = None
            
            logger.info(f"Circuit breaker for {self.name} manually reset to closed state")
    
    def force_open(self, reason: str = "Manual intervention"):
        """
        Force the circuit into the open state
        
        Args:
            reason: Reason for forcing the circuit open
        """
        with self.lock:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()
            
            logger.warning(f"Circuit breaker for {self.name} manually forced open",
                          reason=reason)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the circuit breaker
        
        Returns:
            Dictionary with current state information
        """
        with self.lock:
            state_info = {
                "name": self.name,
                "state": self.state,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "current_timeout": self.current_timeout,
            }
            
            if self.last_failure_time:
                state_info["last_failure_time"] = self.last_failure_time.isoformat()
                
            if self.opened_at:
                state_info["opened_at"] = self.opened_at.isoformat()
                state_info["open_duration_seconds"] = (datetime.now() - self.opened_at).total_seconds()
                
            if self.last_exception:
                state_info["last_error"] = str(self.last_exception)
                state_info["last_error_type"] = type(self.last_exception).__name__
                
            return state_info


class CircuitBreakerDecorator:
    """
    Decorator for applying circuit breaker pattern to functions
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        timeout_multiplier: float = 2.0,
        max_timeout: float = 300.0,
        exclude_exceptions: Optional[List[Type[Exception]]] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize circuit breaker decorator
        
        Args:
            name: Name of the service protected by this circuit breaker
            failure_threshold: Number of consecutive failures before opening circuit
            reset_timeout: Time in seconds before attempting to close circuit
            timeout_multiplier: Factor to increase timeout by on each failure
            max_timeout: Maximum timeout in seconds
            exclude_exceptions: List of exception types that should not count as failures
            circuit_breaker: Existing circuit breaker instance to use
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.timeout_multiplier = timeout_multiplier
        self.max_timeout = max_timeout
        self.exclude_exceptions = exclude_exceptions
        self.circuit_breaker = circuit_breaker
    
    def __call__(self, func):
        """
        Decorate the function
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        # Use function name if name not provided
        name = self.name or f"{func.__module__}.{func.__name__}"
        
        # Create circuit breaker if not provided
        circuit_breaker = self.circuit_breaker or CircuitBreaker(
            name=name,
            failure_threshold=self.failure_threshold,
            reset_timeout=self.reset_timeout,
            timeout_multiplier=self.timeout_multiplier,
            max_timeout=self.max_timeout,
            exclude_exceptions=self.exclude_exceptions
        )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return circuit_breaker.execute(func, *args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit_breaker.execute_async(func, *args, **kwargs)
        
        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    reset_timeout: float = 60.0,
    timeout_multiplier: float = 2.0,
    max_timeout: float = 300.0,
    exclude_exceptions: Optional[List[Type[Exception]]] = None,
    circuit_breaker_instance: Optional[CircuitBreaker] = None
):
    """
    Decorator for applying circuit breaker pattern to functions
    
    Args:
        name: Name of the service protected by this circuit breaker
        failure_threshold: Number of consecutive failures before opening circuit
        reset_timeout: Time in seconds before attempting to close circuit
        timeout_multiplier: Factor to increase timeout by on each failure
        max_timeout: Maximum timeout in seconds
        exclude_exceptions: List of exception types that should not count as failures
        circuit_breaker_instance: Existing circuit breaker instance to use
        
    Returns:
        Decorated function
    """
    return CircuitBreakerDecorator(
        name=name,
        failure_threshold=failure_threshold,
        reset_timeout=reset_timeout,
        timeout_multiplier=timeout_multiplier,
        max_timeout=max_timeout,
        exclude_exceptions=exclude_exceptions,
        circuit_breaker=circuit_breaker_instance
    )


# Registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """
    Get a circuit breaker by name
    
    Args:
        name: Name of the circuit breaker
        
    Returns:
        Circuit breaker instance or None if not found
    """
    return _circuit_breakers.get(name)

def register_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Register a circuit breaker in the global registry
    
    Args:
        circuit_breaker: Circuit breaker instance to register
    """
    _circuit_breakers[circuit_breaker.name] = circuit_breaker
    logger.info(f"Registered circuit breaker for {circuit_breaker.name}")

def create_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    reset_timeout: float = 60.0,
    timeout_multiplier: float = 2.0,
    max_timeout: float = 300.0,
    exclude_exceptions: Optional[List[Type[Exception]]] = None
) -> CircuitBreaker:
    """
    Create and register a new circuit breaker
    
    Args:
        name: Name of the service protected by this circuit breaker
        failure_threshold: Number of consecutive failures before opening circuit
        reset_timeout: Time in seconds before attempting to close circuit
        timeout_multiplier: Factor to increase timeout by on each failure
        max_timeout: Maximum timeout in seconds
        exclude_exceptions: List of exception types that should not count as failures
        
    Returns:
        Circuit breaker instance
    """
    circuit_breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        reset_timeout=reset_timeout,
        timeout_multiplier=timeout_multiplier,
        max_timeout=max_timeout,
        exclude_exceptions=exclude_exceptions
    )
    
    register_circuit_breaker(circuit_breaker)
    return circuit_breaker

def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """
    Get all registered circuit breakers
    
    Returns:
        Dictionary of circuit breaker instances
    """
    return _circuit_breakers.copy()

def get_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """
    Get the current state of all circuit breakers
    
    Returns:
        Dictionary mapping circuit breaker names to their states
    """
    return {name: cb.get_state() for name, cb in _circuit_breakers.items()}
