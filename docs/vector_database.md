# Vector Database in P.U.L.S.E.

This document describes the vector database implementation in P.U.L.S.E. for semantic search capabilities.

## Overview

P.U.L.S.E. includes a robust vector database system that enables semantic search of chat history and memories. The system uses:

1. **Sentence Transformers** - For encoding text into vector embeddings
2. **LanceDB** - Primary storage for vector embeddings (supports both legacy 0.3.0 and modern 0.4.0+ versions)
3. **SQLite** - Fallback storage when LanceDB is unavailable

The vector database is used for finding semantically similar past conversations, enabling the system to provide relevant context for new queries.

> **Note:** The vector database implementation has been updated to support both legacy LanceDB 0.3.0 and modern LanceDB versions (0.4.0+). See the [LanceDB Upgrade Guide](lancedb_upgrade.md) for details on upgrading.

## Components

### VectorDatabase Class

The `VectorDatabase` class in `utils/vector_db.py` is the main interface for vector operations. It provides methods to:

- Encode text into vector embeddings
- Store vector embeddings in LanceDB or SQLite
- Search for similar vectors using semantic similarity
- Retrieve historical context for queries

### Sentence Transformers

The system uses the `sentence-transformers/all-MiniLM-L6-v2` model to encode text into 384-dimensional vector embeddings. This model provides a good balance between performance and accuracy for semantic search.

### LanceDB

LanceDB is used as the primary vector database. It provides:

- Efficient storage of vector embeddings
- Fast nearest-neighbor search
- Support for filtering by user ID and other metadata

The system supports two LanceDB API versions:

1. **Legacy API (0.3.x)** - Uses PyArrow schema definition approach
2. **Modern API (0.4.0+)** - Uses pandas DataFrame and improved indexing

The code automatically detects which version is installed and uses the appropriate API.

### SQLite Fallback

If LanceDB is unavailable or fails to initialize, the system falls back to SQLite for vector storage. While not as efficient as LanceDB for vector search, it provides a reliable fallback mechanism.

## Usage

### Storing Vectors

```python
# Initialize the vector database
vector_db = VectorDatabase(db_path="data/vector_db")

# Store a vector
result = await vector_db.store_vector(
    text="This is a test message",
    user_id="user123",
    chat_id=12345
)
```

### Searching for Similar Vectors

```python
# Search for similar vectors
result = await vector_db.search_vectors(
    query="test message",
    user_id="user123",
    limit=5
)

# Process results
if result["success"]:
    for item in result["results"]:
        print(f"Text: {item['text']}")
        print(f"Score: {item['score']}")
```

### Getting Historical Context

```python
# Get historical context for a query
context = await vector_db.get_historical_context(
    query="test message",
    user_id="user123",
    limit=3
)

# Use the context in a model prompt
prompt = f"Answer the following question with this context:\n{context}\n\nQuestion: {query}"
```

## Configuration

The vector database uses the following configuration:

- **Database Path** - Set in the constructor as `db_path` (default: "data/vector_db")
- **Model Name** - Set in the constructor as `model_name` (default: "sentence-transformers/all-MiniLM-L6-v2")
- **SQLite Path** - Set in the constructor as `sqlite_path` (default: "data/pulse_memory.db")

## Dependencies

- **sentence-transformers** - For text embeddings (version >= 2.2.2)
- **lancedb** - Vector database (version 0.3.0 or >= 0.4.0)
- **pandas** - Required for LanceDB operations (version >= 2.0.0)
- **pyarrow** - Required for LanceDB schema definition
- **numpy** - For vector operations
- **sqlite3** - For SQLite fallback

> **Note:** For the latest LanceDB features, we recommend upgrading to LanceDB 0.22.0 or newer. See the [LanceDB Upgrade Guide](lancedb_upgrade.md) for details.

## Error Handling

The vector database includes robust error handling:

- If sentence-transformers fails to initialize, vector operations will be disabled
- If LanceDB fails to initialize, the system falls back to SQLite
- If both LanceDB and SQLite fail, operations return error messages with details

## Testing

The vector database can be tested using the test script:

```bash
python scripts/test_vector_db.py
```

This script tests:

1. Initialization of the vector database
2. Encoding text into vector embeddings
3. Storing and searching vectors
4. Fallback to SQLite when LanceDB is unavailable

## Troubleshooting

### LanceDB Initialization Failure

If you encounter LanceDB initialization issues:

#### For LanceDB 0.3.0 (Legacy)

If you see an error like "module 'lancedb' has no attribute 'Vector'", ensure you have:

1. Installed lancedb version 0.3.0: `pip install lancedb==0.3.0`
2. Installed pandas: `pip install pandas`
3. Installed pyarrow: `pip install pyarrow`

#### For LanceDB 0.4.0+ (Modern)

If you see errors with the modern API:

1. Ensure you have the latest pandas: `pip install --upgrade pandas`
2. Ensure you have a compatible pyarrow version: `pip install --upgrade pyarrow`
3. Check the [LanceDB documentation](https://lancedb.github.io/lancedb/) for version-specific requirements

For more detailed troubleshooting, see the [LanceDB Upgrade Guide](lancedb_upgrade.md).

### Search Performance Issues

If vector search is slow, consider:

1. Reducing the number of vectors stored (by limiting chat history)
2. Increasing the limit parameter in search methods
3. Using a smaller sentence transformer model

### Memory Usage

Vector operations can be memory-intensive. If you encounter memory issues:

1. Reduce the batch size for encoding operations
2. Implement pagination for search results
3. Use a smaller sentence transformer model
