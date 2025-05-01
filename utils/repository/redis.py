"""
Redis Caching Layer for P.U.L.S.E.
Provides Redis caching for repositories
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, cast
from datetime import datetime, timedelta
import structlog

from utils.repository.base import Entity, Repository, CacheableRepository
from utils.error_handler import with_error_handling, ErrorSource
from utils.circuit_breaker import circuit_breaker

# Configure logger
logger = structlog.get_logger("redis_cache")

# Type variables
T = TypeVar('T', bound=Entity)

# Try to import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, install with 'pip install redis'")

class RedisCache:
    """Redis cache for repositories"""
    
    def __init__(
        self,
        prefix: str,
        entity_class: type,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 3600,  # 1 hour
        connection_string: Optional[str] = None
    ):
        """
        Initialize Redis cache
        
        Args:
            prefix: Cache key prefix
            entity_class: Entity class
            host: Redis host
            port: Redis port
            db: Redis database
            password: Redis password
            ttl: Cache TTL in seconds
            connection_string: Redis connection string (from env if not provided)
        """
        self.prefix = prefix
        self.entity_class = entity_class
        self.ttl = ttl
        
        # Initialize Redis client
        self.client = None
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, caching disabled")
            return
        
        try:
            # Get connection string from environment if not provided
            if not connection_string:
                connection_string = os.getenv("REDIS_URL")
            
            # Create Redis client
            if connection_string:
                self.client = redis.from_url(connection_string)
            else:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=False
                )
                
            logger.info(f"Redis cache initialized: {prefix}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {str(e)}")
            self.client = None
    
    def _get_key(self, id: str) -> str:
        """
        Get cache key for entity ID
        
        Args:
            id: Entity ID
            
        Returns:
            Cache key
        """
        return f"{self.prefix}:{id}"
    
    def _entity_to_json(self, entity: Entity) -> str:
        """
        Convert entity to JSON
        
        Args:
            entity: Entity to convert
            
        Returns:
            JSON string
        """
        return json.dumps(entity.to_dict())
    
    def _json_to_entity(self, json_str: str) -> Entity:
        """
        Convert JSON to entity
        
        Args:
            json_str: JSON string
            
        Returns:
            Entity instance
        """
        data = json.loads(json_str)
        return self.entity_class.from_dict(data)
    
    @circuit_breaker(name="redis", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.REDIS)
    async def get(self, id: str) -> Optional[Entity]:
        """
        Get entity from cache
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found in cache, None otherwise
        """
        if not self.client or not REDIS_AVAILABLE:
            return None
        
        # Get entity from cache
        key = self._get_key(id)
        json_str = await self.client.get(key)
        
        # Return entity if found
        if json_str:
            try:
                return self._json_to_entity(json_str)
            except Exception as e:
                logger.warning(f"Failed to deserialize entity from cache: {str(e)}")
                
        return None
    
    @circuit_breaker(name="redis", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.REDIS)
    async def set(self, entity: Entity) -> bool:
        """
        Set entity in cache
        
        Args:
            entity: Entity to cache
            
        Returns:
            True if entity was cached, False otherwise
        """
        if not self.client or not REDIS_AVAILABLE:
            return False
        
        try:
            # Convert entity to JSON
            json_str = self._entity_to_json(entity)
            
            # Set entity in cache
            key = self._get_key(entity.id)
            await self.client.set(key, json_str, ex=self.ttl)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to cache entity: {str(e)}")
            return False
    
    @circuit_breaker(name="redis", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.REDIS)
    async def delete(self, id: str) -> bool:
        """
        Delete entity from cache
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted from cache, False otherwise
        """
        if not self.client or not REDIS_AVAILABLE:
            return False
        
        # Delete entity from cache
        key = self._get_key(id)
        result = await self.client.delete(key)
        
        return result > 0
    
    @circuit_breaker(name="redis", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.REDIS)
    async def clear(self) -> bool:
        """
        Clear cache
        
        Returns:
            True if cache was cleared, False otherwise
        """
        if not self.client or not REDIS_AVAILABLE:
            return False
        
        try:
            # Get all keys with prefix
            pattern = f"{self.prefix}:*"
            keys = []
            
            # Scan for keys
            cursor = 0
            while True:
                cursor, partial_keys = await self.client.scan(cursor, match=pattern)
                keys.extend(partial_keys)
                
                if cursor == 0:
                    break
            
            # Delete keys
            if keys:
                await self.client.delete(*keys)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")
            return False
    
    @circuit_breaker(name="redis", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.REDIS)
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of Redis cache
        
        Returns:
            Health check result with status and details
        """
        if not self.client or not REDIS_AVAILABLE:
            return {
                "status": "down",
                "details": {
                    "error": "Redis client not initialized"
                }
            }
        
        try:
            # Ping Redis
            await self.client.ping()
            
            # Get cache info
            info = await self.client.info()
            
            return {
                "status": "up",
                "details": {
                    "prefix": self.prefix,
                    "ttl": self.ttl,
                    "redis_version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human")
                }
            }
        except Exception as e:
            return {
                "status": "down",
                "details": {
                    "error": str(e)
                }
            }

