#!/usr/bin/env python3
"""
Test script to verify LanceDB fix in the main application
"""

import os
import sys
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.vector_db import VectorDatabase, LANCEDB_VERSION, LANCEDB_MODERN, HAS_LANCEDB_VECTOR

async def print_lancedb_info():
    """Print LanceDB information"""
    print("\n=== LanceDB Information ===")
    print(f"LanceDB version: {LANCEDB_VERSION}")
    print(f"LanceDB API: {'modern' if LANCEDB_MODERN else 'legacy'}")
    print(f"LanceDB Vector class: {'available' if HAS_LANCEDB_VECTOR else 'not available'}")

async def test_direct_vector_db():
    """Test vector database directly"""
    print("\n=== Testing Vector Database Directly ===")

    # Initialize vector database
    vector_db = VectorDatabase(db_path="data/test_vector_db")

    # Store a test vector
    result = await vector_db.store_vector(
        text="This is a direct test of the vector database",
        user_id="test_user",
        chat_id=12345
    )

    print(f"\nStored vector: {result}")

    # Query similar vectors
    query_result = await vector_db.query_similar(
        text="vector database",
        user_id="test_user",
        limit=3
    )

    print(f"\nQuery result success: {query_result.get('success', False)}")
    print(f"Found {len(query_result.get('data', []))} similar items")

    # Get historical context
    context = await vector_db.get_historical_context(
        query="vector database",
        user_id="test_user",
        limit=3
    )

    print(f"\nHistorical context: {context[:200]}...")

    # Close the vector database
    await vector_db.close()

    print("\nDirect vector database test completed successfully!")

async def run_tests():
    """Run all tests"""
    try:
        await print_lancedb_info()
        await test_direct_vector_db()
        print("\nAll vector database tests completed successfully!")
    except Exception as e:
        print(f"\nError during tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_tests())
