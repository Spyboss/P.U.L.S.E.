"""
Test script for timezone conversion
"""

import datetime
import pytz

def test_timezone_conversion():
    """Test timezone conversion"""
    print("Testing timezone conversion...")
    
    # Get current UTC time
    utc_now = datetime.datetime.now(pytz.UTC)
    print(f"Current UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Convert to Tokyo time
    tokyo_tz = pytz.timezone("Asia/Tokyo")
    tokyo_time = utc_now.astimezone(tokyo_tz)
    print(f"Tokyo time: {tokyo_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+9)")
    
    # Convert to London time
    london_tz = pytz.timezone("Europe/London")
    london_time = utc_now.astimezone(london_tz)
    print(f"London time: {london_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+1/BST)")
    
    # Convert to New York time
    ny_tz = pytz.timezone("America/New_York")
    ny_time = utc_now.astimezone(ny_tz)
    print(f"New York time: {ny_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC-4/EDT)")
    
    # Get local time
    local_time = datetime.datetime.now().astimezone()
    print(f"Local time: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

if __name__ == "__main__":
    test_timezone_conversion()
