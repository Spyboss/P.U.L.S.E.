# Model Files

This document provides information about the model files used in General Pulse and how to obtain them.

## Excluded Model Files

The following large model files have been excluded from the repository to keep it lightweight:

- `models/distilbert-intent/model.safetensors`
- `models/distilbert-intent/models--distilbert-base-uncased/`

## Downloading Model Files

### Option 1: Using Hugging Face Transformers

You can download the model files directly using the Hugging Face Transformers library:

```python
from transformers import AutoTokenizer, AutoModel

# Download the tokenizer
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')

# Download the model
model = AutoModel.from_pretrained('distilbert-base-uncased')
```

### Option 2: Using the Provided Script

General Pulse includes a script to download and prepare the DistilBERT model:

```bash
python scripts/prep_distilbert.py
```

This script will:
1. Download the DistilBERT model from Hugging Face
2. Save it to the appropriate directory
3. Configure it for intent classification

### Option 3: Using MiniLM Instead

General Pulse now includes a more lightweight alternative to DistilBERT called MiniLM. This model is smaller and faster, making it ideal for low-resource environments.

MiniLM is automatically downloaded when needed and doesn't require manual setup.

## Model Directory Structure

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

## Offline Models with Ollama

For offline usage, General Pulse can use Ollama to run local models:

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull the Phi model:
   ```bash
   ollama pull phi
   ```
3. Enable offline mode in General Pulse:
   ```
   enable offline mode
   ```

## Model Performance Considerations

- **DistilBERT**: Requires ~500MB of RAM
- **MiniLM**: Requires ~100MB of RAM
- **Ollama/Phi**: Requires ~2GB of RAM

For low-resource environments, MiniLM is recommended as it provides a good balance between performance and resource usage.
