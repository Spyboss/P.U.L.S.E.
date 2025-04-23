"""
Test script to verify the shutdown process
"""

import asyncio
import signal
import sys
import time
import traceback
import structlog
from skills.pulse_agent import PulseAgent

# Configure logger
logger = structlog.get_logger("test_shutdown")

# Global variables
pulse_agent = None
running = True

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    global running, pulse_agent
    try:
        print("\nShutting down Pulse...")
        running = False
        
        # Shutdown the pulse agent if it exists
        if pulse_agent:
            try:
                pulse_agent.shutdown()
                print("Pulse Agent shutdown complete.")
            except Exception as e:
                logger.error(f"Error shutting down Pulse Agent: {str(e)}")
                logger.error(traceback.format_exc())
                print(f"Error shutting down Pulse Agent: {str(e)}")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Shutdown error: {str(e)}")
    finally:
        print("Shutdown complete.")
        sys.exit(0)

async def main():
    """Main function"""
    global pulse_agent, running
    
    print("Initializing Pulse Agent...")
    pulse_agent = PulseAgent(user_id="test_user", simulate_responses=True)
    print("Pulse Agent initialized.")
    
    print("Press Ctrl+C to test shutdown...")
    
    # Wait for Ctrl+C
    while running:
        await asyncio.sleep(1)
    
    return 0

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        try:
            print("\nShutting down Pulse...")
            if pulse_agent:
                try:
                    pulse_agent.shutdown()
                    print("Pulse Agent shutdown complete.")
                except Exception as e:
                    logger.error(f"Error shutting down Pulse Agent: {str(e)}")
                    logger.error(traceback.format_exc())
                    print(f"Error shutting down Pulse Agent: {str(e)}")
            print("Shutdown complete.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Shutdown error: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Shutdown error: {str(e)}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Unhandled exception: {str(e)}")
        sys.exit(1)
