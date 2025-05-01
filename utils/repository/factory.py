"""
Repository Factory for P.U.L.S.E.
Provides factory for creating repositories with primary-backup architecture
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, cast
import structlog
from enum import Enum

from utils.repository.base import Entity, Repository, RepositoryFactory
from utils.repository.chat import Message, Conversation, Memory, MessageRepository, ConversationRepository, MemoryRepository
from utils.repository.mongodb import MongoDBMessageRepository, MongoDBConversationRepository, MongoDBMemoryRepository
from utils.repository.sqlite import SQLiteMessageRepository, SQLiteConversationRepository, SQLiteMemoryRepository
from utils.repository.redis import RedisCache, CachedMessageRepository, CachedConversationRepository, CachedMemoryRepository
from utils.error_handler import with_error_handling, ErrorSource

# Configure logger
logger = structlog.get_logger("repository_factory")

# Type variables
T = TypeVar('T', bound=Entity)

class StorageType(str, Enum):
    """Storage type enum"""
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    MEMORY = "memory"

class PrimaryBackupRepository(Repository[T, str]):
    """
    Primary-backup repository with automatic failover
    
    This repository uses a primary repository for all operations,
    but falls back to a backup repository if the primary fails.
    """
    
    def __init__(
        self,
        primary: Repository[T, str],
        backup: Repository[T, str],
        entity_type: str
    ):
        """
        Initialize primary-backup repository
        
        Args:
            primary: Primary repository
            backup: Backup repository
            entity_type: Entity type name
        """
        self.primary = primary
        self.backup = backup
        self.entity_type = entity_type
        self.primary_healthy = True
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
    
    async def _check_primary_health(self) -> bool:
        """
        Check if primary repository is healthy
        
        Returns:
            True if primary is healthy, False otherwise
        """
        # Skip health check if recently checked
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_health_check < self.health_check_interval:
            return self.primary_healthy
        
        # Update last health check time
        self.last_health_check = current_time
        
        # Check health
        try:
            if hasattr(self.primary, 'check_health'):
                health = await self.primary.check_health()
                self.primary_healthy = health.get('status') == 'up'
            else:
                # If no health check method, try a simple operation
                await self.primary.count()
                self.primary_healthy = True
                
            if not self.primary_healthy:
                logger.warning(f"Primary repository for {self.entity_type} is unhealthy, using backup")
            elif not self.primary_healthy and self.primary_healthy:
                logger.info(f"Primary repository for {self.entity_type} is healthy again")
                
            return self.primary_healthy
        except Exception as e:
            logger.warning(f"Failed to check primary repository health: {str(e)}")
            self.primary_healthy = False
            return False
    
    async def _sync_to_primary(self, entity: T) -> None:
        """
        Sync entity to primary repository when it becomes healthy again
        
        Args:
            entity: Entity to sync
        """
        if not self.primary_healthy:
            return
            
        try:
            # Check if entity exists in primary
            exists = await self.primary.exists(entity.id)
            
            if not exists:
                # Save entity to primary
                await self.primary.save(entity)
                logger.info(f"Synced {self.entity_type} {entity.id} to primary repository")
        except Exception as e:
            logger.warning(f"Failed to sync {self.entity_type} to primary repository: {str(e)}")
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def save(self, entity: T) -> T:
        """
        Save entity to repository
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Save to primary
                return await self.primary.save(entity)
            except Exception as e:
                logger.warning(f"Failed to save {self.entity_type} to primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Save to backup
        saved_entity = await self.backup.save(entity)
        
        # Schedule sync to primary when it becomes healthy again
        asyncio.create_task(self._sync_to_primary(saved_entity))
        
        return saved_entity
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                entity = await self.primary.find_by_id(id)
                
                if entity:
                    return entity
            except Exception as e:
                logger.warning(f"Failed to find {self.entity_type} in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        entity = await self.backup.find_by_id(id)
        
        # Schedule sync to primary if found
        if entity and not primary_healthy:
            asyncio.create_task(self._sync_to_primary(entity))
            
        return entity
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_all(self) -> List[T]:
        """
        Find all entities
        
        Returns:
            List of all entities
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find all in primary
                return await self.primary.find_all()
            except Exception as e:
                logger.warning(f"Failed to find all {self.entity_type} in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find all in backup
        return await self.backup.find_all()
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def delete(self, id: str) -> bool:
        """
        Delete entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        result = False
        
        if primary_healthy:
            try:
                # Delete from primary
                result = await self.primary.delete(id)
            except Exception as e:
                logger.warning(f"Failed to delete {self.entity_type} from primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Delete from backup
        backup_result = await self.backup.delete(id)
        
        # Return true if either operation succeeded
        return result or backup_result
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def exists(self, id: str) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Check if exists in primary
                return await self.primary.exists(id)
            except Exception as e:
                logger.warning(f"Failed to check if {self.entity_type} exists in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Check if exists in backup
        return await self.backup.exists(id)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def count(self) -> int:
        """
        Count entities in repository
        
        Returns:
            Number of entities
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Count in primary
                return await self.primary.count()
            except Exception as e:
                logger.warning(f"Failed to count {self.entity_type} in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Count in backup
        return await self.backup.count()

class PrimaryBackupMessageRepository(PrimaryBackupRepository[Message], MessageRepository):
    """Primary-backup repository for chat messages"""
    
    def __init__(
        self,
        primary: MessageRepository,
        backup: MessageRepository
    ):
        """
        Initialize primary-backup message repository
        
        Args:
            primary: Primary message repository
            backup: Backup message repository
        """
        super().__init__(primary, backup, "message")
        self.primary_message_repo = primary
        self.backup_message_repo = backup
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Find messages by conversation ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_message_repo.find_by_conversation_id(conversation_id)
            except Exception as e:
                logger.warning(f"Failed to find messages by conversation ID in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_message_repo.find_by_conversation_id(conversation_id)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Message]:
        """
        Find messages by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_message_repo.find_by_user_id(user_id, limit)
            except Exception as e:
                logger.warning(f"Failed to find messages by user ID in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_message_repo.find_by_user_id(user_id, limit)

class PrimaryBackupConversationRepository(PrimaryBackupRepository[Conversation], ConversationRepository):
    """Primary-backup repository for conversations"""
    
    def __init__(
        self,
        primary: ConversationRepository,
        backup: ConversationRepository
    ):
        """
        Initialize primary-backup conversation repository
        
        Args:
            primary: Primary conversation repository
            backup: Backup conversation repository
        """
        super().__init__(primary, backup, "conversation")
        self.primary_conversation_repo = primary
        self.backup_conversation_repo = backup
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """
        Find conversations by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_conversation_repo.find_by_user_id(user_id, limit)
            except Exception as e:
                logger.warning(f"Failed to find conversations by user ID in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_conversation_repo.find_by_user_id(user_id, limit)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_recent(self, limit: int = 10) -> List[Conversation]:
        """
        Find recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_conversation_repo.find_recent(limit)
            except Exception as e:
                logger.warning(f"Failed to find recent conversations in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_conversation_repo.find_recent(limit)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """
        Add message to conversation
        
        Args:
            conversation_id: Conversation ID
            message: Message to add
            
        Returns:
            Added message
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Add message to primary
                return await self.primary_conversation_repo.add_message(conversation_id, message)
            except Exception as e:
                logger.warning(f"Failed to add message to conversation in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Add message to backup
        return await self.backup_conversation_repo.add_message(conversation_id, message)

class PrimaryBackupMemoryRepository(PrimaryBackupRepository[Memory], MemoryRepository):
    """Primary-backup repository for memories"""
    
    def __init__(
        self,
        primary: MemoryRepository,
        backup: MemoryRepository
    ):
        """
        Initialize primary-backup memory repository
        
        Args:
            primary: Primary memory repository
            backup: Backup memory repository
        """
        super().__init__(primary, backup, "memory")
        self.primary_memory_repo = primary
        self.backup_memory_repo = backup
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_memory_repo.find_by_user_id(user_id, limit)
            except Exception as e:
                logger.warning(f"Failed to find memories by user ID in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_memory_repo.find_by_user_id(user_id, limit)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_category(self, category: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by category
        
        Args:
            category: Memory category
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_memory_repo.find_by_category(category, limit)
            except Exception as e:
                logger.warning(f"Failed to find memories by category in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_memory_repo.find_by_category(category, limit)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def find_by_user_and_category(self, user_id: str, category: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by user ID and category
        
        Args:
            user_id: User ID
            category: Memory category
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Find in primary
                return await self.primary_memory_repo.find_by_user_and_category(user_id, category, limit)
            except Exception as e:
                logger.warning(f"Failed to find memories by user ID and category in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Find in backup
        return await self.backup_memory_repo.find_by_user_and_category(user_id, category, limit)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def search_similar(self, content: str, limit: int = 5) -> List[Memory]:
        """
        Search for similar memories
        
        Args:
            content: Content to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Check primary health
        primary_healthy = await self._check_primary_health()
        
        if primary_healthy:
            try:
                # Search in primary
                return await self.primary_memory_repo.search_similar(content, limit)
            except Exception as e:
                logger.warning(f"Failed to search similar memories in primary repository: {str(e)}")
                self.primary_healthy = False
        
        # Search in backup
        return await self.backup_memory_repo.search_similar(content, limit)

class PulseRepositoryFactory(RepositoryFactory):
    """Factory for creating P.U.L.S.E. repositories"""
    
    def __init__(
        self,
        primary_type: StorageType = StorageType.MONGODB,
        backup_type: StorageType = StorageType.SQLITE,
        mongodb_uri: Optional[str] = None,
        sqlite_path: str = "data/pulse.db",
        redis_url: Optional[str] = None,
        enable_caching: bool = True
    ):
        """
        Initialize repository factory
        
        Args:
            primary_type: Primary storage type
            backup_type: Backup storage type
            mongodb_uri: MongoDB connection string (from env if not provided)
            sqlite_path: SQLite database path
            redis_url: Redis connection string (from env if not provided)
            enable_caching: Whether to enable Redis caching
        """
        self.primary_type = primary_type
        self.backup_type = backup_type
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        self.sqlite_path = sqlite_path
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.enable_caching = enable_caching
        
        # Cache for repositories
        self._repositories = {}
        
        logger.info(f"Repository factory initialized with primary={primary_type}, backup={backup_type}")
    
    def _create_message_repository(self, storage_type: StorageType) -> MessageRepository:
        """
        Create message repository
        
        Args:
            storage_type: Storage type
            
        Returns:
            Message repository
        """
        if storage_type == StorageType.MONGODB:
            return MongoDBMessageRepository(connection_string=self.mongodb_uri)
        elif storage_type == StorageType.SQLITE:
            return SQLiteMessageRepository(db_path=self.sqlite_path)
        else:
            # Default to SQLite
            return SQLiteMessageRepository(db_path=self.sqlite_path)
    
    def _create_conversation_repository(self, storage_type: StorageType) -> ConversationRepository:
        """
        Create conversation repository
        
        Args:
            storage_type: Storage type
            
        Returns:
            Conversation repository
        """
        if storage_type == StorageType.MONGODB:
            return MongoDBConversationRepository(connection_string=self.mongodb_uri)
        elif storage_type == StorageType.SQLITE:
            return SQLiteConversationRepository(db_path=self.sqlite_path)
        else:
            # Default to SQLite
            return SQLiteConversationRepository(db_path=self.sqlite_path)
    
    def _create_memory_repository(self, storage_type: StorageType) -> MemoryRepository:
        """
        Create memory repository
        
        Args:
            storage_type: Storage type
            
        Returns:
            Memory repository
        """
        if storage_type == StorageType.MONGODB:
            return MongoDBMemoryRepository(connection_string=self.mongodb_uri)
        elif storage_type == StorageType.SQLITE:
            return SQLiteMemoryRepository(db_path=self.sqlite_path)
        else:
            # Default to SQLite
            return SQLiteMemoryRepository(db_path=self.sqlite_path)
    
    def _add_caching(self, repository: Repository, entity_class: type, prefix: str) -> Repository:
        """
        Add caching to repository
        
        Args:
            repository: Repository to cache
            entity_class: Entity class
            prefix: Cache key prefix
            
        Returns:
            Cached repository
        """
        if not self.enable_caching:
            return repository
            
        # Create Redis cache
        cache = RedisCache(
            prefix=prefix,
            entity_class=entity_class,
            connection_string=self.redis_url
        )
        
        # Create cached repository
        if isinstance(repository, MessageRepository):
            return CachedMessageRepository(repository, cache)
        elif isinstance(repository, ConversationRepository):
            return CachedConversationRepository(repository, cache)
        elif isinstance(repository, MemoryRepository):
            return CachedMemoryRepository(repository, cache)
        else:
            return repository
    
    def create_repository(self, entity_type: str) -> Repository:
        """
        Create repository for entity type
        
        Args:
            entity_type: Entity type
            
        Returns:
            Repository instance
        """
        # Check if repository already exists
        if entity_type in self._repositories:
            return self._repositories[entity_type]
            
        # Create primary and backup repositories
        if entity_type == "message":
            primary = self._create_message_repository(self.primary_type)
            backup = self._create_message_repository(self.backup_type)
            
            # Add caching if enabled
            if self.enable_caching:
                primary = self._add_caching(primary, Message, "message")
                backup = self._add_caching(backup, Message, "message_backup")
                
            # Create primary-backup repository
            repository = PrimaryBackupMessageRepository(primary, backup)
            
        elif entity_type == "conversation":
            primary = self._create_conversation_repository(self.primary_type)
            backup = self._create_conversation_repository(self.backup_type)
            
            # Add caching if enabled
            if self.enable_caching:
                primary = self._add_caching(primary, Conversation, "conversation")
                backup = self._add_caching(backup, Conversation, "conversation_backup")
                
            # Create primary-backup repository
            repository = PrimaryBackupConversationRepository(primary, backup)
            
        elif entity_type == "memory":
            primary = self._create_memory_repository(self.primary_type)
            backup = self._create_memory_repository(self.backup_type)
            
            # Add caching if enabled
            if self.enable_caching:
                primary = self._add_caching(primary, Memory, "memory")
                backup = self._add_caching(backup, Memory, "memory_backup")
                
            # Create primary-backup repository
            repository = PrimaryBackupMemoryRepository(primary, backup)
            
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        # Cache repository
        self._repositories[entity_type] = repository
        
        return repository
    
    def get_message_repository(self) -> MessageRepository:
        """
        Get message repository
        
        Returns:
            Message repository
        """
        return cast(MessageRepository, self.create_repository("message"))
    
    def get_conversation_repository(self) -> ConversationRepository:
        """
        Get conversation repository
        
        Returns:
            Conversation repository
        """
        return cast(ConversationRepository, self.create_repository("conversation"))
    
    def get_memory_repository(self) -> MemoryRepository:
        """
        Get memory repository
        
        Returns:
            Memory repository
        """
        return cast(MemoryRepository, self.create_repository("memory"))
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of all repositories
        
        Returns:
            Health check result with status and details
        """
        result = {
            "status": "up",
            "repositories": {}
        }
        
        # Check health of each repository
        for entity_type, repository in self._repositories.items():
            if hasattr(repository, 'check_health'):
                repo_health = await repository.check_health()
                result["repositories"][entity_type] = repo_health
                
                # If any repository is down, the overall status is down
                if repo_health.get("status") == "down":
                    result["status"] = "down"
        
        return result
