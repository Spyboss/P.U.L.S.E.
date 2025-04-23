# Timezone Feature Documentation

## Overview

The timezone feature in General Pulse allows users to query the current time in different locations around the world. This feature has been enhanced to properly handle timezone conversions and provide accurate time information.

## Implementation Details

### Intent Classification

The system uses both DistilBERT and keyword-based classification to identify time-related queries. When a user asks about the time in a specific location, the system:

1. Classifies the intent as "time"
2. Extracts the location from the query
3. Maps the location to a timezone
4. Determines if it's a date query or just a time query
5. Routes the query to the appropriate model

### Timezone Mapping

The system includes a comprehensive mapping of locations to their corresponding timezones:

```python
timezone_map = {
    "local": "local",
    "new york": "EST",
    "los angeles": "PST",
    "london": "GMT",
    "paris": "CET",
    "tokyo": "JST",
    "sydney": "AEST",
    "beijing": "CST",
    "moscow": "MSK",
    "dubai": "GST",
    "singapore": "SGT",
    "hong kong": "HKT",
    "berlin": "CET",
    "rome": "CET",
    "madrid": "CET",
    "toronto": "EST",
    "vancouver": "PST",
    "chicago": "CST",
    "mexico city": "CST",
    "sao paulo": "BRT",
    "johannesburg": "SAST",
    "cairo": "EET",
    "istanbul": "TRT",
    "mumbai": "IST",
    "delhi": "IST",
    "bangkok": "ICT",
    "jakarta": "WIB",
    "seoul": "KST",
    "auckland": "NZST"
}
```

If a location is not found in the map, the system attempts to find a partial match. If no match is found, it defaults to UTC.

### Model Routing

Time queries can be handled by any model, but the system prefers:
- Gemini in online mode
- Phi in offline mode

The model selection is based on the current system status and the availability of models.

## Usage Examples

Users can ask about the time in different ways:

- "What time is it in Tokyo?"
- "What's the current time in London?"
- "Tell me the time in New York"
- "What day is it in Sydney?"
- "What's the date in Paris?"

## Error Handling

If the system cannot determine the timezone for a location, it defaults to UTC. The system also handles cases where the location is misspelled or not recognized by looking for partial matches in the timezone map.

## Future Improvements

Planned improvements for the timezone feature include:

1. Adding more locations to the timezone map
2. Implementing daylight saving time adjustments
3. Supporting relative time queries (e.g., "What time will it be in Tokyo in 3 hours?")
4. Adding support for timezone abbreviations (e.g., "What time is it in EST?")
5. Improving location extraction from natural language queries
