"""
Timezone Utilities for General Pulse
Provides timezone conversion and formatting
"""

import datetime
import pytz
import structlog
from typing import Optional, Tuple

# Initialize logger
logger = structlog.get_logger("timezone_utils")

class TimezoneConverter:
    """
    Utility for timezone conversion and formatting
    """

    def __init__(self):
        """Initialize the timezone converter"""
        self.logger = structlog.get_logger("timezone_utils")

        # Common city to timezone mappings
        self.city_to_timezone = {
            # North America
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "toronto": "America/Toronto",
            "vancouver": "America/Vancouver",
            "mexico city": "America/Mexico_City",

            # Europe
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid",
            "amsterdam": "Europe/Amsterdam",
            "zurich": "Europe/Zurich",
            "moscow": "Europe/Moscow",

            # Asia
            "tokyo": "Asia/Tokyo",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "hong kong": "Asia/Hong_Kong",
            "singapore": "Asia/Singapore",
            "seoul": "Asia/Seoul",
            "dubai": "Asia/Dubai",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "bangkok": "Asia/Bangkok",

            # Australia/Pacific
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "auckland": "Pacific/Auckland",

            # South America
            "sao paulo": "America/Sao_Paulo",
            "buenos aires": "America/Argentina/Buenos_Aires",

            # Africa
            "johannesburg": "Africa/Johannesburg",
            "cairo": "Africa/Cairo",
            "lagos": "Africa/Lagos"
        }

        # Country to timezone mappings (for fallback)
        self.country_to_timezone = {
            "usa": "America/New_York",
            "united states": "America/New_York",
            "uk": "Europe/London",
            "united kingdom": "Europe/London",
            "england": "Europe/London",
            "france": "Europe/Paris",
            "germany": "Europe/Berlin",
            "italy": "Europe/Rome",
            "spain": "Europe/Madrid",
            "japan": "Asia/Tokyo",
            "china": "Asia/Shanghai",
            "india": "Asia/Kolkata",
            "australia": "Australia/Sydney",
            "canada": "America/Toronto",
            "brazil": "America/Sao_Paulo",
            "russia": "Europe/Moscow",
            "south korea": "Asia/Seoul",
            "mexico": "America/Mexico_City"
        }

        # Get the local timezone
        self.local_timezone = datetime.datetime.now().astimezone().tzinfo

        self.logger.info("Timezone converter initialized")

    def get_time_in_timezone(self, location: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get the current time in a specific timezone

        Args:
            location: Location name (city or country)

        Returns:
            Tuple of (formatted time, timezone name, error message if any)
        """
        # Normalize location
        location = location.lower().strip()

        # Try to find the timezone for this location
        timezone_str = self.city_to_timezone.get(location)

        # If not found in cities, try countries
        if not timezone_str:
            timezone_str = self.country_to_timezone.get(location)

        # If still not found, try to find a partial match
        if not timezone_str:
            for city, tz in self.city_to_timezone.items():
                if location in city or city in location:
                    timezone_str = tz
                    break

            if not timezone_str:
                for country, tz in self.country_to_timezone.items():
                    if location in country or country in location:
                        timezone_str = tz
                        break

        # If still not found, try to use the location as a timezone directly
        if not timezone_str:
            try:
                # Try to find a timezone that contains the location name
                for tz in pytz.all_timezones:
                    if location.replace(" ", "_") in tz.lower():
                        timezone_str = tz
                        break
            except Exception as e:
                self.logger.error(f"Error finding timezone for {location}: {str(e)}")

        # If we found a timezone, get the current time in that timezone
        if timezone_str:
            try:
                # Get the timezone object
                tz = pytz.timezone(timezone_str)

                # Get current UTC time and convert to the target timezone
                utc_now = datetime.datetime.now(pytz.UTC)
                local_time = utc_now.astimezone(tz)

                # Format the time
                formatted_time = local_time.strftime("%I:%M %p")
                timezone_name = self._get_friendly_timezone_name(timezone_str)

                # Add the UTC offset for clarity
                utc_offset = local_time.strftime("%z")
                formatted_offset = f"UTC{utc_offset[:3]}:{utc_offset[3:]}" if utc_offset else ""

                # Add timezone info to the formatted time
                formatted_time_with_tz = f"{formatted_time} {formatted_offset}"

                self.logger.info(f"Converted time for {location} ({timezone_str}): {formatted_time_with_tz}")

                return formatted_time_with_tz, timezone_name, None
            except Exception as e:
                self.logger.error(f"Error getting time for timezone {timezone_str}: {str(e)}")
                return None, None, f"Error getting time for {location}: {str(e)}"

        # If we couldn't find a timezone, return an error
        return None, None, f"Could not find timezone for {location}"

    def get_current_time(self) -> str:
        """
        Get the current local time

        Returns:
            Formatted current time
        """
        # Get current time with timezone info
        current_time = datetime.datetime.now().astimezone()
        return current_time.strftime("%I:%M %p")

    def get_current_date(self) -> str:
        """
        Get the current local date

        Returns:
            Formatted current date
        """
        # Get current date with timezone info
        current_date = datetime.datetime.now().astimezone()
        return current_date.strftime("%A, %B %d, %Y")

    def _get_friendly_timezone_name(self, timezone_str: str) -> str:
        """
        Get a friendly name for a timezone

        Args:
            timezone_str: Timezone string (e.g. 'America/New_York')

        Returns:
            Friendly timezone name (e.g. 'Eastern Time (ET)')
        """
        # Common timezone abbreviations
        timezone_abbreviations = {
            "America/New_York": "Eastern Time (ET)",
            "America/Chicago": "Central Time (CT)",
            "America/Denver": "Mountain Time (MT)",
            "America/Los_Angeles": "Pacific Time (PT)",
            "America/Anchorage": "Alaska Time (AKT)",
            "America/Honolulu": "Hawaii Time (HT)",
            "America/Toronto": "Eastern Time (ET)",
            "America/Vancouver": "Pacific Time (PT)",
            "Europe/London": "Greenwich Mean Time (GMT)",
            "Europe/Paris": "Central European Time (CET)",
            "Europe/Berlin": "Central European Time (CET)",
            "Europe/Moscow": "Moscow Time (MSK)",
            "Asia/Tokyo": "Japan Standard Time (JST)",
            "Asia/Shanghai": "China Standard Time (CST)",
            "Asia/Kolkata": "India Standard Time (IST)",
            "Asia/Dubai": "Gulf Standard Time (GST)",
            "Australia/Sydney": "Australian Eastern Time (AET)",
            "Pacific/Auckland": "New Zealand Standard Time (NZST)"
        }

        return timezone_abbreviations.get(timezone_str, timezone_str.replace("_", " "))
