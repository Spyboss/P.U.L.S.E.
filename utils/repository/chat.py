"""
Chat Repository Pattern for P.U.L.S.E.
Provides chat-specific entities and repositories
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
import structlog
from enum import Enum

from utils.repository.base import Entity, Repository, TransactionalRepository, CacheableRepository

# Configure logger
logger = structlog.get_logger("chat_repository")

class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(Entity):
    """Chat message entity"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        role: Union[MessageRole, str] = MessageRole.USER,
        content: str = "",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize chat message
        
        Args:
            id: Optional message ID (generated if not provided)
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            timestamp: Message timestamp (current time if not provided)
            metadata: Optional metadata
        """
        super().__init__(id)
        self.conversation_id = conversation_id
        
        # Convert string role to enum if needed
        if isinstance(role, str):
            try:
                self.role = MessageRole(role)
            except ValueError:
                self.role = MessageRole.USER
                logger.warning(f"Invalid message role: {role}, using USER")
        else:
            self.role = role
            
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary
        
        Returns:
            Dictionary representation of message
        """
        result = super().to_dict()
        result.update({
            "conversation_id": self.conversation_id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create message from dictionary
        
        Args:
            data: Dictionary representation of message
            
        Returns:
            Message instance
        """
        # Create base entity
        entity = super(Message, cls).from_dict(data)
        
        # Parse timestamp
        timestamp = None
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        # Create message
        return Message(
            id=entity.id,
            conversation_id=data.get("conversation_id"),
            role=data.get("role", MessageRole.USER),
            content=data.get("content", ""),
            timestamp=timestamp or entity.created_at,
            metadata=data.get("metadata", {})
        )

class Conversation(Entity):
    """Chat conversation entity"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "default",
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Message]] = None
    ):
        """
        Initialize chat conversation
        
        Args:
            id: Optional conversation ID (generated if not provided)
            user_id: User ID
            title: Conversation title
            start_time: Conversation start time (current time if not provided)
            end_time: Conversation end time
            summary: Conversation summary
            metadata: Optional metadata
            messages: Optional list of messages
        """
        super().__init__(id)
        self.user_id = user_id
        self.title = title
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.summary = summary
        self.metadata = metadata or {}
        self.messages = messages or []
    
    def add_message(self, message: Message) -> Message:
        """
        Add message to conversation
        
        Args:
            message: Message to add
            
        Returns:
            Added message
        """
        # Set conversation ID if not set
        if not message.conversation_id:
            message.conversation_id = self.id
            
        # Add message to conversation
        self.messages.append(message)
        
        # Update conversation
        self.updated_at = datetime.now()
        
        return message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert conversation to dictionary
        
        Returns:
            Dictionary representation of conversation
        """
        result = super().to_dict()
        result.update({
            "user_id": self.user_id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "summary": self.summary,
            "metadata": self.metadata,
            "messages": [message.to_dict() for message in self.messages]
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        Create conversation from dictionary
        
        Args:
            data: Dictionary representation of conversation
            
        Returns:
            Conversation instance
        """
        # Create base entity
        entity = super(Conversation, cls).from_dict(data)
        
        # Parse timestamps
        start_time = None
        if "start_time" in data:
            if isinstance(data["start_time"], str):
                start_time = datetime.fromisoformat(data["start_time"])
            elif isinstance(data["start_time"], datetime):
                start_time = data["start_time"]
                
        end_time = None
        if "end_time" in data and data["end_time"]:
            if isinstance(data["end_time"], str):
                end_time = datetime.fromisoformat(data["end_time"])
            elif isinstance(data["end_time"], datetime):
                end_time = data["end_time"]
        
        # Parse messages
        messages = []
        if "messages" in data and data["messages"]:
            for message_data in data["messages"]:
                messages.append(Message.from_dict(message_data))
        
        # Create conversation
        return Conversation(
            id=entity.id,
            user_id=data.get("user_id", "default"),
            title=data.get("title"),
            start_time=start_time or entity.created_at,
            end_time=end_time,
            summary=data.get("summary"),
            metadata=data.get("metadata", {}),
            messages=messages
        )

class Memory(Entity):
    """Memory entity for long-term storage"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "default",
        category: str = "general",
        content: str = "",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        vector: Optional[List[float]] = None
    ):
        """
        Initialize memory
        
        Args:
            id: Optional memory ID (generated if not provided)
            user_id: User ID
            category: Memory category
            content: Memory content
            timestamp: Memory timestamp (current time if not provided)
            metadata: Optional metadata
            vector: Optional vector embedding
        """
        super().__init__(id)
        self.user_id = user_id
        self.category = category
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.vector = vector
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert memory to dictionary
        
        Returns:
            Dictionary representation of memory
        """
        result = super().to_dict()
        result.update({
            "user_id": self.user_id,
            "category": self.category,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        })
        
        # Add vector if available
        if self.vector:
            result["vector"] = self.vector
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """
        Create memory from dictionary
        
        Args:
            data: Dictionary representation of memory
            
        Returns:
            Memory instance
        """
        # Create base entity
        entity = super(Memory, cls).from_dict(data)
        
        # Parse timestamp
        timestamp = None
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        # Create memory
        return Memory(
            id=entity.id,
            user_id=data.get("user_id", "default"),
            category=data.get("category", "general"),
            content=data.get("content", ""),
            timestamp=timestamp or entity.created_at,
            metadata=data.get("metadata", {}),
            vector=data.get("vector")
        )

class MessageRepository(Repository[Message, str]):
    """Repository interface for chat messages"""
    
    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Find messages by conversation ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages
        """
        pass
    
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Message]:
        """
        Find messages by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        pass

class ConversationRepository(Repository[Conversation, str]):
    """Repository interface for conversations"""
    
    async def find_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """
        Find conversations by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        pass
    
    async def find_recent(self, limit: int = 10) -> List[Conversation]:
        """
        Find recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        pass
    
    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """
        Add message to conversation
        
        Args:
            conversation_id: Conversation ID
            message: Message to add
            
        Returns:
            Added message
        """
        pass

class MemoryRepository(Repository[Memory, str]):
    """Repository interface for memories"""
    
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        pass
    
    async def find_by_category(self, category: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by category
        
        Args:
            category: Memory category
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        pass
    
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
        pass
    
    async def search_similar(self, content: str, limit: int = 5) -> List[Memory]:
        """
        Search for similar memories
        
        Args:
            content: Content to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        pass
