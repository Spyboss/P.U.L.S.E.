#!/usr/bin/env python
"""
Test script for the datetime handler
"""

import os
import sys
import structlog
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_datetime")

# Make sure we can import from the package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Mock the model interface for testing  
class MockModelInterface:
    def __init__(self):
        self.simulate_responses = False
        
def test_datetime_handler():
    """Test the datetime handler directly"""
    from utils.intent_handler import IntentHandler
    
    # Create a mock model interface
    model_interface = MockModelInterface()
    
    # Create the intent handler
    handler = IntentHandler(model_interface)
    
    # Test cases
    test_cases = [
        "What time is it?",
        "What's today's date?",
        "What is the date today?",
        "What time is it in Tokyo?",
        "What time is it in London?",
        "What time is it in New York?",
        "What time is it in Paris?",
        "What time is it in Berlin?",
        "What time is it in Sydney?",
        "What's the current time in Tokyo, Japan?",
        "Tell me the time in India"
    ]
    
    # Test each case
    for query in test_cases:
        print(f"\nQuery: '{query}'")
        result = handler._handle_datetime_intent(query)
        print(f"Result: {result}")
    
    print("\nTest completed successfully!")
    return True

if __name__ == "__main__":
    test_datetime_handler() 