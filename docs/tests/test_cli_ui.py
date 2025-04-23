import asyncio
from utils.cli_ui import PulseCLIUI

async def test():
    # Initialize the CLI UI without an agent
    cli_ui = PulseCLIUI()
    
    # Print a message
    print("CLI UI initialized successfully")
    print("Press Ctrl+C to exit")
    
    # Try to run the CLI UI
    try:
        await cli_ui.run()
    except Exception as e:
        print(f"Error running CLI UI: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\nExiting...")
