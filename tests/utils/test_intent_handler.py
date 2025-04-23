"""
Test script for the intent handler
"""

import os
import sys
import asyncio

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from utils.intent_handler import IntentHandler

async def test_intent_handler():
    """
    Test the intent handler
    """
    try:
        # Initialize the intent handler
        intent_handler = IntentHandler()
        
        # Test some queries
        test_queries = [
            "debug my code",
            "what time is it",
            "remind me to buy milk",
            "write a function to calculate fibonacci",
            "explain how transformers work",
            "ollama status",
            "ollama on",
            "ollama off",
            "ollama pull phi-2",
            "enable offline mode",
            "disable offline mode",
            "test intent debug my code"
        ]
        
        print("Testing intent classification...")
        for query in test_queries:
            intent = await intent_handler.classify(query)
            print(f"Query: {query}")
            print(f"Intent: {intent}")
            print()
            
        print("Testing command parsing...")
        for query in test_queries:
            command = await intent_handler.parse_command(query)
            print(f"Query: {query}")
            print(f"Command: {command}")
            print()
            
        print("Intent handler test completed successfully!")
        
    except Exception as e:
        print(f"Error testing intent handler: {str(e)}")

if __name__ == "__main__":
    print("=== Intent Handler Test ===")
    asyncio.run(test_intent_handler())
