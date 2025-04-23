# DateTime Functionality

General Pulse provides comprehensive date and time functionality, including timezone conversion, date calculations, and more.

## Current Implementation

The DateTime functionality in General Pulse includes:

- Current date and time information
- Timezone conversion between different locations
- Date calculations (days between dates, add/subtract time)
- Natural language date and time queries

## Usage Examples

### Basic Time Queries

```
what time is it?
what's the current time?
```

These commands return the current local time.

### Date Queries

```
what's today's date?
what day is it today?
what's the current date?
```

These commands return the current date.

### Timezone Conversion

```
what time is it in Tokyo?
what's the time in London?
time in New York
```

These commands convert the current time to the specified location's timezone.

### Time Difference Queries

```
what's the time difference between Tokyo and London?
how many hours between New York and Paris?
```

These commands calculate the time difference between two locations.

### Date Calculations

```
how many days until Christmas?
what date is 30 days from now?
what day of the week is July 4th?
```

These commands perform date calculations.

## Implementation Details

### Core Components

The DateTime functionality is implemented in the following files:

- `utils/timezone_utils.py` - Timezone conversion and date/time utilities
- `skills/agent.py` - Command handling for date/time queries
- `utils/command_parser.py` - Command pattern recognition for date/time queries

### TimezoneConverter Class

The `TimezoneConverter` class in `utils/timezone_utils.py` provides the core functionality:

```python
class TimezoneConverter:
    def __init__(self):
        self.logger = structlog.get_logger("timezone_converter")
        
    def get_current_time(self):
        """Get the current local time"""
        now = datetime.datetime.now()
        return now.strftime("%I:%M %p")
        
    def get_current_date(self):
        """Get the current date"""
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y")
        
    def get_time_in_timezone(self, location):
        """Get the current time in a specific location"""
        # Implementation details...
```

### Command Handling

Time and date queries are handled in the `_handle_time_query` method in `skills/agent.py`:

```python
def _handle_time_query(self, query):
    """Handle a time or date query directly"""
    query = query.lower()
    
    # Check for timezone queries with various patterns
    timezone_patterns = [
        r"time(?:\s+in|\s+at)\s+([a-zA-Z\s]+)",
        r"what(?:'s| is) the time in ([a-zA-Z\s]+)",
        r"what time is it in ([a-zA-Z\s]+)"
    ]
    
    for pattern in timezone_patterns:
        timezone_match = re.search(pattern, query)
        if timezone_match:
            location = timezone_match.group(1).strip()
            time_str, timezone_name, error = self.timezone_converter.get_time_in_timezone(location)
            
            if error:
                return f"I couldn't find the time in {location}. {error}"
            
            return f"The current time in {location.title()} is {time_str} ({timezone_name})."
    
    # Handle date queries
    if "date" in query:
        date_str = self.timezone_converter.get_current_date()
        return f"Today's date is {date_str}."
    
    # Handle time queries
    elif "time" in query or "what time" in query:
        time_str = self.timezone_converter.get_current_time()
        return f"The current time is {time_str}."
    
    # Handle general time/date queries
    else:
        date_str = self.timezone_converter.get_current_date()
        time_str = self.timezone_converter.get_current_time()
        return f"Today is {date_str} and the current time is {time_str}."
```

## Dependencies

The DateTime functionality relies on the following Python packages:

- `datetime` - Core Python datetime functionality
- `pytz` - Timezone database and conversion utilities
- `python-dateutil` - Advanced date manipulation utilities

## Future Enhancements

Planned enhancements for the DateTime functionality include:

- Date formatting options (different format standards)
- Calendar integration (view upcoming events)
- Reminders and scheduling
- Countdowns and timers
- Recurring date calculations (next Monday, third Thursday of month, etc.)
- Holiday detection and information
- Meeting time suggestions across timezones

For more details on planned enhancements, see the [Development Roadmap](../development/roadmap.md).
