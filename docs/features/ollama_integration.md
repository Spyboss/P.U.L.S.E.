# Ollama Integration

General Pulse integrates with Ollama to provide offline AI capabilities, allowing the system to function without internet connectivity or to reduce API costs.

## Overview

The Ollama integration in General Pulse is managed by the `OllamaManager` class in `utils/ollama_manager.py`. This component handles the lifecycle of the Ollama service, manages models, and provides a seamless interface for offline AI capabilities.

## Key Features

### 1. Service Lifecycle Management

- **Automatic Discovery:** Automatically finds the Ollama executable on the system
- **On-Demand Startup:** Starts Ollama only when needed to conserve resources
- **Graceful Shutdown:** Properly shuts down Ollama when not in use to free memory
- **Health Monitoring:** Continuously monitors the health of the Ollama service

### 2. Resource Optimization

- **Memory Monitoring:** Tracks memory usage to prevent system slowdowns
- **CPU Monitoring:** Monitors CPU usage to ensure responsive operation
- **Adaptive Loading:** Adjusts model loading based on available resources
- **Force CPU Mode:** Automatically switches to CPU-only mode on low-memory systems

### 3. Model Management

- **Model Discovery:** Automatically discovers available models
- **Model Pulling:** Pulls models from Ollama's model library
- **Model Caching:** Intelligently caches frequently used models
- **Model Unloading:** Unloads unused models to free memory

### 4. Offline Mode

- **Toggle Control:** Easy toggling between online and offline modes
- **Automatic Activation:** Can automatically activate offline mode when online APIs fail
- **Seamless Transition:** Provides a smooth transition between online and offline operation
- **Status Reporting:** Clearly reports the current mode and available models

### 5. Integration with Model Interface

- **Unified API:** Provides a consistent API for both online and offline models
- **Fallback Mechanism:** Serves as a fallback when online APIs are unavailable
- **Query Routing:** Routes appropriate queries to Ollama models
- **Performance Monitoring:** Tracks performance metrics for optimization

## Usage

### Basic Usage

```python
from utils.ollama_manager import OllamaManager

# Initialize the Ollama manager
ollama_manager = OllamaManager()

# Check Ollama status
status = await ollama_manager.check_status()

# Start the Ollama service
result = await ollama_manager.start_service()

# Enable offline mode
result = await ollama_manager.toggle_offline_mode(True)

# Pull a model
result = await ollama_manager.pull_model("mistral")

# Generate text with a model
response = await ollama_manager.generate_text(
    "What is the capital of France?",
    model="mistral"
)

# Stop the Ollama service
result = await ollama_manager.stop_service()
```

### Integration with Model Interface

The Ollama manager is primarily used through the Optimized Model Interface:

```python
from skills.optimized_model_interface import OptimizedModelInterface

# Initialize the model interface
model_interface = OptimizedModelInterface()

# Enable offline mode (this will start Ollama if needed)
await model_interface.set_offline_mode(True)

# Query using Ollama models
response = await model_interface.query(
    "What is the capital of France?",
    query_type="general"
)

# Disable offline mode
await model_interface.set_offline_mode(False)
```

## CLI Commands

General Pulse provides CLI commands for managing Ollama:

```
ollama status  # Check Ollama status
ollama on      # Start Ollama service and enable offline mode
ollama off     # Stop Ollama service and disable offline mode
ollama pull mistral  # Pull the mistral model
enable offline mode  # Enable offline mode
disable offline mode  # Disable offline mode
```

## System Requirements

For optimal Ollama performance:

1. **Memory:** At least 8GB RAM (16GB recommended for larger models)
2. **Storage:** At least 10GB free space for model storage
3. **CPU:** Modern multi-core CPU (Intel i5 or equivalent)
4. **GPU:** Optional but recommended for faster inference

## Troubleshooting

Common issues and solutions:

1. **Ollama Not Found:** Ensure Ollama is installed and in your PATH
2. **Service Won't Start:** Check for port conflicts on 11434
3. **Out of Memory:** Try using smaller models or increasing swap space
4. **Slow Performance:** Consider using CPU-only mode on low-spec systems

## Supported Models

The following models are recommended for use with Ollama in General Pulse:

1. **mistral** - Good general-purpose model with reasonable resource requirements
2. **phi-2** - Lightweight model for simple queries
3. **llama2** - Balanced performance and quality
4. **tinyllama** - Very lightweight model for resource-constrained systems

## Future Improvements

Planned improvements for the Ollama integration:

1. **Model Quantization:** Support for different quantization levels
2. **Multi-Model Loading:** Load multiple models simultaneously for faster switching
3. **Performance Profiling:** Better performance metrics and optimization
4. **Custom Model Support:** Support for custom fine-tuned models
