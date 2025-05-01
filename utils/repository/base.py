"""
Base Repository Pattern for P.U.L.S.E.
Provides abstract base classes for storage providers
"""

import abc
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from datetime import datetime
import uuid
import structlog

# Configure logger
logger = structlog.get_logger("repository")

# Type variables
T = TypeVar('T')
ID = TypeVar('ID')

class Entity:
    """Base entity class for all repository objects"""
    
    def __init__(self, id: Optional[str] = None):
        """
        Initialize entity with optional ID
        
        Args:
            id: Optional entity ID (generated if not provided)
        """
        self.id = id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to dictionary
        
        Returns:
            Dictionary representation of entity
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """
        Create entity from dictionary
        
        Args:
            data: Dictionary representation of entity
            
        Returns:
            Entity instance
        """
        entity = cls(id=data.get("id"))
        
        # Parse timestamps if available
        if "created_at" in data:
            if isinstance(data["created_at"], str):
                entity.created_at = datetime.fromisoformat(data["created_at"])
            elif isinstance(data["created_at"], datetime):
                entity.created_at = data["created_at"]
                
        if "updated_at" in data:
            if isinstance(data["updated_at"], str):
                entity.updated_at = datetime.fromisoformat(data["updated_at"])
            elif isinstance(data["updated_at"], datetime):
                entity.updated_at = data["updated_at"]
                
        return entity

class Repository(Generic[T, ID], abc.ABC):
    """
    Abstract base repository interface
    
    Generic parameters:
        T: Entity type
        ID: ID type
    """
    
    @abc.abstractmethod
    async def save(self, entity: T) -> T:
        """
        Save entity to repository
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        pass
    
    @abc.abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """
        Find entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abc.abstractmethod
    async def find_all(self) -> List[T]:
        """
        Find all entities
        
        Returns:
            List of all entities
        """
        pass
    
    @abc.abstractmethod
    async def delete(self, id: ID) -> bool:
        """
        Delete entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def exists(self, id: ID) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def count(self) -> int:
        """
        Count entities in repository
        
        Returns:
            Number of entities
        """
        pass

class HealthCheck(abc.ABC):
    """Interface for health check functionality"""
    
    @abc.abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of repository
        
        Returns:
            Health check result with status and details
        """
        pass

class TransactionalRepository(Repository[T, ID], abc.ABC):
    """
    Abstract base repository interface with transaction support
    
    Generic parameters:
        T: Entity type
        ID: ID type
    """
    
    @abc.abstractmethod
    async def begin_transaction(self) -> Any:
        """
        Begin a transaction
        
        Returns:
            Transaction object
        """
        pass
    
    @abc.abstractmethod
    async def commit_transaction(self, transaction: Any) -> bool:
        """
        Commit a transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            True if transaction was committed, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def rollback_transaction(self, transaction: Any) -> bool:
        """
        Rollback a transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            True if transaction was rolled back, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def save_in_transaction(self, transaction: Any, entity: T) -> T:
        """
        Save entity in transaction
        
        Args:
            transaction: Transaction object
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        pass
    
    @abc.abstractmethod
    async def delete_in_transaction(self, transaction: Any, id: ID) -> bool:
        """
        Delete entity in transaction
        
        Args:
            transaction: Transaction object
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        pass

class CacheableRepository(Repository[T, ID], abc.ABC):
    """
    Abstract base repository interface with caching support
    
    Generic parameters:
        T: Entity type
        ID: ID type
    """
    
    @abc.abstractmethod
    async def get_from_cache(self, id: ID) -> Optional[T]:
        """
        Get entity from cache
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found in cache, None otherwise
        """
        pass
    
    @abc.abstractmethod
    async def put_in_cache(self, entity: T) -> bool:
        """
        Put entity in cache
        
        Args:
            entity: Entity to cache
            
        Returns:
            True if entity was cached, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def remove_from_cache(self, id: ID) -> bool:
        """
        Remove entity from cache
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was removed from cache, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def clear_cache(self) -> bool:
        """
        Clear cache
        
        Returns:
            True if cache was cleared, False otherwise
        """
        pass

class RepositoryFactory(abc.ABC):
    """Abstract factory for creating repositories"""
    
    @abc.abstractmethod
    def create_repository(self, entity_type: str) -> Repository:
        """
        Create repository for entity type
        
        Args:
            entity_type: Entity type
            
        Returns:
            Repository instance
        """
        pass
