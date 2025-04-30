# P.U.L.S.E. Identity and Chat Persistence Fixes

This document describes the fixes implemented to address issues with P.U.L.S.E.'s identity and chat persistence.

## Issues Fixed

1. **Identity Issues**:
   - P.U.L.S.E. was identifying as "Mistral Small" instead of having its own unique identity
   - The system prompt was not being properly passed to the Mistral-Small model

2. **Repetitive Greetings**:
   - Every response included greetings like "Hey there, Uminda!" despite being in the same session
   - Session tracking was implemented but not being used for response formatting

3. **LanceDB Warning**:
   - Fixed the FutureWarning about the deprecated `field_by_name` method in LanceDB

## Changes Made

### 1. Fixed System Prompt for Mistral-Small

Modified `skills/model_orchestrator.py` to ensure the Mistral-specific system prompt is always used for the main_brain model:

```python
# For Mistral-Small model, always use the "mistral" prompt
if model_id == MODEL_IDS.get("main_brain"):
    system_prompt = get_prompt("mistral")
    self.logger.info("Using Mistral-specific system prompt for main_brain model")
else:
    system_prompt = get_prompt(model_key)
```

### 2. Enhanced Model Personality to Handle Mistral-Small

Updated `utils/model_personality.py` to handle Mistral-Small specifically:

```python
# If this is Gemini or Mistral-Small (main_brain) and we have a personality engine, use it
if (model_id == "gemini" or model_id == "mistralai/mistral-small-3.1-24b-instruct:free") and self.personality_engine:
    return self.personality_engine.format_response(content, success=success, model_id=model_id, is_new_session=is_new_session)
```

### 3. Added Session Tracking to Response Formatting

Modified `skills/model_orchestrator.py` to check for session status and pass it to the personality engine:

```python
# Check if this is a new session
is_new_session = False
if hasattr(self, 'rich_context_manager') and self.rich_context_manager:
    try:
        # Get the context manager from the rich context manager
        context_manager = self.rich_context_manager.context_manager
        if hasattr(context_manager, 'is_new_session'):
            is_new_session = context_manager.is_new_session()
            self.logger.info(f"Session status: {'New session' if is_new_session else 'Existing session'}")
    except Exception as e:
        self.logger.error(f"Error checking session status: {str(e)}")

# Format the response with model-specific personality
if hasattr(self, 'model_personality') and self.model_personality:
    formatted_content = self.model_personality.format_response(
        content, 
        model_id, 
        success=True,
        is_new_session=is_new_session
    )
```

### 4. Fixed LanceDB FutureWarning

Updated `utils/vector_db.py` to use the `field` parameter instead of the deprecated `field_by_name` method:

```python
# Legacy LanceDB API (0.3.x)
# Use field parameter instead of field_by_name to avoid FutureWarning
results = (
    self.table.search(query_embedding.tolist(), field="vector")
    .where(f"user_id = '{user_id}'")
    .limit(limit)
    .to_arrow()
    .to_pandas()
)
```

## Testing

To test these changes:

1. **Identity Test**:
   - Run `pulse-cli> hi pulse!` and verify that P.U.L.S.E. identifies itself correctly without mentioning "Mistral Small"

2. **Session Tracking Test**:
   - Run multiple queries in succession and verify that only the first response includes a greeting
   - Wait 5+ minutes, then run another query and verify that it includes a greeting (new session)

3. **LanceDB Warning Test**:
   - Check the logs to verify that the FutureWarning about `field_by_name` no longer appears

## Future Improvements

1. **Adaptive Session Timeout**:
   - Implement a dynamic session timeout based on user interaction patterns

2. **Enhanced Context Awareness**:
   - Further improve how historical context is used in responses

3. **Personality Customization**:
   - Add more anime and Sri Lankan cultural references to the personality
   - Allow users to customize the personality traits
