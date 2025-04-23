"""
Notion Integration Tool for General Pulse
Handles interaction with Notion databases and pages
"""

import os
import requests
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import logger, load_yaml_config, save_json_data, ensure_directory_exists

class NotionIntegration:
    """Tool for interacting with Notion databases and pages."""
    
    def __init__(self, config_path="configs/agent_config.yaml"):
        """Initialize Notion integration with configuration."""
        self.config_path = config_path
        self.logger = logger
        self.logger.debug(f"NotionIntegration initializing with config path: {config_path}")
        
        try:
            self.config = load_yaml_config(config_path)
            self.notion_config = self.config.get('integrations', {}).get('notion', {})
            self.enabled = self.notion_config.get('enabled', False)
            self.token_env = self.notion_config.get('token_env', 'NOTION_API_KEY')
            self.token = os.environ.get(self.token_env)
            self.version_env = self.notion_config.get('version_env', 'NOTION_VERSION')
            self.version = os.environ.get(self.version_env, '2022-06-28')
            self.base_url = "https://api.notion.com/v1"
            
            if self.enabled:
                self.logger.info("Notion integration enabled")
                if not self.token:
                    self.logger.warning(f"Notion token not found in environment variable: {self.token_env}")
            else:
                self.logger.info("Notion integration disabled")
        except Exception as e:
            self.logger.error(f"Error initializing Notion integration: {str(e)}", exc_info=True)
            self.config = {}
            self.notion_config = {}
            self.enabled = False
            self.token_env = 'NOTION_API_KEY'
            self.token = None
            self.version_env = 'NOTION_VERSION'
            self.version = '2022-06-28'
            self.base_url = "https://api.notion.com/v1"
    
    def is_configured(self):
        """Check if Notion integration is properly configured."""
        # Check for token first (most important)
        if not self.token:
            self.logger.warning("Notion API key not found. Please set NOTION_API_KEY in your .env file.")
            return False
            
        # Check if enabled in config (less important, default to True if token exists)
        if not self.notion_config:
            self.logger.warning("Notion configuration not found in config file. Using default settings.")
            # If token exists but no config, assume enabled
            return True
            
        configured = self.enabled and self.token is not None
        self.logger.debug(f"Notion integration configured: {configured}")
        return configured

    def get_user(self):
        """Get current user information from Notion API."""
        try:
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
            
            self.logger.info("Getting current user information")
            
            url = f"{self.base_url}/users/me"
            headers = self._get_headers()
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def list_databases(self):
        """List all databases that the integration has access to."""
        try:
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
            
            self.logger.info("Listing available databases")
            
            url = f"{self.base_url}/search"
            headers = self._get_headers()
            data = {
                "filter": {
                    "value": "database",
                    "property": "object"
                }
            }
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Cache the results
                self._cache_databases(result)
                return result
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            
            # Try to use cached data if available
            cached_data = self._get_cached_databases()
            if cached_data:
                self.logger.info("Using cached database list")
                cached_data["from_cache"] = True
                return cached_data
                
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error listing databases: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def get_database(self, database_id):
        """Get information about a specific database."""
        try:
            if not database_id:
                self.logger.warning("Missing database ID")
                return {"error": "Database ID is required"}
                
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
                
            self.logger.info(f"Getting database info: {database_id}")
            
            url = f"{self.base_url}/databases/{database_id}"
            headers = self._get_headers()
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                database_data = response.json()
                # Cache the result
                self._cache_database(database_id, database_data)
                return database_data
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            
            # Try to use cached data if available
            cached_data = self._get_cached_database(database_id)
            if cached_data:
                self.logger.info(f"Using cached data for database {database_id}")
                cached_data["from_cache"] = True
                return cached_data
                
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error getting database info: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def query_database(self, database_id, filter_params=None, sorts=None):
        """Query a database for pages with optional filters and sorting."""
        try:
            if not database_id:
                self.logger.warning("Missing database ID")
                return {"error": "Database ID is required"}
                
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
                
            self.logger.info(f"Querying database: {database_id}")
            
            url = f"{self.base_url}/databases/{database_id}/query"
            headers = self._get_headers()
            
            # Prepare request body
            body = {}
            if filter_params:
                body["filter"] = filter_params
            if sorts:
                body["sorts"] = sorts
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.post(url, headers=headers, json=body)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error querying database: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def create_page(self, title, content=None, parent_id=None, template="default"):
        """
        Create a new Notion page with the specified title and content.
        
        Args:
            title (str): The title of the new page
            content (str, optional): The content to add to the page. Can be plain text or markdown.
            parent_id (str, optional): The ID of the parent page or database. If None, uses a default parent page.
            template (str, optional): Template to use ('default', 'todo', 'notes', 'journal')
            
        Returns:
            dict: Information about the created page, including URL and success status
        """
        try:
            self.logger.info(f"Creating new Notion page: {title}")
            
            # Prepare the parent object
            if not parent_id:
                # If no parent specified, try to find a default page to use
                # We'll search for pages we can access
                pages_result = self._make_api_request("search", "POST", {
                    "filter": {
                        "value": "page",
                        "property": "object"
                    },
                    "page_size": 1
                })
                
                if pages_result and "results" in pages_result and len(pages_result["results"]) > 0:
                    # Use the first page as parent
                    parent_id = pages_result["results"][0]["id"]
                    self.logger.info(f"Using default parent page: {parent_id}")
                    parent = {"page_id": parent_id}
                else:
                    self.logger.error("No accessible pages found to use as parent")
                    return {
                        "success": False,
                        "error": "No accessible pages found to use as parent. Please specify a parent_id."
                    }
            else:
                # Use the provided parent_id
                # Determine if it's a page or database ID
                # For simplicity, we'll try as page_id first
                parent = {"page_id": parent_id}
            
            # Prepare the properties object (includes title)
            properties = {
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
            
            # Basic page creation payload
            payload = {
                "parent": parent,
                "properties": properties,
                "children": []
            }
            
            # If content is provided, prepare the children blocks
            if content:
                # Parse content and convert to Notion blocks
                children = self._text_to_blocks(content, template)
                payload["children"] = children
                
            # Make the API request to create the page
            response = self._make_api_request("pages", "POST", payload)
            
            # If page creation successful, return info including URL
            if response and "id" in response:
                page_id = response.get("id", "").replace("-", "")
                # Generate URL
                page_url = f"https://notion.so/{page_id}"
                
                return {
                    "success": True,
                    "page_id": page_id,
                    "url": page_url,
                    "title": title,
                    "response": response
                }
            else:
                self.logger.error(f"Failed to create page: {response}")
                return {
                    "success": False,
                    "error": f"Failed to create page: {response.get('error', 'Unknown error')}",
                    "response": response
                }
                
        except Exception as e:
            self.logger.error(f"Error creating page: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error creating page: {str(e)}"
            }
            
    def _text_to_blocks(self, content, template="default"):
        """
        Convert text content to Notion blocks based on template type.
        
        Args:
            content (str): The content to convert (plain text or markdown)
            template (str): The template type to use
            
        Returns:
            list: List of Notion block objects
        """
        blocks = []
        
        # Split content into lines
        lines = content.split("\n")
        
        if template == "todo":
            # Create a to-do list
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if it's a completed to-do item
                completed = False
                if line.startswith("- [x]") or line.startswith("* [x]"):
                    completed = True
                    line = line[5:].strip()
                elif line.startswith("- [ ]") or line.startswith("* [ ]"):
                    line = line[5:].strip()
                elif line.startswith("-") or line.startswith("*"):
                    line = line[1:].strip()
                    
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": line}}],
                        "checked": completed
                    }
                })
                
        elif template == "journal":
            # Create a journal template with headings and paragraphs
            current_heading = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for headings
                if line.startswith("# "):
                    blocks.append({
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                        }
                    })
                    current_heading = "h1"
                elif line.startswith("## "):
                    blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                        }
                    })
                    current_heading = "h2"
                elif line.startswith("### "):
                    blocks.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                        }
                    })
                    current_heading = "h3"
                else:
                    # Regular paragraph
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        }
                    })
        else:
            # Default template - simple paragraphs
            for line in lines:
                line = line.strip()
                if not line:
                    # Add a blank line
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": []
                        }
                    })
                else:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        }
                    })
                    
        return blocks
    
    def get_page(self, page_id):
        """Get information about a specific page."""
        try:
            if not page_id:
                self.logger.warning("Missing page ID")
                return {"error": "Page ID is required"}
                
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
                
            self.logger.info(f"Getting page info: {page_id}")
            
            url = f"{self.base_url}/pages/{page_id}"
            headers = self._get_headers()
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                page_data = response.json()
                # Cache the result
                self._cache_page(page_id, page_data)
                return page_data
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            
            # Try to use cached data if available
            cached_data = self._get_cached_page(page_id)
            if cached_data:
                self.logger.info(f"Using cached data for page {page_id}")
                cached_data["from_cache"] = True
                return cached_data
                
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error getting page info: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def update_page(self, page_id, properties=None):
        """Update properties of an existing page."""
        try:
            if not page_id:
                self.logger.warning("Missing page ID")
                return {"error": "Page ID is required"}
                
            if not properties:
                self.logger.warning("No properties provided for update")
                return {"error": "At least one property must be provided for update"}
                
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
                
            self.logger.info(f"Updating page: {page_id}")
            
            url = f"{self.base_url}/pages/{page_id}"
            headers = self._get_headers()
            
            # Prepare request body
            body = {
                "properties": properties
            }
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.patch(url, headers=headers, json=body)
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Page updated successfully: {page_id}")
                # Invalidate cache for this page
                self._invalidate_page_cache(page_id)
                return result
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error updating page: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def get_block_children(self, block_id):
        """Get children blocks of a page or block."""
        try:
            if not block_id:
                self.logger.warning("Missing block ID")
                return {"error": "Block ID is required"}
                
            if not self.is_configured():
                self.logger.warning("Notion integration not configured")
                return {"error": "Notion integration not configured"}
                
            self.logger.info(f"Getting children blocks of: {block_id}")
            
            url = f"{self.base_url}/blocks/{block_id}/children"
            headers = self._get_headers()
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error getting block children: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def _get_headers(self):
        """Get the headers for Notion API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }
    
    def _make_api_request(self, endpoint, method="GET", data=None):
        """
        Make an API request to the Notion API.
        
        Args:
            endpoint (str): API endpoint (e.g., "pages", "databases")
            method (str): HTTP method (GET, POST, PATCH, DELETE)
            data (dict, optional): Data to send with the request
            
        Returns:
            dict: Response from the API or error information
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = self._get_headers()
            
            self.logger.debug(f"Making {method} request to: {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return {"error": f"Unsupported HTTP method: {method}"}
                
            # Check for successful response
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {"error": f"Notion API error: {response.status_code}", "details": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {str(e)}", exc_info=True)
            return {"error": f"Notion API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error making API request: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}
    
    def _cache_databases(self, data):
        """Cache databases list to a local file."""
        try:
            storage_dir = "memory/notion"
            ensure_directory_exists(storage_dir)
            
            cache_file = os.path.join(storage_dir, "databases_list.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                data_to_cache = data.copy()
                data_to_cache["cache_time"] = datetime.now().isoformat()
                json.dump(data_to_cache, f, indent=2)
                
            self.logger.debug("Cached databases list")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache databases list: {str(e)}", exc_info=True)
            return False
    
    def _get_cached_databases(self):
        """Retrieve cached databases list."""
        try:
            storage_dir = "memory/notion"
            cache_file = os.path.join(storage_dir, "databases_list.json")
            
            if not os.path.exists(cache_file):
                return None
                
            # Check if cache is fresh (less than 1 hour old)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() > 3600:  # 1 hour in seconds
                self.logger.debug(f"Cache for databases list is too old ({cache_age})")
                return None
                
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error retrieving cached databases list: {str(e)}", exc_info=True)
            return None
    
    def _cache_database(self, database_id, data):
        """Cache database information to a local file."""
        try:
            storage_dir = "memory/notion"
            ensure_directory_exists(storage_dir)
            
            cache_file = os.path.join(storage_dir, f"database_{database_id}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                data_to_cache = data.copy()
                data_to_cache["cache_time"] = datetime.now().isoformat()
                json.dump(data_to_cache, f, indent=2)
                
            self.logger.debug(f"Cached database info for {database_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache database info: {str(e)}", exc_info=True)
            return False
    
    def _get_cached_database(self, database_id):
        """Retrieve cached database information."""
        try:
            storage_dir = "memory/notion"
            cache_file = os.path.join(storage_dir, f"database_{database_id}.json")
            
            if not os.path.exists(cache_file):
                return None
                
            # Check if cache is fresh (less than 1 hour old)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() > 3600:  # 1 hour in seconds
                self.logger.debug(f"Cache for database {database_id} is too old ({cache_age})")
                return None
                
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error retrieving cached database info: {str(e)}", exc_info=True)
            return None
    
    def _cache_page(self, page_id, data):
        """Cache page information to a local file."""
        try:
            storage_dir = "memory/notion"
            ensure_directory_exists(storage_dir)
            
            cache_file = os.path.join(storage_dir, f"page_{page_id}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                data_to_cache = data.copy()
                data_to_cache["cache_time"] = datetime.now().isoformat()
                json.dump(data_to_cache, f, indent=2)
                
            self.logger.debug(f"Cached page info for {page_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache page info: {str(e)}", exc_info=True)
            return False
    
    def _get_cached_page(self, page_id):
        """Retrieve cached page information."""
        try:
            storage_dir = "memory/notion"
            cache_file = os.path.join(storage_dir, f"page_{page_id}.json")
            
            if not os.path.exists(cache_file):
                return None
                
            # Check if cache is fresh (less than 1 hour old)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() > 3600:  # 1 hour in seconds
                self.logger.debug(f"Cache for page {page_id} is too old ({cache_age})")
                return None
                
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error retrieving cached page info: {str(e)}", exc_info=True)
            return None
    
    def _invalidate_page_cache(self, page_id):
        """Invalidate cached page information."""
        try:
            storage_dir = "memory/notion"
            cache_file = os.path.join(storage_dir, f"page_{page_id}.json")
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
                self.logger.debug(f"Invalidated cache for page {page_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error invalidating page cache: {str(e)}", exc_info=True)
            return False
    
    def extract_id_from_url(self, url):
        """
        Extract Notion page or database ID from a URL.
        
        Args:
            url (str): The Notion URL, e.g., 'https://www.notion.so/Username/Page-Name-1d334ba186ed80b9800fc1dc708cdad4'
            
        Returns:
            str: The extracted page or database ID, or None if no ID could be extracted
        """
        try:
            if not url:
                self.logger.warning("No URL provided")
                return None
                
            self.logger.debug(f"Extracting ID from URL: {url}")
            
            # Handle different URL formats
            # Format 1: https://www.notion.so/workspace/pagename-1d334ba186ed80b9800fc1dc708cdad4
            # Format 2: https://www.notion.so/1d334ba186ed80b9800fc1dc708cdad4
            # Format 3: https://notion.so/1d334ba186ed80b9800fc1dc708cdad4
            
            # Try to extract using regex for 32-character hex ID
            import re
            pattern = r'([a-f0-9]{32})'
            match = re.search(pattern, url)
            
            if match:
                page_id = match.group(1)
                self.logger.debug(f"Extracted ID: {page_id}")
                return page_id
                
            # Try to extract the last path component
            from urllib.parse import urlparse
            path = urlparse(url).path
            if path:
                parts = path.strip('/').split('/')
                last_part = parts[-1] if parts else None
                
                # Check if last part contains a dash followed by 32 hex chars
                if last_part and '-' in last_part:
                    potential_id = last_part.split('-')[-1]
                    if re.match(r'^[a-f0-9]{32}$', potential_id):
                        self.logger.debug(f"Extracted ID: {potential_id}")
                        return potential_id
            
            self.logger.warning(f"Could not extract ID from URL: {url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting ID from URL: {str(e)}", exc_info=True)
            return None
            
    def analyze_journal_page(self, url_or_id):
        """
        Analyze a Notion journal page to extract key information.
        
        Args:
            url_or_id (str): Either a Notion URL or a page ID
            
        Returns:
            dict: Analysis results containing page content and extracted information
        """
        try:
            # Determine if input is URL or ID
            page_id = url_or_id
            if '://' in url_or_id:  # It's a URL
                page_id = self.extract_id_from_url(url_or_id)
                if not page_id:
                    return {"error": "Could not extract page ID from URL"}
            
            self.logger.info(f"Analyzing journal page with ID: {page_id}")
            
            # Get page content
            page_info = self.get_page(page_id)
            if not page_info or 'error' in page_info:
                return {"error": f"Failed to retrieve page: {page_info.get('error', 'Unknown error')}"}
            
            # Get page blocks (content)
            blocks = self.get_block_children(page_id)
            if not blocks or 'error' in blocks:
                return {"error": f"Failed to retrieve page content: {blocks.get('error', 'Unknown error')}"}
            
            # Extract page properties
            properties = page_info.get('properties', {})
            title = self._extract_property_value(properties.get('title', {}))
            
            # Process blocks to extract text content
            content = self._process_blocks_to_text(blocks.get('results', []))
            
            # Basic sentiment and topic analysis
            sentiment = self._analyze_sentiment(content)
            topics = self._extract_topics(content)
            
            return {
                "title": title,
                "content": content,
                "sentiment": sentiment,
                "topics": topics,
                "word_count": len(content.split()),
                "character_count": len(content),
                "page_id": page_id,
                "raw_page": page_info,
                "raw_blocks": blocks
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing journal page: {str(e)}", exc_info=True)
            return {"error": f"Failed to analyze journal: {str(e)}"}
    
    def _extract_property_value(self, property_data):
        """Extract the actual value from a Notion property object."""
        if not property_data:
            return ""
            
        property_type = property_data.get('type')
        if property_type == 'title':
            title_parts = property_data.get('title', [])
            return "".join([part.get('plain_text', '') for part in title_parts])
        elif property_type == 'rich_text':
            text_parts = property_data.get('rich_text', [])
            return "".join([part.get('plain_text', '') for part in text_parts])
        elif property_type == 'date':
            date_value = property_data.get('date', {})
            return date_value.get('start', '')
        else:
            # Handle other property types as needed
            return str(property_data)
    
    def _process_blocks_to_text(self, blocks):
        """Process Notion blocks into plain text content."""
        text_content = []
        
        for block in blocks:
            block_type = block.get('type')
            if block_type == 'paragraph':
                paragraph = block.get('paragraph', {})
                text_parts = paragraph.get('rich_text', [])
                if text_parts:
                    text_content.append("".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'heading_1':
                heading = block.get('heading_1', {})
                text_parts = heading.get('rich_text', [])
                if text_parts:
                    text_content.append("# " + "".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'heading_2':
                heading = block.get('heading_2', {})
                text_parts = heading.get('rich_text', [])
                if text_parts:
                    text_content.append("## " + "".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'heading_3':
                heading = block.get('heading_3', {})
                text_parts = heading.get('rich_text', [])
                if text_parts:
                    text_content.append("### " + "".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'bulleted_list_item':
                item = block.get('bulleted_list_item', {})
                text_parts = item.get('rich_text', [])
                if text_parts:
                    text_content.append("• " + "".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'numbered_list_item':
                item = block.get('numbered_list_item', {})
                text_parts = item.get('rich_text', [])
                if text_parts:
                    text_content.append("1. " + "".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'to_do':
                todo = block.get('to_do', {})
                text_parts = todo.get('rich_text', [])
                checked = todo.get('checked', False)
                prefix = "[x] " if checked else "[ ] "
                if text_parts:
                    text_content.append(prefix + "".join([part.get('plain_text', '') for part in text_parts]))
            elif block_type == 'toggle':
                toggle = block.get('toggle', {})
                text_parts = toggle.get('rich_text', [])
                if text_parts:
                    text_content.append("▶ " + "".join([part.get('plain_text', '') for part in text_parts]))
                    
        return "\n\n".join(text_content)
    
    def _analyze_sentiment(self, text):
        """Basic sentiment analysis on text content."""
        # This is a placeholder for actual sentiment analysis
        # In a real implementation, you might use NLTK, TextBlob, or an API
        positive_words = ['good', 'great', 'excellent', 'happy', 'positive', 'joy', 'love', 'wonderful']
        negative_words = ['bad', 'terrible', 'sad', 'negative', 'awful', 'hate', 'poor', 'disappointing']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count * 2:
            return "very positive"
        elif positive_count > negative_count:
            return "somewhat positive"
        elif negative_count > positive_count * 2:
            return "very negative"
        elif negative_count > positive_count:
            return "somewhat negative"
        else:
            return "neutral"
    
    def _extract_topics(self, text):
        """Extract potential topics from text content."""
        # This is a placeholder for actual topic extraction
        # In a real implementation, you might use NLP techniques or an API
        common_topics = {
            "work": ["meeting", "project", "deadline", "work", "job", "task", "email", "client"],
            "health": ["exercise", "workout", "gym", "health", "doctor", "medicine", "diet", "sleep"],
            "personal": ["family", "friend", "relationship", "home", "house", "personal", "life"],
            "learning": ["learn", "study", "book", "course", "class", "knowledge", "skill"],
            "finance": ["money", "finance", "budget", "invest", "expense", "income", "saving"],
        }
        
        text_lower = text.lower()
        found_topics = {}
        
        for topic, keywords in common_topics.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                found_topics[topic] = matches
                
        # Sort by number of matches in descending order
        sorted_topics = sorted(found_topics.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:3]]  # Return top 3 topics
        
    def append_journal_entry(self, page_id_or_url, entry_content, date=None):
        """
        Append a journal entry to an existing Notion page.
        
        Args:
            page_id_or_url (str): The Notion page ID or URL to append to
            entry_content (str): The content of the journal entry
            date (str, optional): The date for the entry. If None, uses current date.
            
        Returns:
            dict: Result of the operation with success status and details
        """
        try:
            # Extract page ID if URL provided
            page_id = page_id_or_url
            if '://' in page_id_or_url:
                page_id = self.extract_id_from_url(page_id_or_url)
                if not page_id:
                    return {
                        "success": False,
                        "error": "Could not extract page ID from URL"
                    }
            
            self.logger.info(f"Appending journal entry to page: {page_id}")
            
            # Get current date if not provided
            from datetime import datetime
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
                
            # Format the entry with date header
            formatted_entry = f"## {date}\n\n{entry_content}"
            
            # Convert entry to Notion blocks
            blocks = self._text_to_blocks(formatted_entry, template="journal")
            
            # Get current children to append after them
            current_blocks = self.get_block_children(page_id)
            if "error" in current_blocks:
                return {
                    "success": False,
                    "error": f"Failed to get existing content: {current_blocks.get('error')}"
                }
                
            # Add a separator if there's existing content
            if current_blocks.get("results", []):
                blocks.insert(0, {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            
            # Make API request to append blocks
            url = f"{self.base_url}/blocks/{page_id}/children"
            headers = self._get_headers()
            
            payload = {
                "children": blocks
            }
            
            self.logger.debug(f"Sending request to: {url}")
            response = requests.patch(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Journal entry appended successfully to page: {page_id}")
                return {
                    "success": True,
                    "page_id": page_id,
                    "date": date,
                    "block_count": len(blocks)
                }
            else:
                self.logger.error(f"Notion API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Failed to append journal entry: API error {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            self.logger.error(f"Error appending journal entry: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error appending journal entry: {str(e)}"
            }
            
    def create_daily_journal_entry(self, journal_page_url, content=None):
        """
        Create a daily journal entry on a specific Notion page.
        
        Args:
            journal_page_url (str): URL or ID of the journal page
            content (str, optional): Journal entry content. If None, generates a template.
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Get current date
            from datetime import datetime
            today = datetime.now()
            date_str = today.strftime("%Y-%m-%d")
            weekday = today.strftime("%A")
            
            # Generate a template if no content provided
            if not content:
                content = (
                    f"### {weekday}\n\n"
                    "#### Accomplishments\n\n"
                    "- \n\n"
                    "#### Challenges\n\n"
                    "- \n\n"
                    "#### Tomorrow's Focus\n\n"
                    "- "
                )
            
            # Add header with date
            header = f"## {date_str}"
            if header not in content:
                content = f"{header}\n\n{content}"
                
            # Append to the journal page
            result = self.append_journal_entry(journal_page_url, content, date_str)
            
            if result.get("success"):
                page_id = result.get("page_id")
                page_url = f"https://notion.so/{page_id}"
                
                return {
                    "success": True,
                    "message": f"Daily journal entry for {date_str} created successfully",
                    "date": date_str,
                    "url": page_url
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Error creating daily journal entry: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error creating daily journal entry: {str(e)}"
            }

# Global function for easier access from other modules
def is_notion_configured():
    """External helper to check if Notion integration is configured"""
    try:
        notion = NotionIntegration()
        return notion.is_configured()
    except Exception as e:
        logger.error(f"Error checking Notion configuration: {str(e)}")
        return False 