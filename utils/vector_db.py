"""
Vector database utilities for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides semantic search capabilities for chat history
"""

import os
import sqlite3
import structlog
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timezone
import importlib.metadata

# Configure logger
logger = structlog.get_logger("vector_db")

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, vector search will be disabled")

# Try to import lancedb and check version
try:
    import lancedb
    import pyarrow as pa

    # Get LanceDB version
    try:
        LANCEDB_VERSION = importlib.metadata.version('lancedb')
        LANCEDB_VERSION_TUPLE = tuple(map(int, LANCEDB_VERSION.split('.')))
        LANCEDB_MODERN = LANCEDB_VERSION_TUPLE >= (0, 4, 0)
        logger.info(f"LanceDB version: {LANCEDB_VERSION} ({'modern' if LANCEDB_MODERN else 'legacy'} API)")
    except Exception as e:
        logger.warning(f"Failed to determine LanceDB version: {str(e)}")
        LANCEDB_VERSION = "0.3.0"  # Assume legacy version
        LANCEDB_VERSION_TUPLE = (0, 3, 0)
        LANCEDB_MODERN = False

    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    LANCEDB_VERSION = None
    LANCEDB_VERSION_TUPLE = (0, 0, 0)
    LANCEDB_MODERN = False
    logger.warning("lancedb not available, vector search will be disabled")

# Constants
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

