"""
Execution Flow for General Pulse
Handles cascading fallback strategies and fault-tolerant execution
"""

import asyncio
import time
import hashlib
import json
import structlog
import traceback
from functools import wraps
from typing import List, Dict, Any, Callable, TypeVar, Awaitable, Optional, Tuple, Union
import random
import os
import httpx

from utils.cache_manager import get_cache_manager

logger = structlog.get_logger("execution_flow")

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Simple in-memory cache - transitioning to SQLite
RESPONSE_CACHE: Dict[str, Any] = {}

class ResponseCache:
    """Simple in-memory cache for API responses"""

    def __init__(self, ttl: int = 300):
        """
        Initialize cache

        Args:
            ttl: Time-to-live in seconds for cache entries
        """
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired

        Args:
            key: Cache key

        Returns:
            The cached value or None if not found or expired
        """
        if key not in self.cache:
            return None

        # Check if entry is expired
        timestamp = self.timestamps.get(key, 0)
        if time.time() - timestamp > self.ttl:
            # Expired, remove from cache
            self.invalidate(key)
            return None

        return self.cache[key]

    def set(self, key: str, value: Any):
        """
        Store value in cache

        Args:
            key: Cache key
            value: Value to store
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def invalidate(self, key: str):
        """
        Remove entry from cache

        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()

class ExecutionFlow:
    """
    Utility class for executing functions with retries, caching, and fallbacks
    """

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize execution flow manager

        Args:
            cache_ttl: Time-to-live for cached responses in seconds (default: 1 hour)
        """
        self.cache_ttl = cache_ttl
        self.cache_timestamps: Dict[str, float] = {}
        # Model registry for multi-model queries
        self.model_registry = {}
        # Use legacy ResponseCache for backward compatibility
        self.response_cache = ResponseCache(ttl=cache_ttl)
        # Initialize SQLite cache manager
        self.sqlite_cache = get_cache_manager(db_path="cache.db", default_ttl=cache_ttl)
        # Clean up expired entries on startup
        # Commented out to avoid asyncio error when not in event loop
        # asyncio.create_task(self._cleanup_expired())

        self._model_interface = None

    @property
    def model_interface(self):
        """
        Lazy-loaded model interface to avoid circular imports

        Returns:
            ModelInterface instance
        """
        if self._model_interface is None:
            # Import locally to avoid circular imports
            from skills.optimized_model_interface import OptimizedModelInterface
            self._model_interface = OptimizedModelInterface()
        return self._model_interface

    async def _cleanup_expired(self):
        """Periodically clean up expired cache entries"""
        try:
            cleared = self.sqlite_cache.clear_expired()
            if cleared > 0:
                logger.info(f"Cleaned up {cleared} expired cache entries")
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {str(e)}")

    async def execute_query(self, prompt, model_preference=None, system_prompt="", temperature=0.7, max_tokens=1000):
        """
        Executes a query with the specified parameters, with caching.
        Returns content and metadata if successful, raises an exception if not.
        """
        # Generate a unique cache key
        cache_key = self._generate_cache_key(prompt, model_preference, system_prompt, temperature, max_tokens)

        # Check if we have a cached response in SQLite
        cached_response = self.sqlite_cache.get(cache_key)
        if cached_response:
            logger.info(f"Using cached response for {model_preference} from SQLite")
            return cached_response

        if os.environ.get("SIMULATE_API_CALLS") == "1":
            # Simulate a successful API call
            simulated_content = "This is a simulated response. API calls are currently being simulated."
            response = {
                "success": True,
                "model": model_preference or "gpt-4",
                "content": simulated_content,
                "finish_reason": "stop",
                "elapsed_time": 2.5,
                "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
            }
            # Store in SQLite cache
            self.sqlite_cache.set(cache_key, response)
            return response

        try:
            # Use the lazy-loaded model interface for API calls
            logger.info(f"Calling model {model_preference} with prompt: {prompt[:100]}...")

            if model_preference == "multi_model":
                response = await self.model_interface.call_models_concurrently(
                    prompts={"default": prompt},
                    system_prompts={"default": system_prompt},
                    models=["gpt-4", "claude-3-haiku"],  # Default models
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Multi-model response format is different, so we need to adapt it
                if not response or all(not v.get("success", False) for v in response.values()):
                    error_msgs = [v.get("error", "Unknown error") for v in response.values() if "error" in v]
                    error_msg = "; ".join(error_msgs) or "Unknown error in multi-model call"
                    logger.error(f"Error in multi-model call: {error_msg}")
                    raise Exception(f"Error in multi-model call: {error_msg}")

                # Cache the response in SQLite
                self.sqlite_cache.set(cache_key, response)
                return response
            else:
                response = await self.model_interface.call_model_api_async(
                    model_name=model_preference,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Check if the response indicates success
                if not response or not response.get("success", False):
                    error_msg = response.get("error", "Unknown error in model API call") if response else "No response from model API"
                    logger.error(f"Error calling model API: {error_msg}")
                    raise Exception(f"Error calling model API: {error_msg}")

                logger.info(f"Received successful response from {model_preference}")

                # Cache the successful response in SQLite
                self.sqlite_cache.set(cache_key, response)
                return response

        except Exception as e:
            logger.error(f"Exception during model API call: {str(e)}")
            raise

    async def multi_model_query(self, prompt, models=None, system_prompt=None, temperature=0.7, max_tokens=1000, simulate=False):
        """
        Query multiple models with the same prompt

        Args:
            prompt: The prompt to send to the models
            models: List of model names to query
            system_prompt: Optional system prompt
            temperature: The temperature to use for sampling
            max_tokens: The maximum number of tokens to generate
            simulate: Whether to return simulated responses

        Returns:
            Dictionary mapping model names to their responses
        """
        # Generate a cache key for the multi-model query
        cache_key = {
            "type": "multi_model",
            "prompt": prompt,
            "models": models,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Check SQLite cache first
        cached_result = self.sqlite_cache.get(cache_key)
        if cached_result:
            logger.info(f"Using cached multi-model results for {len(models) if models else 'default'} models")
            return cached_result

        results = {}
        models = models or list(self.model_registry.keys())

        for model in models:
            results[model] = await self.execute_query(
                prompt=prompt,
                model_preference=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )

        # Cache the combined results
        self.sqlite_cache.set(cache_key, results)
        return results

    async def execute_with_fallbacks(
        self,
        primary_fn: Callable[[], Awaitable[T]],
        fallback_fns: List[Callable[[], Awaitable[T]]],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None
    ) -> T:
        """
        Execute a function with retries and fallbacks

        Args:
            primary_fn: Primary async function to execute
            fallback_fns: List of fallback async functions to try if primary fails
            max_retries: Maximum number of retries for primary function
            retry_delay: Initial delay between retries in seconds
            retry_backoff: Factor to increase delay by on each retry
            cache_key: Optional key for caching response
            cache_ttl: Optional custom TTL for this specific cache entry

        Returns:
            Result of successful function execution
        """
        # Check SQLite cache first if cache_key is provided
        if cache_key:
            cached_result = self.sqlite_cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result

        # Try primary function with retries
        delay = retry_delay
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for primary function")

                result = await primary_fn()

                # Cache result if cache_key provided
                if cache_key:
                    ttl = cache_ttl or self.cache_ttl
                    self.sqlite_cache.set(cache_key, result, ttl=ttl)

                return result

            except Exception as e:
                logger.warning(f"Primary function failed on attempt {attempt+1}/{max_retries}: {str(e)}")

                if attempt < max_retries - 1:
                    # Add some jitter to avoid thundering herd
                    jitter = random.uniform(0.8, 1.2)
                    sleep_time = delay * jitter
                    logger.debug(f"Waiting {sleep_time:.2f}s before retry")
                    await asyncio.sleep(sleep_time)
                    delay *= retry_backoff

        # Try fallback functions in sequence
        for i, fallback_fn in enumerate(fallback_fns):
            try:
                logger.info(f"Trying fallback function {i+1}/{len(fallback_fns)}")
                result = await fallback_fn()

                # Cache fallback result
                if cache_key:
                    ttl = cache_ttl or self.cache_ttl
                    self.sqlite_cache.set(cache_key, result, ttl=ttl)

                return result

            except Exception as e:
                logger.warning(f"Fallback function {i+1} failed: {str(e)}")

        # If we've reached here, all attempts failed
        raise Exception("All execution attempts failed, including fallbacks")

    def clear_cache(self, prefix: Optional[str] = None):
        """
        Clear the cache

        Args:
            prefix: Optional prefix to selectively clear cache entries
        """
        # Clear SQLite cache
        cleared = self.sqlite_cache.clear(prefix=prefix)
        logger.debug(f"Cleared {cleared} SQLite cache entries{' with prefix ' + prefix if prefix else ''}")

        # Also clear in-memory cache for backward compatibility
        if prefix:
            keys_to_remove = [k for k in RESPONSE_CACHE if k.startswith(prefix)]
            for k in keys_to_remove:
                if k in RESPONSE_CACHE:
                    del RESPONSE_CACHE[k]
                if k in self.cache_timestamps:
                    del self.cache_timestamps[k]
            logger.debug(f"Cleared {len(keys_to_remove)} in-memory cache entries with prefix: {prefix}")
        else:
            RESPONSE_CACHE.clear()
            self.cache_timestamps.clear()
            logger.debug("In-memory cache completely cleared")

        # Clear response cache
        self.response_cache.clear()

    def _generate_cache_key(self, prompt, model_preference, system_prompt, temperature, max_tokens):
        """
        Generate a unique cache key based on the input parameters

        Args:
            prompt: The prompt to send to the model
            model_preference: The model name to use
            system_prompt: The system prompt
            temperature: The temperature setting
            max_tokens: The maximum number of tokens

        Returns:
            Dictionary suitable for the cache key
        """
        # Return a structured dictionary for the CacheManager to hash
        return {
            "type": "model_call",
            "prompt": prompt,
            "model": model_preference,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

def retry_async(max_retries=3, initial_delay=1.0, backoff_factor=2.0):
    """
    Decorator for async functions to retry with exponential backoff

    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplicative factor for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt+1}/{max_retries} for {func.__name__} after error",
                            error=str(e),
                            next_retry_in=delay
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}",
                            error=str(e)
                        )
                        raise

            # Should never get here, but just in case
            raise last_exception or RuntimeError("Unexpected retry failure")

        return wrapper
    return decorator