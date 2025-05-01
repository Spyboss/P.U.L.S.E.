"""
Retry utilities for P.U.L.S.E.
Provides standardized retry mechanisms with various backoff strategies
"""

import asyncio
import random
import time
import functools
import structlog
from typing import Callable, TypeVar, Any, Optional, Dict, List, Union, Awaitable, Type, Tuple
from enum import Enum

from utils.error_taxonomy import ErrorInfo, classify_exception, RetryStrategy, ErrorType

# Logger
logger = structlog.get_logger("retry")

# Type variables
T = TypeVar('T')
E = TypeVar('E', bound=Exception)

class RetryableError(Exception):
    """Base exception for errors that should be retried"""
    pass

class NonRetryableError(Exception):
    """Base exception for errors that should not be retried"""
    pass

class RetryResult(Enum):
    """Result of a retry operation"""
    SUCCESS = "success"  # Operation succeeded
    FAILURE = "failure"  # Operation failed after all retries
    ABORT = "abort"      # Operation was aborted due to non-retryable error


def calculate_backoff(
    attempt: int,
    strategy: RetryStrategy,
    base_delay: float,
    max_delay: float,
    multiplier: float = 2.0,
    jitter_factor: float = 0.2
) -> float:
    """
    Calculate backoff delay based on retry strategy
    
    Args:
        attempt: Current attempt number (0-based)
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Multiplier for exponential backoff
        jitter_factor: Jitter factor for randomization (0.0-1.0)
        
    Returns:
        Delay in seconds
    """
    if strategy == RetryStrategy.NO_RETRY:
        return 0
    
    if strategy == RetryStrategy.IMMEDIATE_RETRY:
        return 0
    
    if strategy == RetryStrategy.LINEAR_BACKOFF:
        delay = base_delay * (attempt + 1)
    
    elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        delay = base_delay * (multiplier ** attempt)
    
    else:  # Default to jittered backoff
        delay = base_delay * (multiplier ** attempt)
        # Add jitter
        jitter = delay * jitter_factor
        delay = random.uniform(delay - jitter, delay + jitter)
    
    # Cap at max delay
    return min(delay, max_delay)


async def retry_async(
    func: Callable[..., Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_strategy: RetryStrategy = RetryStrategy.JITTERED_BACKOFF,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[int, Exception, float], Awaitable[None]]] = None,
    retry_condition: Optional[Callable[[Exception], Awaitable[bool]]] = None,
    timeout: Optional[float] = None,
    *args, **kwargs
) -> Tuple[RetryResult, Union[T, Exception]]:
    """
    Retry an async function with configurable backoff
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_strategy: Strategy for calculating retry delays
        retryable_exceptions: List of exception types that should be retried
        non_retryable_exceptions: List of exception types that should not be retried
        on_retry: Callback function to call before each retry
        retry_condition: Function to determine if an exception should be retried
        timeout: Timeout for each function call in seconds
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (RetryResult, result_or_exception)
    """
    retryable_exceptions = retryable_exceptions or [RetryableError, Exception]
    non_retryable_exceptions = non_retryable_exceptions or [NonRetryableError]
    
    # Ensure RetryableError is in retryable_exceptions
    if RetryableError not in retryable_exceptions:
        retryable_exceptions.append(RetryableError)
    
    # Ensure NonRetryableError is in non_retryable_exceptions
    if NonRetryableError not in non_retryable_exceptions:
        non_retryable_exceptions.append(NonRetryableError)
    
    attempt = 0
    last_exception = None
    
    while attempt <= max_retries:
        try:
            # Call the function with timeout if specified
            if timeout:
                return RetryResult.SUCCESS, await asyncio.wait_for(func(*args, **kwargs), timeout)
            else:
                return RetryResult.SUCCESS, await func(*args, **kwargs)
                
        except tuple(non_retryable_exceptions) as e:
            # Non-retryable exception, abort immediately
            logger.warning(f"Non-retryable exception in {func.__name__}", 
                          exception=str(e),
                          exception_type=type(e).__name__)
            return RetryResult.ABORT, e
            
        except tuple(retryable_exceptions) as e:
            last_exception = e
            
            # Check if we've reached the maximum number of retries
            if attempt >= max_retries:
                logger.warning(f"Maximum retries ({max_retries}) reached for {func.__name__}",
                              exception=str(e),
                              exception_type=type(e).__name__,
                              attempt=attempt,
                              max_retries=max_retries)
                return RetryResult.FAILURE, e
            
            # Check custom retry condition if provided
            should_retry = True
            if retry_condition:
                try:
                    should_retry = await retry_condition(e)
                except Exception as condition_error:
                    logger.warning(f"Error in retry condition for {func.__name__}",
                                  exception=str(condition_error),
                                  original_exception=str(e))
            
            if not should_retry:
                logger.info(f"Retry condition returned False for {func.__name__}",
                           exception=str(e),
                           attempt=attempt)
                return RetryResult.ABORT, e
            
            # Calculate backoff delay
            delay = calculate_backoff(
                attempt=attempt,
                strategy=retry_strategy,
                base_delay=base_delay,
                max_delay=max_delay
            )
            
            # Call on_retry callback if provided
            if on_retry:
                try:
                    await on_retry(attempt, e, delay)
                except Exception as callback_error:
                    logger.warning(f"Error in on_retry callback for {func.__name__}",
                                  exception=str(callback_error),
                                  original_exception=str(e))
            
            # Log retry attempt
            logger.info(f"Retrying {func.__name__} after error",
                       exception=str(e),
                       exception_type=type(e).__name__,
                       attempt=attempt,
                       max_retries=max_retries,
                       delay=delay)
            
            # Wait before retrying
            await asyncio.sleep(delay)
            
            # Increment attempt counter
            attempt += 1
    
    # This should not be reached, but just in case
    return RetryResult.FAILURE, last_exception or Exception("Unknown error")


