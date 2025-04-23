"""
Test script for DistilBERT intent classification
"""

import os
import sys
import asyncio

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from utils.distilbert_classifier import DistilBERTClassifier

async def test_distilbert():
    """
    Test DistilBERT for intent classification
    """
    try:
        # Initialize the classifier
        classifier = DistilBERTClassifier()

        # Test some queries
        test_queries = [
            "debug my code",
            "what time is it",
            "remind me to buy milk",
            "write a function to calculate fibonacci",
            "explain how transformers work",
            "ollama status",
            "help me troubleshoot my Docker container",
            "write a blog post about AI ethics",
            "what are the latest trends in AI",
            "brainstorm ideas for my new app",
            "solve this math problem: 2x + 3 = 7",
            "create a technical document for my API"
        ]

        print("Testing intent classification...")
        for query in test_queries:
            result = await classifier.classify_intent(query)
            print(f"Query: {query}")
            print(f"Intent: {result['intent']}")
            print(f"Confidence: {result.get('confidence', 0.0)}")
            print()

        print("Intent classification test completed successfully!")

    except Exception as e:
        print(f"Error testing intent classification: {str(e)}")

async def test_intent_classifier():
    """
    Test the intent classifier in the application
    """
    try:
        # Import the intent classifier
        from utils.intent_handler import IntentHandler

        # Initialize the intent handler
        intent_handler = IntentHandler()

        # Test some queries
        test_queries = [
            "debug my code",
            "what time is it",
            "remind me to buy milk",
            "write a function to calculate fibonacci",
            "explain how transformers work",
            "ollama status"
        ]

        print("Testing intent classifier...")
        for query in test_queries:
            intent = await intent_handler.classify(query)
            print(f"Query: {query}")
            print(f"Intent: {intent}")
            print()

        print("Intent classifier test completed successfully!")

    except Exception as e:
        print(f"Error testing intent classifier: {str(e)}")

if __name__ == "__main__":
    print("=== DistilBERT Test ===")
    asyncio.run(test_distilbert())
