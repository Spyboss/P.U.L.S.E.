"""
MongoDB Repository Implementation for P.U.L.S.E.
Provides MongoDB-specific repository implementations
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, cast
from datetime import datetime
import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError, ServerSelectionTimeoutError
from pymongo import ReturnDocument
from bson import ObjectId
from dotenv import load_dotenv

from utils.repository.base import Entity, Repository, TransactionalRepository, CacheableRepository, HealthCheck
from utils.repository.chat import Message, Conversation, Memory, MessageRepository, ConversationRepository, MemoryRepository
from utils.error_handler import with_error_handling, ErrorSource
from utils.circuit_breaker import circuit_breaker
from utils.dns_resolver import get_hostname_from_uri, resolve_with_retry, check_mongodb_dns

# Configure logger
logger = structlog.get_logger("mongodb_repository")

# Load environment variables
load_dotenv()

# Type variables
T = TypeVar('T', bound=Entity)

class MongoDBRepository(Repository[T, str], HealthCheck):
    """Base MongoDB repository implementation"""

    def __init__(
        self,
        collection_name: str,
        entity_class: type,
        db_name: str = "pulse",
        connection_string: Optional[str] = None
    ):
        """
        Initialize MongoDB repository

        Args:
            collection_name: MongoDB collection name
            entity_class: Entity class
            db_name: MongoDB database name
            connection_string: MongoDB connection string (from env if not provided)
        """
        self.collection_name = collection_name
        self.entity_class = entity_class
        self.db_name = db_name
        self.connection_string = connection_string or os.getenv("MONGODB_URI")

        # Initialize client and database
        self.client = None
        self.db = None
        self.collection = None

        # Initialize MongoDB connection
        if self.connection_string:
            self._init_mongodb()
        else:
            logger.warning(f"MongoDB connection string not provided for {collection_name}")

    def _init_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        try:
            # Check DNS resolution first - but don't wait for it
            dns_check_task = asyncio.create_task(self._check_dns_resolution())

            # Try to create a connection with the original connection string
            try:
                # Check if we have a cached IP for this hostname
                from utils.dns_resolver import _dns_cache, get_hostname_from_uri
                hostname = get_hostname_from_uri(self.connection_string)

                # If we have a cached IP, use direct connection
                if hostname and hostname in _dns_cache:
                    ip_address, _ = _dns_cache[hostname]
                    logger.info(f"Using cached IP for MongoDB: {hostname} -> {ip_address}")

                    # Extract credentials and database from the connection string
                    from urllib.parse import urlparse
                    parsed_uri = urlparse(self.connection_string)

                    # Extract username and password
                    auth_part = parsed_uri.netloc.split('@')[0]
                    username = auth_part.split(':')[0]
                    password = auth_part.split(':')[1] if ':' in auth_part else ''

                    # Create a direct connection string with cached IP
                    direct_uri = f"mongodb://{username}:{password}@{ip_address}:27017/?retryWrites=true&w=majority"

                    # Create MongoDB client with direct connection
                    self.client = AsyncIOMotorClient(
                        direct_uri,
                        serverSelectionTimeoutMS=5000,    # Increased from 2000
                        connectTimeoutMS=5000,            # Increased from 2000
                        socketTimeoutMS=10000,            # Increased from 3000
                        maxIdleTimeMS=60000,              # 60 seconds
                        retryWrites=True,                 # Enable retry for write operations
                        retryReads=True,                  # Enable retry for read operations
                        waitQueueTimeoutMS=5000,          # Increased from 2000
                        appName="P.U.L.S.E.",             # Application name for monitoring
                        directConnection=True,            # Use direct connection
                        tlsInsecure=True,                 # Allow insecure TLS
                        tlsAllowInvalidCertificates=True  # Allow invalid certificates
                    )
                else:
                    # Create MongoDB client with optimized connection settings
                    self.client = AsyncIOMotorClient(
                        self.connection_string,
                        serverSelectionTimeoutMS=5000,  # Increased from 2000
                        connectTimeoutMS=5000,          # Increased from 2000
                        socketTimeoutMS=10000,          # Increased from 3000
                        maxIdleTimeMS=60000,            # 60 seconds
                        retryWrites=True,               # Enable retry for write operations
                        retryReads=True,                # Enable retry for read operations
                        waitQueueTimeoutMS=5000,        # Increased from 2000
                        appName="P.U.L.S.E.",           # Application name for monitoring
                        directConnection=False,         # Use replica set discovery
                    maxPoolSize=10,                 # Maximum connection pool size
                    minPoolSize=1,                  # Minimum connection pool size
                    maxConnecting=2,                # Maximum number of connections being established
                    heartbeatFrequencyMS=10000,     # Heartbeat frequency in milliseconds
                    tlsInsecure=True,               # Allow insecure TLS connections
                    tlsAllowInvalidCertificates=True  # Allow invalid certificates
                )

                # Test connection with a quick ping
                self.client.admin.command('ping', serverSelectionTimeoutMS=2000)

                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]

                # Create indexes - but don't wait for it
                index_task = asyncio.create_task(self._create_indexes())

                logger.info(f"Connected to MongoDB Atlas: {self.db_name}.{self.collection_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect with original connection string: {str(e)}")
                # Continue to try with direct connection

            # If the original connection failed, try with direct connection using hardcoded IP
            try:
                # Use the direct connection utility
                from utils.direct_connection import get_mongodb_direct_connection

                # Get direct connection client
                self.client = get_mongodb_direct_connection(self.connection_string)

                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]

                # Create indexes - but don't wait for it
                index_task = asyncio.create_task(self._create_indexes())

                logger.info(f"Connected to MongoDB Atlas using direct connection: {self.db_name}.{self.collection_name}")
                return
            except Exception as e:
                logger.error(f"Failed to connect with direct connection: {str(e)}")
                # Fall through to error handling

            # If we got here, both connection attempts failed
            logger.error("All MongoDB connection attempts failed")
            self.client = None
            self.db = None
            self.collection = None

            # Try to reconnect in the background after a delay
            asyncio.create_task(self._delayed_reconnect())
        except (ConnectionFailure, OperationFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            self.collection = None

            # Try to reconnect in the background after a delay
            asyncio.create_task(self._delayed_reconnect())

    async def _delayed_reconnect(self, delay: float = 5.0, max_attempts: int = 3) -> None:
        """
        Attempt to reconnect to MongoDB after a delay

        Args:
            delay: Delay in seconds before reconnecting
            max_attempts: Maximum number of reconnection attempts
        """
        for attempt in range(max_attempts):
            # Wait before reconnecting
            await asyncio.sleep(delay * (attempt + 1))  # Increasing delay with each attempt

            logger.info(f"Attempting to reconnect to MongoDB (attempt {attempt + 1}/{max_attempts})")

            try:
                # Create MongoDB client with optimized connection settings
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=3000,
                    connectTimeoutMS=3000,
                    socketTimeoutMS=5000,
                    maxIdleTimeMS=60000,
                    retryWrites=True,
                    retryReads=True,
                    waitQueueTimeoutMS=3000,
                    appName="P.U.L.S.E.",
                    directConnection=False,
                    maxPoolSize=10,
                    minPoolSize=1,
                    maxConnecting=2,
                    heartbeatFrequencyMS=10000
                )

                # Test connection with ping
                await self.client.admin.command("ping")

                # Connection successful, initialize database and collection
                self.db = self.client[self.db_name]
                self.collection = self.db[self.collection_name]

                # Create indexes
                await self._create_indexes()

                logger.info(f"Successfully reconnected to MongoDB: {self.db_name}.{self.collection_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to reconnect to MongoDB (attempt {attempt + 1}/{max_attempts}): {str(e)}")

                # Close client if it was created
                if self.client:
                    self.client.close()
                    self.client = None
                    self.db = None
                    self.collection = None

        logger.error(f"Failed to reconnect to MongoDB after {max_attempts} attempts")

    async def _check_dns_resolution(self) -> None:
        """Check DNS resolution for MongoDB URI"""
        if not self.connection_string:
            return

        try:
            # Check MongoDB DNS resolution
            dns_result = await check_mongodb_dns(self.connection_string)

            if dns_result["resolvable"]:
                logger.info(f"MongoDB DNS resolution successful: {dns_result['hostname']} -> {dns_result['ip_address']}")
            else:
                logger.warning(f"MongoDB DNS resolution failed: {dns_result['message']}")

                # Try with fallback DNS servers
                from utils.dns_resolver import resolve_with_fallback_dns, get_hostname_from_uri
                hostname = get_hostname_from_uri(self.connection_string)
                if hostname:
                    ip_address = await resolve_with_fallback_dns(hostname)
                    if ip_address:
                        logger.info(f"MongoDB DNS resolution successful with fallback DNS: {hostname} -> {ip_address}")
                    else:
                        logger.error(f"MongoDB DNS resolution failed with all DNS servers for {hostname}")
        except Exception as e:
            logger.error(f"Error checking MongoDB DNS resolution: {str(e)}")

    async def _create_indexes(self) -> None:
        """Create indexes for collection"""
        # Override in subclasses to create specific indexes
        pass

    def _entity_to_document(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to MongoDB document

        Args:
            entity: Entity to convert

        Returns:
            MongoDB document
        """
        # Convert entity to dictionary
        doc = entity.to_dict()

        # Use MongoDB ObjectId for _id
        doc["_id"] = doc.pop("id")

        return doc

    def _document_to_entity(self, doc: Dict[str, Any]) -> T:
        """
        Convert MongoDB document to entity

        Args:
            doc: MongoDB document

        Returns:
            Entity instance
        """
        # Convert MongoDB _id to id
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))

        # Create entity from dictionary
        return self.entity_class.from_dict(doc)

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def save(self, entity: T) -> T:
        """
        Save entity to MongoDB

        Args:
            entity: Entity to save

        Returns:
            Saved entity with ID
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Update timestamp
        entity.updated_at = datetime.now()

        # Convert entity to document
        doc = self._entity_to_document(entity)

        # Insert or update document
        try:
            result = await self.collection.find_one_and_replace(
                {"_id": doc["_id"]},
                doc,
                upsert=True,
                return_document=ReturnDocument.AFTER
            )

            # Convert result to entity
            return self._document_to_entity(result)
        except DuplicateKeyError:
            # Handle duplicate key error
            logger.warning(f"Duplicate key error for {self.collection_name}: {entity.id}")

            # Try to get existing document
            existing = await self.collection.find_one({"_id": doc["_id"]})
            if existing:
                return self._document_to_entity(existing)

            # If not found, raise error
            raise

    @circuit_breaker(name="mongodb", failure_threshold=5, reset_timeout=60.0)
    @with_error_handling(source=ErrorSource.MONGODB, reraise=False)
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find entity by ID

        Args:
            id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        if not self.collection:
            logger.warning(f"MongoDB collection not initialized, using fallback for find_by_id({id})")
            return None

        try:
            # Find document by ID with timeout
            doc = await asyncio.wait_for(
                self.collection.find_one({"_id": id}),
                timeout=5.0  # 5 second timeout
            )

            # Return entity if found
            if doc:
                return self._document_to_entity(doc)

            return None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout while finding document by ID: {id}")
            return None
        except Exception as e:
            logger.warning(f"Error finding document by ID: {id}, error: {str(e)}")
            return None

    @circuit_breaker(name="mongodb", failure_threshold=5, reset_timeout=60.0)
    @with_error_handling(source=ErrorSource.MONGODB, reraise=False)
    async def find_all(self) -> List[T]:
        """
        Find all entities

        Returns:
            List of all entities
        """
        if not self.collection:
            logger.warning("MongoDB collection not initialized, using fallback for find_all()")
            return []

        try:
            # Find all documents with timeout
            entities = []

            # Create cursor
            cursor = self.collection.find().limit(100)  # Limit to 100 documents for safety

            # Process cursor with timeout
            try:
                async with asyncio.timeout(10.0):  # 10 second timeout
                    async for doc in cursor:
                        entities.append(self._document_to_entity(doc))
            except asyncio.TimeoutError:
                logger.warning("Timeout while processing cursor in find_all()")
                # Return whatever we've collected so far

            return entities
        except Exception as e:
            logger.warning(f"Error in find_all(): {str(e)}")
            return []

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def delete(self, id: str) -> bool:
        """
        Delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if entity was deleted, False otherwise
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Delete document by ID
        result = await self.collection.delete_one({"_id": id})

        # Return True if document was deleted
        return result.deleted_count > 0

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def exists(self, id: str) -> bool:
        """
        Check if entity exists

        Args:
            id: Entity ID

        Returns:
            True if entity exists, False otherwise
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Count documents with ID
        count = await self.collection.count_documents({"_id": id})

        # Return True if document exists
        return count > 0

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def count(self) -> int:
        """
        Count entities in repository

        Returns:
            Number of entities
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Count all documents
        return await self.collection.count_documents({})

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of MongoDB repository

        Returns:
            Health check result with status and details
        """
        if not self.client:
            return {
                "status": "down",
                "details": {
                    "error": "MongoDB client not initialized"
                }
            }

        try:
            # Ping MongoDB
            await self.client.admin.command("ping")

            # Count documents
            count = await self.count()

            return {
                "status": "up",
                "details": {
                    "collection": self.collection_name,
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

class MongoDBMessageRepository(MongoDBRepository[Message], MessageRepository):
    """MongoDB repository for chat messages"""

    def __init__(
        self,
        collection_name: str = "messages",
        db_name: str = "pulse",
        connection_string: Optional[str] = None
    ):
        """
        Initialize MongoDB message repository

        Args:
            collection_name: MongoDB collection name
            db_name: MongoDB database name
            connection_string: MongoDB connection string (from env if not provided)
        """
        super().__init__(collection_name, Message, db_name, connection_string)

    async def _create_indexes(self) -> None:
        """Create indexes for messages collection"""
        if not self.collection:
            return

        # Create indexes
        await self.collection.create_index("conversation_id")
        await self.collection.create_index([("conversation_id", 1), ("timestamp", 1)])
        await self.collection.create_index("timestamp")

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Find messages by conversation ID

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find messages by conversation ID
        cursor = self.collection.find({"conversation_id": conversation_id}).sort("timestamp", 1)

        # Convert documents to entities
        messages = []
        async for doc in cursor:
            messages.append(self._document_to_entity(doc))

        return messages

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Message]:
        """
        Find messages by user ID

        Args:
            user_id: User ID
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find conversations by user ID
        conversation_cursor = self.db["conversations"].find({"user_id": user_id})

        # Get conversation IDs
        conversation_ids = []
        async for doc in conversation_cursor:
            conversation_ids.append(str(doc["_id"]))

        if not conversation_ids:
            return []

        # Find messages by conversation IDs
        cursor = self.collection.find({"conversation_id": {"$in": conversation_ids}}).sort("timestamp", -1).limit(limit)

        # Convert documents to entities
        messages = []
        async for doc in cursor:
            messages.append(self._document_to_entity(doc))

        return messages

