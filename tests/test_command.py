"""
Test script for the intent handler
"""

import asyncio
from utils.intent_handler import IntentHandler

async def main():
    """
    Main function
    """
    # Initialize the intent handler
    intent_handler = IntentHandler()
    
    # Test the "test all" command
    command = "test all"
    print(f"Testing command: {command}")
    result = await intent_handler.parse_command(command)
    print(f"Result: {result}")
    
    # Test other commands for comparison
    commands = [
        "test gemini",
        "test intent what time is it",
        "ollama status",
        "launch cli ui"
    ]
    
    for command in commands:
        print(f"\nTesting command: {command}")
        result = await intent_handler.parse_command(command)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
