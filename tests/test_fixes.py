"""
Test script for the fixes we've made to the model query and personality commands
"""

import asyncio
import os
import sys
import structlog

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from skills.pulse_agent import PulseAgent
from utils.intent_handler import IntentHandler

# Configure logging
logger = structlog.get_logger("test_fixes")

async def test_commands():
    """Test various commands to verify our fixes"""
    print("\n=== INITIALIZING TEST ===\n")

    # Initialize the agent
    agent = PulseAgent()
    # The agent is initialized in the constructor

    # Test commands
    commands = [
        "help",
        "show personality",
        "adjust humor to 0.8",
        "ask gemini what is the capital of France?",
        "ask deepseek how to write a Python function to calculate fibonacci numbers",
        "ask code how to implement a binary search tree in Python",
        "search memory",
        "save to memory test: This is a test memory",
        "search memory test"
    ]

    # Run each command and print the response
    for command in commands:
        print(f"\n=== TESTING: {command} ===\n")
        try:
            response = await agent.process_input(command)
            print(f"\nRESPONSE:\n{response}\n")
        except Exception as e:
            print(f"ERROR: {str(e)}")
        print("=" * 80)

        # Small delay between commands
        await asyncio.sleep(1)

    print("\n=== TEST COMPLETE ===\n")

if __name__ == "__main__":
    # Run the test
    try:
        asyncio.run(test_commands())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.\n")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}\n")
        import traceback
        traceback.print_exc()