class CachedRepository(Repository[T, str]):
    """Repository with Redis caching"""
    
    def __init__(
        self,
        repository: Repository[T, str],
        cache: RedisCache,
        ttl: int = 3600  # 1 hour
    ):
        """
        Initialize cached repository
        
        Args:
            repository: Base repository
            cache: Redis cache
            ttl: Cache TTL in seconds
        """
        self.repository = repository
        self.cache = cache
        self.ttl = ttl
    
    async def save(self, entity: T) -> T:
        """
        Save entity to repository and cache
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        # Save entity to repository
        saved_entity = await self.repository.save(entity)
        
        # Cache entity
        await self.cache.set(saved_entity)
        
        return saved_entity
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find entity by ID with caching
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        # Try to get entity from cache
        entity = await self.cache.get(id)
        
        if entity:
            return cast(T, entity)
        
        # Get entity from repository
        entity = await self.repository.find_by_id(id)
        
        # Cache entity if found
        if entity:
            await self.cache.set(entity)
        
        return entity
    
    async def find_all(self) -> List[T]:
        """
        Find all entities (not cached)
        
        Returns:
            List of all entities
        """
        return await self.repository.find_all()
    
    async def delete(self, id: str) -> bool:
        """
        Delete entity by ID and from cache
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        # Delete entity from repository
        result = await self.repository.delete(id)
        
        # Delete entity from cache
        await self.cache.delete(id)
        
        return result
    
    async def exists(self, id: str) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        # Try to get entity from cache
        entity = await self.cache.get(id)
        
        if entity:
            return True
        
        # Check if entity exists in repository
        return await self.repository.exists(id)
    
    async def count(self) -> int:
        """
        Count entities in repository
        
        Returns:
            Number of entities
        """
        return await self.repository.count()

class CachedMessageRepository(CachedRepository[Message], MessageRepository):
    """Cached repository for chat messages"""
    
    def __init__(
        self,
        repository: MessageRepository,
        cache: RedisCache
    ):
        """
        Initialize cached message repository
        
        Args:
            repository: Base message repository
            cache: Redis cache
        """
        super().__init__(repository, cache)
        self.message_repository = repository
    
    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Find messages by conversation ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages
        """
        return await self.message_repository.find_by_conversation_id(conversation_id)
    
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Message]:
        """
        Find messages by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        return await self.message_repository.find_by_user_id(user_id, limit)

class CachedConversationRepository(CachedRepository[Conversation], ConversationRepository):
    """Cached repository for conversations"""
    
    def __init__(
        self,
        repository: ConversationRepository,
        cache: RedisCache
    ):
        """
        Initialize cached conversation repository
        
        Args:
            repository: Base conversation repository
            cache: Redis cache
        """
        super().__init__(repository, cache)
        self.conversation_repository = repository
    
    async def find_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """
        Find conversations by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        return await self.conversation_repository.find_by_user_id(user_id, limit)
    
    async def find_recent(self, limit: int = 10) -> List[Conversation]:
        """
        Find recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        return await self.conversation_repository.find_recent(limit)
    
    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """
        Add message to conversation
        
        Args:
            conversation_id: Conversation ID
            message: Message to add
            
        Returns:
            Added message
        """
        # Add message to conversation
        saved_message = await self.conversation_repository.add_message(conversation_id, message)
        
        # Invalidate conversation cache
        await self.cache.delete(conversation_id)
        
        return saved_message

class CachedMemoryRepository(CachedRepository[Memory], MemoryRepository):
    """Cached repository for memories"""
    
    def __init__(
        self,
        repository: MemoryRepository,
        cache: RedisCache
    ):
        """
        Initialize cached memory repository
        
        Args:
            repository: Base memory repository
            cache: Redis cache
        """
        super().__init__(repository, cache)
        self.memory_repository = repository
    
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        return await self.memory_repository.find_by_user_id(user_id, limit)
    
    async def find_by_category(self, category: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by category
        
        Args:
            category: Memory category
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        return await self.memory_repository.find_by_category(category, limit)
    
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
        return await self.memory_repository.find_by_user_and_category(user_id, category, limit)
    
    async def search_similar(self, content: str, limit: int = 5) -> List[Memory]:
        """
        Search for similar memories
        
        Args:
            content: Content to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        return await self.memory_repository.search_similar(content, limit)
