# GitHub-Notion Synchronization

The GitHub-Notion Sync feature provides bidirectional synchronization between GitHub repositories and Notion databases, allowing you to track your development work across both platforms.

## Overview

The GitHub-Notion Sync module synchronizes data between GitHub repositories and Notion databases, ensuring that your project information is consistent across both platforms. It tracks commits, issues, and other GitHub activities in Notion, and can also update GitHub based on changes in Notion.

## Key Features

### Bidirectional Synchronization

The sync module provides two-way synchronization between GitHub and Notion:

- **GitHub to Notion**: Syncs commits, pull requests, and issues from GitHub to Notion
- **Notion to GitHub**: Updates GitHub issues and pull requests based on changes in Notion
- **Conflict Resolution**: Handles conflicts when the same item is updated in both systems

### Memory-Aware Scheduling

The sync module intelligently schedules sync operations based on system resources:

- **Adaptive Scheduling**: Adjusts sync frequency based on system memory usage
- **Resource Monitoring**: Monitors CPU and memory usage to avoid overloading the system
- **Deferred Execution**: Defers sync operations when system resources are constrained

### MongoDB Tracking

The sync module uses MongoDB Atlas for tracking sync status and history:

- **Sync History**: Records all sync operations with timestamps and results
- **Status Tracking**: Tracks the status of each synced item across platforms
- **Error Logging**: Logs errors and retries for failed sync operations

### Error Handling

The sync module includes robust error handling for API rate limits and connection issues:

- **Rate Limit Handling**: Respects API rate limits and implements backoff strategies
- **Connection Error Recovery**: Recovers gracefully from connection errors
- **Retry Logic**: Implements intelligent retry logic for failed operations

## Implementation

The GitHub-Notion Sync is implemented in `integrations/sync.py` and consists of the following components:

### GitHubNotionSync Class

The main sync class that handles bidirectional synchronization:

```python
class GitHubNotionSync:
    def __init__(self, github_token=None, notion_token=None, mongodb_uri=None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.notion_token = notion_token or os.getenv("NOTION_TOKEN")
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        
        # Initialize clients
        self._init_github_client()
        self._init_notion_client()
        self._init_mongodb_client()
        
        # Sync state
        self.is_running = False
        self.is_syncing = False
        self.last_sync_time = 0
        
    async def start_sync_loop(self):
        # Set the running flag
        self.is_running = True
        
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
                        await self.sync()
                        self.last_sync_time = current_time
                else:
                    # Use standard interval
                    if current_time - self.last_sync_time >= SYNC_INTERVAL:
                        await self.sync()
                        self.last_sync_time = current_time
                        
                # Wait before checking again
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
```

### Sync Operations

The sync module implements various sync operations:

```python
async def sync(self):
    if self.is_syncing:
        logger.info("Sync already in progress, skipping")
        return {"success": False, "error": "Sync already in progress"}
        
    self.is_syncing = True
    
    try:
        # Sync GitHub commits to Notion
        github_to_notion_result = await self._sync_github_to_notion()
        
        # Sync Notion updates to GitHub
        notion_to_github_result = await self._sync_notion_to_github()
        
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
```

### MongoDB Integration

The sync module uses MongoDB Atlas for tracking sync status:

```python
async def _init_mongodb_client(self):
    if not self.mongodb_uri:
        logger.warning("MongoDB URI not provided, sync history will not be stored")
        self.db = None
        return
        
    try:
        # Create MongoDB client
        self.mongo_client = AsyncIOMotorClient(self.mongodb_uri)
        
        # Get database
        self.db = self.mongo_client[MONGODB_DATABASE]
        
        # Ensure indexes
        await self.db[SYNC_COLLECTION].create_index([("type", 1), ("source_id", 1)], unique=True)
        
        logger.info("MongoDB client initialized")
    except Exception as e:
        logger.error(f"Error initializing MongoDB client: {str(e)}")
        self.db = None
```

## Configuration

The GitHub-Notion Sync module can be configured through environment variables or direct parameters:

```
# GitHub configuration
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username

# Notion configuration
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_notion_database_id

# MongoDB configuration
MONGODB_URI=your_mongodb_uri
MONGODB_DATABASE=pulse

# Sync configuration
SYNC_INTERVAL=3600  # 1 hour in seconds
MAX_ITEMS_PER_SYNC=50
```

## Usage

The GitHub-Notion Sync module can be used as follows:

```python
# Initialize the sync module
sync = GitHubNotionSync()

# Start the sync loop
await sync.start_sync_loop()

# Or perform a one-time sync
result = await sync.sync()
print(f"Sync result: {result}")

# Stop the sync loop
sync.is_running = False
```

## Future Improvements

Planned improvements for the GitHub-Notion Sync module include:

1. **Enhanced Conflict Resolution**: Improve conflict resolution with more sophisticated strategies
2. **Selective Sync**: Allow selective synchronization of specific repositories or databases
3. **Webhook Integration**: Use webhooks for real-time synchronization
4. **Custom Field Mapping**: Allow custom mapping between GitHub and Notion fields
5. **Multi-Database Support**: Support synchronization with multiple Notion databases

## Related Documentation

- [GitHub Integration](github_integration.md) - Working with GitHub repositories
- [Notion Integration](notion_integration.md) - Working with Notion documents
- [MongoDB Integration](mongodb_integration.md) - Working with MongoDB Atlas
