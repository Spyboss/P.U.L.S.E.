#!/usr/bin/env python
"""
Test script for Grok API integration within the agent
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GrokAgentTest")

# Force set the Grok API key directly
os.environ["GROK_API_KEY"] = "9f227c2932254ae1becfe42d6bc7b7ac"
logger.info(f"Set GROK_API_KEY environment variable directly: {os.environ['GROK_API_KEY']}")

# Import the agent
try:
    from main import PulseAgent
    logger.info("Successfully imported PulseAgent")
except ImportError as e:
    logger.error(f"Failed to import PulseAgent: {str(e)}")
    sys.exit(1)

async def test_grok_api_with_agent():
    """Test using Grok through the agent's model_query_intent."""
    logger.info("Initializing PulseAgent...")
    agent = PulseAgent()

    # Create a test request
    test_request = {
        "command": "model grok What is your name and what can you do?",
        "model": "grok"
    }

    logger.info(f"Testing model_query_intent with Grok...")
    response = await agent.model_query_intent(test_request)

    logger.info(f"Response from agent: {response}")
    return response

if __name__ == "__main__":
    logger.info("Starting Grok integration test with agent...")
    # Load environment variables after we've set our key
    load_dotenv(override=False)  # Don't override our direct setting

    # Run the async test
    response = asyncio.run(test_grok_api_with_agent())

    # Check if it's a simulation or real API call
    message = response.get("message", "")

    if "simulated" in message.lower():
        logger.warning("Response appears to be simulated, not a real Grok API call")
    else:
        logger.info("Success! Received a real response from Grok API")

    print("\nGrok Response:")
    print(message)