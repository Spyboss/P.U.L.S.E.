"""
Unit tests for the integration error handler
"""

import unittest
import json
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

from utils.integration_error_handler import (
    IntegrationError,
    GitHubError,
    NotionError,
    handle_github_error,
    handle_notion_error,
    with_error_handling,
    extract_error_details,
    format_user_friendly_error,
    is_retryable_error
)


class TestIntegrationErrorHandler(unittest.TestCase):
    """Test cases for the integration error handler"""

    def test_github_error_handling(self):
        """Test GitHub error handling"""
        # Test 401 error
        error_401 = MagicMock()
        error_401.status_code = 401
        error_401.__str__.return_value = "Bad credentials"

        result = handle_github_error(error_401, "get_repo_info")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "github_error")
        self.assertEqual(result["status_code"], 401)
        self.assertIn("authentication", result["user_message"].lower())

        # Test 403 rate limit error
        error_403 = MagicMock()
        error_403.status_code = 403
        error_403.__str__.return_value = "API rate limit exceeded"

        result = handle_github_error(error_403, "get_repo_info")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "github_error")
        self.assertEqual(result["status_code"], 403)
        self.assertIn("rate limit", result["user_message"].lower())

        # Test 404 error
        error_404 = MagicMock()
        error_404.status_code = 404
        error_404.__str__.return_value = "Repository not found"

        result = handle_github_error(error_404, "get_repo_info")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "github_error")
        self.assertEqual(result["status_code"], 404)
        self.assertIn("not found", result["user_message"].lower())

        # Test network error
        network_error = ConnectionError("Failed to establish a connection")

        result = handle_github_error(network_error, "get_repo_info")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertIn("connection", result["user_message"].lower())

    def test_notion_error_handling(self):
        """Test Notion error handling"""
        # Test 401 error
        error_401 = MagicMock()
        error_401.status_code = 401
        error_401.__str__.return_value = "Invalid API key"

        result = handle_notion_error(error_401, "create_page")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "notion_error")
        self.assertEqual(result["status_code"], 401)
        self.assertIn("notion_api_key", result["user_message"].lower())

        # Test 403 error
        error_403 = MagicMock()
        error_403.status_code = 403
        error_403.__str__.return_value = "Permission denied"

        result = handle_notion_error(error_403, "create_page")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "notion_error")
        self.assertEqual(result["status_code"], 403)
        self.assertIn("permission", result["user_message"].lower())

        # Test 404 error with database
        error_404 = MagicMock()
        error_404.status_code = 404
        error_404.__str__.return_value = "Database not found"

        result = handle_notion_error(error_404, "create_page")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "notion_error")
        self.assertEqual(result["status_code"], 404)
        self.assertIn("not found", result["user_message"].lower())

        # Test network error
        network_error = ConnectionError("Failed to establish a connection")

        result = handle_notion_error(network_error, "create_page")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertIn("connection", result["user_message"].lower())

        # Test API key not configured
        config_error = ValueError("API key not configured")

        result = handle_notion_error(config_error, "create_page")
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "notion_error")
        self.assertIn("not configured", result["user_message"].lower())

    def test_with_error_handling_decorator_sync(self):
        """Test the with_error_handling decorator for sync functions"""
        # Define a test function that will raise an exception
        @with_error_handling("github", "test_operation")
        def test_function(should_fail=True):
            if should_fail:
                raise ConnectionError("Test connection error")
            return {"success": True, "message": "Operation succeeded"}

        # Test with failure
        result = test_function(should_fail=True)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertIn("connection", result["user_message"].lower())

        # Test without failure
        result = test_function(should_fail=False)
        self.assertEqual(result["success"], True)
        self.assertEqual(result["message"], "Operation succeeded")

    def test_with_error_handling_decorator_async(self):
        """Test the with_error_handling decorator for async functions"""
        # Define a test async function that will raise an exception
        @with_error_handling("notion", "test_operation")
        async def test_async_function(should_fail=True):
            if should_fail:
                raise ConnectionError("Test connection error")
            return {"success": True, "message": "Operation succeeded"}

        # Run the async function in a synchronous context
        import asyncio

        # Test with failure
        result = asyncio.run(test_async_function(should_fail=True))
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_type"], "network_error")
        self.assertIn("connection", result["user_message"].lower())

        # Test without failure
        result = asyncio.run(test_async_function(should_fail=False))
        self.assertEqual(result["success"], True)
        self.assertEqual(result["message"], "Operation succeeded")

    def test_extract_error_details(self):
        """Test extracting error details from responses"""
        # Test GitHub error format
        github_response = MagicMock()
        github_response.json.return_value = {
            "message": "API rate limit exceeded",
            "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
        }

        message, details = extract_error_details(github_response)
        self.assertEqual(message, "API rate limit exceeded")
        self.assertIn("documentation_url", details)

        # Test Notion error format
        notion_response = MagicMock()
        notion_response.json.return_value = {
            "object": "error",
            "status": 404,
            "code": "object_not_found",
            "message": "Database not found"
        }

        message, details = extract_error_details(notion_response)
        self.assertEqual(message, "Database not found")
        self.assertEqual(details["code"], "object_not_found")

        # Test non-JSON response
        text_response = MagicMock()
        text_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        text_response.text = "Internal Server Error"

        message, details = extract_error_details(text_response)
        self.assertEqual(message, "Internal Server Error")
        self.assertEqual(details["raw_text"], "Internal Server Error")

    def test_format_user_friendly_error(self):
        """Test formatting user-friendly error messages"""
        # Test with user_message
        error_dict = {
            "success": False,
            "error_type": "github_error",
            "user_message": "Repository not found. Please check the repository name."
        }

        message = format_user_friendly_error(error_dict)
        self.assertEqual(message, "Repository not found. Please check the repository name.")

        # Test with message but no user_message
        error_dict = {
            "success": False,
            "error_type": "github_error",
            "message": "Not Found"
        }

        message = format_user_friendly_error(error_dict)
        self.assertEqual(message, "Error: Not Found")

        # Test with neither message nor user_message
        error_dict = {
            "success": False,
            "error_type": "github_error"
        }

        message = format_user_friendly_error(error_dict)
        self.assertEqual(message, "An unknown error occurred. Please try again later.")

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
            "error_type": "github_error",
            "message": "API rate limit exceeded",
            "status_code": 403
        }

        self.assertTrue(is_retryable_error(rate_limit_error))

        # Test server error
        server_error = {
            "success": False,
            "error_type": "github_error",
            "message": "Internal Server Error",
            "status_code": 500
        }

        self.assertTrue(is_retryable_error(server_error))

        # Test specific retryable status code
        specific_error = {
            "success": False,
            "error_type": "github_error",
            "message": "Too Many Requests",
            "status_code": 429
        }

        self.assertTrue(is_retryable_error(specific_error))

        # Test non-retryable error
        non_retryable_error = {
            "success": False,
            "error_type": "github_error",
            "message": "Not Found",
            "status_code": 404
        }

        self.assertFalse(is_retryable_error(non_retryable_error))


if __name__ == '__main__':
    unittest.main()