def retry_sync(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_strategy: RetryStrategy = RetryStrategy.JITTERED_BACKOFF,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    retry_condition: Optional[Callable[[Exception], bool]] = None,
    *args, **kwargs
) -> Tuple[RetryResult, Union[T, Exception]]:
    """
    Retry a synchronous function with configurable backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_strategy: Strategy for calculating retry delays
        retryable_exceptions: List of exception types that should be retried
        non_retryable_exceptions: List of exception types that should not be retried
        on_retry: Callback function to call before each retry
        retry_condition: Function to determine if an exception should be retried
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (RetryResult, result_or_exception)
    """
    retryable_exceptions = retryable_exceptions or [RetryableError, Exception]
    non_retryable_exceptions = non_retryable_exceptions or [NonRetryableError]
    
    # Ensure RetryableError is in retryable_exceptions
    if RetryableError not in retryable_exceptions:
        retryable_exceptions.append(RetryableError)
    
    # Ensure NonRetryableError is in non_retryable_exceptions
    if NonRetryableError not in non_retryable_exceptions:
        non_retryable_exceptions.append(NonRetryableError)
    
    attempt = 0
    last_exception = None
    
    while attempt <= max_retries:
        try:
            return RetryResult.SUCCESS, func(*args, **kwargs)
                
        except tuple(non_retryable_exceptions) as e:
            # Non-retryable exception, abort immediately
            logger.warning(f"Non-retryable exception in {func.__name__}", 
                          exception=str(e),
                          exception_type=type(e).__name__)
            return RetryResult.ABORT, e
            
        except tuple(retryable_exceptions) as e:
            last_exception = e
            
            # Check if we've reached the maximum number of retries
            if attempt >= max_retries:
                logger.warning(f"Maximum retries ({max_retries}) reached for {func.__name__}",
                              exception=str(e),
                              exception_type=type(e).__name__,
                              attempt=attempt,
                              max_retries=max_retries)
                return RetryResult.FAILURE, e
            
            # Check custom retry condition if provided
            should_retry = True
            if retry_condition:
                try:
                    should_retry = retry_condition(e)
                except Exception as condition_error:
                    logger.warning(f"Error in retry condition for {func.__name__}",
                                  exception=str(condition_error),
                                  original_exception=str(e))
            
            if not should_retry:
                logger.info(f"Retry condition returned False for {func.__name__}",
                           exception=str(e),
                           attempt=attempt)
                return RetryResult.ABORT, e
            
            # Calculate backoff delay
            delay = calculate_backoff(
                attempt=attempt,
                strategy=retry_strategy,
                base_delay=base_delay,
                max_delay=max_delay
            )
            
            # Call on_retry callback if provided
            if on_retry:
                try:
                    on_retry(attempt, e, delay)
                except Exception as callback_error:
                    logger.warning(f"Error in on_retry callback for {func.__name__}",
                                  exception=str(callback_error),
                                  original_exception=str(e))
            
            # Log retry attempt
            logger.info(f"Retrying {func.__name__} after error",
                       exception=str(e),
                       exception_type=type(e).__name__,
                       attempt=attempt,
                       max_retries=max_retries,
                       delay=delay)
            
            # Wait before retrying
            time.sleep(delay)
            
            # Increment attempt counter
            attempt += 1
    
    # This should not be reached, but just in case
    return RetryResult.FAILURE, last_exception or Exception("Unknown error")


