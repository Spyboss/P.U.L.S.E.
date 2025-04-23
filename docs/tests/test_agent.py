"""
Test script for the PulseAgent
"""

import asyncio
from skills.pulse_agent import PulseAgent

async def main():
    """
    Main function
    """
    # Create a PulseAgent instance
    agent = PulseAgent()
    
    # Test the "test all" command
    command = "test all"
    print(f"Testing command: {command}")
    response = await agent.process_input(command)
    print(f"Response: {response}")
    
    # Test other commands for comparison
    commands = [
        "test gemini",
        "test intent what time is it",
        "ollama status",
        "launch cli ui"
    ]
    
    for command in commands:
        print(f"\nTesting command: {command}")
        response = await agent.process_input(command)
        print(f"Response: {response}")
    
    # Wait a bit to allow any background tasks to complete
    print("\nWaiting for background tasks to complete...")
    await asyncio.sleep(5)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
