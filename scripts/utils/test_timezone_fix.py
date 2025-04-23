#!/usr/bin/env python
"""
Test script to verify the timezone conversion functionality is working correctly.
This script tests multiple locations to ensure they return different times.
"""

import sys
import os
import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parents[2])
sys.path.append(project_root)

from utils.timezone_utils import TimezoneConverter

def test_timezone_conversion():
    """Test timezone conversion for multiple locations"""
    print("Testing timezone conversion for multiple locations...")
    
    # Create a TimezoneConverter instance
    converter = TimezoneConverter()
    
    # Test locations in different timezones
    locations = [
        "New York",
        "London",
        "Tokyo",
        "Sydney",
        "Los Angeles",
        "Berlin",
        "Dubai"
    ]
    
    results = {}
    
    # Get time for each location
    for location in locations:
        print(f"\nTesting {location}:")
        time_str, timezone_name, error = converter.get_time_in_timezone(location)
        
        if error:
            print(f"Error: {error}")
            results[location] = {"error": error}
        else:
            print(f"Time: {time_str}")
            print(f"Timezone: {timezone_name}")
            results[location] = {"time": time_str, "timezone": timezone_name}
    
    # Verify that times are different
    print("\nVerifying times are different:")
    times = [results[loc].get("time") for loc in locations if "time" in results.get(loc, {})]
    unique_times = set(times)
    
    print(f"Number of locations tested: {len(locations)}")
    print(f"Number of successful time conversions: {len(times)}")
    print(f"Number of unique times: {len(unique_times)}")
    
    if len(unique_times) < len(times) * 0.5:  # If less than half are unique, there's likely a problem
        print("WARNING: Many locations have the same time. This suggests the timezone conversion may not be working correctly.")
    else:
        print("SUCCESS: Different locations have different times. Timezone conversion appears to be working correctly.")
    
    # Print all times for comparison
    print("\nAll times:")
    for location in locations:
        if location in results and "time" in results[location]:
            print(f"{location}: {results[location]['time']}")

if __name__ == "__main__":
    test_timezone_conversion()
