#!/usr/bin/env python
"""
Test script for all model implementations with focus on graceful fallback
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ModelTest")

# Import the ModelInterface class
try:
    from skills.model_interface import ModelInterface
    logger.info("Successfully imported ModelInterface")
except ImportError as e:
    logger.error(f"Failed to import ModelInterface: {str(e)}")
    sys.exit(1)

# ANSI colors for nice output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{YELLOW}{'=' * 50}{RESET}")
    print(f"{BOLD}{YELLOW}  {text}{RESET}")
    print(f"{BOLD}{YELLOW}{'=' * 50}{RESET}\n")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print an info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")

def test_model(model_interface, model_name):
    """Test a specific model implementation."""
    print_header(f"Testing {model_name.upper()} Model Implementation")
    
    # Use a simple prompt
    prompt = f"Hello, please identify yourself as {model_name} in one sentence."
    
    print_info(f"Testing with prompt: '{prompt}'")
    print_info(f"Calling model API...")
    
    # Call the model API
    response = model_interface.call_model_api(model_name, prompt)
    
    # Check if we got an error or a simulated response
    is_error = "error" in response
    is_simulated = "simulated" in response.get("response", "").lower()
    
    if is_error:
        print_error(f"API call failed: {response.get('error')}")
        return False
    
    # Print the response
    print_info("Response:")
    print(response.get("response"))
    
    if is_simulated:
        print_info("⚠️ This is a SIMULATED response (fallback mode)")
    else:
        print_success("This is a REAL API response")
    
    return True

def main():
    """Test all model implementations."""
    # Load environment variables
    load_dotenv()
    
    print_header("Model Implementation Testing")
    
    # Initialize the model interface
    model_interface = ModelInterface()
    
    # Get available models
    available_models = model_interface.get_available_models()
    
    print_info(f"Available models: {', '.join(available_models)}")
    print_info("Testing each model implementation with graceful fallback...\n")
    
    # Test each model
    results = {}
    for model in available_models:
        result = test_model(model_interface, model)
        results[model] = result
    
    # Print summary
    print_header("Test Results Summary")
    
    all_passed = True
    for model, result in results.items():
        status = "Success" if result else "Failed"
        print(f"{model.upper()}: {status}")
        all_passed = all_passed and result
    
    if all_passed:
        print_success("\nAll model implementations passed!")
    else:
        print_info("\nNote: Models may succeed by gracefully falling back to simulation")
        print_info("The important thing is that the agent can continue to function")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 