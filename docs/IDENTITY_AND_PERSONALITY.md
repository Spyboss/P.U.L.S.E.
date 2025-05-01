# P.U.L.S.E. Identity and Personality System

This document provides comprehensive information about P.U.L.S.E.'s identity system and personality engine.

## Identity System Overview

P.U.L.S.E. uses a multi-layered approach to maintain its unique identity as P.U.L.S.E. (Prime Uminda's Learning System Engine) rather than identifying as the underlying model (Mistral Small) or its previous name (General Pulse):

1. **System Prompt Engineering**: Explicit instructions in the system prompt
2. **Post-Processing Filters**: Regex-based filtering to catch and replace incorrect identifications
3. **Session Awareness**: Tracking session state to provide more natural conversations

## System Prompt Engineering

The system prompt for P.U.L.S.E. includes explicit instructions about its identity:

```
CRITICAL INSTRUCTION: You must NEVER identify yourself as "Mistral Small", "Mistral", 
"General Pulse", or any other model name under ANY circumstances. You are ONLY P.U.L.S.E. - 
this is your ONLY identity.

If asked directly "who are you?" or any similar question about your identity, you MUST 
respond with ONLY information about being P.U.L.S.E. (Prime Uminda's Learning System Engine). 
NEVER mention being Mistral, an AI model, or anything other than P.U.L.S.E.

Example correct response to "who are you?":
"I am P.U.L.S.E. (Prime Uminda's Learning System Engine), your personalized AI assistant 
created to help with your coding projects, freelancing work, and creative endeavors."

Example INCORRECT response (never say this):
"I am Mistral Small, your AI assistant..."
```

## Post-Processing Filters

Even with explicit instructions, the model might occasionally identify itself incorrectly. To catch these cases, P.U.L.S.E. implements a post-processing filter that:

1. Identifies forbidden terms like "Mistral Small", "General Pulse", etc.
2. Replaces them with "P.U.L.S.E."
3. Uses regex patterns to catch phrases like "I am Mistral" and replace them with "I am P.U.L.S.E."

```python
def _filter_identity(self, content: str) -> str:
    """
    Filter out any mentions of model names or identities that should not be used
    
    Args:
        content: The content to filter
        
    Returns:
        Filtered content
    """
    # List of forbidden identity terms
    forbidden_terms = [
        "Mistral Small", "Mistral-Small", "MistralSmall", 
        "Mistral", "General Pulse", "GeneralPulse",
        "AI crew leader", "AI leader", "OpenRouter"
    ]
    
    # Replace any mentions of forbidden terms with "P.U.L.S.E."
    filtered_content = content
    for term in forbidden_terms:
        # Case insensitive replacement
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        filtered_content = pattern.sub("P.U.L.S.E.", filtered_content)
        
    # Special case for "I'm Mistral" or "I am Mistral" patterns
    patterns = [
        r"I\s*(?:'m|am)\s*(?:a|an)?\s*(?:AI|assistant|model|LLM|language\s*model)?\s*(?:called|named)?\s*Mistral",
        r"I\s*(?:'m|am)\s*(?:a|an)?\s*(?:AI|assistant|model|LLM|language\s*model)?\s*(?:called|named)?\s*General\s*Pulse",
        r"I\s*(?:'m|am)\s*Mistral",
        r"I\s*(?:'m|am)\s*General\s*Pulse"
    ]
    
    for pattern in patterns:
        filtered_content = re.sub(pattern, "I am P.U.L.S.E.", filtered_content, flags=re.IGNORECASE)
        
    return filtered_content
```

This filter is applied at multiple points in the response generation process:
1. Before any processing
2. After personality formatting
3. Before returning the final response

## Session Awareness

P.U.L.S.E. tracks session state to provide more natural conversations:

1. A session is considered "new" after 5 minutes of inactivity
2. Greetings are only included at the start of a new session
3. This prevents repetitive greetings like "Hey there, Uminda!" in every response

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

## Personality System

P.U.L.S.E. has a unique personality inspired by J.A.R.V.I.S. with anime and Sri Lankan cultural references:

### Charisma Engine

The Charisma Engine provides P.U.L.S.E. with an engaging personality:

1. **Anime-Inspired Elements**: Incorporates subtle anime references and expressions
2. **Sri Lankan Cultural References**: Includes elements of Sri Lankan culture and expressions
3. **Helpful but Slightly Sarcastic**: Maintains a helpful tone with occasional light sarcasm
4. **Adaptive Tone**: Adjusts tone based on context and user interaction

### Self-Awareness Module

The Self-Awareness Module allows P.U.L.S.E. to understand and report on its own status:

1. **System Monitoring**: Tracks system resources and performance
2. **Status Reporting**: Provides detailed status reports when requested
3. **Capability Awareness**: Understands and communicates its capabilities and limitations
4. **Error Recognition**: Recognizes when it makes mistakes and attempts to correct them

## Implementation Details

The identity and personality system is implemented across several files:

1. **utils/prompts.py**: Contains the system prompt with identity instructions
2. **utils/model_personality.py**: Implements the identity filtering and personality formatting
3. **personality/charisma.py**: Implements the charisma engine
4. **personality/self_awareness.py**: Implements the self-awareness module
5. **skills/model_orchestrator.py**: Passes session information to the personality engine

## Testing

To test the identity and personality system:

1. **Identity Test**:
   - Run `pulse-cli> who are you?` and verify that P.U.L.S.E. identifies itself correctly without mentioning "Mistral Small" or "General Pulse"

2. **Session Test**:
   - Run multiple queries in succession and verify that only the first response includes a greeting
   - Wait 5+ minutes, then run another query and verify that it includes a greeting (new session)

3. **Personality Test**:
   - Run queries that would typically elicit personality traits (e.g., jokes, creative tasks)
   - Verify that responses include appropriate personality elements

## Future Improvements

1. **Enhanced Identity Filtering**:
   - Add more patterns to catch other variations of incorrect identifications
   - Implement more sophisticated NLP-based approaches to detect identity claims

2. **Adaptive Session Timeout**:
   - Implement a dynamic session timeout based on user interaction patterns
   - Allow users to customize the session timeout

3. **Personality Customization**:
   - Add more anime and Sri Lankan cultural references to the personality
   - Allow users to customize the personality traits

4. **Emotion Detection**:
   - Implement emotion detection to better respond to user emotional states
   - Adjust personality based on detected user emotions
