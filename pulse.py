#!/usr/bin/env python3
"""
General Pulse - Your loyal AI companion
Main application entry point
"""

import os
import sys
import asyncio
import argparse
import signal
import traceback
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

# Import components
from skills.pulse_agent import PulseAgent
from utils.optimization import optimize_for_hardware, get_system_status
from utils.cli_ui import PulseCLIUI
from utils.logger import get_logger

# Get logger from centralized logger module
logger = get_logger("pulse")

# Load environment variables
load_dotenv()

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

async def main():
    """Main application entry point"""
    global pulse_agent

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="General Pulse - Your loyal AI companion")
    parser.add_argument("--simulate", action="store_true", help="Simulate AI responses (for testing)")
    parser.add_argument("--user", type=str, default="uminda", help="User identifier")
    parser.add_argument("--memory", type=str, default="pulse_memory.db", help="Path to memory database")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Enable debug mode if requested
    debug_mode = args.debug
    if debug_mode:
        print("DEBUG MODE ENABLED")

    # Print a beautiful initialization header
    if not debug_mode:
        print("""
+----------------------------------------------------------+
|                                                          |
|              INITIALIZING GENERAL PULSE                  |
|                                                          |
+----------------------------------------------------------+
        """)

    # Apply hardware optimizations
    if debug_mode:
        print("DEBUG: Applying hardware optimizations...")
    else:
        print("Applying hardware optimizations...")
    optimize_for_hardware()

    # Print system status
    if debug_mode:
        print("DEBUG: Getting system status...")
    else:
        print("Checking system status...")
    system_status = get_system_status()

    # Format memory and CPU values for display
    try:
        memory_used = float(system_status['memory']['used'].split('GB')[0])
        memory_total = float(system_status['memory']['total'].split('GB')[0]) if 'total' in system_status['memory'] else memory_used / (system_status['memory']['percent'] / 100)
        memory_str = f"{memory_used:.2f}GB / {memory_total:.2f}GB"
    except:
        memory_str = system_status['memory']['used']

    # Log system status
    logger.info(
        "System status",
        memory_used=system_status["memory"]["used"],
        memory_percent=system_status["memory"]["percent"],
        disk_used=system_status["disk"]["used"],
        disk_percent=system_status["disk"]["percent"],
        cpu_percent=system_status["cpu"]["percent"]
    )

    # Print formatted system status
    if debug_mode:
        print(f"DEBUG: System status - Memory: {system_status['memory']['percent']}%, CPU: {system_status['cpu']['percent']}%")
    else:
        print(f"Memory: {memory_str} ({system_status['memory']['percent']}%)")
        print(f"CPU: {system_status['cpu']['percent']}% used")

    # Initialize Pulse Agent
    try:
        if debug_mode:
            print("DEBUG: About to initialize Pulse Agent...")
        else:
            print("Initializing AI components...")

        pulse_agent = PulseAgent(
            user_id=args.user,
            memory_path=args.memory,
            simulate_responses=args.simulate
        )

        if debug_mode:
            print("DEBUG: Pulse Agent initialized successfully!")
        else:
            print("AI components initialized successfully!")

        logger.info("Pulse Agent initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize Pulse Agent: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"Failed to initialize Pulse Agent: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

    # Print welcome message
    print_welcome_message()

    # Initialize CLI UI
    try:
        if debug_mode:
            print("DEBUG: Initializing CLI UI...")
        else:
            print("Initializing CLI UI...")

        cli_ui = PulseCLIUI(agent=pulse_agent)

        if debug_mode:
            print("DEBUG: CLI UI initialized successfully!")
        else:
            print("CLI UI initialized successfully!")

        logger.info("CLI UI initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize CLI UI: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"Failed to initialize CLI UI: {str(e)}")
        logger.error(traceback.format_exc())

        # Fall back to basic interaction loop
        print("Falling back to basic interaction loop...")

        # Main interaction loop (fallback)
        global running
        while running:
            try:
                # Get user input
                user_input = input("\n> ")

                # Check for exit command
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye! Have a great day!")
                    break

                # Process input
                if debug_mode:
                    print(f"DEBUG: Processing input: {user_input}")

                response = await pulse_agent.process_input(user_input)

                if debug_mode:
                    print(f"DEBUG: Got response from agent")

                # Print response
                print(f"\n{response}")

            except KeyboardInterrupt:
                print("\nShutting down Pulse...")
                break

            except Exception as e:
                print(f"\nERROR in main loop: {str(e)}")
                print(traceback.format_exc())
                logger.error(f"Error in main loop: {str(e)}")
                logger.error(traceback.format_exc())
                print(f"\nSorry, I encountered an error: {str(e)}")

        return 0

    # Run the CLI UI
    try:
        await cli_ui.run()
    except Exception as e:
        print(f"\nERROR in CLI UI: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"Error in CLI UI: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\nSorry, I encountered an error in the CLI UI: {str(e)}")

    # Shutdown
    if pulse_agent:
        try:
            pulse_agent.shutdown()
            logger.info("Pulse Agent shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Pulse Agent: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Error shutting down Pulse Agent: {str(e)}")

    return 0

def print_welcome_message():
    """Print welcome message"""
    welcome_message = """
    +----------------------------------------------------------+
    |                                                          |
    |                     GENERAL PULSE                        |
    |                                                          |
    |              Your loyal AI companion                     |
    |                                                          |
    +----------------------------------------------------------+

    Hey there, brdh! I'm Pulse, your loyal AI companion.
    I'm here to help you with coding, freelancing, and leveling up in life!

    The CLI UI is now starting. Type 'help' to see available commands.

    Some useful commands:
    - status: Check system status
    - ollama status: Check Ollama status
    - ollama on: Start Ollama service and enable offline mode
    - ollama off: Stop Ollama service and disable offline mode
    - test intent <query>: Test intent classification
    - test <model> <query>: Test a specific model
    - enable offline mode: Switch to offline mode using Ollama
    - disable offline mode: Switch back to online mode

    You can also just chat with me naturally! Try saying "hi bruv!" or
    asking me a question like "what's the latest in AI?"

    Let's build something epic together!
    """
    print(welcome_message)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the main function
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