class MongoDBConversationRepository(MongoDBRepository[Conversation], ConversationRepository):
    """MongoDB repository for conversations"""

    def __init__(
        self,
        collection_name: str = "conversations",
        db_name: str = "pulse",
        connection_string: Optional[str] = None
    ):
        """
        Initialize MongoDB conversation repository

        Args:
            collection_name: MongoDB collection name
            db_name: MongoDB database name
            connection_string: MongoDB connection string (from env if not provided)
        """
        super().__init__(collection_name, Conversation, db_name, connection_string)

        # Initialize message repository
        self.message_repository = MongoDBMessageRepository(
            db_name=db_name,
            connection_string=connection_string
        )

    async def _create_indexes(self) -> None:
        """Create indexes for conversations collection"""
        if not self.collection:
            return

        # Create indexes
        await self.collection.create_index("user_id")
        await self.collection.create_index("start_time")
        await self.collection.create_index([("user_id", 1), ("start_time", -1)])

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def find_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """
        Find conversations by user ID

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return

        Returns:
            List of conversations
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find conversations by user ID
        cursor = self.collection.find({"user_id": user_id}).sort("start_time", -1).limit(limit)

        # Convert documents to entities
        conversations = []
        async for doc in cursor:
            conversation = self._document_to_entity(doc)

            # Load messages for conversation
            conversation.messages = await self.message_repository.find_by_conversation_id(conversation.id)

            conversations.append(conversation)

        return conversations

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def find_recent(self, limit: int = 10) -> List[Conversation]:
        """
        Find recent conversations

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversations
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find recent conversations
        cursor = self.collection.find().sort("start_time", -1).limit(limit)

        # Convert documents to entities
        conversations = []
        async for doc in cursor:
            conversation = self._document_to_entity(doc)

            # Load messages for conversation
            conversation.messages = await self.message_repository.find_by_conversation_id(conversation.id)

            conversations.append(conversation)

        return conversations

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """
        Add message to conversation

        Args:
            conversation_id: Conversation ID
            message: Message to add

        Returns:
            Added message
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Set conversation ID if not set
        if not message.conversation_id:
            message.conversation_id = conversation_id

        # Save message
        saved_message = await self.message_repository.save(message)

        # Update conversation
        await self.collection.update_one(
            {"_id": conversation_id},
            {"$set": {"updated_at": datetime.now().isoformat()}}
        )

        return saved_message

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
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

class MongoDBMemoryRepository(MongoDBRepository[Memory], MemoryRepository):
    """MongoDB repository for memories"""

    def __init__(
        self,
        collection_name: str = "memories",
        db_name: str = "pulse",
        connection_string: Optional[str] = None
    ):
        """
        Initialize MongoDB memory repository

        Args:
            collection_name: MongoDB collection name
            db_name: MongoDB database name
            connection_string: MongoDB connection string (from env if not provided)
        """
        super().__init__(collection_name, Memory, db_name, connection_string)

    async def _create_indexes(self) -> None:
        """Create indexes for memories collection"""
        if not self.collection:
            return

        # Create indexes
        await self.collection.create_index("user_id")
        await self.collection.create_index("category")
        await self.collection.create_index([("user_id", 1), ("category", 1)])
        await self.collection.create_index("timestamp")

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by user ID

        Args:
            user_id: User ID
            limit: Maximum number of memories to return

        Returns:
            List of memories
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find memories by user ID
        cursor = self.collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)

        # Convert documents to entities
        memories = []
        async for doc in cursor:
            memories.append(self._document_to_entity(doc))

        return memories

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def find_by_category(self, category: str, limit: int = 100) -> List[Memory]:
        """
        Find memories by category

        Args:
            category: Memory category
            limit: Maximum number of memories to return

        Returns:
            List of memories
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find memories by category
        cursor = self.collection.find({"category": category}).sort("timestamp", -1).limit(limit)

        # Convert documents to entities
        memories = []
        async for doc in cursor:
            memories.append(self._document_to_entity(doc))

        return memories

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
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
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Find memories by user ID and category
        cursor = self.collection.find({
            "user_id": user_id,
            "category": category
        }).sort("timestamp", -1).limit(limit)

        # Convert documents to entities
        memories = []
        async for doc in cursor:
            memories.append(self._document_to_entity(doc))

        return memories

    @circuit_breaker(name="mongodb", failure_threshold=3, reset_timeout=30.0)
    @with_error_handling(source=ErrorSource.MONGODB)
    async def search_similar(self, content: str, limit: int = 5) -> List[Memory]:
        """
        Search for similar memories

        Args:
            content: Content to search for
            limit: Maximum number of memories to return

        Returns:
            List of memories
        """
        if not self.collection:
            raise ConnectionError("MongoDB collection not initialized")

        # Use text search if available
        if "text" in [idx["name"] for idx in await self.collection.list_indexes()]:
            # Find memories by text search
            cursor = self.collection.find(
                {"$text": {"$search": content}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)

            # Convert documents to entities
            memories = []
            async for doc in cursor:
                memories.append(self._document_to_entity(doc))

            return memories

        # Fallback to simple regex search
        cursor = self.collection.find({
            "content": {"$regex": content, "$options": "i"}
        }).limit(limit)

        # Convert documents to entities
        memories = []
        async for doc in cursor:
            memories.append(self._document_to_entity(doc))

        return memories
