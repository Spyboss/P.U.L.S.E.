# P.U.L.S.E. Model Routing System

This document provides comprehensive information about the model routing system in P.U.L.S.E. (Prime Uminda's Learning System Engine).

## Overview

The Model Routing System in P.U.L.S.E. enables intelligent routing of user queries to the most appropriate AI model based on intent, context, and system status. This system ensures that each query is handled by the model best suited for the task, while providing rich context data to all models for more informed responses.

## Key Components

### Adaptive Neural Router

The Adaptive Neural Router is a key component that intelligently routes queries to the most appropriate AI model based on query intent, system resources, and other factors. It adapts to changing system conditions and user needs, ensuring the best possible response while managing system resources efficiently.

### Neural Intent Classification

The router uses neural networks to determine the intent of user queries:

- **Intent Detection**: Analyzes query text to determine the most likely intent
- **Confidence Scoring**: Assigns confidence scores to routing decisions
- **Keyword Analysis**: Identifies specialized queries through keyword detection
- **Pattern Matching**: Uses regex patterns to identify specific query types

## Key Features

### Hardware-Aware Routing

The router continuously monitors system resources and adapts its routing decisions accordingly:

- **CPU Monitoring**: Tracks CPU usage and routes to less intensive models when CPU is constrained
- **Memory Monitoring**: Monitors available memory and falls back to lightweight models when memory is low
- **Internet Connectivity**: Detects offline mode and routes to local models when internet is unavailable
- **Ollama Availability**: Checks if Ollama is running for local model access

### Adaptive Behavior

The router adapts to changing conditions and requirements:

- **Memory-Constrained Mode**: Automatically activates when system memory is low
- **CPU-Constrained Mode**: Activates when CPU usage is high
- **Offline Mode**: Automatically switches to local models when internet connectivity is lost
- **Caching**: Caches routing decisions to reduce overhead and improve response time

### Rich Context Data

All models receive rich context data to provide more informed responses:

1. **System Status**:

   - Memory usage (total, available, percent used)
   - CPU usage
   - Disk usage

2. **Ollama Status**:

   - Running status
   - Offline mode status

3. **Conversation History**:

   - Recent messages (up to 5 turns)
   - User and assistant roles clearly marked

4. **Metadata**:
   - Session start time
   - Interaction count
   - Last updated timestamp

### Handoff Mechanism

For specialized intents, the system implements a handoff mechanism:

1. The primary model provides an initial response to the query
2. The primary model introduces the specialized model with a handoff message
3. The specialized model provides its expert response
4. Both responses are combined and returned to the user

Example handoff:

```
[Primary model's initial response to the query]

Handing off to DeepSeek for specialized debugging assistance...

[DeepSeek's expert response to the query]
```

## AI Models and Routing

P.U.L.S.E. uses a crew of specialized AI models, each with a specific role:

| Model           | Role              | Specialization                 | Source     |
| --------------- | ----------------- | ------------------------------ | ---------- |
| Mistral-Small   | Leader            | General queries, orchestration | OpenRouter |
| DeepSeek        | Troubleshooter    | Debugging, error diagnosis     | OpenRouter |
| DeepCoder       | Code Expert       | Code generation, optimization  | OpenRouter |
| Llama-Doc       | Documentation     | Explanations, documentation    | OpenRouter |
| Mistral-Small   | Trends Analyst    | Market and AI trends           | OpenRouter |
| Llama-Content   | Content Creator   | Blog posts, articles           | OpenRouter |
| Llama-Technical | Technical Writer  | Technical explanations         | OpenRouter |
| Hermes          | Brainstormer      | Creative ideas, innovation     | OpenRouter |
| Olmo            | Ethics Expert     | Ethical considerations         | OpenRouter |
| MistralAI       | Automation Expert | Task automation                | OpenRouter |
| Kimi            | Visual Reasoner   | UI/UX, visual design           | OpenRouter |
| Nemotron        | Reasoning Expert  | Complex problem-solving        | OpenRouter |
| Phi             | Local Model       | Offline support                | Ollama     |

## Intent to Model Mapping

The system maps intents to specialized models:

```
debug → DeepSeek
code → DeepCoder
docs/explain → Llama-Doc
troubleshoot → DeepSeek
trends → Mistral-Small
content → Llama-Content
technical → Llama-Technical
brainstorm → Hermes
ethics → Olmo
automate → MistralAI
visual → Kimi
reasoning → Nemotron
```

## Model ID Mappings

P.U.L.S.E. uses the following model IDs for OpenRouter API calls:

```python
MODEL_IDS = {
    # Main brain
    "mistral_small": "mistralai/mistral-small-3.1-24b-instruct:free",

    # Specialized models
    "debug_troubleshooting": "deepseek-ai/deepseek-coder-33b-instruct:free",
    "code_generation": "deepseek-ai/deepseek-coder-33b-instruct:free",
    "documentation": "meta-llama/llama-3-70b-instruct:free",
    "explanation": "meta-llama/llama-3-70b-instruct:free",
    "trends_analysis": "mistralai/mistral-small-3.1-24b-instruct:free",
    "content_creation": "meta-llama/llama-3-70b-instruct:free",
    "technical_writing": "meta-llama/llama-3-70b-instruct:free",
    "brainstorming": "teknium/hermes-2-pro-mistral-7b:free",
    "ethics": "allenai/olmo-7b-instruct:free",
    "automation": "mistralai/mistral-7b-instruct-v0.2:free",
    "visual_reasoning": "anthropic/claude-3-haiku:free",
    "reasoning": "databricks/dbrx-instruct:free",

    # Fallback model
    "fallback": "mistralai/mistral-7b-instruct-v0.2:free"
}
```

### Model Selection Logic

The model selection logic is implemented in the `_select_model_for_intent` method:

```python
def _select_model_for_intent(self, intent):
    """
    Select the appropriate model based on the intent.

    Args:
        intent: The detected intent

    Returns:
        model_id: The selected model ID
    """
    intent_to_model = {
        "debug": "debug_troubleshooting",
        "code": "code_generation",
        "docs": "documentation",
        "explain": "explanation",
        "troubleshoot": "debug_troubleshooting",
        "trends": "trends_analysis",
        "content": "content_creation",
        "technical": "technical_writing",
        "brainstorm": "brainstorming",
        "ethics": "ethics",
        "automate": "automation",
        "visual": "visual_reasoning",
        "reasoning": "reasoning"
    }

    model_key = intent_to_model.get(intent, "mistral_small")
    return MODEL_IDS[model_key]
```

### Free vs. Paid Models

P.U.L.S.E. uses only free models to avoid unexpected charges:

```python
# Free models (OpenRouter free tier)
self.free_models = {
    "debug": MODEL_IDS["debug_troubleshooting"],
    "code": MODEL_IDS["code_generation"],
    "docs": MODEL_IDS["documentation"],
    "explain": MODEL_IDS["explanation"],
    "troubleshoot": MODEL_IDS["debug_troubleshooting"],
    "trends": MODEL_IDS["trends_analysis"],
    "content": MODEL_IDS["content_creation"],
    "technical": MODEL_IDS["technical_writing"],
    "brainstorm": MODEL_IDS["brainstorming"],
    "ethics": MODEL_IDS["ethics"],
    "automate": MODEL_IDS["automation"],
    "visual": MODEL_IDS["visual_reasoning"],
    "reasoning": MODEL_IDS["reasoning"]
}

# Paid models (not used by default)
self.paid_models = {
    "premium_debug": "anthropic/claude-3-opus-20240229",
    "premium_code": "anthropic/claude-3-opus-20240229",
    "premium_docs": "anthropic/claude-3-opus-20240229"
}
```

## Implementation

The Adaptive Neural Router is implemented in `routing/router.py` and consists of the following components:

### AdaptiveRouter Class

The main router class that handles model selection based on system resources and query intent:

```python
class AdaptiveRouter:
    def __init__(self, neural_router=None):
        self.neural_router = neural_router
        self.routing_cache = {}
        self.system_status = self._get_system_status()
        self.model_usage = {model: 0 for model in MODEL_CONFIGS}

    async def route(self, query, intent=None):
        # Update system status
        await self._update_system_status()

        # Try neural routing
        if self.neural_router and not self.system_status["memory_constrained"]:
            neural_model, neural_confidence = await self.neural_router.route_query(query, intent=intent)

        # Select model based on constraints and intent
        selected_model = self._select_model_for_constraints(query_type)

        # Return routing result
        return {
            "model": selected_model,
            "model_name": model_config["name"],
            "provider": model_config["provider"],
            "offline_compatible": model_config["offline"],
            "neural_confidence": neural_confidence,
            "system_status": {...}
        }
```

### System Status Monitoring

The router monitors system status to make informed routing decisions:

```python
def _get_system_status(self):
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # Get memory info
    memory = psutil.virtual_memory()
    memory_free_percent = memory.available / memory.total

    # Check if we're in offline mode
    offline_mode = not self._check_internet_connection()

    # Check if Ollama is available
    ollama_available = self._check_ollama_available()

    return {
        "cpu_percent": cpu_percent,
        "memory_free_percent": memory_free_percent,
        "memory_free_mb": memory_free_mb,
        "offline_mode": offline_mode,
        "ollama_available": ollama_available,
        "timestamp": time.time()
    }
```

## Model Configuration

The router uses a configuration dictionary to define the characteristics of each model:

```python
MODEL_CONFIGS = {
    "mistral-small": {
        "name": MODEL_IDS["mistral_small"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 1
    },
    "deepseek": {
        "name": MODEL_IDS["debug_troubleshooting"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 2
    },
    # Additional models...
}
```

## Offline Mode

When offline or when Ollama is running:

1. All queries are routed to local models via Ollama
2. Phi is used as the default model
3. Rich context data is still provided to local models
4. The system automatically detects internet connectivity and enables offline mode when needed

## Usage Examples

### Debug Intent

```python
response = await model_interface.generate_response(
    prompt="Low memory detected, how can I fix this?",
    intent="debug"
)
```

### Direct Model Call

```python
response = await model_interface.generate_response(
    prompt="Write a Python script",
    model="deepcoder"
)
```

### Offline Mode

```python
# Enable offline mode
await model_interface.toggle_offline_mode(True)

# Generate response (will use local models)
response = await model_interface.generate_response(
    prompt="What's the time in Tokyo?",
    intent="time"
)
```

## Local Model Files

P.U.L.S.E. uses several local model files for intent classification and offline operation. These files are excluded from the repository to keep it lightweight.

### Excluded Model Files

The following large model files have been excluded from the repository:

- `models/distilbert-intent/model.safetensors`
- `models/distilbert-intent/models--distilbert-base-uncased/`

### Downloading Model Files

#### Option 1: Using Hugging Face Transformers

You can download the model files directly using the Hugging Face Transformers library:

```python
from transformers import AutoTokenizer, AutoModel

# Download the tokenizer
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')

# Download the model
model = AutoModel.from_pretrained('distilbert-base-uncased')
```

#### Option 2: Using the Provided Script

P.U.L.S.E. includes a script to download and prepare the DistilBERT model:

```bash
python scripts/prep_distilbert.py
```

This script will:

1. Download the DistilBERT model from Hugging Face
2. Save it to the appropriate directory
3. Configure it for intent classification

#### Option 3: Using MiniLM Instead

P.U.L.S.E. now includes a more lightweight alternative to DistilBERT called MiniLM. This model is smaller and faster, making it ideal for low-resource environments.

MiniLM is automatically downloaded when needed and doesn't require manual setup.

### Model Directory Structure

The model directory structure should look like this:

```
models/
├── distilbert-intent/
│   ├── config.json
│   ├── model.safetensors (excluded from repository)
│   ├── special_tokens_map.json
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   ├── vocab.txt
│   └── models--distilbert-base-uncased/ (excluded from repository)
│       ├── .no_exist/
│       ├── blobs/
│       ├── refs/
│       └── snapshots/
└── keyword_classifier/
    ├── classifier.py
    └── keywords.json
```

### Offline Models with Ollama

For offline usage, P.U.L.S.E. can use Ollama to run local models:

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull the Phi model:
   ```bash
   ollama pull phi
   ```
3. Enable offline mode in P.U.L.S.E.:
   ```
   enable offline mode
   ```

### Model Performance Considerations

- **DistilBERT**: Requires ~500MB of RAM
- **MiniLM**: Requires ~100MB of RAM
- **Ollama/Phi**: Requires ~2GB of RAM

For low-resource environments, MiniLM is recommended as it provides a good balance between performance and resource usage.

## Future Improvements

1. **Enhanced Intent Classification**: Improve intent classification accuracy with more training data
2. **Dynamic Model Loading**: Load and unload models dynamically based on usage patterns
3. **User Preference Learning**: Learn user preferences for model selection over time
4. **Multi-Factor Routing**: Consider additional factors like query complexity and expected response time
5. **Federated Routing**: Distribute routing decisions across multiple instances for scalability
6. **Dynamic Model Selection**: Use machine learning to improve model selection based on past performance
7. **Context Optimization**: Intelligently trim context data based on model capabilities and query needs
8. **Multi-Model Collaboration**: Allow multiple specialized models to collaborate on complex queries
9. **User Feedback Integration**: Incorporate user feedback to improve model routing decisions
10. **Custom Model Roles**: Allow users to define custom roles and model assignments
