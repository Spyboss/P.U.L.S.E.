"""
SQLite Repository Implementation for P.U.L.S.E.
Provides SQLite-specific repository implementations
"""

import os
import json
import sqlite3
import asyncio
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, cast
from datetime import datetime
import structlog
import aiosqlite
import numpy as np

from utils.repository.base import Entity, Repository, TransactionalRepository, CacheableRepository, HealthCheck
from utils.repository.chat import Message, Conversation, Memory, MessageRole, MessageRepository, ConversationRepository, MemoryRepository
from utils.error_handler import with_error_handling, ErrorSource
from utils.circuit_breaker import circuit_breaker
from utils.sqlite_utils import optimize_sqlite_db, create_table

# Configure logger
logger = structlog.get_logger("sqlite_repository")

# Type variables
T = TypeVar('T', bound=Entity)

class SQLiteRepository(Repository[T, str], HealthCheck):
    """Base SQLite repository implementation"""
    
    def __init__(
        self,
        table_name: str,
        entity_class: type,
        db_path: str = "data/pulse.db",
        schema: Optional[Dict[str, str]] = None
    ):
        """
        Initialize SQLite repository
        
        Args:
            table_name: SQLite table name
            entity_class: Entity class
            db_path: SQLite database path
            schema: Table schema (column name -> type)
        """
        self.table_name = table_name
        self.entity_class = entity_class
        self.db_path = db_path
        self.schema = schema or {}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database"""
        try:
            # Optimize SQLite database
            optimize_sqlite_db(self.db_path)
            
            # Create table if it doesn't exist
            if self.schema:
                create_table(
                    db_path=self.db_path,
                    table_name=self.table_name,
                    columns=self.schema,
                    primary_key="id",
                    indexes=[]  # Override in subclasses
                )
                
            logger.info(f"SQLite repository initialized: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {str(e)}")
    
    def _entity_to_row(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to SQLite row
        
        Args:
            entity: Entity to convert
            
        Returns:
            SQLite row
        """
        # Convert entity to dictionary
        row = entity.to_dict()
        
        # Convert complex types to JSON
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value)
            elif isinstance(value, datetime):
                row[key] = value.isoformat()
                
        return row
    
    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        """
        Convert SQLite row to entity
        
        Args:
            row: SQLite row
            
        Returns:
            Entity instance
        """
        # Convert JSON strings to objects
        for key, value in row.items():
            if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                try:
                    row[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass
                    
        # Create entity from dictionary
        return self.entity_class.from_dict(row)
    
    async def _execute(self, query: str, params: tuple = ()) -> Any:
        """
        Execute SQLite query
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query result
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor
    
    async def _fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute SQLite query and fetch all results
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of rows
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def _fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute SQLite query and fetch one result
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Row or None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def save(self, entity: T) -> T:
        """
        Save entity to SQLite
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        # Update timestamp
        entity.updated_at = datetime.now()
        
        # Convert entity to row
        row = self._entity_to_row(entity)
        
        # Check if entity exists
        exists = await self.exists(entity.id)
        
        if exists:
            # Update entity
            set_clause = ", ".join([f"{key} = ?" for key in row.keys()])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
            params = tuple(row.values()) + (entity.id,)
            
            await self._execute(query, params)
        else:
            # Insert entity
            columns = ", ".join(row.keys())
            placeholders = ", ".join(["?"] * len(row))
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            params = tuple(row.values())
            
            await self._execute(query, params)
        
        # Return entity
        return entity
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        # Find entity by ID
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = await self._fetchone(query, (id,))
        
        # Return entity if found
        if row:
            return self._row_to_entity(row)
        
        return None
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_all(self) -> List[T]:
        """
        Find all entities
        
        Returns:
            List of all entities
        """
        # Find all entities
        query = f"SELECT * FROM {self.table_name}"
        rows = await self._fetchall(query)
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def delete(self, id: str) -> bool:
        """
        Delete entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        # Delete entity by ID
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        cursor = await self._execute(query, (id,))
        
        # Return True if entity was deleted
        return cursor.rowcount > 0
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def exists(self, id: str) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        # Check if entity exists
        query = f"SELECT 1 FROM {self.table_name} WHERE id = ?"
        row = await self._fetchone(query, (id,))
        
        # Return True if entity exists
        return row is not None
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def count(self) -> int:
        """
        Count entities in repository
        
        Returns:
            Number of entities
        """
        # Count entities
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        row = await self._fetchone(query)
        
        # Return count
        return row["count"] if row else 0
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of SQLite repository
        
        Returns:
            Health check result with status and details
        """
        try:
            # Check if database file exists
            if not os.path.exists(self.db_path):
                return {
                    "status": "down",
                    "details": {
                        "error": f"Database file not found: {self.db_path}"
                    }
                }
            
            # Check if table exists
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            row = await self._fetchone(query, (self.table_name,))
            
            if not row:
                return {
                    "status": "down",
                    "details": {
                        "error": f"Table not found: {self.table_name}"
                    }
                }
            
            # Count entities
            count = await self.count()
            
            return {
                "status": "up",
                "details": {
                    "table": self.table_name,
                    "count": count
                }
            }
        except Exception as e:
            return {
                "status": "down",
                "details": {
                    "error": str(e)
                }
            }

class SQLiteMessageRepository(SQLiteRepository[Message], MessageRepository):
    """SQLite repository for chat messages"""
    
    def __init__(self, db_path: str = "data/pulse.db"):
        """
        Initialize SQLite message repository
        
        Args:
            db_path: SQLite database path
        """
        super().__init__(
            table_name="messages",
            entity_class=Message,
            db_path=db_path,
            schema={
                "id": "TEXT PRIMARY KEY",
                "conversation_id": "TEXT",
                "role": "TEXT",
                "content": "TEXT",
                "timestamp": "TEXT",
                "created_at": "TEXT",
                "updated_at": "TEXT",
                "metadata": "TEXT"  # JSON string
            }
        )
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create indexes for messages table"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create indexes
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_conversation_id ON {self.table_name} (conversation_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp ON {self.table_name} (timestamp)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_conversation_timestamp ON {self.table_name} (conversation_id, timestamp)")
            
            # Commit changes
            conn.commit()
            
            # Close connection
            conn.close()
        except Exception as e:
            logger.error(f"Failed to create indexes for {self.table_name}: {str(e)}")
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Find messages by conversation ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages
        """
        # Find messages by conversation ID
        query = f"SELECT * FROM {self.table_name} WHERE conversation_id = ? ORDER BY timestamp ASC"
        rows = await self._fetchall(query, (conversation_id,))
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Message]:
        """
        Find messages by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        # Find conversations by user ID
        query = f"""
            SELECT m.* FROM {self.table_name} m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        """
        rows = await self._fetchall(query, (user_id, limit))
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]

class SQLiteConversationRepository(SQLiteRepository[Conversation], ConversationRepository):
    """SQLite repository for conversations"""
    
    def __init__(self, db_path: str = "data/pulse.db"):
        """
        Initialize SQLite conversation repository
        
        Args:
            db_path: SQLite database path
        """
        super().__init__(
            table_name="conversations",
            entity_class=Conversation,
            db_path=db_path,
            schema={
                "id": "TEXT PRIMARY KEY",
                "user_id": "TEXT",
                "title": "TEXT",
                "start_time": "TEXT",
                "end_time": "TEXT",
                "summary": "TEXT",
                "created_at": "TEXT",
                "updated_at": "TEXT",
                "metadata": "TEXT"  # JSON string
            }
        )
        
        # Initialize message repository
        self.message_repository = SQLiteMessageRepository(db_path=db_path)
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create indexes for conversations table"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create indexes
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id ON {self.table_name} (user_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_start_time ON {self.table_name} (start_time)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_start ON {self.table_name} (user_id, start_time)")
            
            # Commit changes
            conn.commit()
            
            # Close connection
            conn.close()
        except Exception as e:
            logger.error(f"Failed to create indexes for {self.table_name}: {str(e)}")
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """
        Find conversations by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        # Find conversations by user ID
        query = f"SELECT * FROM {self.table_name} WHERE user_id = ? ORDER BY start_time DESC LIMIT ?"
        rows = await self._fetchall(query, (user_id, limit))
        
        # Convert rows to entities
        conversations = [self._row_to_entity(row) for row in rows]
        
        # Load messages for each conversation
        for conversation in conversations:
            conversation.messages = await self.message_repository.find_by_conversation_id(conversation.id)
        
        return conversations
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_recent(self, limit: int = 10) -> List[Conversation]:
        """
        Find recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations
        """
        # Find recent conversations
        query = f"SELECT * FROM {self.table_name} ORDER BY start_time DESC LIMIT ?"
        rows = await self._fetchall(query, (limit,))
        
        # Convert rows to entities
        conversations = [self._row_to_entity(row) for row in rows]
        
        # Load messages for each conversation
        for conversation in conversations:
            conversation.messages = await self.message_repository.find_by_conversation_id(conversation.id)
        
        return conversations
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """
        Add message to conversation
        
        Args:
            conversation_id: Conversation ID
            message: Message to add
            
        Returns:
            Added message
        """
        # Set conversation ID if not set
        if not message.conversation_id:
            message.conversation_id = conversation_id
        
        # Save message
        saved_message = await self.message_repository.save(message)
        
        # Update conversation
        query = f"UPDATE {self.table_name} SET updated_at = ? WHERE id = ?"
        await self._execute(query, (datetime.now().isoformat(), conversation_id))
        
        return saved_message
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_id(self, id: str) -> Optional[Conversation]:
        """
        Find conversation by ID
        
        Args:
            id: Conversation ID
            
        Returns:
            Conversation if found, None otherwise
        """
        # Find conversation
        conversation = await super().find_by_id(id)
        
        if conversation:
            # Load messages for conversation
            conversation.messages = await self.message_repository.find_by_conversation_id(conversation.id)
        
        return conversation

class SQLiteMemoryRepository(SQLiteRepository[Memory], MemoryRepository):
    """SQLite repository for memories"""
    
    def __init__(self, db_path: str = "data/pulse.db"):
        """
        Initialize SQLite memory repository
        
        Args:
            db_path: SQLite database path
        """
        super().__init__(
            table_name="memories",
            entity_class=Memory,
            db_path=db_path,
            schema={
                "id": "TEXT PRIMARY KEY",
                "user_id": "TEXT",
                "category": "TEXT",
                "content": "TEXT",
                "timestamp": "TEXT",
                "created_at": "TEXT",
                "updated_at": "TEXT",
                "metadata": "TEXT",  # JSON string
                "vector_blob": "BLOB"  # Binary vector data
            }
        )
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create indexes for memories table"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create indexes
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id ON {self.table_name} (user_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_category ON {self.table_name} (category)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp ON {self.table_name} (timestamp)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_category ON {self.table_name} (user_id, category)")
            
            # Create virtual table for full-text search
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name}_fts USING fts5(
                    content,
                    content_rowid=id
                )
            """)
            
            # Create trigger to update FTS table
            cursor.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {self.table_name}_ai AFTER INSERT ON {self.table_name} BEGIN
                    INSERT INTO {self.table_name}_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)
            
            cursor.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {self.table_name}_ad AFTER DELETE ON {self.table_name} BEGIN
                    INSERT INTO {self.table_name}_fts({self.table_name}_fts, rowid, content) VALUES('delete', old.id, old.content);
                END
            """)
            
            cursor.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {self.table_name}_au AFTER UPDATE ON {self.table_name} BEGIN
                    INSERT INTO {self.table_name}_fts({self.table_name}_fts, rowid, content) VALUES('delete', old.id, old.content);
                    INSERT INTO {self.table_name}_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)
            
            # Commit changes
            conn.commit()
            
            # Close connection
            conn.close()
        except Exception as e:
            logger.error(f"Failed to create indexes for {self.table_name}: {str(e)}")
    
    def _entity_to_row(self, entity: Memory) -> Dict[str, Any]:
        """
        Convert entity to SQLite row
        
        Args:
            entity: Entity to convert
            
        Returns:
            SQLite row
        """
        # Convert entity to row
        row = super()._entity_to_row(entity)
        
        # Convert vector to binary
        if entity.vector:
            row["vector_blob"] = np.array(entity.vector, dtype=np.float32).tobytes()
        
        return row
    
    def _row_to_entity(self, row: Dict[str, Any]) -> Memory:
        """
        Convert SQLite row to entity
        
        Args:
            row: SQLite row
            
        Returns:
            Entity instance
        """
        # Convert binary vector to list
        if "vector_blob" in row and row["vector_blob"]:
            try:
                vector = np.frombuffer(row["vector_blob"], dtype=np.float32).tolist()
                row["vector"] = vector
            except Exception as e:
                logger.warning(f"Failed to convert vector blob: {str(e)}")
        
        # Convert row to entity
        return super()._row_to_entity(row)
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by user ID
        
        Args:
            user_id: User ID
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Find memories by user ID
        query = f"SELECT * FROM {self.table_name} WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?"
        rows = await self._fetchall(query, (user_id, limit))
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def find_by_category(self, category: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by category
        
        Args:
            category: Memory category
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Find memories by category
        query = f"SELECT * FROM {self.table_name} WHERE category = ? ORDER BY timestamp DESC LIMIT ?"
        rows = await self._fetchall(query, (category, limit))
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
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
        # Find memories by user ID and category
        query = f"SELECT * FROM {self.table_name} WHERE user_id = ? AND category = ? ORDER BY timestamp DESC LIMIT ?"
        rows = await self._fetchall(query, (user_id, category, limit))
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]
    
    @circuit_breaker(name="sqlite", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.SQLITE)
    async def search_similar(self, content: str, limit: int = 5) -> List[Memory]:
        """
        Search for similar memories
        
        Args:
            content: Content to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        # Search for similar memories using FTS
        query = f"""
            SELECT m.* FROM {self.table_name} m
            JOIN {self.table_name}_fts fts ON m.id = fts.rowid
            WHERE fts.content MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        rows = await self._fetchall(query, (content, limit))
        
        # Convert rows to entities
        return [self._row_to_entity(row) for row in rows]
