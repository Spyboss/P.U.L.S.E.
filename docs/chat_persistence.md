# Chat Persistence in P.U.L.S.E.

This document describes the chat persistence implementation in P.U.L.S.E.

## Overview

P.U.L.S.E. now includes a robust chat persistence system that stores and retrieves chat history using multiple storage mechanisms:

1. **MongoDB Atlas** - Primary storage for chat history and memories
2. **SQLite** - Fallback storage when MongoDB is unavailable
3. **Vector Database** - Semantic search for relevant past conversations

The system is designed to be resilient, with automatic fallback mechanisms if one storage method fails.

## Components

### ChatHistoryManager

The `ChatHistoryManager` class in `context/history.py` is the main interface for chat persistence. It provides methods to:

- Add new interactions to the chat history
- Retrieve recent interactions
- Get context for models, including recent interactions and relevant memories
- Get historical context for queries using semantic search
- Add and retrieve memories

### Vector Database

The `VectorDatabase` class in `utils/vector_db.py` provides semantic search capabilities for chat history. It uses:

- **Sentence Transformers** - For encoding text into vector embeddings
- **LanceDB** - For storing and querying vector embeddings
- **SQLite** - As a fallback for vector storage

### SQLite Utilities

The `sqlite_utils.py` module provides utilities for working with SQLite databases, including:

- Optimizing SQLite databases with WAL mode
- Creating tables with proper indexes
- Executing queries with proper error handling

## Usage

### Adding Interactions

```python
# Add a new interaction to the chat history
result = await history_manager.add_interaction(
    user_input="Hello, how are you?",
    assistant_response="I'm doing well, thank you for asking!",
    metadata={"model": "mistral-small", "intent": "greeting"}
)
```

### Getting Historical Context

```python
# Get historical context for a query
context = await history_manager.get_historical_context(
    query="Tell me about Python programming"
)
```

### Searching Memories

```python
# Search for relevant memories
result = await history_manager.get_relevant_memories(
    query="Python programming"
)
```

## Storage Schema

### MongoDB Collections

- **history** - Stores chat interactions
  - `user_id` - User identifier
  - `interaction_id` - Unique identifier for the interaction
  - `timestamp` - When the interaction occurred
  - `user_input` - User's input text
  - `assistant_response` - Assistant's response text
  - `metadata` - Additional information about the interaction
  - `summarized` - Whether the interaction has been summarized

- **memories** - Stores memories and summaries
  - `user_id` - User identifier
  - `category` - Memory category (e.g., "conversation_summary", "goal")
  - `content` - Memory content
  - `timestamp` - When the memory was created
  - `metadata` - Additional information about the memory

### SQLite Tables

- **chat_history** - Stores chat interactions
  - `id` - Unique identifier
  - `user_id` - User identifier
  - `timestamp` - When the interaction occurred
  - `user_input` - User's input text
  - `assistant_response` - Assistant's response text
  - `model` - Model used for the response
  - `metadata` - JSON string with additional information

- **chat_memories** - Stores memories and summaries
  - `id` - Unique identifier
  - `user_id` - User identifier
  - `category` - Memory category
  - `content` - Memory content
  - `timestamp` - When the memory was created
  - `metadata` - JSON string with additional information

- **chat_vectors** - Stores vector embeddings for semantic search
  - `id` - Unique identifier
  - `user_id` - User identifier
  - `chat_id` - Reference to chat history entry
  - `text` - Text that was encoded
  - `vector_blob` - Binary vector data
  - `timestamp` - When the vector was created

## Configuration

The chat persistence system uses the following configuration:

- **MongoDB URI** - Set in the `.env` file as `MONGODB_URI`
- **SQLite Database Path** - Set in `context/history.py` as `SQLITE_DB_PATH`
- **Vector Database Path** - Set in `utils/vector_db.py` as `db_path`

## Dependencies

- **motor** - Async MongoDB driver
- **pymongo** - MongoDB driver
- **sqlite3** - SQLite database
- **lancedb** - Vector database
- **sentence-transformers** - For text embeddings
- **scikit-learn** - For vector similarity calculations
- **numpy** - For vector operations
- **zstandard** - For compression
