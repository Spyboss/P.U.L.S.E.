"""
Simple test script to verify the shutdown process
"""

import asyncio
import sys
import traceback
import structlog
from skills.pulse_agent import PulseAgent

# Configure logger
logger = structlog.get_logger("test_shutdown")

async def main():
    """Main function"""
    print("Initializing Pulse Agent...")
    agent = PulseAgent(user_id="test_user", simulate_responses=True)
    print("Pulse Agent initialized.")
    
    print("Testing shutdown...")
    try:
        agent.shutdown()
        print("Shutdown successful!")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Error during shutdown: {str(e)}")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Unhandled exception: {str(e)}")
        sys.exit(1)
