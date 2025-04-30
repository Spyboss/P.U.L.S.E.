#!/usr/bin/env python3
"""
Script to run the vector database tests
"""

import os
import sys
import asyncio

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the test module
from tests.utils.test_vector_db import TestVectorDatabase

async def run_tests():
    """Run the vector database tests"""
    print("Running Vector Database Tests...")

    # Create a test instance
    test_case = TestVectorDatabase()

    # Set up the test environment
    test_case.setUp()

    try:
        # Run the initialization test
        print("\nTest: Initialization")
        test_case.test_initialization()
        print("✅ Initialization test passed")

        # Run the encoding test
        print("\nTest: Encoding")
        test_case.test_encoding()
        print("✅ Encoding test passed")

        # Run the store and search test
        print("\nTest: Store and Search")
        await test_case.test_store_and_search()
        print("✅ Store and Search test passed")

        # Run the fallback to SQLite test
        print("\nTest: Fallback to SQLite")
        await test_case.test_fallback_to_sqlite()
        print("✅ Fallback to SQLite test passed")

        print("\nAll tests passed! ✅")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
    finally:
        # Clean up the test environment
        test_case.tearDown()

def main():
    """Main function"""
    asyncio.run(run_tests())

if __name__ == "__main__":
    main()
