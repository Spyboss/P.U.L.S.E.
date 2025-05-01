#!/usr/bin/env python3
"""
P.U.L.S.E. - Prime Uminda's Learning System Engine
Your loyal AI companion
Main application entry point
"""

import sys
import asyncio
import argparse
import signal
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Import components
from pulse_core import PulseCore
from utils.optimization import optimize_for_hardware, get_system_status
from utils.cli_ui import PulseCLIUI
from utils.unified_logger import get_logger, configure_logging

# Configure unified logging system
configure_logging(log_file="logs/pulse.log")

# Get logger from unified logger module
logger = get_logger("pulse")

# Load environment variables
load_dotenv()

# Global variables
pulse_core = None
running = True

def signal_handler(sig, frame):  # pylint: disable=unused-argument
    """Handle interrupt signals (sig and frame params required by signal module)"""
    global running, pulse_core
    try:
        print("\nShutting down Pulse...")
        running = False

        # Shutdown the pulse core if it exists
        if pulse_core:
            try:
                asyncio.create_task(pulse_core.shutdown())
                print("Pulse Core shutdown initiated.")
            except Exception as e:
                logger.error(f"Error shutting down Pulse Core: {str(e)}")
                logger.error(traceback.format_exc())
                print(f"Error shutting down Pulse Core: {str(e)}")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Shutdown error: {str(e)}")
    finally:
        print("Shutdown complete.")

async def main():
    """Main application entry point"""
    global pulse_core

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="P.U.L.S.E. - Prime Uminda's Learning System Engine")
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
╭──────────────────────────────────────────────────────────╮
│                                                          │
│              INITIALIZING P.U.L.S.E.                     │
│         Prime Uminda's Learning System Engine            │
│                                                          │
╰──────────────────────────────────────────────────────────╯
        """)

        # Print startup progress
        print("┌─ Startup Progress ───────────────────────────────────────┐")
        print("│ [1/6] Loading environment...                             │")

    # Apply hardware optimizations
    if debug_mode:
        print("DEBUG: Applying hardware optimizations...")
    else:
        print("│ [2/6] Applying hardware optimizations...                   │")
    optimize_for_hardware()

    # Print system status
    if debug_mode:
        print("DEBUG: Getting system status...")
    else:
        print("│ [3/6] Checking system status...                            │")
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
        print(f"│ ✓ Memory: {memory_str} ({system_status['memory']['percent']}%)          │")
        print(f"│ ✓ CPU: {system_status['cpu']['percent']}% used                                  │")

    # Initialize Pulse Core
    try:
        if debug_mode:
            print("DEBUG: About to initialize Pulse Core...")
        else:
            print("│ [4/6] Initializing AI components...                        │")

        pulse_core = PulseCore(
            user_id=args.user,
            debug_mode=args.debug
        )

        if debug_mode:
            print("DEBUG: Pulse Core initialized successfully!")
        else:
            print("│ ✓ AI components initialized successfully                   │")

        logger.info("Pulse Core initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize Pulse Core: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"Failed to initialize Pulse Core: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

    # Initialize CLI UI
    try:
        if debug_mode:
            print("DEBUG: Initializing CLI UI...")
        else:
            print("│ [5/6] Initializing CLI UI...                              │")

        # Create a more complete adapter for CLI UI to work with PulseCore
        class PulseCoreAdapter:
            def __init__(self, core):
                self.core = core
                # Add required attributes for CLI UI
                self.model_orchestrator = core.model_orchestrator
                self.router = core.router
                self.memory_manager = core.memory_manager
                self.history_manager = core.history_manager
                self.charisma_engine = core.charisma_engine

            async def process_input(self, user_input):
                return await self.core.process_input(user_input)

            def shutdown(self):
                asyncio.create_task(self.core.shutdown())

        adapter = PulseCoreAdapter(pulse_core)
        cli_ui = PulseCLIUI(agent=adapter)

        if debug_mode:
            print("DEBUG: CLI UI initialized successfully!")
        else:
            print("│ ✓ CLI UI initialized successfully                         │")
            print("│ [6/6] Loading welcome message...                          │")
            print("└─────────────────────────────────────────────────────────────┘")

            # Print welcome message
            print_welcome_message()

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

                response = await pulse_core.process_input(user_input)

                if debug_mode:
                    print(f"DEBUG: Got response from core")

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
    if pulse_core:
        try:
            await pulse_core.shutdown()
            logger.info("Pulse Core shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Pulse Core: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Error shutting down Pulse Core: {str(e)}")

    return 0

def print_welcome_message():
    """Print welcome message"""
    # Get current time to determine greeting
    current_hour = datetime.now().hour
    greeting = "Good morning"
    if 12 <= current_hour < 18:
        greeting = "Good afternoon"
    elif current_hour >= 18:
        greeting = "Good evening"

    # In a real implementation, you would get actual pending tasks
    # For now, we'll use a placeholder
    pending_tasks = 3

    welcome_message = f"""
    ╭──────────────────────────────────────────╮
    │ Prime Uminda's Learning System Engine    │
    │ ver 2.1 | Memory: 6.1/8GB | CPU: 55%     │
    ╰──────────────────────────────────────────╯

    {greeting} Uminda. P.U.L.S.E. systems nominal.
    {pending_tasks} pending tasks. Shall we begin?

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

    You can also just chat with me naturally! Try asking me a question
    like "what's the latest in AI?" or "help me with my project".

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
            if pulse_core:
                try:
                    asyncio.run(pulse_core.shutdown())
                    print("Pulse Core shutdown complete.")
                except Exception as e:
                    logger.error(f"Error shutting down Pulse Core: {str(e)}")
                    logger.error(traceback.format_exc())
                    print(f"Error shutting down Pulse Core: {str(e)}")
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
