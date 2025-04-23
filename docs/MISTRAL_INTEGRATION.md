# Mistral-Small Integration

## Overview

General Pulse now uses Mistral-Small (via OpenRouter) as its main brain, replacing the previous Gemini model. This document outlines the integration details, testing procedures, and best practices for working with Mistral-Small.

## Model Details

- **Model ID**: `mistralai/mistral-small-3.1-24b-instruct:free`
- **Provider**: OpenRouter
- **Parameters**: 24 billion
- **Strengths**: Strong reasoning, instruction following, and general knowledge
- **Use Cases**: Main brain for orchestration, chat, and general queries

## Integration Architecture

Mistral-Small is integrated into General Pulse through the following components:

1. **Model Orchestrator**: Manages API calls to Mistral-Small via OpenRouter
2. **Neural Router**: Routes queries to Mistral-Small or specialized models based on intent
3. **Natural Intent Handler**: Uses Mistral-Small for intent classification when online
4. **CLI UI**: Provides testing capabilities for the Mistral-Small API key

## Testing

### Testing the API Key

You can test the Mistral-Small API key using the CLI UI:

```bash
python pulse.py
# Then in the CLI:
test main_brain_api_key
```

This will:
1. Verify that your OpenRouter API key is valid
2. Test Mistral-Small with a simple query
3. Display the response

### Testing with a Custom Script

A dedicated test script is available in the `docs/tests` directory:

```bash
python docs/tests/test_main_brain.py
```

This script tests:
1. OpenRouter API key validation
2. Mistral-Small model response
3. Error handling and timeouts

## Configuration

Mistral-Small is configured in the `configs/models.yaml` file with the following settings:

```yaml
main_brain:
  model_id: mistralai/mistral-small-3.1-24b-instruct:free
  provider: openrouter
  max_tokens: 4096
  temperature: 0.7
```

## Best Practices

1. **API Key Management**: Store your OpenRouter API key in the `.env` file
2. **Error Handling**: The system includes retry logic and exponential backoff for API failures
3. **Timeout Management**: API calls have a 30-second timeout to prevent hanging
4. **Fallback Strategy**: If Mistral-Small is unavailable, the system falls back to other models

## Troubleshooting

### Common Issues

1. **API Key Invalid**: Ensure your OpenRouter API key is correctly set in the `.env` file
2. **Rate Limiting**: OpenRouter has rate limits; the system includes retry logic for these cases
3. **Timeout Errors**: Check your internet connection if you experience timeout errors
4. **Model Unavailable**: OpenRouter occasionally performs maintenance; the system will fall back to other models

### Logs

Check the logs for detailed information about API calls and errors:

```
logs/pulse.log
```

## Implementation Details

The Mistral-Small integration includes:

1. **Updated Neural Router**: Routes queries to Mistral-Small instead of Gemini
2. **Enhanced Error Handling**: Improved retry logic and error reporting
3. **Specialized Testing**: Dedicated methods for testing the Mistral-Small integration
4. **Consistent Naming**: Updated all references from Gemini to Mistral-Small

## Future Improvements

1. **Streaming Responses**: Implement streaming for real-time responses
2. **Context Window Optimization**: Better utilize Mistral-Small's context window
3. **Fine-Tuning**: Explore fine-tuning options for specialized tasks
4. **Caching**: Implement response caching for common queries
