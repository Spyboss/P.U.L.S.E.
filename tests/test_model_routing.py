"""
Test script for model routing with rich context data
This script tests the handoff between Gemini and specialized models
"""

import os
import sys
import asyncio
import logging
from unittest.mock import patch, MagicMock

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
        logging.FileHandler("logs/test_model_routing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_model_routing')

# Import the model interface
from skills.optimized_model_interface import OptimizedModelInterface

async def test_debug_intent_routing():
    """
    Test routing a debug intent to DeepSeek
    """
    logger.info("Starting debug intent routing test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Test debug intent routing
    logger.info("Testing debug intent routing")
    response = await model_interface.generate_response(
        prompt="Low memory detected, how can I fix this?",
        intent="debug",
        temperature=0.7,
        max_tokens=1000
    )

    logger.info(f"Debug intent routing response: {response}")

    # Verify that the response was generated
    assert response["success"], "Response generation should succeed"

    # Verify that the response includes a handoff message or error message about DeepSeek
    assert ("Handing off to Deepseek" in response["content"] or
            "deepseek" in response["content"].lower() or
            "hand off to deepseek" in response["content"].lower()), \
        "Response should include handoff message or reference to DeepSeek"

    logger.info("Debug intent routing test completed successfully")
    return response

async def test_code_intent_routing():
    """
    Test routing a code intent to DeepCoder
    """
    logger.info("Starting code intent routing test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Test code intent routing
    logger.info("Testing code intent routing")
    response = await model_interface.generate_response(
        prompt="Write a Python script to monitor system memory usage",
        intent="code",
        temperature=0.7,
        max_tokens=1000
    )

    logger.info(f"Code intent routing response: {response}")

    # Verify that the response was generated
    assert response["success"], "Response generation should succeed"

    # Verify that the response includes a handoff message or error message about DeepCoder
    assert ("Handing off to Deepcoder" in response["content"] or
            "deepcoder" in response["content"].lower() or
            "hand off to deepcoder" in response["content"].lower()), \
        "Response should include handoff message or reference to DeepCoder"

    logger.info("Code intent routing test completed successfully")
    return response

async def test_direct_model_call():
    """
    Test calling a model directly
    """
    logger.info("Starting direct model call test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Test direct model call
    logger.info("Testing direct model call to DeepCoder")
    response = await model_interface.generate_response(
        prompt="Explain how to optimize Python code for memory usage",
        model="deepcoder",
        temperature=0.7,
        max_tokens=1000
    )

    logger.info(f"Direct model call response: {response}")

    # Verify that the response was generated
    assert response["success"], "Response generation should succeed"

    logger.info("Direct model call test completed successfully")
    return response

async def test_offline_mode_routing():
    """
    Test routing in offline mode
    """
    logger.info("Starting offline mode routing test")

    # Create a model interface
    model_interface = OptimizedModelInterface()

    # Enable offline mode
    await model_interface.toggle_offline_mode(True)

    # Test debug intent routing in offline mode
    logger.info("Testing debug intent routing in offline mode")
    response = await model_interface.generate_response(
        prompt="Low memory detected, how can I fix this?",
        intent="debug",
        temperature=0.7,
        max_tokens=1000
    )

    logger.info(f"Offline mode routing response: {response}")

    # Log the response for debugging
    logger.info(f"Response success: {response.get('success', False)}")
    logger.info(f"Response error: {response.get('error', 'None')}")

    # If the response was successful, check if it mentions offline mode or Ollama
    if response.get("success", False):
        assert ("offline mode" in response["content"].lower() or
                "ollama" in response["content"].lower()), \
            "Response should mention offline mode or Ollama"
    else:
        # If the response failed, check if the error message mentions Ollama
        assert "ollama" in response.get("error", "").lower(), \
            f"Error should mention Ollama, got: {response.get('error', '')}"

    # Disable offline mode
    await model_interface.toggle_offline_mode(False)

    logger.info("Offline mode routing test completed successfully")
    return response

async def run_all_tests():
    """
    Run all tests
    """
    logger.info("Starting model routing tests")

    # Run all tests
    debug_response = await test_debug_intent_routing()
    code_response = await test_code_intent_routing()
    direct_response = await test_direct_model_call()
    offline_response = await test_offline_mode_routing()

    # Print summary
    logger.info("Model routing tests completed")
    logger.info(f"Debug intent routing: {debug_response['success']}")
    logger.info(f"Code intent routing: {code_response['success']}")
    logger.info(f"Direct model call: {direct_response['success']}")
    logger.info(f"Offline mode routing: {offline_response['success']}")

    return {
        "debug": debug_response,
        "code": code_response,
        "direct": direct_response,
        "offline": offline_response
    }

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())
