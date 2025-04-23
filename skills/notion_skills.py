"""
Notion Skills Module for General Pulse
Provides functionality for interacting with Notion
"""

import os
import re
import json
import asyncio
import time
import structlog
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from utils.notion_client import NotionClient, NotionAPIError
from utils.integration_error_handler import with_error_handling, handle_notion_error, format_user_friendly_error, is_retryable_error

logger = structlog.get_logger("notion_skills")

class NotionSkills:
    """
    Provides functionality for interacting with Notion
    """

    def __init__(self):
        """Initialize Notion skills"""
        self.logger = structlog.get_logger("notion_skills")

        # Load environment variables
        load_dotenv()

        # Initialize Notion client
        self.client = NotionClient()

        # Check if Notion is configured
        self._is_configured = self.client.is_configured()

        if not self._is_configured:
            self.logger.warning("Notion API key not found in environment variables")
        else:
            self.logger.info("Notion skills initialized")

    def is_configured(self) -> bool:
        """
        Check if Notion is configured

        Returns:
            bool: True if Notion is configured, False otherwise
        """
        return self._is_configured

    def extract_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract page ID from Notion URL

        Args:
            url: Notion URL

        Returns:
            Extracted page ID or None if not found
        """
        # Pattern for extracting page ID from various Notion URL formats
        patterns = [
            # UUID format (8-4-4-4-12)
            r'([a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12})',
            # Title with 32-char ID
            r'notion\.so/[^/]*?([a-zA-Z0-9]{32})',
            # Raw 32-character ID
            r'([a-zA-Z0-9]{32})',
            # ID after a dash
            r'-([a-zA-Z0-9]{32})',
            # ID after a slash
            r'/([a-zA-Z0-9]{32})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    @with_error_handling("notion", "search_pages")
    async def search_notion_pages_async(self, query: str, max_retries=3) -> Dict[str, Any]:
        """
        Search Notion pages

        Args:
            query: Search query
            max_retries: Maximum number of retries for retryable errors

        Returns:
            Dictionary with search results or error details
        """
        if not self._is_configured:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "Notion API not configured",
                "user_message": "Notion is not configured. Please set the NOTION_API_KEY environment variable."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # In a real implementation, we would call the Notion API
                # For now, we'll simulate the search
                if os.getenv("SIMULATE_NOTION", "true").lower() == "true":
                    # Simulate search results
                    simulated_results = [
                        {"id": "page1", "title": "Project Ideas", "last_edited": "2 days ago"},
                        {"id": "page2", "title": "Meeting Notes", "last_edited": "yesterday"},
                        {"id": "page3", "title": "Research Document", "last_edited": "1 week ago"}
                    ]

                    # Format the response
                    formatted_response = f"Notion search results for: {query}\n\n"
                    for i, result in enumerate(simulated_results, 1):
                        formatted_response += f"{i}. {result['title']} (last edited {result['last_edited']})\n"

                    return {
                        "success": True,
                        "formatted_response": formatted_response,
                        "results": simulated_results,
                        "query": query
                    }
                else:
                    # Actually search Notion
                    results = await self.client.search(query)

                    # Format the response
                    formatted_response = f"Notion search results for: {query}\n\n"
                    for i, result in enumerate(results, 1):
                        title = result.get("title", "Untitled")
                        last_edited = result.get("last_edited_time", "unknown")
                        formatted_response += f"{i}. {title} (last edited {last_edited})\n"

                    return {
                        "success": True,
                        "formatted_response": formatted_response,
                        "results": results,
                        "query": query
                    }

            except Exception as e:
                last_error = e
                error_dict = handle_notion_error(e, "search_pages")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying search_pages ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}

    @with_error_handling("notion", "create_document")
    async def create_document_async(self, title: str, content: str = "", max_retries=3) -> Dict[str, Any]:
        """
        Create a Notion document

        Args:
            title: Document title
            content: Document content
            max_retries: Maximum number of retries for retryable errors

        Returns:
            Dictionary with document information or error details
        """
        if not self._is_configured:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "Notion API not configured",
                "user_message": "Notion is not configured. Please set the NOTION_API_KEY environment variable."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # In a real implementation, we would get the parent page ID from settings
                # For now, we'll simulate the creation
                parent_id = "page_123456789"

                # Create the page
                # In simulation mode, we don't actually call the API
                if os.getenv("SIMULATE_NOTION", "true").lower() == "true":
                    # Simulate document creation
                    preview = f"Content preview: {content[:100]}..." if len(content) > 100 else content
                    formatted_response = f"Notion document created: {title}\n\n{preview}"

                    # Simulate a document ID
                    document_id = f"page_{int(time.time())}"

                    return {
                        "success": True,
                        "formatted_response": formatted_response,
                        "document": {
                            "id": document_id,
                            "title": title,
                            "parent_id": parent_id,
                            "url": f"https://notion.so/{document_id}",
                            "created_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        }
                    }
                else:
                    # Actually create the page
                    result = await self.client.create_page(parent_id, title, content)

                    return {
                        "success": True,
                        "formatted_response": f"Notion document created: {title}",
                        "document": {
                            "id": result.get("id"),
                            "title": title,
                            "parent_id": parent_id,
                            "url": result.get("url"),
                            "created_time": result.get("created_time")
                        }
                    }

            except Exception as e:
                last_error = e
                error_dict = handle_notion_error(e, "create_document")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying create_document ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}

    @with_error_handling("notion", "create_journal_entry")
    async def create_journal_entry_async(self, content: str = "", template: bool = False, max_retries=3) -> Dict[str, Any]:
        """
        Create a journal entry in Notion

        Args:
            content: Journal entry content
            template: Whether to use a template
            max_retries: Maximum number of retries for retryable errors

        Returns:
            Dictionary with journal entry information or error details
        """
        if not self._is_configured:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "Notion API not configured",
                "user_message": "Notion is not configured. Please set the NOTION_API_KEY environment variable."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Create entry content with template if requested
                if template:
                    # Use a template
                    entry_content = "# Daily Journal Entry\n\n" + \
                                f"## Date: {self._get_current_date()}\n\n" + \
                                "## Highlights\n- \n- \n- \n\n" + \
                                "## Challenges\n- \n- \n- \n\n" + \
                                "## Tomorrow's Focus\n- \n- \n- "
                else:
                    # Use provided content
                    entry_content = f"# Journal Entry - {self._get_current_date()}\n\n{content}"

                # In a real implementation, we would get the journal database ID from settings
                # For now, we'll simulate the creation
                journal_db_id = "database_123456789"
                title = f"Journal Entry - {self._get_current_date()}"

                # Create the journal entry
                # In simulation mode, we don't actually call the API
                if os.getenv("SIMULATE_NOTION", "true").lower() == "true":
                    # Simulate journal entry creation
                    preview = f"Content preview: {entry_content[:100]}..." if len(entry_content) > 100 else entry_content
                    formatted_response = f"Journal entry created for {self._get_current_date()}"

                    # Simulate an entry ID
                    entry_id = f"page_{int(time.time())}"

                    return {
                        "success": True,
                        "formatted_response": formatted_response,
                        "journal_entry": {
                            "id": entry_id,
                            "title": title,
                            "date": self._get_current_date(),
                            "database_id": journal_db_id,
                            "url": f"https://notion.so/{entry_id}",
                            "created_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "template_used": template
                        }
                    }
                else:
                    # Actually create the journal entry
                    result = await self.client.create_page(journal_db_id, title, entry_content)

                    return {
                        "success": True,
                        "formatted_response": f"Journal entry created for {self._get_current_date()}",
                        "journal_entry": {
                            "id": result.get("id"),
                            "title": title,
                            "date": self._get_current_date(),
                            "database_id": journal_db_id,
                            "url": result.get("url"),
                            "created_time": result.get("created_time"),
                            "template_used": template
                        }
                    }

            except Exception as e:
                last_error = e
                error_dict = handle_notion_error(e, "create_journal_entry")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying create_journal_entry ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}

    def _get_current_date(self) -> str:
        """
        Get current date formatted for journal entries

        Returns:
            Formatted date string
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
