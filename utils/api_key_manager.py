"""
API Key Manager for General Pulse

This module provides centralized API key management with caching,
error handling, and automatic reloading capabilities.
"""

import os
import time
import structlog
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logger
logger = structlog.get_logger("api_key_manager")

class APIKeyManager:
    """
    Centralized API key management with caching and error handling
    """

    def __init__(self, auto_reload: bool = True, cache_ttl: int = 300):
        """
        Initialize the API key manager

        Args:
            auto_reload: Whether to automatically reload .env file when keys are missing
            cache_ttl: Cache time-to-live in seconds
        """
        self.auto_reload = auto_reload
        self.cache_ttl = cache_ttl

        # Cache for API keys
        self.key_cache: Dict[str, Dict[str, Any]] = {}

        # Load environment variables from .env file
        self._load_env_file()

        # Initialize the cache with current keys
        self._init_cache()

        logger.info("API Key Manager initialized")

    def _load_env_file(self) -> bool:
        """
        Load environment variables from .env file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load .env file with override to ensure latest values
            load_dotenv(override=True)
            logger.info("Environment variables loaded from .env file")
            return True
        except Exception as e:
            logger.error(f"Failed to load environment variables: {str(e)}")
            return False

    def _init_cache(self) -> None:
        """
        Initialize the cache with current API keys
        """
        # List of API keys to cache
        key_names = [
            "OPENROUTER_API_KEY"
            # Mistral Small uses OpenRouter, so no separate API key needed
            # OpenAI API is not used in this application
        ]

        # Initialize cache for each key
        current_time = time.time()
        for key_name in key_names:
            key_value = os.getenv(key_name)
            if key_value:
                # Mask the key for logging
                masked_key = self._mask_key(key_value)
                logger.info(f"Cached API key: {key_name} = {masked_key}")

                self.key_cache[key_name] = {
                    "value": key_value,
                    "timestamp": current_time,
                    "attempts": 0
                }
            else:
                logger.warning(f"API key not found: {key_name}")

    def _mask_key(self, key: str) -> str:
        """
        Mask an API key for logging

        Args:
            key: API key to mask

        Returns:
            Masked API key
        """
        if not key or len(key) < 8:
            return "***"

        return key[:4] + "*" * (len(key) - 8) + key[-4:]

    def get_key(self, key_name: str, force_reload: bool = False) -> Optional[str]:
        """
        Get an API key

        Args:
            key_name: Name of the API key
            force_reload: Whether to force reload from .env file

        Returns:
            API key value or None if not found
        """
        # Check if we need to force reload
        if force_reload:
            self._load_env_file()

        # Check cache first
        current_time = time.time()
        if key_name in self.key_cache and not force_reload:
            cache_entry = self.key_cache[key_name]

            # Check if cache is still valid
            if current_time - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["value"]

        # Get from environment
        key_value = os.getenv(key_name)

        # If key not found and auto_reload is enabled, try reloading
        if not key_value and self.auto_reload:
            logger.info(f"API key {key_name} not found, attempting to reload .env file")
            self._load_env_file()
            key_value = os.getenv(key_name)

        # Update cache
        if key_value:
            # Mask the key for logging
            masked_key = self._mask_key(key_value)
            logger.info(f"Retrieved API key: {key_name} = {masked_key}")

            self.key_cache[key_name] = {
                "value": key_value,
                "timestamp": current_time,
                "attempts": 0
            }
            return key_value
        else:
            # Increment attempts counter
            if key_name in self.key_cache:
                self.key_cache[key_name]["attempts"] += 1
                attempts = self.key_cache[key_name]["attempts"]

                # Log with increasing severity based on attempts
                if attempts <= 3:
                    logger.warning(f"API key {key_name} not found (attempt {attempts})")
                else:
                    logger.error(f"API key {key_name} not found after {attempts} attempts")
            else:
                logger.error(f"API key {key_name} not found")

            return None

    def refresh_all_keys(self) -> Dict[str, bool]:
        """
        Refresh all API keys

        Returns:
            Dictionary of key names and whether they were successfully refreshed
        """
        # Reload environment variables
        self._load_env_file()

        # Refresh all keys in cache
        results = {}
        for key_name in list(self.key_cache.keys()):
            key_value = os.getenv(key_name)
            if key_value:
                self.key_cache[key_name]["value"] = key_value
                self.key_cache[key_name]["timestamp"] = time.time()
                self.key_cache[key_name]["attempts"] = 0
                results[key_name] = True
            else:
                results[key_name] = False

        return results

    def clear_cache(self) -> None:
        """
        Clear the API key cache
        """
        self.key_cache.clear()
        logger.info("API key cache cleared")
