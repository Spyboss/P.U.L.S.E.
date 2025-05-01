# P.U.L.S.E. Features Documentation

This document provides comprehensive information about the features of P.U.L.S.E. (Prime Uminda's Learning System Engine).

## Core Features

### Chat Persistence

P.U.L.S.E. implements enhanced chat persistence to maintain context across sessions:

- **Vector Database Storage** - Stores conversation embeddings for semantic search
- **SQLite Fallback** - Falls back to SQLite when vector database is unavailable
- **Context Windowing** - Maintains relevant context within token limits
- **Memory Prioritization** - Prioritizes important information for retention

### Vector Database

P.U.L.S.E. uses LanceDB for vector storage and semantic search:

- **Embedding Storage** - Stores embeddings for semantic search
- **Similarity Search** - Finds similar conversations and information
- **Metadata Storage** - Stores additional information with embeddings
- **Fallback Mechanism** - Falls back to SQLite when LanceDB is unavailable

### Model Routing

The Neural Router directs queries to the appropriate model:

- **Intent-Based Routing** - Routes based on detected intent
- **Hardware-Aware Routing** - Considers available hardware resources
- **Fallback Chains** - Implements fallback chains for model unavailability
- **Specialized Routing** - Routes specialized tasks to appropriate models

### Adaptive Router

The Adaptive Router adjusts to hardware capabilities:

- **Resource Monitoring** - Monitors CPU, RAM, and GPU usage
- **Dynamic Adjustment** - Adjusts model selection based on resource availability
- **Offline Detection** - Detects offline status and routes accordingly
- **Performance Optimization** - Optimizes for performance based on hardware

### DateTime Functionality

P.U.L.S.E. provides comprehensive date and time functionality:

- **Current Time** - Shows current time in various formats
- **Timezone Conversion** - Converts between timezones
- **Date Calculations** - Performs date arithmetic
- **Calendar Integration** - Integrates with calendar systems

#### Timezone Feature

The timezone feature in P.U.L.S.E. allows users to query the current time in different locations around the world. This feature has been enhanced to properly handle timezone conversions and provide accurate time information.

##### Implementation Details

###### Intent Classification

The system uses both DistilBERT and keyword-based classification to identify time-related queries. When a user asks about the time in a specific location, the system:

1. Classifies the intent as "time"
2. Extracts the location from the query
3. Maps the location to a timezone
4. Determines if it's a date query or just a time query
5. Routes the query to the appropriate model

###### Timezone Mapping

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

###### Usage Examples

Users can ask about the time in different ways:

- "What time is it in Tokyo?"
- "What's the current time in London?"
- "Tell me the time in New York"
- "What day is it in Sydney?"
- "What's the date in Paris?"

###### Error Handling

If the system cannot determine the timezone for a location, it defaults to UTC. The system also handles cases where the location is misspelled or not recognized by looking for partial matches in the timezone map.

###### Future Improvements

Planned improvements for the timezone feature include:

1. Adding more locations to the timezone map
2. Implementing daylight saving time adjustments
3. Supporting relative time queries (e.g., "What time will it be in Tokyo in 3 hours?")
4. Adding support for timezone abbreviations (e.g., "What time is it in EST?")
5. Improving location extraction from natural language queries

### Offline Mode

P.U.L.S.E. can operate offline using local models:

- **Ollama Integration** - Uses Ollama for local model inference
- **DistilBERT Intent Classification** - Uses DistilBERT for offline intent classification
- **Local Data Access** - Accesses locally cached data
- **Seamless Transition** - Transitions between online and offline modes

#### Local Models Implementation

P.U.L.S.E. uses Ollama to run local models when offline or when specified by the user:

1. **Phi-2** - Default local model for general queries
2. **Llama2** - Alternative local model for more complex queries
3. **Mistral** - Local version of Mistral for specialized tasks

##### Ollama Integration

The Ollama integration is implemented in `utils/ollama_client.py`:

```python
class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.logger = logging.getLogger("pulse.ollama")

    async def is_running(self):
        """Check if Ollama is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/tags", timeout=2) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.warning(f"Ollama not running: {str(e)}")
            return False

    async def generate(self, model="phi", prompt="", system="", max_tokens=1000):
        """Generate a response using Ollama"""
        if not await self.is_running():
            return {"success": False, "error": "Ollama not running"}

        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system,
                "options": {"num_predict": max_tokens}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/generate", json=payload, timeout=60) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"Ollama API error: {response.status}"}

                    result = await response.json()
                    return {"success": True, "response": result.get("response", "")}
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {str(e)}")
            return {"success": False, "error": str(e)}
```

##### Offline Mode Detection

The system automatically detects when it's offline and switches to local models:

```python
def _check_internet_connection(self):
    """Check if we have an internet connection"""
    try:
        # Try to connect to a reliable server
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return True
    except OSError:
        return False

async def toggle_offline_mode(self, enable=None):
    """Toggle offline mode"""
    if enable is not None:
        self.offline_mode = enable
    else:
        self.offline_mode = not self.offline_mode

    # Check if Ollama is running when enabling offline mode
    if self.offline_mode:
        ollama_running = await self.ollama_client.is_running()
        if not ollama_running:
            return {"success": False, "message": "Offline mode requires Ollama to be running"}

    return {"success": True, "offline_mode": self.offline_mode}
```

##### Model Fallback Chain

When offline, the system uses a fallback chain to ensure it can always respond:

1. Try Phi-2 model first (lightweight, fast)
2. If Phi-2 fails, try Llama2 (more capable but heavier)
3. If both fail, use a simple rule-based response system

```python
async def _call_local_model(self, prompt, system="", model="phi"):
    """Call a local model via Ollama"""
    # Try the requested model first
    result = await self.ollama_client.generate(
        model=model,
        prompt=prompt,
        system=system
    )

    # If the requested model fails, try fallbacks
    if not result["success"] and model != "phi":
        self.logger.warning(f"Falling back to phi model after {model} failed")
        result = await self.ollama_client.generate(
            model="phi",
            prompt=prompt,
            system=system
        )

    # If all models fail, return a simple response
    if not result["success"]:
        self.logger.error("All local models failed")
        return {"success": True, "response": "I'm sorry, I'm having trouble accessing my local models right now."}

    return result
```

##### Offline Intent Classification

When offline, P.U.L.S.E. uses a local DistilBERT model for intent classification:

```python
class LocalIntentClassifier:
    def __init__(self):
        self.model_path = "models/intent_classifier"
        self.tokenizer = None
        self.model = None
        self.labels = ["general", "debug", "code", "docs", "explain", "troubleshoot"]
        self.logger = logging.getLogger("pulse.local_intent")

    def load_model(self):
        """Load the local intent classification model"""
        try:
            if self.model is None:
                self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
                self.model = DistilBertForSequenceClassification.from_pretrained(self.model_path)
                self.logger.info("Loaded local intent classification model")
            return True
        except Exception as e:
            self.logger.error(f"Error loading local intent model: {str(e)}")
            return False

    def classify(self, text):
        """Classify the intent of a text using the local model"""
        if not self.load_model():
            return {"intent": "general", "confidence": 0.0}

        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)

            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=1)[0]
            max_prob, max_idx = torch.max(probabilities, dim=0)

            intent = self.labels[max_idx.item()]
            confidence = max_prob.item()

            return {"intent": intent, "confidence": confidence}
        except Exception as e:
            self.logger.error(f"Error classifying intent: {str(e)}")
            return {"intent": "general", "confidence": 0.0}
```

### Intent Classification

P.U.L.S.E. uses a sophisticated intent classification system:

- **MiniLM Classification** - Uses MiniLM for quick command classification
- **Mistral-Small Classification** - Uses Mistral-Small for complex intent classification
- **Hybrid Approach** - Combines both models for optimal performance
- **Confidence Scoring** - Scores classification confidence for decision making

## Advanced Features

### AI Commit Messages

P.U.L.S.E. can generate descriptive commit messages:

- **Diff Analysis** - Analyzes code diffs to understand changes
- **Context-Aware Generation** - Generates messages based on code context
- **Customizable Style** - Adjusts message style based on preferences
- **Integration with GitHub** - Integrates with GitHub workflow

### Bug Bounty Hunter

P.U.L.S.E. includes an AI-powered bug detection system (in development):

- **Code Scanning** - Scans code for potential bugs
- **Security Analysis** - Identifies security vulnerabilities
- **Performance Issues** - Detects performance bottlenecks
- **Fix Suggestions** - Suggests fixes for identified issues

## Personality System

### Charisma Engine

P.U.L.S.E. has an engaging personality:

- **Anime-Inspired Responses** - Incorporates anime-inspired elements
- **Sri Lankan Cultural References** - Includes Sri Lankan cultural elements
- **Adaptive Tone** - Adjusts tone based on context
- **Humor Integration** - Incorporates appropriate humor

### Self-Awareness Module

P.U.L.S.E. is self-aware of its status and capabilities:

- **System Monitoring** - Monitors its own performance
- **Resource Reporting** - Reports on resource usage
- **Capability Awareness** - Understands its own capabilities
- **Limitation Recognition** - Recognizes and communicates its limitations
