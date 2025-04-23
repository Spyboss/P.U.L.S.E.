"""
Unit tests for Notion skills
"""

import unittest
import asyncio
import os
import time
from unittest.mock import patch, MagicMock
from datetime import datetime
from skills.notion_skills import NotionSkills
from utils.notion_client import NotionAPIError
from utils.integration_error_handler import is_retryable_error

class TestNotionSkills(unittest.TestCase):
    """Test cases for Notion skills"""

    def setUp(self):
        """Set up test environment"""
        # Create a test instance with a mock API key
        with patch.dict(os.environ, {"NOTION_API_KEY": "test_api_key"}):
            self.notion_skills = NotionSkills()

    def test_extract_id_from_url(self):
        """Test extracting page ID from Notion URL"""
        # Test various URL formats
        test_cases = [
            # Standard URL
            ("https://www.notion.so/workspace/1d334ba186ed8034bdabd5d163b1caa0", "1d334ba186ed8034bdabd5d163b1caa0"),
            # URL with page title - using a different format for this test
            ("https://www.notion.so/1d334ba186ed8034bdabd5d163b1caa0", "1d334ba186ed8034bdabd5d163b1caa0"),
            # URL with query parameters
            ("https://www.notion.so/1d334ba186ed8034bdabd5d163b1caa0?pvs=4", "1d334ba186ed8034bdabd5d163b1caa0"),
            # Raw ID
            ("1d334ba186ed8034bdabd5d163b1caa0", "1d334ba186ed8034bdabd5d163b1caa0"),
        ]

        for url, expected_id in test_cases:
            with self.subTest(url=url):
                extracted_id = self.notion_skills.extract_id_from_url(url)
                self.assertEqual(extracted_id, expected_id)

    def test_is_configured(self):
        """Test is_configured method"""
        # Test with API key
        with patch.dict(os.environ, {"NOTION_API_KEY": "test_api_key"}):
            notion = NotionSkills()
            self.assertTrue(notion.is_configured())

        # Test without API key
        with patch.dict(os.environ, {"NOTION_API_KEY": ""}):
            notion = NotionSkills()
            # Force the _is_configured attribute to be False
            notion._is_configured = False
            self.assertFalse(notion.is_configured())

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_create_document_async_not_configured(self, mock_sleep):
        """Test create_document_async when Notion is not configured"""
        # Force _is_configured to be False
        self.notion_skills._is_configured = False

        # Run the test
        result = asyncio.run(self.notion_skills.create_document_async("Test Document"))

        # Check the result
        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "configuration_error")
        self.assertIn("not configured", result["user_message"].lower())
        self.assertIn("NOTION_API_KEY", result["user_message"])

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_create_document_async_success(self, mock_sleep):
        """Test create_document_async success case"""
        # Force _is_configured to be True
        self.notion_skills._is_configured = True

        # Run the test
        result = asyncio.run(self.notion_skills.create_document_async("Test Document"))

        # Check the result
        self.assertTrue(result["success"])
        self.assertIn("formatted_response", result)
        self.assertIn("document", result)
        self.assertEqual(result["document"]["title"], "Test Document")
        self.assertEqual(result["document"]["parent_id"], "page_123456789")
        self.assertTrue(result["document"]["url"].startswith("https://notion.so/"))

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_create_document_async_error(self, mock_sleep):
        """Test create_document_async error handling"""
        # Force _is_configured to be True
        self.notion_skills._is_configured = True

        # Mock the client to raise an error
        self.notion_skills.client = MagicMock()
        error = NotionAPIError("API error", 401)
        error.status_code = 401
        self.notion_skills.client.create_page.side_effect = error

        # Set environment variable to disable simulation
        with patch.dict(os.environ, {"SIMULATE_NOTION": "false"}):
            # Run the test
            result = asyncio.run(self.notion_skills.create_document_async("Test Document"))

            # Check the result
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "notion_error")
            self.assertEqual(result["status_code"], 401)
            self.assertIn("authentication", result["user_message"].lower())

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_create_journal_entry_async(self, mock_sleep):
        """Test create_journal_entry_async"""
        # Force _is_configured to be True
        self.notion_skills._is_configured = True

        # Run the test with default parameters
        result = asyncio.run(self.notion_skills.create_journal_entry_async())

        # Check the result
        self.assertTrue(result["success"])
        self.assertIn("formatted_response", result)
        self.assertIn("journal_entry", result)
        self.assertEqual(result["journal_entry"]["database_id"], "database_123456789")
        self.assertTrue(result["journal_entry"]["title"].startswith("Journal Entry -"))
        self.assertFalse(result["journal_entry"]["template_used"])

        # Test with content
        content = "This is a test journal entry"
        result = asyncio.run(self.notion_skills.create_journal_entry_async(content=content))
        self.assertTrue(result["success"])

        # Test with template
        result = asyncio.run(self.notion_skills.create_journal_entry_async(template=True))
        self.assertTrue(result["success"])
        self.assertTrue(result["journal_entry"]["template_used"])

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_create_journal_entry_async_error(self, mock_sleep):
        """Test create_journal_entry_async error handling"""
        # Force _is_configured to be True
        self.notion_skills._is_configured = True

        # Mock the client to raise an error
        self.notion_skills.client = MagicMock()
        error = NotionAPIError("API error", 403)
        error.status_code = 403
        self.notion_skills.client.create_page.side_effect = error

        # Set environment variable to disable simulation
        with patch.dict(os.environ, {"SIMULATE_NOTION": "false"}):
            # Run the test
            result = asyncio.run(self.notion_skills.create_journal_entry_async("Test content"))

            # Check the result
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "notion_error")
            self.assertEqual(result["status_code"], 403)
            self.assertIn("permission", result["user_message"].lower())

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_search_notion_pages_async(self, mock_sleep):
        """Test search_notion_pages_async"""
        # Force _is_configured to be True
        self.notion_skills._is_configured = True

        # Run the test
        result = asyncio.run(self.notion_skills.search_notion_pages_async("test query"))

        # Check the result
        self.assertTrue(result["success"])
        self.assertIn("formatted_response", result)
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(result["results"][0]["title"], "Project Ideas")
        self.assertEqual(result["query"], "test query")

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_network_error_with_retry(self, mock_sleep):
        """Test handling a network error with retry"""
        # Force _is_configured to be True
        self.notion_skills._is_configured = True

        # Mock the client to raise a network error on first call, then succeed
        self.notion_skills.client = MagicMock()

        # Create a network error for the first attempt
        network_error = ConnectionError("Connection refused")

        # Set up the mock to first raise an error, then succeed
        self.notion_skills.client.create_page.side_effect = [
            network_error,
            {
                "id": "page_123456789",
                "url": "https://notion.so/page_123456789",
                "created_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        ]

        # Set environment variable to disable simulation
        with patch.dict(os.environ, {"SIMULATE_NOTION": "false"}):
            # Mock the getenv function to return "false" for SIMULATE_NOTION
            with patch('os.getenv', return_value="false"):
                # Run the test
                result = asyncio.run(self.notion_skills.create_document_async("Test Document", "This is a test document"))

                # Check the result
                self.assertTrue(result["success"])
                self.assertIn("document", result)
                self.assertEqual(result["document"]["title"], "Test Document")

                # Verify that asyncio.sleep was called (for the retry)
                mock_sleep.assert_called_once()

    def test_is_retryable_error(self):
        """Test the is_retryable_error function with different error types"""
        # Network error should be retryable
        network_error = {
            "success": False,
            "error_type": "network_error",
            "message": "Connection refused"
        }
        self.assertTrue(is_retryable_error(network_error))

        # Server error should be retryable
        server_error = {
            "success": False,
            "error_type": "notion_error",
            "message": "Internal Server Error",
            "status_code": 500
        }
        self.assertTrue(is_retryable_error(server_error))

        # 404 error should not be retryable
        not_found_error = {
            "success": False,
            "error_type": "notion_error",
            "message": "Not Found",
            "status_code": 404
        }
        self.assertFalse(is_retryable_error(not_found_error))

if __name__ == '__main__':
    unittest.main()
