"""
Notion API Client for General Pulse
Provides async methods for interacting with the Notion API
"""

import os
import json
import aiohttp
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = structlog.get_logger("notion_client")

class NotionAPIError(Exception):
    """Exception raised for Notion API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class NotionClient:
    """
    Async client for the Notion API
    """
    
    def __init__(self, api_key: Optional[str] = None, notion_version: str = "2022-06-28"):
        """
        Initialize the Notion client
        
        Args:
            api_key: Notion API key (defaults to NOTION_API_KEY env var)
            notion_version: Notion API version
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.notion_version = notion_version
        self.base_url = "https://api.notion.com/v1"
        self.logger = structlog.get_logger("notion_client")
        
        # Check if API key is available
        self._is_configured = self.api_key is not None
        
        if not self._is_configured:
            self.logger.warning("Notion API key not found")
    
    def is_configured(self) -> bool:
        """
        Check if the client is configured with an API key
        
        Returns:
            True if configured, False otherwise
        """
        return self._is_configured
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Notion API
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data
            
        Returns:
            Response data
            
        Raises:
            NotionAPIError: If the request fails
        """
        if not self._is_configured:
            raise NotionAPIError("Notion API key not configured")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        error_message = response_data.get("message", "Unknown error")
                        raise NotionAPIError(
                            f"Notion API error: {error_message}",
                            status_code=response.status,
                            response=response_data
                        )
                    
                    return response_data
        except aiohttp.ClientError as e:
            raise NotionAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise NotionAPIError("Invalid JSON response from Notion API")
    
    async def search(self, query: str, filter_type: Optional[str] = None) -> Dict:
        """
        Search Notion pages
        
        Args:
            query: Search query
            filter_type: Filter by object type (page, database)
            
        Returns:
            Search results
        """
        data = {"query": query}
        
        if filter_type:
            data["filter"] = {"property": "object", "value": filter_type}
        
        return await self._make_request("POST", "search", data)
    
    async def create_page(self, parent_id: str, title: str, content: Optional[str] = None) -> Dict:
        """
        Create a new page
        
        Args:
            parent_id: Parent page or database ID
            title: Page title
            content: Page content
            
        Returns:
            Created page data
        """
        # Determine if parent is a page or database
        parent_type = "page_id"
        if parent_id.startswith("database_"):
            parent_type = "database_id"
        
        data = {
            "parent": {parent_type: parent_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        }
        
        # Add content if provided
        if content:
            data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]
        
        return await self._make_request("POST", "pages", data)
    
    async def get_page(self, page_id: str) -> Dict:
        """
        Get a page by ID
        
        Args:
            page_id: Page ID
            
        Returns:
            Page data
        """
        return await self._make_request("GET", f"pages/{page_id}")
    
    async def get_block_children(self, block_id: str) -> Dict:
        """
        Get children of a block
        
        Args:
            block_id: Block ID
            
        Returns:
            Block children data
        """
        return await self._make_request("GET", f"blocks/{block_id}/children")
    
    async def append_block_children(self, block_id: str, children: List[Dict]) -> Dict:
        """
        Append children to a block
        
        Args:
            block_id: Block ID
            children: List of block objects
            
        Returns:
            Updated block data
        """
        data = {"children": children}
        return await self._make_request("PATCH", f"blocks/{block_id}/children", data)
    
    def format_date(self, date_str: Optional[str] = None) -> str:
        """
        Format a date for Notion
        
        Args:
            date_str: Date string (defaults to today)
            
        Returns:
            Formatted date string
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        return date_str
