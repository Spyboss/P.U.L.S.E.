#!/usr/bin/env python3
"""
Test script for the Vector Database functionality
"""

import asyncio
import os
import shutil
import unittest
import numpy as np
from utils.vector_db import VectorDatabase

class TestVectorDatabase(unittest.TestCase):
    """Test cases for the Vector Database"""

    def setUp(self):
        """Set up test environment"""
        # Create a test directory for the vector database
        self.test_db_path = "data/test_vector_db"

        # Create the test directory if it doesn't exist
        os.makedirs(self.test_db_path, exist_ok=True)

        # Initialize the vector database
        self.vector_db = VectorDatabase(
            db_path=self.test_db_path,
            fallback_to_sqlite=True
        )

    def tearDown(self):
        """Clean up after tests"""
        # Remove the test directory
        if os.path.exists(self.test_db_path):
            shutil.rmtree(self.test_db_path)

    def test_initialization(self):
        """Test vector database initialization"""
        # Check if the vector database was initialized correctly
        self.assertIsNotNone(self.vector_db)
        self.assertIsNotNone(self.vector_db.encoder)

        # Check if LanceDB is available
        if self.vector_db.lancedb is not None:
            self.assertIsNotNone(self.vector_db.table)

    async def test_store_and_search(self):
        """Test storing and searching vectors"""
        # Store a test vector
        test_text = "This is a test message for vector search"
        test_user_id = "test_user"
        test_chat_id = 12345

        # Store the vector
        result = await self.vector_db.store_vector(
            text=test_text,
            user_id=test_user_id,
            chat_id=test_chat_id
        )

        # Check if the vector was stored successfully
        self.assertTrue(result["success"])

        # Search for the vector
        search_results = await self.vector_db.query_similar(
            text="test message",
            user_id=test_user_id,
            limit=5
        )

        # Check if the search returned results
        self.assertTrue(search_results["success"])
        self.assertGreater(len(search_results["data"]), 0)

        # Check if the first result contains our test text
        self.assertIn(test_text, search_results["data"][0]["text"])

    def test_encoding(self):
        """Test text encoding"""
        # Test text
        test_text = "This is a test message for encoding"

        # Encode the text
        embedding = self.vector_db.encode_text(test_text)

        # Check if the embedding is a numpy array with the correct dimension
        self.assertIsInstance(embedding, np.ndarray)
        # Use the global VECTOR_DIMENSION constant
        from utils.vector_db import VECTOR_DIMENSION
        self.assertEqual(embedding.shape[0], VECTOR_DIMENSION)

    async def test_fallback_to_sqlite(self):
        """Test fallback to SQLite when LanceDB is unavailable"""
        # Create a vector database with LanceDB disabled
        db_with_fallback = VectorDatabase(
            db_path=self.test_db_path,
            fallback_to_sqlite=True,
            _force_sqlite_fallback=True  # This is a test parameter
        )

        # Store a test vector
        test_text = "This is a test message for SQLite fallback"
        test_user_id = "test_user"

        # Store the vector
        result = await db_with_fallback.store_vector(
            text=test_text,
            user_id=test_user_id
        )

        # Check if the vector was stored successfully
        self.assertTrue(result["success"])

        # Search for the vector
        search_results = await db_with_fallback.query_similar(
            text="SQLite fallback",
            user_id=test_user_id,
            limit=5
        )

        # Check if the search returned results
        self.assertTrue(search_results["success"])
        self.assertGreater(len(search_results["data"]), 0)

        # Check if the first result contains our test text
        self.assertIn(test_text, search_results["data"][0]["text"])

async def run_async_tests():
    """Run the async tests"""
    # Create a test suite
    suite = unittest.TestSuite()

    # Add the async tests
    test_case = TestVectorDatabase()
    suite.addTest(test_case)

    # Run the tests
    runner = unittest.TextTestRunner()
    runner.run(suite)

def main():
    """Main function"""
    # Run the async tests
    asyncio.run(run_async_tests())

if __name__ == "__main__":
    main()
