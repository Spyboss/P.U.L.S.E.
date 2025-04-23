
# CLI UI Launcher
import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the CLI UI
from utils.cli_ui import PulseCLIUI
from skills.pulse_agent import PulseAgent

# Create a new agent instance
agent = PulseAgent()

# Create the CLI UI
cli_ui = PulseCLIUI(agent)

# Run the CLI UI
asyncio.run(cli_ui.run())
