"""
Test script for the TimezoneConverter class
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.timezone_utils import TimezoneConverter

def test_timezone_converter():
    """Test the TimezoneConverter class"""
    print("Testing TimezoneConverter class...")
    
    # Create a TimezoneConverter instance
    converter = TimezoneConverter()
    
    # Test Tokyo
    print("\nTesting Tokyo:")
    time_str, timezone_name, error = converter.get_time_in_timezone("Tokyo")
    print(f"Time: {time_str}")
    print(f"Timezone: {timezone_name}")
    print(f"Error: {error}")
    
    # Test London
    print("\nTesting London:")
    time_str, timezone_name, error = converter.get_time_in_timezone("London")
    print(f"Time: {time_str}")
    print(f"Timezone: {timezone_name}")
    print(f"Error: {error}")
    
    # Test New York
    print("\nTesting New York:")
    time_str, timezone_name, error = converter.get_time_in_timezone("New York")
    print(f"Time: {time_str}")
    print(f"Timezone: {timezone_name}")
    print(f"Error: {error}")
    
    # Test current time
    print("\nTesting current time:")
    time_str = converter.get_current_time()
    print(f"Current time: {time_str}")
    
    # Test current date
    print("\nTesting current date:")
    date_str = converter.get_current_date()
    print(f"Current date: {date_str}")

if __name__ == "__main__":
    test_timezone_converter()
