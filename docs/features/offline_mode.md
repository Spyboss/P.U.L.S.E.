# Offline Mode with Ollama

General Pulse now supports offline mode using Ollama, allowing you to work with local models even when you don't have an internet connection.

## Overview

The offline mode feature provides:

- Local model execution using Ollama
- Local intent classification using DistilBERT
- Seamless switching between online and offline modes
- Memory and resource management for low-spec hardware

## Requirements

- [Ollama](https://ollama.com/) installed on your system
- At least 1.5GB of free RAM for DistilBERT
- At least 2-3GB of free RAM for Phi-2 model (recommended)

## Installation

1. Install Ollama from [ollama.com](https://ollama.com/)
2. Install the required Python packages:

```bash
pip install transformers torch
```

## Usage

### CLI Commands

```bash
# Check Ollama status
ollama status

# Start Ollama service
ollama on

# Stop Ollama service
ollama off

# Pull a model from Ollama
ollama pull phi-2
```

### CLI UI Commands

The CLI UI provides a more detailed interface for managing Ollama:

```bash
# Launch the CLI UI
python cli_ui.py

# Then use these commands in the CLI UI
ollama status
ollama on
ollama off
ollama pull phi-2
```

## Supported Models

The following models are recommended for offline use:

- **phi-2**: Microsoft's 2.7B parameter model, good for general purpose use
- **llama2**: Meta's Llama 2 model, available in various sizes
- **mistral**: Mistral AI's 7B model, good for general purpose use
- **orca-mini**: A smaller model optimized for low-resource environments

## Intent Classification

In offline mode, General Pulse uses DistilBERT for intent classification. This allows the system to understand your commands even when offline.

The intent classifier is automatically initialized when the system starts, and it's used when Ollama is enabled.

## Resource Management

Offline mode is designed to work efficiently on low-spec hardware:

- DistilBERT requires approximately 1GB of RAM
- Phi-2 requires approximately 2-3GB of RAM
- The system automatically manages memory usage to prevent crashes
- You can monitor memory usage with the `ollama status` command

## Troubleshooting

If you encounter issues with Ollama:

1. Check if Ollama is installed correctly: `ollama --version`
2. Ensure port 11434 is not blocked by another application
3. Check Ollama logs: `C:\Users\<YourUsername>\.ollama\logs` on Windows
4. Free up RAM by closing other applications
5. Try pulling a smaller model like `orca-mini` if you have limited RAM

## Implementation Details

The offline mode is implemented using:

- `OllamaManager`: Manages the Ollama service lifecycle
- `OllamaClient`: Communicates with the Ollama API
- `IntentClassifier`: Uses DistilBERT for intent classification
- `PulseAgent`: Integrates Ollama into the agent workflow

The system automatically falls back to online mode if Ollama is not available or if a query requires capabilities not available offline.
