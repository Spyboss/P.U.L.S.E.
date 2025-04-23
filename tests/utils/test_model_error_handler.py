"""
Unit tests for the model error handler
"""

import unittest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import aiohttp

from utils.model_error_handler import (
    ModelError,
    handle_model_error,
    with_model_error_handling,
    format_user_friendly_error,
    is_retryable_error,
    extract_model_error_details
)


class TestModelErrorHandler(unittest.TestCase):
    """Test cases for the model error handler"""

    def test_handle_model_error(self):
        """Test handling model errors"""
        # Test network error
        network_error = httpx.ConnectError("Failed to establish a connection")

        result = handle_model_error(network_error, "generate_text", "gpt-4")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertEqual(result["model"], "gpt-4")
        self.assertEqual(result["operation"], "generate_text")
        self.assertIn("connection", result["user_message"].lower())

        # Test authentication error
        auth_error = Exception("Invalid API key")

        result = handle_model_error(auth_error, "generate_text", "claude-3")
        self.assertEqual(result["success"], False)
        self.assertIn("authentication", result["message"].lower())
        self.assertEqual(result["model"], "claude-3")
        self.assertIn("api key", result["user_message"].lower())

        # Test rate limit error
        rate_limit_error = Exception("Rate limit exceeded")

        result = handle_model_error(rate_limit_error, "generate_text", "gemini-pro")
        self.assertEqual(result["success"], False)
        self.assertIn("rate limit", result["message"].lower())
        self.assertEqual(result["model"], "gemini-pro")
        self.assertIn("rate limit", result["user_message"].lower())

        # Test context length error
        context_error = Exception("Input too long for model context window")

        result = handle_model_error(context_error, "generate_text", "gpt-3.5")
        self.assertEqual(result["success"], False)
        self.assertIn("too long", result["message"].lower())
        self.assertEqual(result["model"], "gpt-3.5")
        self.assertIn("too long", result["user_message"].lower())

        # Test server error with status code
        server_error = MagicMock()
        server_error.status_code = 500
        server_error.__str__.return_value = "Internal Server Error"

        result = handle_model_error(server_error, "generate_text", "deepseek")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["model"], "deepseek")
        self.assertIn("internal error", result["user_message"].lower())

    def test_with_model_error_handling_sync(self):
        """Test the with_model_error_handling decorator for sync functions"""
        # Define a test function that will raise an exception
        @with_model_error_handling("test_operation")
        def test_function(self_param, model_name="test-model", should_fail=True):
            if should_fail:
                raise httpx.ConnectError("Test connection error")
            return {"success": True, "message": "Operation succeeded"}

        # Test with failure
        result = test_function(None, "test-model", True)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertEqual(result["model"], "test-model")
        self.assertIn("connection", result["user_message"].lower())

        # Test without failure
        result = test_function(None, "test-model", False)
        self.assertEqual(result["success"], True)
        self.assertEqual(result["message"], "Operation succeeded")

    def test_with_model_error_handling_async(self):
        """Test the with_model_error_handling decorator for async functions"""
        # Define a test async function that will raise an exception
        @with_model_error_handling("test_operation")
        async def test_async_function(self_param, model_name="test-model", should_fail=True):
            if should_fail:
                raise httpx.ConnectError("Test connection error")
            return {"success": True, "message": "Operation succeeded"}

        # Run the async function in a synchronous context
        # Test with failure
        result = asyncio.run(test_async_function(None, "test-model", True))
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertEqual(result["model"], "test-model")
        self.assertIn("connection", result["user_message"].lower())

        # Test without failure
        result = asyncio.run(test_async_function(None, "test-model", False))
        self.assertEqual(result["success"], True)
        self.assertEqual(result["message"], "Operation succeeded")

    def test_format_user_friendly_error(self):
        """Test formatting user-friendly error messages"""
        # Test with user_message
        error_dict = {
            "success": False,
            "error_type": "network_error",
            "user_message": "Could not connect to the AI model service. Please check your internet connection."
        }

        message = format_user_friendly_error(error_dict)
        self.assertEqual(message, "Could not connect to the AI model service. Please check your internet connection.")

        # Test with message but no user_message
        error_dict = {
            "success": False,
            "error_type": "model_error",
            "message": "Failed to generate text"
        }

        message = format_user_friendly_error(error_dict)
        self.assertEqual(message, "Error: Failed to generate text")

        # Test with neither message nor user_message
        error_dict = {
            "success": False,
            "error_type": "model_error"
        }

        message = format_user_friendly_error(error_dict)
        self.assertEqual(message, "An unknown error occurred with the AI model. Please try again later.")

    def test_is_retryable_error(self):
        """Test determining if an error is retryable"""
        # Test network error
        network_error = {
            "success": False,
            "error_type": "network_error",
            "message": "Connection refused"
        }

        self.assertTrue(is_retryable_error(network_error))

        # Test rate limit error
        rate_limit_error = {
            "success": False,
            "error_type": "model_error",
            "message": "Rate limit exceeded",
            "status_code": 429
        }

        self.assertTrue(is_retryable_error(rate_limit_error))

        # Test server error
        server_error = {
            "success": False,
            "error_type": "model_error",
            "message": "Internal Server Error",
            "status_code": 500
        }

        self.assertTrue(is_retryable_error(server_error))

        # Test non-retryable error
        non_retryable_error = {
            "success": False,
            "error_type": "model_error",
            "message": "Invalid API key",
            "status_code": 401
        }

        self.assertFalse(is_retryable_error(non_retryable_error))

    def test_extract_model_error_details(self):
        """Test extracting error details from model API responses"""
        # Test OpenAI error format
        openai_response = {
            "error": {
                "message": "The model `gpt-5` does not exist",
                "type": "invalid_request_error",
                "param": "model",
                "code": "model_not_found"
            }
        }

        message, details = extract_model_error_details(openai_response)
        self.assertEqual(message, "The model `gpt-5` does not exist")
        self.assertEqual(details["type"], "invalid_request_error")

        # Test OpenRouter error format
        openrouter_response = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error"
            }
        }

        message, details = extract_model_error_details(openrouter_response)
        self.assertEqual(message, "Rate limit exceeded")
        self.assertEqual(details["type"], "rate_limit_error")

        # Test generic error format
        generic_response = {
            "status": "error",
            "code": 500,
            "message": "Internal server error"
        }

        message, details = extract_model_error_details(generic_response)
        self.assertEqual(message, "Unknown model API error")
        self.assertEqual(details["raw_response"], generic_response)


if __name__ == '__main__':
    unittest.main()
