"""
Unit tests for the TimezoneConverter class
"""

import unittest
import sys
import os
from pathlib import Path
import datetime
import pytz

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parents[2])
sys.path.append(project_root)

from utils.timezone_utils import TimezoneConverter

class TestTimezoneConverter(unittest.TestCase):
    """Test cases for the TimezoneConverter class"""

    def setUp(self):
        """Set up the test environment"""
        self.converter = TimezoneConverter()

    def test_get_current_time(self):
        """Test getting the current time"""
        time_str = self.converter.get_current_time()
        self.assertIsNotNone(time_str)
        self.assertIsInstance(time_str, str)
        # Time should be in format like "10:30 PM"
        self.assertRegex(time_str, r'\d{1,2}:\d{2} [AP]M')

    def test_get_current_date(self):
        """Test getting the current date"""
        date_str = self.converter.get_current_date()
        self.assertIsNotNone(date_str)
        self.assertIsInstance(date_str, str)
        # Date should include day of week and month
        self.assertTrue(any(day in date_str for day in
                           ["Monday", "Tuesday", "Wednesday", "Thursday",
                            "Friday", "Saturday", "Sunday"]))
        self.assertTrue(any(month in date_str for month in
                           ["January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]))

    def test_get_time_in_timezone_valid_city(self):
        """Test getting time in a valid city timezone"""
        time_str, timezone_name, error = self.converter.get_time_in_timezone("Tokyo")
        self.assertIsNone(error)
        self.assertIsNotNone(time_str)
        self.assertIsNotNone(timezone_name)
        self.assertEqual(timezone_name, "Japan Standard Time (JST)")
        # Time should include UTC offset
        self.assertIn("UTC+09:00", time_str)

    def test_get_time_in_timezone_valid_country(self):
        """Test getting time in a valid country timezone"""
        time_str, timezone_name, error = self.converter.get_time_in_timezone("Japan")
        self.assertIsNone(error)
        self.assertIsNotNone(time_str)
        self.assertIsNotNone(timezone_name)
        # Time should include UTC offset
        self.assertIn("UTC+09:00", time_str)

    def test_get_time_in_timezone_invalid_location(self):
        """Test getting time in an invalid location"""
        time_str, timezone_name, error = self.converter.get_time_in_timezone("NonExistentPlace")
        self.assertIsNone(time_str)
        self.assertIsNone(timezone_name)
        self.assertIsNotNone(error)
        self.assertIn("Could not find timezone", error)

    def test_timezone_differences(self):
        """Test that different timezones return different times"""
        # Get times for locations in different timezones
        tokyo_result = self.converter.get_time_in_timezone("Tokyo")
        new_york_result = self.converter.get_time_in_timezone("New York")
        london_result = self.converter.get_time_in_timezone("London")

        # Extract just the time part (without UTC offset)
        tokyo_time = tokyo_result[0].split(" UTC")[0] if tokyo_result[0] else None
        new_york_time = new_york_result[0].split(" UTC")[0] if new_york_result[0] else None
        london_time = london_result[0].split(" UTC")[0] if london_result[0] else None

        # Verify that the times are different
        if tokyo_time and new_york_time:
            self.assertNotEqual(tokyo_time, new_york_time)
        if tokyo_time and london_time:
            self.assertNotEqual(tokyo_time, london_time)
        if new_york_time and london_time:
            self.assertNotEqual(new_york_time, london_time)

    def test_friendly_timezone_names(self):
        """Test that friendly timezone names are returned correctly"""
        # Test a few common timezones
        self.assertEqual(self.converter._get_friendly_timezone_name("America/New_York"), "Eastern Time (ET)")
        self.assertEqual(self.converter._get_friendly_timezone_name("Europe/London"), "Greenwich Mean Time (GMT)")
        self.assertEqual(self.converter._get_friendly_timezone_name("Asia/Tokyo"), "Japan Standard Time (JST)")

        # Test a timezone not in the mapping
        self.assertEqual(self.converter._get_friendly_timezone_name("Africa/Cairo"), "Africa/Cairo".replace("_", " "))

if __name__ == '__main__':
    unittest.main()
