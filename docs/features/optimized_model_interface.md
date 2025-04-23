# Optimized Model Interface

The Optimized Model Interface is a key component of General Pulse that manages interactions with AI models, optimizes resource usage, and provides fallback mechanisms for API failures.

## Overview

The `OptimizedModelInterface` class in `skills/optimized_model_interface.py` serves as the central interface for all AI model interactions in General Pulse. It's designed to work efficiently on low-spec hardware while providing robust error handling and fallback mechanisms.

## Key Features

### 1. Memory Optimization

- **Garbage Collection:** Proactive garbage collection to free memory after model calls
- **Resource Monitoring:** Continuous monitoring of system resources to prevent memory issues
- **Batch Processing:** Efficient processing of large requests in manageable chunks
- **Context Management:** Careful management of context size to prevent token overflow

### 2. Ollama Integration

- **On-Demand Startup:** Starts Ollama only when needed to conserve resources
- **Automatic Shutdown:** Shuts down Ollama when not in use to free memory
- **Model Caching:** Intelligent caching of frequently used models
- **Resource Monitoring:** Monitors Ollama's resource usage and adjusts accordingly

### 3. Fallback Mechanisms

- **API Failure Handling:** Graceful handling of API failures with automatic retries
- **Model Fallbacks:** Automatic fallback to alternative models when primary models fail
- **Offline Mode:** Seamless transition to offline mode when online APIs are unavailable
- **Degraded Operation:** Continues to function with reduced capabilities when resources are limited

### 4. Model Routing

- **Intelligent Routing:** Routes queries to the most appropriate model based on query type
- **Load Balancing:** Distributes load across models to prevent rate limiting
- **Cost Optimization:** Prioritizes free models when appropriate to reduce costs
- **Specialized Handling:** Custom handling for different model types (Gemini, OpenRouter, Ollama)

### 5. Performance Monitoring

- **Response Time Tracking:** Monitors response times to identify performance issues
- **Error Rate Monitoring:** Tracks error rates to identify problematic models
- **Resource Usage Tracking:** Monitors memory and CPU usage during model calls
- **Adaptive Throttling:** Adjusts request rate based on system load

## Usage

### Basic Usage

```python
from skills.optimized_model_interface import OptimizedModelInterface

# Initialize the model interface
model_interface = OptimizedModelInterface()

# Send a query to a specific model
response = await model_interface.query_model(
    "What is the capital of France?",
    model_id="gemini-2.0-flash-thinking-exp-01-21"
)

# Send a query with automatic model selection
response = await model_interface.query(
    "What is the capital of France?",
    query_type="general"
)
```

### Offline Mode

```python
# Enable offline mode
await model_interface.set_offline_mode(True)

# Query using offline models
response = await model_interface.query(
    "What is the capital of France?",
    query_type="general"
)

# Disable offline mode
await model_interface.set_offline_mode(False)
```

### Resource Management

```python
# Get system resource status
status = await model_interface.get_system_status()

# Get Ollama status
ollama_status = await model_interface.get_ollama_status()

# Manually start Ollama
await model_interface.start_ollama()

# Manually stop Ollama
await model_interface.stop_ollama()
```

## Configuration

The Optimized Model Interface can be configured through the following methods:

1. **Environment Variables:** Set environment variables to configure API keys and endpoints
2. **Configuration Files:** Use YAML configuration files for model mappings and settings
3. **Runtime Configuration:** Configure behavior at runtime through method parameters

## Error Handling

The interface provides comprehensive error handling:

1. **Retries:** Automatically retries failed requests with exponential backoff
2. **Fallbacks:** Falls back to alternative models when primary models fail
3. **Graceful Degradation:** Continues to function with reduced capabilities when resources are limited
4. **Detailed Error Messages:** Provides detailed error messages for troubleshooting

## Performance Considerations

For optimal performance on low-spec hardware:

1. **Enable Offline Mode:** Use offline mode when possible to reduce API calls
2. **Limit Concurrent Requests:** Avoid making too many concurrent requests
3. **Monitor Memory Usage:** Keep an eye on memory usage and free resources when needed
4. **Use Appropriate Models:** Choose smaller models for simple queries to conserve resources
