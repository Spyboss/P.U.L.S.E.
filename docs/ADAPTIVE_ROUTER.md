# Adaptive Neural Router

The Adaptive Neural Router is a key component of P.U.L.S.E. that intelligently routes queries to the most appropriate AI model based on query intent, system resources, and other factors.

## Overview

The Adaptive Neural Router combines hardware awareness with neural intent classification to provide optimal model selection for each query. It adapts to changing system conditions and user needs, ensuring the best possible response while managing system resources efficiently.

## Key Features

### Hardware-Aware Routing

The router continuously monitors system resources and adapts its routing decisions accordingly:

- **CPU Monitoring**: Tracks CPU usage and routes to less intensive models when CPU is constrained
- **Memory Monitoring**: Monitors available memory and falls back to lightweight models when memory is low
- **Internet Connectivity**: Detects offline mode and routes to local models when internet is unavailable
- **Ollama Availability**: Checks if Ollama is running for local model access

### Neural Intent Classification

The router uses neural networks to determine the intent of user queries:

- **Intent Detection**: Analyzes query text to determine the most likely intent
- **Confidence Scoring**: Assigns confidence scores to routing decisions
- **Keyword Analysis**: Identifies specialized queries through keyword detection
- **Pattern Matching**: Uses regex patterns to identify specific query types

### Adaptive Behavior

The router adapts to changing conditions and requirements:

- **Memory-Constrained Mode**: Automatically activates when system memory is low
- **CPU-Constrained Mode**: Activates when CPU usage is high
- **Offline Mode**: Automatically switches to local models when internet connectivity is lost
- **Caching**: Caches routing decisions to reduce overhead and improve response time

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

## Usage

The Adaptive Neural Router is used by the Model Orchestrator to select the appropriate model for each query:

```python
# Example usage in model_orchestrator.py
async def generate_response(self, prompt, intent=None, model=None):
    if not model:
        # Use the router to select a model
        routing_result = await self.router.route(prompt, intent)
        model = routing_result["model"]
        
    # Generate response using the selected model
    response = await self._call_model(prompt, model)
    return response
```

## Future Improvements

Planned improvements for the Adaptive Neural Router include:

1. **Enhanced Intent Classification**: Improve intent classification accuracy with more training data
2. **Dynamic Model Loading**: Load and unload models dynamically based on usage patterns
3. **User Preference Learning**: Learn user preferences for model selection over time
4. **Multi-Factor Routing**: Consider additional factors like query complexity and expected response time
5. **Federated Routing**: Distribute routing decisions across multiple instances for scalability

## Related Documentation

- [Model Routing](MODEL_ROUTING.md) - Neural routing between different models
- [Model Mappings](MODEL_MAPPINGS.md) - Model ID mappings and configurations
- [Offline Mode](features/offline_mode.md) - Working offline with Ollama and DistilBERT
