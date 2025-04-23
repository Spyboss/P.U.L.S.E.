# Gemini to Mistral-Small Migration

## Overview

This document outlines the migration process from Gemini to Mistral-Small as the main brain for General Pulse. The migration was completed to improve performance, reliability, and to better align with the project's goals.

## Migration Summary

### Key Changes

1. **Main Brain Replacement**: Replaced Gemini with Mistral-Small (24B parameters) via OpenRouter
2. **Neural Router Updates**: Updated the neural router to use Mistral-Small for routing decisions
3. **Intent Classification**: Modified the natural intent handler to use Mistral-Small for classification
4. **Testing Infrastructure**: Enhanced testing capabilities for the main brain
5. **Error Handling**: Improved error handling with retry logic and better error reporting
6. **Documentation**: Updated documentation to reflect the new architecture

### Files Modified

- `utils/cli_ui.py`: Updated the `test_main_brain_api_key` method
- `utils/neural_router.py`: Changed routing logic to use Mistral-Small
- `utils/natural_intent_handler.py`: Renamed and updated classification methods
- `skills/model_orchestrator.py`: Enhanced the `test_main_brain` method
- Documentation files: Updated to reflect the new architecture

## Technical Details

### Model Comparison

| Feature | Gemini | Mistral-Small |
|---------|--------|---------------|
| Parameters | Unknown | 24B |
| Provider | Google | OpenRouter |
| Context Window | Limited | Larger |
| Specialized Tasks | General | General |
| API | Direct | OpenRouter |
| Cost | Free tier | Free tier |

### Implementation Details

#### Neural Router Updates

The neural router was updated to use Mistral-Small for routing decisions:

```python
# Before
model_id = MODEL_IDS["main_brain"]  # Gemini
response = await self.model_interface.call_openrouter(...)

# After
model_id = MODEL_IDS["mistral"]  # Mistral-Small
response = await self.model_interface.call_openrouter(...)
```

#### Intent Classification Updates

The natural intent handler was updated to use Mistral-Small for classification:

```python
# Before
async def _classify_with_gemini(self, text: str) -> Optional[str]:
    # ...
    response = await self.model_interface.call_gemini(...)

# After
async def _classify_with_mistral(self, text: str) -> Optional[str]:
    # ...
    response = await self.model_interface.call_openrouter(
        model_id="mistralai/mistral-small-3.1-24b-instruct:free",
        query=prompt,
        max_tokens=50
    )
```

#### Testing Infrastructure

Enhanced testing capabilities were added to the CLI UI:

```python
# Added Mistral-Small specific testing
mistral_result = await asyncio.wait_for(
    self.agent.model_orchestrator.test_main_brain(test_query),
    timeout=30  # 30 second timeout
)
```

## Migration Benefits

1. **Improved Performance**: Mistral-Small provides better reasoning capabilities
2. **Enhanced Reliability**: OpenRouter provides more reliable access to the model
3. **Better Error Handling**: Improved retry logic and error reporting
4. **Consistent Architecture**: All models now use OpenRouter, simplifying the codebase
5. **Future-Proofing**: Easier to upgrade to newer models as they become available

## Testing the Migration

To test the migration, use the following commands:

```bash
# Test the main brain API key
python pulse.py
# Then in the CLI:
test main_brain_api_key

# Or use the dedicated test script
python docs/tests/test_main_brain.py
```

## Known Issues and Limitations

1. **API Rate Limits**: OpenRouter has rate limits that may affect heavy usage
2. **Offline Mode**: Mistral-Small requires internet access; offline mode still uses Phi
3. **Memory Usage**: The system still requires optimization for low-memory environments

## Future Work

1. **Streaming Responses**: Implement streaming for real-time responses
2. **Context Window Optimization**: Better utilize Mistral-Small's context window
3. **Fine-Tuning**: Explore fine-tuning options for specialized tasks
4. **Caching**: Implement response caching for common queries
