"""
Test script for the CLI UI
"""

import asyncio
from utils.cli_ui import PulseCLIUI
from skills.pulse_agent import PulseAgent

async def main():
    """
    Main function
    """
    # Create a Pulse Agent instance
    agent = PulseAgent()

    # Create a CLI UI instance with the agent
    cli_ui = PulseCLIUI(agent=agent)

    # Test all models
    print("Testing all models...")
    await cli_ui.test_all_models()

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
