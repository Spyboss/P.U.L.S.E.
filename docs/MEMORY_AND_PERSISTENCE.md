# P.U.L.S.E. Memory and Persistence System

This document provides comprehensive information about the memory and persistence systems in P.U.L.S.E. (Prime Uminda's Learning System Engine).

## Overview

P.U.L.S.E. includes a robust memory and persistence system that enables:

1. **Chat History Persistence** - Storing and retrieving conversation history
2. **Semantic Search** - Finding relevant past conversations using vector embeddings
3. **Memory Management** - Storing and retrieving long-term memories and information
4. **Context Awareness** - Providing relevant context to models for better responses

The system uses multiple storage mechanisms for resilience:

1. **MongoDB Atlas** - Primary cloud storage for chat history and memories
2. **LanceDB** - Vector database for semantic search
3. **SQLite** - Local fallback storage when cloud services are unavailable

## Chat Persistence

### Components

#### ChatHistoryManager

The `ChatHistoryManager` class in `context/history.py` is the main interface for chat persistence. It provides methods to:

- Add new interactions to the chat history
- Retrieve recent interactions
- Get context for models, including recent interactions and relevant memories
- Get historical context for queries using semantic search
- Add and retrieve memories

#### Session Tracking

P.U.L.S.E. tracks session state to provide more natural conversations:

- A session is considered "new" after 5 minutes of inactivity
- Greetings are only included at the start of a new session
- This prevents repetitive greetings in consecutive responses

```python
# Check if this is a new session
is_new_session = False
if hasattr(self, 'rich_context_manager') and self.rich_context_manager:
    try:
        # Get the context manager from the rich context manager
        context_manager = self.rich_context_manager.context_manager
        if hasattr(context_manager, 'is_new_session'):
            is_new_session = context_manager.is_new_session()
            self.logger.info(f"Session status: {'New session' if is_new_session else 'Existing session'}")
    except Exception as e:
        self.logger.error(f"Error checking session status: {str(e)}")
```

### Storage Schema

#### MongoDB Collections

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

#### SQLite Tables

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

### Usage

#### Adding Interactions

```python
# Add a new interaction to the chat history
result = await history_manager.add_interaction(
    user_input="Hello, how are you?",
    assistant_response="I'm doing well, thank you for asking!",
    metadata={"model": "mistral-small", "intent": "greeting"}
)
```

#### Getting Historical Context

```python
# Get historical context for a query
context = await history_manager.get_historical_context(
    query="Tell me about Python programming"
)
```

#### Searching Memories

```python
# Search for relevant memories
result = await history_manager.get_relevant_memories(
    query="Python programming"
)
```

## Vector Database

### Overview

P.U.L.S.E. includes a robust vector database system that enables semantic search of chat history and memories. The system uses:

1. **Sentence Transformers** - For encoding text into vector embeddings
2. **LanceDB** - Primary storage for vector embeddings (supports both legacy 0.3.0 and modern 0.4.0+ versions)
3. **SQLite** - Fallback storage when LanceDB is unavailable

### Components

#### VectorDatabase Class

The `VectorDatabase` class in `utils/vector_db.py` is the main interface for vector operations. It provides methods to:

- Encode text into vector embeddings
- Store vector embeddings in LanceDB or SQLite
- Search for similar vectors using semantic similarity
- Retrieve historical context for queries

#### Sentence Transformers

The system uses the `sentence-transformers/all-MiniLM-L6-v2` model to encode text into 384-dimensional vector embeddings. This model provides a good balance between performance and accuracy for semantic search.

#### LanceDB

LanceDB is used as the primary vector database. It provides:

- Efficient storage of vector embeddings
- Fast nearest-neighbor search
- Support for filtering by user ID and other metadata

The system supports two LanceDB API versions:

1. **Legacy API (0.3.x)** - Uses PyArrow schema definition approach
2. **Modern API (0.4.0+)** - Uses pandas DataFrame and improved indexing

The code automatically detects which version is installed and uses the appropriate API.

### Usage

#### Storing Vectors

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

#### Searching for Similar Vectors

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

#### Getting Historical Context

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

### LanceDB Upgrade Guide

P.U.L.S.E. currently uses LanceDB version 0.3.0 for vector storage and semantic search. The vector database implementation in `utils/vector_db.py` has been updated to support both:

1. Legacy LanceDB API (0.3.x)
2. Modern LanceDB API (0.4.0+)

The code will automatically detect which version is installed and use the appropriate API.

#### Upgrading to Latest LanceDB

To upgrade to the latest version of LanceDB:

1. Update the requirements.txt file:
   ```diff
   - lancedb==0.3.0  # Vector database for semantic search
   + lancedb>=0.22.0  # Vector database for semantic search
   ```

2. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the vector database tests to verify the upgrade:
   ```bash
   python scripts/test_vector_db.py
   ```

#### Migration Considerations

When upgrading from LanceDB 0.3.0 to a newer version, consider the following:

1. **Data Migration**: The table schema and storage format have changed between versions. The updated code will handle this automatically for new data, but existing vector data may need to be migrated.

2. **Performance Tuning**: Newer versions of LanceDB offer improved performance and additional configuration options. You may want to adjust the index parameters in `_initialize_modern_lancedb()` method for optimal performance.

3. **API Changes**: The search API has changed in newer versions. The updated code handles these differences, but custom code that directly interacts with LanceDB may need to be updated.

## Recent Improvements

The following improvements have been implemented:

1. **Enhanced Chat Persistence**: Improved how P.U.L.S.E. leverages past interactions by enhancing the vector database retrieval and ensuring the context is properly passed to the model.

2. **Session Tracking**: Implemented session tracking to avoid repetitive greetings in consecutive responses, making conversations feel more natural.

3. **LanceDB Stability**: Confirmed LanceDB version 0.3.0 is pinned for stability.

4. **Enhanced Vector Database Retrieval**:
   - Enhanced `get_historical_context()` to include more information about past interactions
   - Added timestamps and relevance scores to provide better context
   - Increased the default number of results from 3 to 5
   - Improved formatting of the context for better readability

## Future Improvements

Potential future improvements include:

1. **Adaptive Session Timeout**: Adjust the session timeout based on user interaction patterns
2. **Personalized Greeting Styles**: Learn user preferences for greeting styles
3. **Context Relevance Filtering**: Improve the filtering of historical context based on relevance
4. **Memory Summarization**: Summarize long-term memory for more efficient context retrieval
5. **Enhanced Vector Search**: Implement more sophisticated vector search algorithms
6. **Multi-Modal Memory**: Support storing and retrieving images and other media types
7. **Hierarchical Memory**: Implement a hierarchical memory system for better organization
8. **Memory Compression**: Compress memories to reduce storage requirements
9. **Memory Prioritization**: Prioritize important memories for retention
10. **Memory Forgetting**: Implement a forgetting mechanism for less important memories
