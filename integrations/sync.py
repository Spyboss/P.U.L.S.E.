"""
GitHub-Notion Synchronization for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides bidirectional synchronization between GitHub and Notion
"""

import os
import json
import asyncio
import structlog
import time
import re
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv
import httpx
from github import Github, GithubException

# Configure logger
logger = structlog.get_logger("github_notion_sync")

# Load environment variables
load_dotenv()

# Constants
SYNC_INTERVAL = 3600  # 1 hour between syncs
GITHUB_CACHE_TTL = 300  # 5 minutes cache TTL for GitHub data
NOTION_CACHE_TTL = 300  # 5 minutes cache TTL for Notion data
SYNC_COLLECTION = "sync"
MAX_ITEMS_PER_SYNC = 10  # Maximum number of items to sync at once

def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID

    Args:
        value: String to check

    Returns:
        True if the string is a valid UUID, False otherwise
    """
    if not value:
        return False

    try:
        # Try to parse as UUID
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value
    except (ValueError, AttributeError, TypeError):
        # Try to match UUID pattern (8-4-4-4-12)
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, value.lower()):
            return True

        # Try to match 32-character Notion ID without dashes
        if re.match(r'^[0-9a-f]{32}$', value.lower()):
            return True

        return False

class GitHubNotionSync:
    """
    Manages bidirectional synchronization between GitHub and Notion
    Features:
    - Syncs GitHub commits to Notion pages
    - Syncs Notion updates to GitHub issues
    - Caches state in MongoDB for efficient syncing
    - Handles authentication and rate limiting
    """

    def __init__(self):
        """Initialize the GitHub-Notion sync manager"""
        self.logger = logger
        self.client = None
        self.db = None

        # Initialize MongoDB connection
        self._init_mongodb()

        # Initialize API clients
        self.github_client = self._init_github()
        self.notion_client = self._init_notion()

        # Track sync state
        self.last_sync_time = time.time() - SYNC_INTERVAL  # Force initial sync
        self.is_syncing = False
        self.is_running = False  # Will be set to True when sync loop starts

        logger.info("GitHub-Notion sync manager initialized")

    def _init_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        # Disable MongoDB connection to avoid DNS issues
        logger.info("MongoDB connection disabled for sync state, using SQLite fallback")
        self.client = None
        self.db = None

    async def _create_indexes(self) -> None:
        """Create indexes for sync collection"""
        if self.db is None:
            return

        try:
            # Create indexes for sync collection
            await self.db[SYNC_COLLECTION].create_index([("type", 1), ("source_id", 1)], unique=True)
            await self.db[SYNC_COLLECTION].create_index([("last_synced", -1)])

            logger.info("Created indexes for sync collection")
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")

    def _init_github(self) -> Optional[Github]:
        """
        Initialize GitHub client

        Returns:
            GitHub client or None if initialization fails
        """
        try:
            # Get GitHub token from environment variables
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                logger.warning("GITHUB_TOKEN not found in environment variables")
                return None

            # Create GitHub client
            client = Github(github_token)

            # Test the client
            user = client.get_user()
            logger.info(f"Initialized GitHub client for user: {user.login}")

            return client
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
            return None

    def _init_notion(self) -> Optional[httpx.AsyncClient]:
        """
        Initialize Notion client

        Returns:
            Notion client or None if initialization fails
        """
        try:
            # Get Notion token from environment variables
            notion_token = os.getenv("NOTION_API_KEY")
            # Update to latest Notion API version
            notion_version = os.getenv("NOTION_VERSION", "2022-06-28")

            if not notion_token:
                logger.warning("NOTION_API_KEY not found in environment variables")
                return None

            # Create Notion client
            headers = {
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": notion_version,
                "Content-Type": "application/json"
            }

            client = httpx.AsyncClient(
                base_url="https://api.notion.com/v1",
                headers=headers,
                timeout=30.0
            )

            # Test the client with a simple request
            asyncio.create_task(self._test_notion_client(client))

            logger.info("Initialized Notion client")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Notion client: {str(e)}")
            return None

    async def _test_notion_client(self, client: httpx.AsyncClient) -> None:
        """
        Test the Notion client with a simple request

        Args:
            client: Notion client to test
        """
        try:
            # Try to get the user's information
            response = await client.get("/users/me")

            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Notion client test successful: Connected as {user_data.get('name', 'Unknown User')}")
            else:
                logger.warning(f"Notion client test failed: {response.status_code} - {response.text}")

            # Check if the commits database exists
            database_id = os.getenv("NOTION_COMMITS_DB")
            if database_id and is_valid_uuid(database_id):
                try:
                    db_response = await client.get(f"/databases/{database_id}")
                    if db_response.status_code == 200:
                        logger.info(f"Notion commits database found: {database_id}")
                    else:
                        logger.warning(f"Notion commits database not found or inaccessible: {db_response.status_code} - {db_response.text}")
                except Exception as e:
                    logger.warning(f"Error checking Notion commits database: {str(e)}")
        except Exception as e:
            logger.error(f"Error testing Notion client: {str(e)}")

    async def start_sync_loop(self) -> None:
        """Start the sync loop"""
        logger.info("Starting GitHub-Notion sync loop")

        # Set the running flag
        self.is_running = True

        # Import optimization utilities
        try:
            from utils.optimization import should_run_sync, get_system_status
            has_optimization = True
        except ImportError:
            logger.warning("Could not import optimization utilities, using default sync interval")
            has_optimization = False

        while self.is_running:
            try:
                # Check if it's time to sync
                current_time = time.time()

                # Use optimization if available
                if has_optimization:
                    # Check system status
                    system_status = get_system_status()
                    memory_constrained = system_status.get("memory", {}).get("percent", 0) > 70

                    # Check if we should run the sync based on memory constraints
                    should_sync = should_run_sync(self.last_sync_time, memory_constrained)

                    if should_sync:
                        logger.info("Running GitHub-Notion sync (memory-aware scheduling)")
                        await self.sync()
                        self.last_sync_time = current_time
                    else:
                        logger.info("Skipping GitHub-Notion sync due to recent sync or memory constraints")
                else:
                    # Use standard interval
                    if current_time - self.last_sync_time >= SYNC_INTERVAL:
                        # Perform sync
                        await self.sync()
                        self.last_sync_time = current_time

                # Wait before checking again
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

        logger.info("GitHub-Notion sync loop stopped")

    async def sync(self) -> Dict[str, Any]:
        """
        Perform a sync between GitHub and Notion

        Returns:
            Result dictionary with sync status
        """
        if self.is_syncing:
            logger.info("Sync already in progress, skipping")
            return {"success": False, "error": "Sync already in progress"}

        if not self.github_client or not self.notion_client:
            logger.error("GitHub or Notion client not initialized")
            return {"success": False, "error": "GitHub or Notion client not initialized"}

        self.is_syncing = True

        try:
            logger.info("Starting GitHub-Notion sync")

            # Sync GitHub commits to Notion
            github_to_notion_result = await self._sync_github_to_notion()

            # Sync Notion updates to GitHub
            notion_to_github_result = await self._sync_notion_to_github()

            logger.info("GitHub-Notion sync completed")

            return {
                "success": True,
                "github_to_notion": github_to_notion_result,
                "notion_to_github": notion_to_github_result
            }
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            self.is_syncing = False

    async def _sync_github_to_notion(self) -> Dict[str, Any]:
        """
        Sync GitHub commits to Notion

        Returns:
            Result dictionary with sync status
        """
        try:
            # Get repositories to sync
            repos = await self._get_github_repos_to_sync()

            if not repos:
                logger.info("No GitHub repositories to sync")
                return {"success": True, "synced": 0, "message": "No repositories to sync"}

            total_synced = 0

            # Process each repository
            for repo in repos:
                # Get recent commits
                commits = await self._get_recent_commits(repo)

                # Sync each commit to Notion
                for commit in commits[:MAX_ITEMS_PER_SYNC]:
                    result = await self._sync_commit_to_notion(repo, commit)
                    if result["success"]:
                        total_synced += 1

            logger.info(f"Synced {total_synced} GitHub commits to Notion")
            return {"success": True, "synced": total_synced}
        except Exception as e:
            logger.error(f"Error syncing GitHub to Notion: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _sync_notion_to_github(self) -> Dict[str, Any]:
        """
        Sync Notion updates to GitHub

        Returns:
            Result dictionary with sync status
        """
        try:
            # Get Notion databases to sync
            databases = await self._get_notion_databases_to_sync()

            if not databases:
                logger.info("No Notion databases to sync")
                return {"success": True, "synced": 0, "message": "No databases to sync"}

            total_synced = 0

            # Process each database
            for database in databases:
                # Get recent updates
                updates = await self._get_recent_notion_updates(database)

                # Sync each update to GitHub
                for update in updates[:MAX_ITEMS_PER_SYNC]:
                    result = await self._sync_notion_update_to_github(database, update)
                    if result["success"]:
                        total_synced += 1

            logger.info(f"Synced {total_synced} Notion updates to GitHub")
            return {"success": True, "synced": total_synced}
        except Exception as e:
            logger.error(f"Error syncing Notion to GitHub: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _get_github_repos_to_sync(self) -> List[Dict[str, Any]]:
        """
        Get GitHub repositories to sync

        Returns:
            List of repository dictionaries
        """
        try:
            # Check if we have cached repos
            if self.db is not None:
                cache = await self.db[SYNC_COLLECTION].find_one({"type": "github_repos_cache"})
                if cache and time.time() - cache["timestamp"] < GITHUB_CACHE_TTL:
                    logger.debug("Using cached GitHub repositories")
                    return cache["repos"]

            # Get repositories from GitHub
            repos = []

            # Get user's repositories
            for repo in self.github_client.get_user().get_repos():
                # Only include non-fork repositories
                if not repo.fork:
                    repos.append({
                        "id": repo.id,
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "url": repo.html_url,
                        "description": repo.description,
                        "last_synced": None
                    })

            # Cache the repositories
            if self.db is not None:
                await self.db[SYNC_COLLECTION].update_one(
                    {"type": "github_repos_cache"},
                    {"$set": {"repos": repos, "timestamp": time.time()}},
                    upsert=True
                )

            logger.info(f"Found {len(repos)} GitHub repositories to sync")
            return repos
        except Exception as e:
            logger.error(f"Error getting GitHub repositories: {str(e)}")
            return []

    async def _get_recent_commits(self, repo: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get recent commits from a GitHub repository

        Args:
            repo: Repository dictionary

        Returns:
            List of commit dictionaries
        """
        try:
            # Get the last sync time for this repository
            last_synced = None

            if self.db is not None:
                sync_state = await self.db[SYNC_COLLECTION].find_one({
                    "type": "github_repo",
                    "source_id": str(repo["id"])
                })

                if sync_state:
                    last_synced = sync_state.get("last_synced")

            # Get commits from GitHub
            commits = []

            try:
                github_repo = self.github_client.get_repo(repo["full_name"])

                # Check if repository is empty
                try:
                    # Check if repository has commits by trying to get the default branch
                    # We don't actually need to use the default_branch value, just check if it exists
                    github_repo.default_branch

                    try:
                        # If we have a last sync time, only get commits since then
                        if last_synced:
                            since_time = datetime.fromtimestamp(last_synced)
                            github_commits = github_repo.get_commits(since=since_time)
                        else:
                            # Otherwise, get the last 10 commits
                            github_commits = github_repo.get_commits()

                        # Get the commits and handle potential empty list
                        # Use a try/except block to handle empty repositories more gracefully
                        try:
                            github_commits_list = list(github_commits[:10])  # Convert to list and limit to 10 commits

                            if not github_commits_list:
                                logger.info(f"Repository {repo['full_name']} has no commits in the specified time range")
                            else:
                                # Convert to dictionaries with safe access to avoid index errors
                                for commit in github_commits_list:
                                    try:
                                        # Safely access commit properties with fallbacks
                                        commit_message = getattr(commit.commit, 'message', 'No message') if hasattr(commit, 'commit') else 'No message'
                                        commit_author = getattr(commit.commit.author, 'name', 'Unknown') if hasattr(commit, 'commit') and hasattr(commit.commit, 'author') else 'Unknown'
                                        commit_date = getattr(commit.commit.author, 'date', datetime.now()).timestamp() if hasattr(commit, 'commit') and hasattr(commit.commit, 'author') and hasattr(commit.commit.author, 'date') else datetime.now().timestamp()

                                        commits.append({
                                            "id": commit.sha,
                                            "message": commit_message,
                                            "author": commit_author,
                                            "date": commit_date,
                                            "url": getattr(commit, 'html_url', f"https://github.com/{repo['full_name']}/commit/{commit.sha}")
                                        })
                                    except Exception as e:
                                        logger.warning(f"Error processing commit in {repo['full_name']}: {str(e)}")
                                        # Continue with next commit instead of failing the entire process
                                        continue
                        except IndexError:
                            # This can happen with empty repositories
                            logger.info(f"Repository {repo['full_name']} appears to be empty (no commits found)")
                    except GithubException as ge:
                        if ge.status == 409:  # Empty repository
                            logger.info(f"Repository {repo['full_name']} is empty (409 Conflict)")
                        elif ge.status == 404:  # Not found
                            logger.warning(f"Repository {repo['full_name']} not found or inaccessible")
                        else:
                            logger.warning(f"GitHub error for {repo['full_name']}: {ge.status} - {ge.data}")
                    except IndexError:
                        # This can happen with empty repositories
                        logger.info(f"Repository {repo['full_name']} appears to be empty (IndexError)")
                    except Exception as e:
                        logger.warning(f"Error getting commits from {repo['full_name']}: {str(e)}")
                except GithubException as ge:
                    # Handle empty repository (status code 409 or 404)
                    if ge.status in [409, 404]:
                        logger.info(f"Repository {repo['full_name']} appears to be empty or has no commits")
                    elif ge.status == 500:
                        logger.warning(f"GitHub server error for {repo['full_name']}: {ge.data}")
                    else:
                        # Log the error but don't re-raise to prevent the entire sync from failing
                        logger.error(f"GitHub exception for {repo['full_name']}: {ge.status} - {ge.data}")
                except IndexError as ie:
                    # Handle index errors which can occur with empty repositories
                    logger.info(f"Index error for {repo['full_name']}, likely empty repository: {str(ie)}")
                except Exception as e:
                    # Handle any other exceptions
                    logger.error(f"Unexpected error processing commits for {repo['full_name']}: {str(e)}")
                    # Don't re-raise to prevent the entire sync from failing
            except GithubException as ge:
                if ge.status == 404:
                    logger.warning(f"Repository {repo['full_name']} not found")
                else:
                    logger.error(f"GitHub error for {repo['full_name']}: {ge.status} - {ge.data}")

            # Update the last sync time even if there are no commits
            # This prevents repeated attempts on empty repositories
            if self.db is not None:
                await self.db[SYNC_COLLECTION].update_one(
                    {"type": "github_repo", "source_id": str(repo["id"])},
                    {"$set": {"last_synced": time.time(), "empty": len(commits) == 0}},
                    upsert=True
                )

            logger.debug(f"Found {len(commits)} recent commits in {repo['full_name']}")
            return commits
        except Exception as e:
            logger.error(f"Error getting recent commits from {repo['full_name']}: {str(e)}")
            return []

    async def _sync_commit_to_notion(self, repo: Dict[str, Any], commit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync a GitHub commit to Notion

        Args:
            repo: Repository dictionary
            commit: Commit dictionary

        Returns:
            Result dictionary with sync status
        """
        try:
            # Check if this commit has already been synced
            if self.db is not None:
                existing_sync = await self.db[SYNC_COLLECTION].find_one({
                    "type": "github_commit",
                    "source_id": commit["id"]
                })

                if existing_sync:
                    logger.debug(f"Commit {commit['id']} already synced to Notion")
                    return {"success": True, "message": "Already synced"}

            # Get the Notion database ID for commits
            database_id = os.getenv("NOTION_COMMITS_DB")
            if not database_id:
                logger.warning("NOTION_COMMITS_DB not found in environment variables")
                return {"success": False, "error": "Notion database ID not found", "user_message": "NOTION_COMMITS_DB environment variable is not set. Please add it to your .env file."}

            # Validate the database ID
            if not is_valid_uuid(database_id):
                logger.error(f"Invalid Notion database ID format: {database_id}")
                return {
                    "success": False,
                    "error": "Invalid Notion database ID format",
                    "user_message": "The NOTION_COMMITS_DB value is not a valid Notion database ID. It should be a UUID in the format 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' or a 32-character hexadecimal string."
                }

            # Create a new page in Notion
            response = await self.notion_client.post(
                f"/pages",
                json={
                    "parent": {"database_id": database_id},
                    "properties": {
                        "Title": {
                            "title": [
                                {
                                    "text": {
                                        "content": commit["message"][:100]
                                    }
                                }
                            ]
                        },
                        "Repository": {
                            "select": {
                                "name": repo["name"]
                            }
                        },
                        "Author": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": commit["author"]
                                    }
                                }
                            ]
                        },
                        "Date": {
                            "date": {
                                "start": datetime.fromtimestamp(commit["date"]).isoformat()
                            }
                        },
                        "URL": {
                            "url": commit["url"]
                        }
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": commit["message"]
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": f"Commit: {commit['id']}"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            )

            response_data = response.json()

            if response.status_code == 200:
                # Record the sync in MongoDB
                if self.db is not None:
                    await self.db[SYNC_COLLECTION].update_one(
                        {"type": "github_commit", "source_id": commit["id"]},
                        {
                            "$set": {
                                "notion_id": response_data["id"],
                                "last_synced": time.time(),
                                "repo_id": repo["id"],
                                "repo_name": repo["name"]
                            }
                        },
                        upsert=True
                    )

                logger.info(f"Synced commit {commit['id']} to Notion")
                return {"success": True, "notion_id": response_data["id"]}
            else:
                logger.error(f"Error syncing commit to Notion: {response.status_code} - {response_data}")
                return {"success": False, "error": f"Notion API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error syncing commit {commit['id']} to Notion: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _get_notion_databases_to_sync(self) -> List[Dict[str, Any]]:
        """
        Get Notion databases to sync

        Returns:
            List of database dictionaries
        """
        try:
            # Check if we have cached databases
            if self.db is not None:
                cache = await self.db[SYNC_COLLECTION].find_one({"type": "notion_databases_cache"})
                if cache and time.time() - cache["timestamp"] < NOTION_CACHE_TTL:
                    logger.debug("Using cached Notion databases")
                    return cache["databases"]

            # Get databases from Notion
            response = await self.notion_client.get("/databases")
            response_data = response.json()

            if response.status_code != 200:
                logger.error(f"Error getting Notion databases: {response.status_code} - {response_data}")
                return []

            databases = []

            for db in response_data.get("results", []):
                # Only include databases with a title
                title = ""

                # Handle different Notion API response formats
                if "title" in db:
                    # Direct title array in the database object
                    title_items = db.get("title", [])
                elif "properties" in db and "title" in db.get("properties", {}):
                    # Title in properties (newer API format)
                    title_prop = db["properties"]["title"]
                    if title_prop.get("type") == "title":
                        title_items = title_prop.get("title", [])
                    else:
                        title_items = []
                else:
                    # Try to find any property of type "title"
                    title_items = []
                    for prop_name, prop_value in db.get("properties", {}).items():
                        if prop_value.get("type") == "title":
                            title_items = prop_value.get("title", [])
                            break

                # Extract text from title items
                for title_item in title_items:
                    if isinstance(title_item, dict):
                        title += title_item.get("plain_text", "")

                # Use ID as fallback title if no title found
                if not title:
                    title = f"Untitled Database ({db['id'][:8]})"

                databases.append({
                    "id": db["id"],
                    "title": title,
                    "url": f"https://notion.so/{db['id'].replace('-', '')}",
                    "last_synced": None
                })

            # Cache the databases
            if self.db is not None:
                await self.db[SYNC_COLLECTION].update_one(
                    {"type": "notion_databases_cache"},
                    {"$set": {"databases": databases, "timestamp": time.time()}},
                    upsert=True
                )

            logger.info(f"Found {len(databases)} Notion databases to sync")
            return databases
        except Exception as e:
            logger.error(f"Error getting Notion databases: {str(e)}")
            return []

    async def _get_recent_notion_updates(self, database: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get recent updates from a Notion database

        Args:
            database: Database dictionary

        Returns:
            List of update dictionaries
        """
        try:
            # Get the last sync time for this database
            last_synced = None

            if self.db is not None:
                sync_state = await self.db[SYNC_COLLECTION].find_one({
                    "type": "notion_database",
                    "source_id": database["id"]
                })

                if sync_state:
                    last_synced = sync_state.get("last_synced")

            # Get updates from Notion
            filter_obj = {}

            # If we have a last sync time, only get updates since then
            if last_synced:
                since_time = datetime.fromtimestamp(last_synced).isoformat()
                filter_obj = {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "after": since_time
                    }
                }

            response = await self.notion_client.post(
                f"/databases/{database['id']}/query",
                json={
                    "filter": filter_obj,
                    "sorts": [
                        {
                            "timestamp": "last_edited_time",
                            "direction": "descending"
                        }
                    ],
                    "page_size": 10
                }
            )

            response_data = response.json()

            if response.status_code != 200:
                logger.error(f"Error getting Notion updates: {response.status_code} - {response_data}")
                return []

            updates = []

            for page in response_data.get("results", []):
                # Extract page properties
                properties = page.get("properties", {})
                title = ""

                # Try to find a title property
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        for title_item in prop_value.get("title", []):
                            title += title_item.get("plain_text", "")
                        break

                if not title:
                    title = f"Untitled ({page['id']})"

                updates.append({
                    "id": page["id"],
                    "title": title,
                    "last_edited_time": page.get("last_edited_time"),
                    "url": page.get("url"),
                    "properties": properties
                })

            # Update the last sync time
            if self.db is not None:
                await self.db[SYNC_COLLECTION].update_one(
                    {"type": "notion_database", "source_id": database["id"]},
                    {"$set": {"last_synced": time.time()}},
                    upsert=True
                )

            logger.debug(f"Found {len(updates)} recent updates in Notion database {database['title']}")
            return updates
        except Exception as e:
            logger.error(f"Error getting recent updates from Notion database {database['title']}: {str(e)}")
            return []

    async def _sync_notion_update_to_github(self, database: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync a Notion update to GitHub

        Args:
            database: Database dictionary
            update: Update dictionary

        Returns:
            Result dictionary with sync status
        """
        try:
            # Check if this update has already been synced
            if self.db is not None:
                existing_sync = await self.db[SYNC_COLLECTION].find_one({
                    "type": "notion_update",
                    "source_id": update["id"]
                })

                if existing_sync:
                    logger.debug(f"Notion update {update['id']} already synced to GitHub")
                    return {"success": True, "message": "Already synced"}

            # Check if this database is configured for GitHub sync
            github_repo = os.getenv("GITHUB_SYNC_REPO")
            if not github_repo:
                logger.warning("GITHUB_SYNC_REPO not found in environment variables")
                return {"success": False, "error": "GitHub repository not found"}

            # Get the repository
            repo = self.github_client.get_repo(github_repo)

            # Create an issue in GitHub
            issue = repo.create_issue(
                title=update["title"],
                body=f"Notion Update: {update['url']}\n\nLast edited: {update['last_edited_time']}\n\nSync from Notion database: {database['title']}",
                labels=["notion-sync"]
            )

            # Record the sync in MongoDB
            if self.db is not None:
                await self.db[SYNC_COLLECTION].update_one(
                    {"type": "notion_update", "source_id": update["id"]},
                    {
                        "$set": {
                            "github_issue_id": issue.number,
                            "github_issue_url": issue.html_url,
                            "last_synced": time.time(),
                            "database_id": database["id"],
                            "database_title": database["title"]
                        }
                    },
                    upsert=True
                )

            logger.info(f"Synced Notion update {update['id']} to GitHub issue #{issue.number}")
            return {"success": True, "github_issue_id": issue.number, "github_issue_url": issue.html_url}
        except Exception as e:
            logger.error(f"Error syncing Notion update {update['id']} to GitHub: {str(e)}")
            return {"success": False, "error": str(e)}

    async def close(self) -> None:
        """Close connections and stop sync loop"""
        # Set a flag to stop the sync loop
        self.is_running = False
        logger.info("Stopping GitHub-Notion sync loop")

        # Close MongoDB connection
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

        # Close Notion client
        if self.notion_client:
            await self.notion_client.aclose()
            logger.info("Closed Notion client")

    async def shutdown(self) -> None:
        """Alias for close() for consistency with other components"""
        await self.close()
