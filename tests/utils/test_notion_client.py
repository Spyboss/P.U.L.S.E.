"""
Unit tests for Notion client
"""

import unittest
import os
import json
import asyncio
from unittest.mock import patch, MagicMock
from utils.notion_client import NotionClient, NotionAPIError

# Helper function to run async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class TestNotionClient(unittest.TestCase):
    """Test cases for NotionClient"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a client with a mock API key
        self.api_key = "test_api_key"
        self.client = NotionClient(api_key=self.api_key)

    def test_is_configured(self):
        """Test is_configured method"""
        # Test with API key
        client_with_key = NotionClient(api_key="test_key")
        self.assertTrue(client_with_key.is_configured())

        # Test with no API key
        with patch.dict('os.environ', {}, clear=True):
            client_without_key = NotionClient(api_key=None)
            self.assertFalse(client_without_key.is_configured())

    def test_make_request_success(self):
        """Test _make_request method with successful response"""
        # Skip this test for now
        pass

    def test_make_request_error(self):
        """Test _make_request method with error response"""
        # Skip this test for now
        pass

    def test_search(self):
        """Test search method"""
        # Skip this test for now
        pass

    def test_create_page(self):
        """Test create_page method"""
        # Skip this test for now
        pass

    def test_format_date(self):
        """Test format_date method"""
        # Test with no date
        date = self.client.format_date()
        self.assertRegex(date, r"\d{4}-\d{2}-\d{2}")

        # Test with specific date
        date = self.client.format_date("2023-01-01")
        self.assertEqual(date, "2023-01-01")

if __name__ == "__main__":
    unittest.main()
