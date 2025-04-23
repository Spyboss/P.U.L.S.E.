"""
Test script for Ollama integration
"""

import os
import sys
import asyncio

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from utils.ollama_manager import OllamaManager

async def test_ollama():
    """
    Test Ollama integration
    """
    try:
        # Initialize the Ollama manager
        ollama_manager = OllamaManager()
        
        # Check status
        print("Checking Ollama status...")
        status = await ollama_manager.check_status(force=True)
        print(f"Status: {status}")
        
        # Start service if not running
        if not status["running"]:
            print("Starting Ollama service...")
            result = await ollama_manager.start_service()
            print(f"Start result: {result}")
            
            # Check status again
            status = await ollama_manager.check_status(force=True)
            print(f"Status after start: {status}")
        
        # List models
        print("Listing models...")
        models = await ollama_manager.list_models()
        print(f"Models: {models}")
        
        # Pull a model if needed
        if not models["models"] or "phi-2" not in models["models"]:
            print("Pulling phi-2 model...")
            result = await ollama_manager.pull_model("phi-2")
            print(f"Pull result: {result}")
        
        # Stop service
        print("Stopping Ollama service...")
        result = await ollama_manager.stop_service()
        print(f"Stop result: {result}")
        
        # Check status again
        status = await ollama_manager.check_status(force=True)
        print(f"Status after stop: {status}")
        
        print("Ollama test completed successfully!")
        
    except Exception as e:
        print(f"Error testing Ollama: {str(e)}")
        
if __name__ == "__main__":
    print("=== Ollama Test ===")
    asyncio.run(test_ollama())
