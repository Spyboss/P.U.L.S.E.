# Setting Up Local Models for General Pulse

This guide provides instructions for setting up local models on low-spec hardware.

## System Requirements

Minimum requirements:

- 8GB RAM
- Intel i5-6500 or equivalent
- 2GB free disk space

## Installation

### 1. Install Base Dependencies

First, install the base dependencies:

```bash
pip install -r requirements.txt
```

### 2. Install Local Model Dependencies

For low-spec hardware, we recommend using CPU-only versions of PyTorch and Transformers:

```bash
pip install -r requirements-local.txt
```

This will install:

- PyTorch (CPU-only version)
- Transformers
- Accelerate
- Sentence-Transformers

### 3. Install Ollama (Optional)

For offline mode with local models, install Ollama:

1. Download from [ollama.com](https://ollama.com)
2. Install following the instructions for your platform
3. Pull the Phi-2 model:

```bash
ollama pull phi
```

## Troubleshooting

### PyTorch or Transformers Disabled

If you see messages like:

```
PyTorch disabled due to compatibility issues. Local models will not be available.
Transformers disabled due to compatibility issues. Local models will not be available.
```

Try the following:

1. Ensure you've installed the CPU-only versions:

   ```bash
   pip install -r requirements-local.txt
   ```

2. Check for conflicts:

   ```bash
   pip list | grep torch
   pip list | grep transformers
   ```

3. If conflicts exist, create a fresh virtual environment:

   ```bash
   python -m venv pulse-env
   # On Windows
   pulse-env\Scripts\activate
   # On Linux/Mac
   source pulse-env/bin/activate
   ```

4. Install dependencies in the new environment:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-local.txt
   ```

### Memory Issues

If you encounter memory errors:

1. Close other applications to free up memory
2. Reduce the number of models loaded in Ollama
3. Use the `--low-memory` flag when starting General Pulse:
   ```bash
   python pulse.py --low-memory
   ```

## Advanced Configuration

For more advanced configuration options, see the main [README.md](../README.md).
