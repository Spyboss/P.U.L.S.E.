"""
Test script for P.U.L.S.E. Core
"""

import asyncio
import logging
import structlog
from pulse_core import PulseCore

# Configure logging
logging.basicConfig(level=logging.DEBUG)
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

async def main():
    print("Initializing P.U.L.S.E. Core...")
    core = PulseCore(user_id="test_user", debug_mode=True)
    print("P.U.L.S.E. Core initialized!")

    print("\nTesting 'ask code' command...")
    code_response = await core.process_input("ask code how to implement a binary search tree in Python")
    print(f"\nResponse to 'ask code' command: {code_response[:100]}...")

    print("\nTesting general query...")
    general_response = await core.process_input("Hello, how are you today?")
    print(f"\nResponse to general query: {general_response[:100]}...")

    print("\nShutting down P.U.L.S.E. Core...")
    await core.shutdown()
    print("P.U.L.S.E. Core shutdown complete!")

if __name__ == "__main__":
    asyncio.run(main())