class RetryDecorator:
    """
    Decorator for retrying functions with configurable backoff
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_strategy: RetryStrategy = RetryStrategy.JITTERED_BACKOFF,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
        on_retry: Optional[Callable[[int, Exception, float], Any]] = None,
        retry_condition: Optional[Callable[[Exception], bool]] = None,
        raise_on_failure: bool = True,
        timeout: Optional[float] = None
    ):
        """
        Initialize retry decorator
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            retry_strategy: Strategy for calculating retry delays
            retryable_exceptions: List of exception types that should be retried
            non_retryable_exceptions: List of exception types that should not be retried
            on_retry: Callback function to call before each retry
            retry_condition: Function to determine if an exception should be retried
            raise_on_failure: Whether to raise the last exception on failure
            timeout: Timeout for each function call in seconds (async only)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_strategy = retry_strategy
        self.retryable_exceptions = retryable_exceptions
        self.non_retryable_exceptions = non_retryable_exceptions
        self.on_retry = on_retry
        self.retry_condition = retry_condition
        self.raise_on_failure = raise_on_failure
        self.timeout = timeout
    
    def __call__(self, func):
        """
        Decorate the function
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result, value = await retry_async(
                func=func,
                max_retries=self.max_retries,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                retry_strategy=self.retry_strategy,
                retryable_exceptions=self.retryable_exceptions,
                non_retryable_exceptions=self.non_retryable_exceptions,
                on_retry=self.on_retry,
                retry_condition=self.retry_condition,
                timeout=self.timeout,
                *args, **kwargs
            )
            
            if result == RetryResult.SUCCESS:
                return value
            elif self.raise_on_failure:
                raise value
            else:
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result, value = retry_sync(
                func=func,
                max_retries=self.max_retries,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                retry_strategy=self.retry_strategy,
                retryable_exceptions=self.retryable_exceptions,
                non_retryable_exceptions=self.non_retryable_exceptions,
                on_retry=self.on_retry,
                retry_condition=self.retry_condition,
                *args, **kwargs
            )
            
            if result == RetryResult.SUCCESS:
                return value
            elif self.raise_on_failure:
                raise value
            else:
                return None
        
        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_strategy: RetryStrategy = RetryStrategy.JITTERED_BACKOFF,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[int, Exception, float], Any]] = None,
    retry_condition: Optional[Callable[[Exception], bool]] = None,
    raise_on_failure: bool = True,
    timeout: Optional[float] = None
):
    """
    Decorator for retrying functions with configurable backoff
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_strategy: Strategy for calculating retry delays
        retryable_exceptions: List of exception types that should be retried
        non_retryable_exceptions: List of exception types that should not be retried
        on_retry: Callback function to call before each retry
        retry_condition: Function to determine if an exception should be retried
        raise_on_failure: Whether to raise the last exception on failure
        timeout: Timeout for each function call in seconds (async only)
        
    Returns:
        Decorated function
    """
    return RetryDecorator(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        retry_strategy=retry_strategy,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
        on_retry=on_retry,
        retry_condition=retry_condition,
        raise_on_failure=raise_on_failure,
        timeout=timeout
    )


async def default_retry_condition(exception: Exception) -> bool:
    """
    Default condition for determining if an exception should be retried
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the exception should be retried, False otherwise
    """
    # Classify the exception
    error_info = classify_exception(exception)
    
    # Check if the error is retryable
    return error_info.is_retryable()


def is_retryable_exception(exception: Exception) -> bool:
    """
    Check if an exception is retryable
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the exception is retryable, False otherwise
    """
    # Classify the exception
    error_info = classify_exception(exception)
    
    # Check if the error is retryable
    return error_info.is_retryable()
