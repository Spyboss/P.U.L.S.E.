#!/usr/bin/env python3
"""
Test script for AI command handling in General Pulse
Tests the fixes for asyncio event loop issues
"""

import os
import sys
import asyncio
import logging
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("test_ai_command")

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_in_thread(coro):
    """Run a coroutine in a separate thread with its own event loop"""
    result = None
    exception = None
    
    def thread_target():
        nonlocal result, exception
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        except Exception as e:
            exception = e
        finally:
            loop.close()
    
    thread = Thread(target=thread_target)
    thread.start()
    thread.join()
    
    if exception:
        raise exception
    return result

async def test_ai_command_handling():
    """Test the AI command handling with our fixes"""
    from skills.agent import Agent
    
    logger.info("Creating agent with simulation mode...")
    agent = Agent(simulate_responses=True)
    
    # Test direct model query
    commands = [
        "ask claude What is machine learning?",
        "ask grok Explain quantum computing",
        "query deepseek How does a neural network work?"
    ]
    
    logger.info("Testing AI commands...")
    for command in commands:
        logger.info(f"Command: {command}")
        response = await agent._handle_ai_command(command)
        logger.info(f"Response: {response}")
        
        # Verify response is not an error
        assert "Error" not in response, f"Error in response: {response}"
        
    logger.info("✅ All commands handled without errors")
    return True

def test_sync_wrapper():
    """Test the synchronous wrapper for AI commands"""
    from skills.model_interface import ModelInterface
    
    logger.info("Creating model interface with simulation mode...")
    model_interface = ModelInterface(simulate_responses=True)
    
    logger.info("Testing direct API call...")
    response = model_interface.call_model_api(
        model_name="claude",
        prompt="What is artificial intelligence?"
    )
    
    logger.info(f"Response: {response}")
    
    # Verify response
    assert "content" in response, "Response missing content"
    assert response["success"] is True, "Response indicates failure"
    
    logger.info("✅ Synchronous API call successful")
    return True

def main():
    """Main test function"""
    logger.info("🧪 Testing AI command handling with asyncio fixes")
    
    # Test synchronous wrapper
    try:
        test_sync_wrapper()
    except Exception as e:
        logger.error(f"❌ Synchronous test failed: {str(e)}")
        return 1
    
    # Test async command handling in a separate thread
    try:
        run_in_thread(test_ai_command_handling())
    except Exception as e:
        logger.error(f"❌ Async test failed: {str(e)}")
        return 1
    
    logger.info("🎉 All tests passed! The fixes are working correctly.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 