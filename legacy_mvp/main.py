#!/usr/bin/env python3
"""
General Pulse - AI Personal Workflow Ops Assistant
Main entry point for running the agent
"""

import os
import sys
import argparse
import logging
import structlog as structlog_package
from skills.agent import Agent
from utils.logger import setup_logger
from dotenv import load_dotenv

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="General Pulse - AI Personal Workflow Ops Assistant")
    parser.add_argument("--simulate", action="store_true", help="Run with simulated AI responses (for testing)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def setup_logging(debug=False):
    """Configure logging"""
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logger(log_level)

def check_dependencies():
    """
    Check if required dependencies are installed and provide helpful error messages
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    logger = structlog_package.get_logger("dependency_check")
    missing_deps = []
    
    # Check for required dependencies
    try:
        import prompt_toolkit
    except ImportError:
        missing_deps.append("prompt_toolkit")
    
    try:
        import structlog
    except ImportError:
        missing_deps.append("structlog")
    
    # Optional but recommended dependencies
    recommended_deps = []
    try:
        import transformers
    except ImportError:
        recommended_deps.append("transformers")
    
    try:
        import torch
    except ImportError:
        recommended_deps.append("torch")
    
    try:
        import openrouter
    except ImportError:
        recommended_deps.append("openrouter")
    
    try:
        import github
    except ImportError:
        recommended_deps.append("PyGithub")
    
    try:
        import ollama
    except ImportError:
        recommended_deps.append("ollama")
    
    # Report missing dependencies
    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        print(f"Error: Missing required dependencies: {', '.join(missing_deps)}")
        print("Please install them with: pip install " + " ".join(missing_deps))
        return False
    
    if recommended_deps:
        logger.warning(f"Missing recommended dependencies: {', '.join(recommended_deps)}")
        print(f"Warning: Missing recommended dependencies: {', '.join(recommended_deps)}")
        print("Some features may be limited. Install them with: pip install " + " ".join(recommended_deps))
    
    return True

def check_environment():
    """
    Check if required environment variables are set
    
    Returns:
        bool: True if all required env vars are set, False otherwise
    """
    logger = structlog_package.get_logger("env_check")
    
    # Load environment variables
    load_dotenv()
    
    # Check for API keys
    api_keys = {
        "OPENROUTER_API_KEY": "OpenRouter",
        "GITHUB_TOKEN": "GitHub"
    }
    
    missing_keys = [key for key, name in api_keys.items() if not os.getenv(key)]
    
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
        print(f"Warning: Missing API keys for: {', '.join([api_keys[key] for key in missing_keys])}")
        print("Some functionality will be limited. Add these keys to your .env file.")
    
    return True

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.debug)
    
    # Get a logger for the main function
    logger = structlog_package.get_logger("main")
    
    # Check dependencies and environment
    deps_ok = check_dependencies()
    env_ok = check_environment()
    
    # Print banner
    print_banner()
    
    # Use simulation mode if explicitly requested or if dependencies are missing
    simulate_mode = args.simulate
    
    # Create and run the agent
    try:
        agent = Agent(simulate_responses=simulate_mode)
        agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped by keyboard interrupt")
        print("\nExiting General Pulse...")
    except Exception as e:
        logger.error(f"Fatal error in agent execution: {str(e)}", exc_info=True)
        print(f"\nFatal error: {str(e)}")
        print("See logs for details.")
        return 1
    
    logger.info("Agent exited successfully")
    return 0

def print_banner():
    """Print a welcome banner"""
    banner = """
  ____                           _   ____        _          
 / ___| ___ _ __   ___ _ __ __ _| | |  _ \ _   _| |___  ___ 
| |  _ / _ \ '_ \ / _ \ '__/ _` | | | |_) | | | | / __|/ _ \\
| |_| |  __/ | | |  __/ | | (_| | | |  __/| |_| | \__ \  __/
 \____|\___|_| |_|\___|_|  \__,_|_| |_|    \__,_|_|___/\___|
                                                             
  AI Personal Workflow Ops Assistant
  """
    print(banner)
    
if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nExiting General Pulse...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
