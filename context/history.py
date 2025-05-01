"""
Chat History Manager for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides persistent chat history storage in MongoDB with memory summarization
and vector-based semantic search
"""

import os
import json
import asyncio
import structlog
from typing import Dict, List, Any, Optional, Union
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Configure logger
logger = structlog.get_logger("chat_history")

# Load environment variables
load_dotenv()

# Constants
MAX_RECENT_INTERACTIONS = 5  # Number of recent interactions to include in context
MAX_TOKENS_PER_INTERACTION = 100  # Approximate token limit per interaction
MEMORY_SUMMARY_INTERVAL = 7  # Days between summarizing old interactions
MEMORY_SUMMARY_BATCH_SIZE = 10  # Number of interactions to summarize at once
SQLITE_DB_PATH = "data/pulse_memory.db"  # Path to SQLite database for fallback storage

class ChatHistoryManager:
    """
    Manages persistent chat history and memories
    Features:
    - MongoDB Atlas integration for persistent storage
    - SQLite fallback for local storage
    - Vector database for semantic search
    - Automatic summarization of old interactions
    - Context-aware memory retrieval
    - Efficient token usage for model context
    """

    def __init__(self, user_id: str = "default"):
        """
        Initialize the chat history manager

        Args:
            user_id: User identifier
        """
        self.logger = logger
        self.user_id = user_id
        self.client = None
        self.db = None
        self.vector_db = None
        self.sqlite_initialized = False

        # Initialize MongoDB connection
        self._init_mongodb()

        # Initialize SQLite database
        self._init_sqlite()

        # Initialize vector database
        self._init_vector_db()

        logger.info(f"Chat history manager initialized for user {user_id}")

    def _init_sqlite(self) -> None:
        """Initialize SQLite database for fallback storage"""
        try:
            # Import here to avoid circular imports
            from utils.sqlite_utils import initialize_chat_history_db

            # Initialize SQLite database
            self.sqlite_initialized = initialize_chat_history_db(SQLITE_DB_PATH)

            if self.sqlite_initialized:
                logger.info(f"Initialized SQLite database for fallback storage: {SQLITE_DB_PATH}")
            else:
                logger.warning(f"Failed to initialize SQLite database: {SQLITE_DB_PATH}")
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {str(e)}")
            self.sqlite_initialized = False

    def _init_vector_db(self) -> None:
        """Initialize vector database for semantic search"""
        try:
            # Import here to avoid circular imports
            from utils.vector_db import VectorDatabase

            # Initialize vector database
            self.vector_db = VectorDatabase(
                db_path="data/vector_db",
                fallback_to_sqlite=True
            )

            logger.info("Initialized vector database for semantic search")
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            self.vector_db = None

    def _init_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        # Disable MongoDB connection to avoid DNS issues
        logger.info("MongoDB connection disabled for chat history, using SQLite fallback")
        self.client = None
        self.db = None

    async def _create_indexes(self) -> None:
        """Create indexes for chat history collections"""
        if self.db is None:
            return

        try:
            # Create indexes for history collection
            await self.db.history.create_index([("user_id", 1), ("timestamp", -1)])
            await self.db.history.create_index([("user_id", 1), ("interaction_id", 1)], unique=True)

            # Create indexes for memories collection
            await self.db.memories.create_index([("user_id", 1), ("category", 1)])
            await self.db.memories.create_index([("user_id", 1), ("timestamp", -1)])

            logger.info("Created indexes for chat history collections")
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")

    async def add_interaction(self, user_input: str, assistant_response: str,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new interaction to the chat history

        Args:
            user_input: User's input text
            assistant_response: Assistant's response text
            metadata: Optional metadata about the interaction

        Returns:
            Result dictionary with success status
        """
        # Prepare timestamp
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        interaction_id = None
        mongodb_success = False
        sqlite_success = False
        vector_success = False

        # Try to store in MongoDB
        if self.db is not None:
            try:
                # Get the next interaction ID
                last_interaction = await self.db.history.find_one(
                    {"user_id": self.user_id},
                    sort=[("interaction_id", -1)]
                )

                interaction_id = 1
                if last_interaction:
                    interaction_id = last_interaction.get("interaction_id", 0) + 1

                # Prepare document
                doc = {
                    "user_id": self.user_id,
                    "interaction_id": interaction_id,
                    "timestamp": timestamp,
                    "user_input": user_input,
                    "assistant_response": assistant_response,
                    "metadata": metadata or {},
                    "summarized": False
                }

                # Insert document
                result = await self.db.history.insert_one(doc)
                mongodb_success = result.acknowledged

                if mongodb_success:
                    logger.debug(f"Added interaction {interaction_id} to MongoDB history")

                    # Schedule summarization of old interactions
                    asyncio.create_task(self._summarize_old_interactions())
                else:
                    logger.error("Failed to add interaction to MongoDB history")
            except Exception as e:
                logger.error(f"Error adding interaction to MongoDB history: {str(e)}")
        else:
            logger.warning("MongoDB not available, falling back to SQLite")

        # Try to store in SQLite if MongoDB failed or is not available
        if not mongodb_success and self.sqlite_initialized:
            try:
                # Import here to avoid circular imports
                from utils.sqlite_utils import execute_query

                # If we don't have an interaction ID yet, get one from SQLite
                if interaction_id is None:
                    # Get the next interaction ID from SQLite
                    result = execute_query(
                        db_path=SQLITE_DB_PATH,
                        query="SELECT MAX(id) as max_id FROM chat_history WHERE user_id = ?",
                        params=(self.user_id,)
                    )

                    if result["success"] and result["data"]:
                        max_id = result["data"][0].get("max_id") or 0
                        interaction_id = max_id + 1
                    else:
                        interaction_id = 1

                # Convert metadata to JSON string
                metadata_json = json.dumps(metadata) if metadata else "{}"

                # Insert into SQLite
                result = execute_query(
                    db_path=SQLITE_DB_PATH,
                    query="""
                    INSERT INTO chat_history
                    (id, user_id, timestamp, user_input, assistant_response, model, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    params=(
                        interaction_id,
                        self.user_id,
                        timestamp.isoformat(),
                        user_input,
                        assistant_response,
                        metadata.get("model", "unknown") if metadata else "unknown",
                        metadata_json
                    )
                )

                sqlite_success = result["success"]

                if sqlite_success:
                    logger.debug(f"Added interaction {interaction_id} to SQLite history")
                else:
                    logger.error(f"Failed to add interaction to SQLite history: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error adding interaction to SQLite history: {str(e)}")

        # Store in vector database for semantic search
        if self.vector_db is not None:
            try:
                # Combine user input and assistant response for vector storage
                combined_text = f"User: {user_input}\nAssistant: {assistant_response}"

                # Store in vector database
                vector_result = await self.vector_db.store_vector(
                    text=combined_text,
                    user_id=self.user_id,
                    chat_id=interaction_id,
                    metadata=metadata
                )

                vector_success = vector_result["success"]

                if vector_success:
                    logger.debug(f"Added interaction {interaction_id} to vector database")
                else:
                    logger.error(f"Failed to add interaction to vector database: {vector_result.get('error')}")
            except Exception as e:
                logger.error(f"Error adding interaction to vector database: {str(e)}")

        # Return success if any storage method succeeded
        if mongodb_success or sqlite_success:
            return {"success": True, "interaction_id": interaction_id}
        else:
            return {"success": False, "error": "Failed to add interaction to any storage"}

    async def get_recent_interactions(self, count: int = MAX_RECENT_INTERACTIONS) -> Dict[str, Any]:
        """
        Get recent interactions from chat history

        Args:
            count: Number of recent interactions to retrieve

        Returns:
            Result dictionary with interactions
        """
        if self.db is None:
            logger.warning("MongoDB not available, interactions not retrieved")
            return {"success": False, "error": "MongoDB not available"}

        try:
            # Retrieve recent interactions
            cursor = self.db.history.find(
                {"user_id": self.user_id},
                sort=[("interaction_id", -1)],
                limit=count
            )

            interactions = await cursor.to_list(length=count)
            interactions.reverse()  # Chronological order

            logger.debug(f"Retrieved {len(interactions)} recent interactions")
            return {"success": True, "interactions": interactions}

        except Exception as e:
            logger.error(f"Error retrieving recent interactions: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_context_for_model(self, max_tokens: int = 500) -> Dict[str, Any]:
        """
        Get context for model prompt, including recent interactions and relevant memories

        Args:
            max_tokens: Maximum tokens to include in context

        Returns:
            Result dictionary with context data
        """
        if self.db is None:
            logger.warning("MongoDB not available, context not retrieved")
            return {"success": False, "error": "MongoDB not available"}

        try:
            # Allocate tokens for recent interactions and memories
            interaction_tokens = int(max_tokens * 0.8)  # 80% for recent interactions
            memory_tokens = max_tokens - interaction_tokens  # 20% for memories

            # Get recent interactions
            interactions_result = await self.get_recent_interactions(
                count=MAX_RECENT_INTERACTIONS
            )

            if not interactions_result["success"]:
                return interactions_result

            interactions = interactions_result["interactions"]

            # Format interactions for context
            context_interactions = []
            token_count = 0

            for interaction in interactions:
                # Estimate tokens (rough approximation)
                interaction_tokens = (
                    len(interaction["user_input"]) +
                    len(interaction["assistant_response"])
                ) // 4  # Rough estimate: 4 chars per token

                if token_count + interaction_tokens > interaction_tokens:
                    break

                context_interactions.append({
                    "user": interaction["user_input"],
                    "assistant": interaction["assistant_response"],
                    "timestamp": interaction["timestamp"]
                })

                token_count += interaction_tokens

            # Get relevant memories
            memories_result = await self.get_relevant_memories(
                max_tokens=memory_tokens
            )

            memories = []
            if memories_result["success"]:
                memories = memories_result["memories"]

            logger.debug(f"Prepared context with {len(context_interactions)} interactions and {len(memories)} memories")
            return {
                "success": True,
                "context": {
                    "recent_interactions": context_interactions,
                    "memories": memories,
                    "user_id": self.user_id
                }
            }

        except Exception as e:
            logger.error(f"Error preparing context for model: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _summarize_old_interactions(self) -> None:
        """Summarize old interactions into memories"""
        if self.db is None:
            return

        try:
            # Find old interactions that haven't been summarized
            cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=MEMORY_SUMMARY_INTERVAL)

            cursor = self.db.history.find({
                "user_id": self.user_id,
                "timestamp": {"$lt": cutoff_date},
                "summarized": False
            }).limit(MEMORY_SUMMARY_BATCH_SIZE)

            old_interactions = await cursor.to_list(length=MEMORY_SUMMARY_BATCH_SIZE)

            if not old_interactions:
                return

            logger.info(f"Summarizing {len(old_interactions)} old interactions")

            # Group interactions by day for summarization
            interactions_by_day = {}

            for interaction in old_interactions:
                day = interaction["timestamp"].strftime("%Y-%m-%d")
                if day not in interactions_by_day:
                    interactions_by_day[day] = []

                interactions_by_day[day].append(interaction)

            # Summarize each day's interactions
            for day, day_interactions in interactions_by_day.items():
                await self._create_summary_for_interactions(day, day_interactions)

                # Mark interactions as summarized
                interaction_ids = [interaction["_id"] for interaction in day_interactions]
                await self.db.history.update_many(
                    {"_id": {"$in": interaction_ids}},
                    {"$set": {"summarized": True}}
                )

            logger.info(f"Summarized interactions for {len(interactions_by_day)} days")

        except Exception as e:
            logger.error(f"Error summarizing old interactions: {str(e)}")

    async def _create_summary_for_interactions(self, day: str, interactions: List[Dict[str, Any]]) -> None:
        """
        Create a summary for a day's interactions

        Args:
            day: Day string (YYYY-MM-DD)
            interactions: List of interactions for the day
        """
        try:
            # Prepare text for summarization
            conversation_text = ""

            for interaction in interactions:
                conversation_text += f"User: {interaction['user_input']}\n"
                conversation_text += f"Assistant: {interaction['assistant_response']}\n\n"

            # Use MiniLM to generate a summary
            summary = await self._generate_summary_with_minilm(conversation_text)

            # Save the summary as a memory
            memory = {
                "user_id": self.user_id,
                "category": "conversation_summary",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "day": day,
                "summary": summary,
                "interaction_count": len(interactions)
            }

            await self.db.memories.insert_one(memory)

            logger.info(f"Created summary for {day} with {len(interactions)} interactions")

        except Exception as e:
            logger.error(f"Error creating summary for {day}: {str(e)}")

    async def _generate_summary_with_minilm(self, text: str) -> str:
        """
        Generate a summary using MiniLM

        Args:
            text: Text to summarize

        Returns:
            Summary text
        """
        try:
            # Import here to avoid circular imports
            from sentence_transformers import SentenceTransformer

            # Load model (or use a singleton)
            model = SentenceTransformer('all-MiniLM-L6-v2')

            # Split text into chunks if it's too long
            max_chunk_length = 512
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]

            # Generate embeddings for each chunk
            embeddings = model.encode(chunks)

            # Average the embeddings
            import numpy as np
            avg_embedding = np.mean(embeddings, axis=0)

            # Generate a summary based on the most important sentences
            sentences = text.split('\n')
            sentence_embeddings = model.encode(sentences)

            # Calculate similarity to the average embedding
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity([avg_embedding], sentence_embeddings)[0]

            # Get the top 3 sentences
            top_indices = similarities.argsort()[-3:][::-1]
            top_sentences = [sentences[i] for i in top_indices]

            # Create a summary
            summary = "On this day: " + " ".join(top_sentences)

            # Truncate if too long
            if len(summary) > 200:
                summary = summary[:197] + "..."

            return summary

        except Exception as e:
            logger.error(f"Error generating summary with MiniLM: {str(e)}")
            return f"Conversation on {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}"

    async def get_relevant_memories(self, query: Optional[str] = None,
                                  max_tokens: int = 100) -> Dict[str, Any]:
        """
        Get relevant memories for context

        Args:
            query: Optional query to find relevant memories
            max_tokens: Maximum tokens for memories

        Returns:
            Result dictionary with memories
        """
        # If no query, just get recent memories from MongoDB or SQLite
        if not query:
            return await self._get_recent_memories(limit=5)

        # If we have a vector database, use it for semantic search
        if self.vector_db is not None:
            try:
                # Query vector database for similar texts
                vector_result = await self.vector_db.query_similar(
                    text=query,
                    user_id=self.user_id,
                    limit=5
                )

                if vector_result["success"] and vector_result.get("data"):
                    # Convert vector results to memory format
                    memories = []
                    for item in vector_result["data"]:
                        memories.append({
                            "user_id": self.user_id,
                            "category": "vector_search",
                            "content": item["text"],
                            "timestamp": datetime.datetime.fromisoformat(item["timestamp"]) if "timestamp" in item else datetime.datetime.now(datetime.timezone.utc),
                            "score": item.get("score", 0),
                            "chat_id": item.get("chat_id")
                        })

                    logger.debug(f"Retrieved {len(memories)} memories from vector search for query: {query}")
                    return {"success": True, "memories": memories}
            except Exception as e:
                logger.error(f"Error retrieving memories from vector database: {str(e)}")
                # Fall through to traditional retrieval

        # Fall back to MongoDB if available
        if self.db is not None:
            try:
                cursor = self.db.memories.find(
                    {"user_id": self.user_id},
                    sort=[("timestamp", -1)],
                    limit=5
                )

                memories = await cursor.to_list(length=5)

                logger.debug(f"Retrieved {len(memories)} memories from MongoDB for query: {query}")
                return {"success": True, "memories": memories}
            except Exception as e:
                logger.error(f"Error retrieving memories from MongoDB: {str(e)}")
                # Fall through to SQLite

        # Fall back to SQLite if MongoDB failed or is not available
        if self.sqlite_initialized:
            try:
                # Import here to avoid circular imports
                from utils.sqlite_utils import execute_query

                # Query SQLite for recent memories
                result = execute_query(
                    db_path=SQLITE_DB_PATH,
                    query="""
                    SELECT id, user_id, category, content, timestamp, metadata
                    FROM chat_memories
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                    """,
                    params=(self.user_id,)
                )

                if result["success"] and result["data"]:
                    # Convert SQLite results to memory format
                    memories = []
                    for row in result["data"]:
                        # Parse metadata JSON
                        try:
                            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                        except:
                            metadata = {}

                        memories.append({
                            "user_id": row["user_id"],
                            "category": row["category"],
                            "content": row["content"],
                            "timestamp": datetime.datetime.fromisoformat(row["timestamp"]),
                            "metadata": metadata
                        })

                    logger.debug(f"Retrieved {len(memories)} memories from SQLite for query: {query}")
                    return {"success": True, "memories": memories}
                else:
                    logger.warning(f"No memories found in SQLite for query: {query}")
                    return {"success": True, "memories": []}
            except Exception as e:
                logger.error(f"Error retrieving memories from SQLite: {str(e)}")

        # If all methods failed, return empty result
        logger.warning("All memory retrieval methods failed, returning empty result")
        return {"success": True, "memories": []}

    async def _get_recent_memories(self, limit: int = 5) -> Dict[str, Any]:
        """
        Get recent memories from storage

        Args:
            limit: Maximum number of memories to retrieve

        Returns:
            Result dictionary with memories
        """
        # Try MongoDB first
        if self.db is not None:
            try:
                cursor = self.db.memories.find(
                    {"user_id": self.user_id},
                    sort=[("timestamp", -1)],
                    limit=limit
                )

                memories = await cursor.to_list(length=limit)

                logger.debug(f"Retrieved {len(memories)} recent memories from MongoDB")
                return {"success": True, "memories": memories}
            except Exception as e:
                logger.error(f"Error retrieving recent memories from MongoDB: {str(e)}")
                # Fall through to SQLite

        # Fall back to SQLite
        if self.sqlite_initialized:
            try:
                # Import here to avoid circular imports
                from utils.sqlite_utils import execute_query

                # Query SQLite for recent memories
                result = execute_query(
                    db_path=SQLITE_DB_PATH,
                    query="""
                    SELECT id, user_id, category, content, timestamp, metadata
                    FROM chat_memories
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    params=(self.user_id, limit)
                )

                if result["success"] and result["data"]:
                    # Convert SQLite results to memory format
                    memories = []
                    for row in result["data"]:
                        # Parse metadata JSON
                        try:
                            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                        except:
                            metadata = {}

                        memories.append({
                            "user_id": row["user_id"],
                            "category": row["category"],
                            "content": row["content"],
                            "timestamp": datetime.datetime.fromisoformat(row["timestamp"]),
                            "metadata": metadata
                        })

                    logger.debug(f"Retrieved {len(memories)} recent memories from SQLite")
                    return {"success": True, "memories": memories}
                else:
                    logger.warning("No recent memories found in SQLite")
                    return {"success": True, "memories": []}
            except Exception as e:
                logger.error(f"Error retrieving recent memories from SQLite: {str(e)}")

        # If all methods failed, return empty result
        return {"success": True, "memories": []}

    async def add_memory(self, category: str, content: str,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a new memory

        Args:
            category: Memory category
            content: Memory content
            metadata: Optional metadata

        Returns:
            Result dictionary with success status
        """
        # Prepare timestamp
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        memory_id = None
        mongodb_success = False
        sqlite_success = False
        vector_success = False

        # Try to store in MongoDB
        if self.db is not None:
            try:
                # Prepare document
                doc = {
                    "user_id": self.user_id,
                    "category": category,
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": metadata or {}
                }

                # Insert document
                result = await self.db.memories.insert_one(doc)
                mongodb_success = result.acknowledged

                if mongodb_success:
                    memory_id = str(result.inserted_id)
                    logger.debug(f"Added memory in category {category} to MongoDB")
                else:
                    logger.error("Failed to add memory to MongoDB")
            except Exception as e:
                logger.error(f"Error adding memory to MongoDB: {str(e)}")
        else:
            logger.warning("MongoDB not available, falling back to SQLite")

        # Try to store in SQLite if MongoDB failed or is not available
        if not mongodb_success and self.sqlite_initialized:
            try:
                # Import here to avoid circular imports
                from utils.sqlite_utils import execute_query

                # If we don't have a memory ID yet, generate one
                if memory_id is None:
                    # Get the next memory ID from SQLite
                    result = execute_query(
                        db_path=SQLITE_DB_PATH,
                        query="SELECT MAX(id) as max_id FROM chat_memories WHERE user_id = ?",
                        params=(self.user_id,)
                    )

                    if result["success"] and result["data"]:
                        max_id = result["data"][0].get("max_id") or 0
                        memory_id = str(max_id + 1)
                    else:
                        memory_id = "1"

                # Convert metadata to JSON string
                metadata_json = json.dumps(metadata) if metadata else "{}"

                # Insert into SQLite
                result = execute_query(
                    db_path=SQLITE_DB_PATH,
                    query="""
                    INSERT INTO chat_memories
                    (id, user_id, category, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    params=(
                        memory_id,
                        self.user_id,
                        category,
                        content,
                        timestamp.isoformat(),
                        metadata_json
                    )
                )

                sqlite_success = result["success"]

                if sqlite_success:
                    logger.debug(f"Added memory in category {category} to SQLite")
                else:
                    logger.error(f"Failed to add memory to SQLite: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error adding memory to SQLite: {str(e)}")

        # Store in vector database for semantic search
        if self.vector_db is not None:
            try:
                # Store in vector database
                vector_result = await self.vector_db.store_vector(
                    text=content,
                    user_id=self.user_id,
                    metadata={"category": category, "memory_id": memory_id}
                )

                vector_success = vector_result["success"]

                if vector_success:
                    logger.debug(f"Added memory in category {category} to vector database")
                else:
                    logger.error(f"Failed to add memory to vector database: {vector_result.get('error')}")
            except Exception as e:
                logger.error(f"Error adding memory to vector database: {str(e)}")

        # Return success if any storage method succeeded
        if mongodb_success or sqlite_success:
            return {"success": True, "memory_id": memory_id}
        else:
            return {"success": False, "error": "Failed to add memory to any storage"}

    async def get_historical_context(self, query: str, max_tokens: int = 500) -> str:
        """
        Get historical context for a query

        Args:
            query: Query text
            max_tokens: Maximum tokens for context

        Returns:
            String with historical context
        """
        # Use vector database if available
        if self.vector_db is not None:
            try:
                context = await self.vector_db.get_historical_context(
                    query=query,
                    user_id=self.user_id,
                    limit=3
                )

                if context:
                    return context
            except Exception as e:
                logger.error(f"Error getting historical context from vector database: {str(e)}")

        # Fall back to relevant memories
        try:
            memories_result = await self.get_relevant_memories(query=query, max_tokens=max_tokens)

            if memories_result["success"] and memories_result.get("memories"):
                memories = memories_result["memories"]

                # Format memories as context
                context_items = []
                for memory in memories:
                    if "content" in memory:
                        context_items.append(memory["content"])
                    elif "summary" in memory:
                        context_items.append(memory["summary"])

                if context_items:
                    return "\n\nRelated past interactions:\n" + "\n".join(context_items)
        except Exception as e:
            logger.error(f"Error getting historical context from memories: {str(e)}")

        # If all methods failed, return empty string
        return ""

    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

        # Close vector database if available
        if self.vector_db is not None:
            try:
                await self.vector_db.close()
            except:
                pass
