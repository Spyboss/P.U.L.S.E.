"""
Memory Manager for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides optimized memory management with MongoDB and Zstandard compression
"""

import os
import json
import time
import asyncio
import psutil
import zstandard as zstd
import structlog
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Configure logger
logger = structlog.get_logger("memory_manager")

# Load environment variables
load_dotenv()

# Constants
MEMORY_LOW_THRESHOLD = 0.20  # 20% free memory threshold
MEMORY_CRITICAL_THRESHOLD = 0.10  # 10% free memory threshold
COMPRESSION_LEVEL = 3  # Zstandard compression level (1-22, higher = more compression but slower)
CACHE_PRUNE_INTERVAL = 300  # 5 minutes between cache pruning checks
DEFAULT_TTL = 86400  # 24 hours default TTL for cached items

class MemoryManager:
    """
    Optimized memory manager for P.U.L.S.E.
    Features:
    - MongoDB Atlas integration for persistent storage
    - Zstandard compression for memory-intensive data
    - Automatic cache pruning when system memory is constrained
    - Memory usage monitoring and optimization
    """

    def __init__(self, db_name: str = "pulse", collection_prefix: str = ""):
        """
        Initialize the memory manager

        Args:
            db_name: MongoDB database name
            collection_prefix: Optional prefix for collection names
        """
        self.logger = logger
        self.db_name = db_name
        self.collection_prefix = collection_prefix
        self.client = None
        self.db = None

        # Memory monitoring
        self.last_prune_time = time.time()
        self.memory_threshold = MEMORY_LOW_THRESHOLD
        self.critical_threshold = MEMORY_CRITICAL_THRESHOLD

        # Initialize compressor
        self.compressor = zstd.ZstdCompressor(level=COMPRESSION_LEVEL)
        self.decompressor = zstd.ZstdDecompressor()

        # Initialize MongoDB connection
        self._init_mongodb()

        # Local memory cache for frequently accessed data
        self.cache = {}

        logger.info("Memory manager initialized")

    def _init_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        # Disable MongoDB connection to avoid DNS issues
        logger.info("MongoDB connection disabled, using SQLite fallback")
        self.client = None
        self.db = None
        return

        # The code below is disabled to avoid DNS issues
        try:
            # Get MongoDB URI from environment variables
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                logger.warning("MONGODB_URI not found in environment variables, using SQLite fallback")
                return

            # Try standard connection first
            try:
                # Create MongoDB client with optimized connection settings
                self.client = AsyncIOMotorClient(
                    mongodb_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=10000,
                    maxIdleTimeMS=60000,
                    retryWrites=True,
                    retryReads=True,
                    waitQueueTimeoutMS=5000,
                    appName="P.U.L.S.E."
                )

                # Test connection with a quick ping
                self.client.admin.command('ping', serverSelectionTimeoutMS=2000)

                self.db = self.client[self.db_name]
                logger.info(f"Connected to MongoDB Atlas: {self.db_name}")
                return
            except Exception as e:
                logger.warning(f"Standard MongoDB connection failed: {str(e)}")

            # If standard connection fails, try direct connection
            from utils.direct_connection import get_mongodb_direct_connection
            self.client = get_mongodb_direct_connection(mongodb_uri)

            if self.client:
                self.db = self.client[self.db_name]
                logger.info(f"Connected to MongoDB Atlas using direct connection: {self.db_name}")
            else:
                logger.error("All MongoDB connection attempts failed")
                self.client = None
                self.db = None

        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None

    def _get_collection_name(self, collection: str) -> str:
        """Get the full collection name with prefix"""
        if self.collection_prefix:
            return f"{self.collection_prefix}_{collection}"
        return collection

    async def _check_memory_pressure(self) -> bool:
        """
        Check if system memory is under pressure

        Returns:
            True if memory is constrained, False otherwise
        """
        # Get memory info
        memory = psutil.virtual_memory()
        free_percent = memory.available / memory.total

        # Log memory status periodically
        current_time = time.time()
        if current_time - self.last_prune_time > CACHE_PRUNE_INTERVAL:
            logger.info(f"Memory status: {free_percent:.2%} free, {memory.available / (1024 * 1024):.2f} MB available")

        # Check if memory is constrained
        if free_percent < self.critical_threshold:
            logger.warning(f"Critical memory pressure: {free_percent:.2%} free, {memory.available / (1024 * 1024):.2f} MB available")
            return True
        elif free_percent < self.memory_threshold:
            logger.info(f"Memory pressure detected: {free_percent:.2%} free, {memory.available / (1024 * 1024):.2f} MB available")
            return True

        return False

    async def _prune_cache_if_needed(self) -> None:
        """Prune cache if memory is constrained"""
        # Check if it's time to check memory pressure
        current_time = time.time()
        if current_time - self.last_prune_time < CACHE_PRUNE_INTERVAL:
            return

        # Update last prune time
        self.last_prune_time = current_time

        # Check memory pressure
        if await self._check_memory_pressure():
            # Clear local cache
            cache_size = len(self.cache)
            self.cache.clear()
            logger.info(f"Pruned local cache ({cache_size} items) due to memory pressure")

    def _compress_data(self, data: Any) -> bytes:
        """
        Compress data using Zstandard

        Args:
            data: Data to compress (will be JSON serialized)

        Returns:
            Compressed bytes
        """
        json_data = json.dumps(data).encode('utf-8')
        return self.compressor.compress(json_data)

    def _decompress_data(self, compressed_data: bytes) -> Any:
        """
        Decompress data using Zstandard

        Args:
            compressed_data: Compressed bytes

        Returns:
            Decompressed data (JSON parsed)
        """
        json_data = self.decompressor.decompress(compressed_data)
        return json.loads(json_data.decode('utf-8'))

    async def store(self, collection: str, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                   key: Optional[str] = None, compress: bool = False,
                   ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Store data in MongoDB

        Args:
            collection: Collection name
            data: Data to store (dictionary or list of dictionaries)
            key: Optional key for the data (if None, a new document is created)
            compress: Whether to compress the data
            ttl: Time-to-live in seconds (if None, data doesn't expire)

        Returns:
            Result dictionary with success status
        """
        await self._prune_cache_if_needed()

        if self.db is None:
            logger.warning("MongoDB not available, data not stored")
            return {"success": False, "error": "MongoDB not available"}

        try:
            # Get collection
            coll_name = self._get_collection_name(collection)
            coll = self.db[coll_name]

            # Handle list of dictionaries (special case for recent_interactions)
            if isinstance(data, list):
                # For lists, we'll store a wrapper document
                doc = {
                    "items": data,
                    "timestamp": datetime.utcnow(),
                    "count": len(data)
                }
            else:
                # Prepare document for single dictionary
                doc = data.copy()
                doc["timestamp"] = datetime.utcnow()

            # Add expiration if TTL is provided
            if ttl:
                doc["expires_at"] = datetime.utcnow() + datetime.timedelta(seconds=ttl)

            # Compress data if requested
            if compress and "content" in doc:
                doc["content_compressed"] = self._compress_data(doc["content"])
                doc["is_compressed"] = True
                del doc["content"]

            # Insert or update document
            if key:
                doc["_id"] = key
                result = await coll.replace_one({"_id": key}, doc, upsert=True)
                success = result.acknowledged
            else:
                result = await coll.insert_one(doc)
                success = result.acknowledged
                key = str(result.inserted_id) if success else None

            if success:
                logger.debug(f"Stored data in {coll_name}" + (f" with key {key}" if key else ""))
                return {"success": True, "key": key}
            else:
                logger.error(f"Failed to store data in {coll_name}")
                return {"success": False, "error": "Failed to store data"}

        except Exception as e:
            logger.error(f"Error storing data in {collection}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def retrieve(self, collection: str, key: Optional[str] = None,
                      query: Optional[Dict[str, Any]] = None,
                      limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve data from MongoDB

        Args:
            collection: Collection name
            key: Optional document key
            query: Optional query dictionary
            limit: Maximum number of documents to retrieve

        Returns:
            Result dictionary with data
        """
        await self._prune_cache_if_needed()

        if self.db is None:
            logger.warning("MongoDB not available, data not retrieved")
            return {"success": False, "error": "MongoDB not available"}

        try:
            # Get collection
            coll_name = self._get_collection_name(collection)
            coll = self.db[coll_name]

            # Retrieve data
            if key:
                # Check cache first
                cache_key = f"{coll_name}:{key}"
                if cache_key in self.cache:
                    logger.debug(f"Retrieved {coll_name}/{key} from cache")
                    cached_data = self.cache[cache_key]

                    # Handle special case for recent_interactions
                    if "items" in cached_data and collection == "recent_interactions":
                        return {"success": True, "data": cached_data["items"]}

                    return {"success": True, "data": cached_data}

                # Retrieve from MongoDB
                doc = await coll.find_one({"_id": key})
                if not doc:
                    logger.debug(f"Document {key} not found in {coll_name}")
                    return {"success": False, "error": "Document not found"}

                # Decompress if needed
                if doc.get("is_compressed", False) and "content_compressed" in doc:
                    doc["content"] = self._decompress_data(doc["content_compressed"])
                    del doc["content_compressed"]
                    del doc["is_compressed"]

                # Cache the result
                self.cache[cache_key] = doc

                # Handle special case for recent_interactions
                if "items" in doc and collection == "recent_interactions":
                    logger.debug(f"Retrieved {doc.get('count', 0)} items from {coll_name}/{key}")
                    return {"success": True, "data": doc["items"]}

                logger.debug(f"Retrieved document {key} from {coll_name}")
                return {"success": True, "data": doc}
            elif query:
                # Execute query
                cursor = coll.find(query).limit(limit)
                docs = await cursor.to_list(length=limit)

                # Decompress if needed
                for doc in docs:
                    if doc.get("is_compressed", False) and "content_compressed" in doc:
                        doc["content"] = self._decompress_data(doc["content_compressed"])
                        del doc["content_compressed"]
                        del doc["is_compressed"]

                # Handle special case for recent_interactions
                if collection == "recent_interactions":
                    # Extract items from documents if they exist
                    result_docs = []
                    for doc in docs:
                        if "items" in doc:
                            result_docs.extend(doc["items"])
                        else:
                            result_docs.append(doc)
                    logger.debug(f"Retrieved {len(result_docs)} items from {coll_name} with query")
                    return {"success": True, "data": result_docs}

                logger.debug(f"Retrieved {len(docs)} documents from {coll_name} with query")
                return {"success": True, "data": docs}
            else:
                # Retrieve all documents (up to limit)
                cursor = coll.find().limit(limit)
                docs = await cursor.to_list(length=limit)

                # Decompress if needed
                for doc in docs:
                    if doc.get("is_compressed", False) and "content_compressed" in doc:
                        doc["content"] = self._decompress_data(doc["content_compressed"])
                        del doc["content_compressed"]
                        del doc["is_compressed"]

                # Handle special case for recent_interactions
                if collection == "recent_interactions":
                    # Extract items from documents if they exist
                    result_docs = []
                    for doc in docs:
                        if "items" in doc:
                            result_docs.extend(doc["items"])
                        else:
                            result_docs.append(doc)
                    logger.debug(f"Retrieved {len(result_docs)} items from {coll_name}")
                    return {"success": True, "data": result_docs}

                logger.debug(f"Retrieved {len(docs)} documents from {coll_name}")
                return {"success": True, "data": docs}

        except Exception as e:
            logger.error(f"Error retrieving data from {collection}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def delete(self, collection: str, key: str) -> Dict[str, Any]:
        """
        Delete data from MongoDB

        Args:
            collection: Collection name
            key: Document key

        Returns:
            Result dictionary with success status
        """
        if self.db is None:
            logger.warning("MongoDB not available, data not deleted")
            return {"success": False, "error": "MongoDB not available"}

        try:
            # Get collection
            coll_name = self._get_collection_name(collection)
            coll = self.db[coll_name]

            # Delete from cache
            cache_key = f"{coll_name}:{key}"
            if cache_key in self.cache:
                del self.cache[cache_key]

            # Delete from MongoDB
            result = await coll.delete_one({"_id": key})

            if result.deleted_count > 0:
                logger.debug(f"Deleted document {key} from {coll_name}")
                return {"success": True}
            else:
                logger.debug(f"Document {key} not found in {coll_name}")
                return {"success": False, "error": "Document not found"}

        except Exception as e:
            logger.error(f"Error deleting data from {collection}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_indexes(self, collection: str, indexes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create indexes in MongoDB collection

        Args:
            collection: Collection name
            indexes: List of index specifications

        Returns:
            Result dictionary with success status
        """
        if self.db is None:
            logger.warning("MongoDB not available, indexes not created")
            return {"success": False, "error": "MongoDB not available"}

        try:
            # Get collection
            coll_name = self._get_collection_name(collection)
            coll = self.db[coll_name]

            # Create indexes
            for index_spec in indexes:
                await coll.create_index(**index_spec)

            logger.info(f"Created {len(indexes)} indexes in {coll_name}")
            return {"success": True}

        except Exception as e:
            logger.error(f"Error creating indexes in {collection}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
