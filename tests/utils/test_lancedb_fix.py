#!/usr/bin/env python3
"""
Test script to verify LanceDB initialization fix
"""

import os
import sys
import asyncio
from utils.vector_db import VectorDatabase, LANCEDB_VERSION, LANCEDB_MODERN

async def test_lancedb():
    """Test LanceDB initialization and operations"""
    print(f"Testing LanceDB initialization (version: {LANCEDB_VERSION}, API: {'modern' if LANCEDB_MODERN else 'legacy'})")
    
    # Initialize vector database
    vector_db = VectorDatabase(db_path="data/test_vector_db")
    
    # Test storing a vector
    result = await vector_db.store_vector(
        text="This is a test message for LanceDB fix verification",
        user_id="test_user",
        chat_id=12345
    )
    
    print(f"Store vector result: {result}")
    
    # Test querying similar vectors
    query_result = await vector_db.query_similar(
        text="test message",
        user_id="test_user",
        limit=3
    )
    
    print(f"Query result success: {query_result.get('success', False)}")
    print(f"Found {len(query_result.get('data', []))} similar items")
    
    # Test getting historical context
    context = await vector_db.get_historical_context(
        query="test message",
        user_id="test_user",
        limit=3
    )
    
    print(f"Historical context: {context[:100]}...")
    
    # Close the vector database
    await vector_db.close()
    
    print("LanceDB test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_lancedb())
