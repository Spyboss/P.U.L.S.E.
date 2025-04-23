"""
Test offline mode functionality
This script tests the auto-start feature of Ollama when offline
"""

import os
import sys
import asyncio
import logging
from unittest.mock import patch

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Make sure the directory exists
os.makedirs("logs", exist_ok=True)

# Import the model interface
from skills.optimized_model_interface import OptimizedModelInterface
from utils.ollama_manager import OllamaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_offline_mode.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_offline_mode')

async def test_offline_mode():
    """
    Test offline mode functionality
    """
    logger.info("Starting offline mode test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Mock the check_internet_connection method to simulate offline mode
    original_check_internet = OllamaManager.check_internet_connection

    try:
        # Patch the check_internet_connection method to always return False
        async def mock_check_internet(*args, **kwargs):
            return False

        OllamaManager.check_internet_connection = mock_check_internet

        # Initialize the model interface
        logger.info("Initializing model interface with mocked offline mode")
        await model_interface._initialize()

        # Check if offline mode is enabled
        status = await model_interface.check_status()
        logger.info(f"Status after initialization: {status}")

        # Verify that offline mode is enabled
        assert model_interface.is_offline_mode, "Offline mode should be enabled"

        # Verify that Ollama is running
        assert status["ollama"]["running"], "Ollama should be running in offline mode"

        # Test intent classification
        logger.info("Testing intent classification in offline mode")
        intent_result = await model_interface.classify_intent("what time is it in tokyo?")
        logger.info(f"Intent classification result: {intent_result}")

        # Verify that the intent was classified
        assert intent_result["success"], "Intent classification should succeed"

        # Test response generation
        logger.info("Testing response generation in offline mode")
        response = await model_interface.generate_response(
            prompt="What time is it in Tokyo?",
            model="phi"
        )
        logger.info(f"Response generation result: {response}")

        # Verify that the response was generated
        assert response["success"], "Response generation should succeed"

        logger.info("Offline mode test completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during offline mode test: {str(e)}")
        return False
    finally:
        # Restore the original method
        OllamaManager.check_internet_connection = original_check_internet

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_offline_mode())