class VectorDatabase:
    """
    Vector database for semantic search of chat history
    Features:
    - Sentence embeddings using sentence-transformers
    - Vector storage in SQLite or LanceDB
    - Semantic search for similar conversations
    """

    def __init__(self, db_path: str = "data/vector_db",
                 model_name: str = DEFAULT_MODEL,
                 fallback_to_sqlite: bool = True,
                 _force_sqlite_fallback: bool = False):
        """
        Initialize the vector database

        Args:
            db_path: Path to the vector database
            model_name: Name of the sentence-transformer model to use
            fallback_to_sqlite: Whether to fallback to SQLite if LanceDB is not available
            _force_sqlite_fallback: Force SQLite fallback (for testing purposes only)
        """
        self.logger = logger
        self.db_path = db_path
        self.model_name = model_name
        self.fallback_to_sqlite = fallback_to_sqlite
        self._force_sqlite_fallback = _force_sqlite_fallback
        self.encoder = None
        self.lancedb = None
        self.table = None
        self.sqlite_path = "data/pulse_memory.db"

        # Initialize the database
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the vector database"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        # Initialize sentence transformer if available
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(self.model_name)
                logger.info(f"Initialized sentence transformer: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize sentence transformer: {str(e)}")
                self.encoder = None

        # Initialize LanceDB if available and not forced to use SQLite
        if LANCEDB_AVAILABLE and not self._force_sqlite_fallback:
            try:
                # Connect to LanceDB
                self.lancedb = lancedb.connect(self.db_path)

                # Initialize table based on LanceDB version
                if LANCEDB_MODERN:
                    # Modern LanceDB (0.4.0+) uses a different API
                    self._initialize_modern_lancedb()
                else:
                    # Legacy LanceDB (0.3.x) uses PyArrow schema
                    self._initialize_legacy_lancedb()

                logger.info(f"Initialized LanceDB: {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize LanceDB: {str(e)}")
                self.lancedb = None
                self.table = None

    def _initialize_legacy_lancedb(self) -> None:
        """Initialize LanceDB using legacy API (0.3.x)"""
        try:
            # Create table if it doesn't exist
            if "chat_vectors" not in self.lancedb.table_names():
                # Create PyArrow schema for LanceDB
                schema = pa.schema([
                    pa.field("vector", pa.list_(pa.float32(), VECTOR_DIMENSION)),
                    pa.field("user_id", pa.string()),
                    pa.field("chat_id", pa.int64()),
                    pa.field("text", pa.string()),
                    pa.field("timestamp", pa.timestamp('us'))
                ])
                # Create empty table with schema
                self.table = self.lancedb.create_table("chat_vectors", schema=schema)
            else:
                self.table = self.lancedb.open_table("chat_vectors")

            logger.info("Initialized LanceDB using legacy API (0.3.x)")
        except Exception as e:
            logger.error(f"Failed to initialize legacy LanceDB: {str(e)}")
            raise

    def _initialize_modern_lancedb(self) -> None:
        """Initialize LanceDB using modern API (0.4.0+)"""
        try:
            # Import pandas for modern LanceDB
            import pandas as pd

            # Check if table exists
            if "chat_vectors" not in self.lancedb.table_names():
                # Create empty DataFrame with required columns
                df = pd.DataFrame({
                    "vector": [],
                    "user_id": [],
                    "chat_id": [],
                    "text": [],
                    "timestamp": []
                })

                # Create table with vector column
                self.table = self.lancedb.create_table(
                    "chat_vectors",
                    data=df,
                    mode="overwrite"
                )

                # Create vector index
                self.table.create_index(
                    vector_column_name="vector",
                    index_type="IVF_PQ",
                    num_partitions=256,
                    num_sub_vectors=16
                )
            else:
                self.table = self.lancedb.open_table("chat_vectors")

            logger.info("Initialized LanceDB using modern API (0.4.0+)")
        except Exception as e:
            logger.error(f"Failed to initialize modern LanceDB: {str(e)}")
            raise

        # Fallback to SQLite if LanceDB is not available or forced to use SQLite
        if self.fallback_to_sqlite and (not LANCEDB_AVAILABLE or self.lancedb is None or self._force_sqlite_fallback):
            try:
                from utils.sqlite_utils import optimize_sqlite_db, create_table

                # Optimize SQLite database
                optimize_sqlite_db(self.sqlite_path)

                # Create chat_vectors table if it doesn't exist
                create_table(
                    db_path=self.sqlite_path,
                    table_name="chat_vectors",
                    columns={
                        "id": "INTEGER",
                        "user_id": "TEXT",
                        "chat_id": "INTEGER",
                        "text": "TEXT",
                        "vector_blob": "BLOB",  # Binary vector data
                        "timestamp": "TIMESTAMP"
                    },
                    primary_key="id",
                    indexes=["user_id", "chat_id"]
                )

                logger.info(f"Initialized SQLite fallback for vector storage: {self.sqlite_path}")
            except Exception as e:
                logger.error(f"Failed to initialize SQLite fallback: {str(e)}")

    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Encode text into a vector embedding

        Args:
            text: Text to encode

        Returns:
            Vector embedding or None if encoding failed
        """
        if self.encoder is None:
            logger.warning("Sentence transformer not available, cannot encode text")
            return None

        try:
            return self.encoder.encode(text)
        except Exception as e:
            logger.error(f"Failed to encode text: {str(e)}")
            return None

    async def store_vector(self, text: str, user_id: str = "uminda",
                          chat_id: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store a vector embedding for text

        Args:
            text: Text to encode and store
            user_id: User ID
            chat_id: Optional chat ID
            metadata: Optional metadata

        Returns:
            Result dictionary with success status
        """
        # Encode text
        embedding = self.encode_text(text)
        if embedding is None:
            return {"success": False, "error": "Failed to encode text"}

        # Get current timestamp
        timestamp = datetime.now(timezone.utc)

        # Store in LanceDB if available and not forced to use SQLite
        if self.table is not None and not self._force_sqlite_fallback:
            try:
                # Prepare data
                data = {
                    "vector": embedding.tolist(),
                    "user_id": user_id,
                    "text": text,
                    "timestamp": timestamp
                }

                # Add chat_id if provided
                if chat_id is not None:
                    data["chat_id"] = chat_id

                # Add metadata if provided
                if metadata is not None and isinstance(metadata, dict):
                    # Flatten metadata to avoid nested structures
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            data[f"meta_{key}"] = value

                # Add to table based on LanceDB version
                if LANCEDB_MODERN:
                    # Modern LanceDB uses pandas DataFrame
                    import pandas as pd
                    df = pd.DataFrame([data])
                    self.table.add(df)
                else:
                    # Legacy LanceDB uses list of dicts
                    self.table.add([data])

                logger.debug(f"Stored vector in LanceDB for user {user_id}")
                return {"success": True}
            except Exception as e:
                logger.error(f"Failed to store vector in LanceDB: {str(e)}")
                # Fall through to SQLite fallback

        # Fallback to SQLite
        if self.fallback_to_sqlite:
            try:
                # Connect to SQLite database
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()

                # Convert embedding to binary
                vector_blob = embedding.tobytes()

                # Insert into database
                cursor.execute(
                    "INSERT INTO chat_vectors (user_id, chat_id, text, vector_blob, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (user_id, chat_id, text, vector_blob, timestamp)
                )

                # Commit changes
                conn.commit()

                # Get inserted ID
                inserted_id = cursor.lastrowid

                # Close connection
                conn.close()

                logger.debug(f"Stored vector in SQLite for user {user_id}")
                return {"success": True, "id": inserted_id}
            except Exception as e:
                logger.error(f"Failed to store vector in SQLite: {str(e)}")
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "No vector storage available"}

    async def query_similar(self, text: str, user_id: str = "uminda",
                           limit: int = 3) -> Dict[str, Any]:
        """
        Query for similar texts

        Args:
            text: Query text
            user_id: User ID to filter by
            limit: Maximum number of results

        Returns:
            Result dictionary with similar texts
        """
        # Encode query text
        query_embedding = self.encode_text(text)
        if query_embedding is None:
            return {"success": False, "error": "Failed to encode query text"}

        # Query LanceDB if available and not forced to use SQLite
        if self.table is not None and not self._force_sqlite_fallback:
            try:
                # Execute query based on LanceDB version
                if LANCEDB_MODERN:
                    # Modern LanceDB API (0.4.0+)
                    results = (
                        self.table.search(query_embedding.tolist(), vector_column_name="vector")
                        .where(f"user_id = '{user_id}'")
                        .limit(limit)
                        .to_pandas()
                    )

                    # Get distance column name (changed in newer versions)
                    distance_col = "_distance"
                    if "_distance" not in results.columns and "score" in results.columns:
                        distance_col = "score"
                else:
                    # Legacy LanceDB API (0.3.x)
                    # Note: field_by_name is deprecated but still required for 0.3.0
                    results = (
                        self.table.search(query_embedding.tolist())
                        .where(f"user_id = '{user_id}'")
                        .limit(limit)
                        .to_arrow()
                        .to_pandas()
                    )
                    distance_col = "_distance"

                # Convert to list of dictionaries
                items = []
                for _, row in results.iterrows():
                    item_data = {
                        "text": row["text"],
                        "score": float(row[distance_col]),
                        "timestamp": row["timestamp"].isoformat() if "timestamp" in row else None
                    }

                    # Add chat_id if available
                    if "chat_id" in row:
                        item_data["chat_id"] = int(row["chat_id"])

                    # Add any metadata fields
                    for col in row.index:
                        if col.startswith("meta_") and col not in item_data:
                            item_data[col] = row[col]

                    items.append(item_data)

                logger.debug(f"Found {len(items)} similar items in LanceDB for user {user_id}")
                return {"success": True, "data": items}
            except Exception as e:
                logger.error(f"Failed to query LanceDB: {str(e)}")
                # Fall through to SQLite fallback

        # Fallback to SQLite
        if self.fallback_to_sqlite:
            try:
                # Connect to SQLite database
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()

                # Get all vectors for the user
                cursor.execute(
                    "SELECT id, chat_id, text, vector_blob, timestamp FROM chat_vectors WHERE user_id = ?",
                    (user_id,)
                )

                # Calculate cosine similarity for each vector
                results = []
                for row in cursor.fetchall():
                    # Extract data
                    id, chat_id, db_text, vector_blob, timestamp = row

                    # Convert binary to numpy array
                    db_vector = np.frombuffer(vector_blob, dtype=np.float32)

                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, db_vector) / (np.linalg.norm(query_embedding) * np.linalg.norm(db_vector))

                    # Add to results
                    results.append({
                        "id": id,
                        "chat_id": chat_id,
                        "text": db_text,
                        "score": float(similarity),
                        "timestamp": timestamp
                    })

                # Sort by similarity (descending)
                results.sort(key=lambda x: x["score"], reverse=True)

                # Limit results
                results = results[:limit]

                # Close connection
                conn.close()

                logger.debug(f"Found {len(results)} similar items in SQLite for user {user_id}")
                return {"success": True, "data": results}
            except Exception as e:
                logger.error(f"Failed to query SQLite: {str(e)}")
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "No vector storage available"}

    async def get_historical_context(self, query: str, user_id: str = "uminda",
                                    limit: int = 5) -> str:
        """
        Get historical context for a query

        Args:
            query: Query text
            user_id: User ID
            limit: Maximum number of results (default: 5)

        Returns:
            String with historical context
        """
        # Query for similar texts
        result = await self.query_similar(query, user_id, limit)

        if not result["success"] or not result.get("data"):
            return ""

        # Format results with more context
        context_items = []
        for i, item in enumerate(result["data"]):
            # Add timestamp if available
            timestamp_str = ""
            if "timestamp" in item and item["timestamp"]:
                try:
                    # Try to parse the timestamp
                    from datetime import datetime
                    if isinstance(item["timestamp"], str):
                        dt = datetime.fromisoformat(item["timestamp"].replace('Z', '+00:00'))
                        timestamp_str = f" (from {dt.strftime('%Y-%m-%d %H:%M')})"
                except Exception:
                    # If parsing fails, just use the raw timestamp
                    timestamp_str = f" (from {item['timestamp']})"

            # Add relevance score
            score_str = ""
            if "score" in item:
                # Format score as percentage
                score_percent = int(item["score"] * 100)
                score_str = f" [Relevance: {score_percent}%]"

            # Add the item with context
            context_items.append(f"Past interaction {i+1}{timestamp_str}{score_str}:\n{item['text']}")

        # Join with newlines and add a header
        if context_items:
            return "\n\n## Related Past Interactions\n\n" + "\n\n".join(context_items)
        return ""

    async def close(self) -> None:
        """Close the vector database"""
        # Close LanceDB if available
        if self.lancedb is not None:
            try:
                self.lancedb.close()
                logger.info("Closed LanceDB connection")
            except:
                pass
