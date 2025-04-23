"""
Test script for the model interface
"""

import os
import sys
import asyncio

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from skills.optimized_model_interface import OptimizedModelInterface

async def test_model_interface():
    """
    Test the model interface
    """
    try:
        # Initialize the model interface
        model_interface = OptimizedModelInterface()

        # Wait for initialization
        await asyncio.sleep(2)

        # Check status
        print("Checking status...")
        status = await model_interface.check_status()
        print(f"Status: {status}")

        # Test intent classification
        print("\nTesting intent classification...")
        test_queries = [
            "debug my code",
            "what time is it",
            "remind me to buy milk",
            "write a function to calculate fibonacci",
            "explain how transformers work",
            "ollama status"
        ]

        for query in test_queries:
            result = await model_interface.classify_intent(query)
            print(f"Query: {query}")
            print(f"Intent: {result['intent']}")
            print(f"Confidence: {result.get('confidence', 0.0)}")
            print(f"Source: {result.get('source', 'unknown')}")
            print()

        # Test Ollama commands
        print("\nTesting Ollama commands...")

        # Check if Ollama is running
        status = await model_interface.check_status()
        if not status["ollama"]["running"]:
            print("Starting Ollama...")
            result = await model_interface.start_ollama()
            print(f"Start result: {result}")

        # List models
        print("\nListing models...")
        models = await model_interface.list_ollama_models()
        print(f"Models: {models}")

        # Toggle offline mode
        print("\nEnabling offline mode...")
        result = await model_interface.toggle_offline_mode(True)
        print(f"Toggle result: {result}")

        # Generate a response
        print("\nGenerating a response...")
        response = await model_interface.generate_response(
            prompt="Hello, how are you?",
            model=None,  # Use default model
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response}")

        # Disable offline mode
        print("\nDisabling offline mode...")
        result = await model_interface.toggle_offline_mode(False)
        print(f"Toggle result: {result}")

        # Stop Ollama
        print("\nStopping Ollama...")
        result = await model_interface.stop_ollama()
        print(f"Stop result: {result}")

        print("\nModel interface test completed successfully!")

    except Exception as e:
        print(f"Error testing model interface: {str(e)}")

if __name__ == "__main__":
    print("=== Model Interface Test ===")
    asyncio.run(test_model_interface())
