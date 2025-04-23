"""
Test script for model mappings
This script tests the model mappings in the ModelInterface class
"""

import os
import sys
import asyncio
import logging

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Make sure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_model_mappings.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_model_mappings')

# Import the model interface
from skills.optimized_model_interface import OptimizedModelInterface

async def test_model_mappings():
    """
    Test the model mappings
    """
    logger.info("Starting model mappings test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Check the model mappings
    logger.info("Checking model mappings")

    # Expected model mappings
    expected_mappings = {
        "gemini": "gemini-2.0-flash-thinking-exp-01-21",
        "deepseek": "deepseek/deepseek-r1-zero:free",
        "deepcoder": "agentica-org/deepcoder-14b-preview:free",
        "llama-doc": "meta-llama/llama-4-scout:free",
        "mistral-small": "mistralai/mistral-small-24b-instruct-2501:free",
        "llama-content": "meta-llama/llama-3.2-11b-vision-instruct:free",
        "llama-technical": "meta-llama/llama-3.3-70b-instruct:free",
        "hermes": "nousresearch/nous-hermes-2-mixtral-8x7b-sft:free",
        "olmo": "allenai/olmo-7b:free",
        "mistralai": "mistralai/mixtral-8x7b-instruct:free",
        "kimi": "moonshot/kimi:free",
        "nemotron": "nvidia/nemotron-4-340b-instruct:free",
        "phi": "microsoft/phi-2:free"
    }

    # Check each mapping
    for model_name, expected_id in expected_mappings.items():
        actual_id = model_interface.models.get(model_name)
        logger.info(f"Model {model_name}: Expected {expected_id}, Actual {actual_id}")
        assert actual_id == expected_id, f"Model {model_name} has incorrect ID: {actual_id} (expected {expected_id})"

    logger.info("Model mappings test completed successfully")
    return True

async def test_gemini_model_id():
    """
    Test the Gemini model ID
    """
    logger.info("Starting Gemini model ID test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Initialize the model interface
    await model_interface._initialize()

    # Check if Gemini is available
    if model_interface.gemini_available and hasattr(model_interface, 'gemini_model'):
        # Get the model name
        model_name = model_interface.gemini_model.model_name
        logger.info(f"Gemini model name: {model_name}")

        # Check if it's the expected model
        expected_model = "gemini-2.0-flash-thinking-exp-01-21"
        # Remove the 'models/' prefix if present
        if model_name.startswith("models/"):
            model_name = model_name.replace("models/", "")

        assert model_name == expected_model, f"Gemini model has incorrect ID: {model_name} (expected {expected_model})"

        logger.info("Gemini model ID test completed successfully")
        return True
    else:
        logger.warning("Gemini is not available, skipping test")
        return None

async def run_all_tests():
    """
    Run all tests
    """
    logger.info("Starting model mapping tests")

    # Run all tests
    mappings_result = await test_model_mappings()
    gemini_result = await test_gemini_model_id()

    # Print summary
    logger.info("Model mapping tests completed")
    logger.info(f"Model mappings test: {mappings_result}")
    logger.info(f"Gemini model ID test: {gemini_result if gemini_result is not None else 'Skipped'}")

    return {
        "mappings": mappings_result,
        "gemini": gemini_result
    }

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())
