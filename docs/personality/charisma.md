# Charisma Engine

The Charisma Engine provides P.U.L.S.E. with a lively, engaging personality inspired by J.A.R.V.I.S. and anime references, making interactions more natural and enjoyable.

## Overview

The Charisma Engine is responsible for formatting responses with personality traits, adding appropriate greetings, references, and stylistic elements. It works primarily with the Mistral-Small model but can be applied to other models as needed. The engine adapts its personality based on the conversation context and user mood.

## Key Features

### Anime-Inspired Wit

The Charisma Engine adds engaging, anime-inspired references to responses:

- **Anime References**: References to popular anime like Jujutsu Kaisen and Solo Leveling
- **Motivational Quotes**: Inspirational quotes from anime characters
- **Witty Remarks**: Clever and humorous remarks inspired by anime dialogue
- **Cultural References**: References to Sri Lankan culture and expressions

### Context-Aware Personality

The engine adapts its personality based on conversation context:

- **Technical Precision**: More precise and technical for code and technical queries
- **Casual Friendliness**: More casual and friendly for general conversation
- **Motivational Tone**: More motivational for goal-setting and productivity queries
- **Helpful Guidance**: More helpful and instructive for troubleshooting queries

### Mood Tracking

The engine tracks and adapts to user mood:

- **Mood Detection**: Detects user mood from input text
- **Adaptive Responses**: Adjusts response style based on detected mood
- **Energy Level**: Maintains an internal energy level that affects response style
- **Empathetic Responses**: Provides empathetic responses for negative moods

### Model-Specific Formatting

The engine applies charismatic formatting only to specific models:

- **Mistral-Small Focus**: Primarily formats responses from Mistral-Small
- **Neutral Mode**: Provides a neutral mode for other models
- **Identity Reinforcement**: Ensures consistent identity across all responses
- **Style Consistency**: Maintains consistent style for each model

## Implementation

The Charisma Engine is implemented in `personality/charisma.py` and consists of the following components:

### CharismaEngine Class

The main class that provides charismatic formatting:

```python
class CharismaEngine:
    """
    Manages the charismatic personality for Mistral-Small
    Features:
    - Anime-inspired wit and references
    - Engaging, lively responses
    - Context-aware personality traits
    - Neutral mode for other models
    """
    
    def __init__(self):
        """Initialize the charisma engine"""
        logger.info("Initializing charisma engine")
        
        # Personality traits (0.0 to 1.0)
        self.traits = {
            "informative": 0.8,    # How detailed and informative
            "courageous": 0.7,     # How willing to take risks
            "positive": 0.8,       # How positive and optimistic
            "casual": 0.6,         # How casual vs formal
            "strict": 0.3,         # How strict and rule-following
            "anime_references": 0.4  # How often to include anime references
        }
        
        # Current mood and energy level
        self.current_mood = "neutral"  # positive, neutral, negative
        self.energy_level = 0.7  # 0.0 to 1.0
        
        # Load anime references
        self.anime_references = self._load_anime_references()
        
        # Initialize self-awareness engine
        try:
            from personality.self_awareness import SelfAwarenessEngine
            self.self_awareness = SelfAwarenessEngine()
            logger.info("Self-awareness engine initialized")
        except ImportError:
            self.self_awareness = None
            logger.warning("Self-awareness engine not available")
```

### Response Formatting

The engine formats responses with personality:

```python
def format_response(self, content: str, context_type: str = "general",
                   model: str = "mistral", success: bool = True) -> str:
    """
    Format a response according to the personality
    
    Args:
        content: Response content
        context_type: Context type (code, explanation, etc.)
        model: Model name
        success: Whether the operation was successful
        
    Returns:
        Formatted response
    """
    # Only apply charismatic formatting to Mistral
    if model.lower() != "mistral" and model.lower() != "mistral-small":
        return content
        
    # Check for error conditions
    if not success:
        return self._format_error_response(content, context_type)
        
    # Get appropriate emoji for the context
    emoji = self._get_emoji_for_context(context_type)
    
    # Get greeting templates for the context
    templates = self._get_greeting_templates(context_type)
    
    # Select a random template
    template = random.choice(templates)
    
    # Format the template
    prefix = template.format(emoji=emoji, user="Uminda")
    
    # Clean up the content
    clean_content = content.strip()
    
    # Remove any "Based on your request:" prefix if present
    if clean_content.startswith("Based on your request:"):
        clean_content = clean_content[len("Based on your request:"):].strip()
        
    # Decide whether to add an anime reference
    anime_ref = ""
    if random.random() < self.traits["anime_references"]:
        anime_ref = self._get_anime_reference(context_type)
        
    # Add British slang if appropriate
    if context_type in ["greeting", "chat", "general"]:
        slang_chance = 0.7
    else:
        slang_chance = 0.3
        
    # Format the final response
    if anime_ref:
        return f"{prefix} {clean_content}\n\n{anime_ref}"
    else:
        return f"{prefix} {clean_content}"
```

### Mood Detection

The engine detects and adapts to user mood:

```python
def update_mood(self, user_input: str) -> None:
    """
    Update the current mood based on user input
    
    Args:
        user_input: User's input text
    """
    # Simple keyword-based mood detection
    lower_input = user_input.lower()
    
    # Check for positive keywords
    if any(word in lower_input for word in ["thanks", "great", "awesome", "good", "love", "like", "happy"]):
        self.current_mood = "positive"
        self.energy_level = min(1.0, self.energy_level + 0.1)
        
    # Check for negative keywords
    elif any(word in lower_input for word in ["bad", "hate", "dislike", "angry", "frustrated", "annoyed"]):
        self.current_mood = "negative"
        self.energy_level = max(0.3, self.energy_level - 0.1)
        
    # Check for neutral keywords or no mood indicators
    else:
        # Gradually return to neutral
        if self.current_mood == "positive":
            self.current_mood = "neutral"
            self.energy_level = max(0.5, self.energy_level - 0.05)
        elif self.current_mood == "negative":
            self.current_mood = "neutral"
            self.energy_level = min(0.7, self.energy_level + 0.05)
```

### Anime References

The engine includes anime references in responses:

```python
def _get_anime_reference(self, context_type: str) -> str:
    """
    Get an anime reference for the given context type
    
    Args:
        context_type: Context type (code, explanation, etc.)
        
    Returns:
        Anime reference string
    """
    # Select appropriate references for the context
    if context_type in ["code", "debug", "technical"]:
        references = self.anime_references.get("technical", [])
    elif context_type in ["motivation", "goals", "productivity"]:
        references = self.anime_references.get("motivation", [])
    elif context_type in ["greeting", "chat", "general"]:
        references = self.anime_references.get("casual", [])
    else:
        references = self.anime_references.get("general", [])
        
    # If no specific references, use general ones
    if not references:
        references = self.anime_references.get("general", [])
        
    # If still no references, return empty string
    if not references:
        return ""
        
    # Select a random reference
    reference = random.choice(references)
    
    # Format the reference
    return f"_{reference}_"
```

## Usage

The Charisma Engine is used by the Model Orchestrator to format responses:

```python
# Initialize the charisma engine
charisma = CharismaEngine()

# Format a response
formatted_response = charisma.format_response(
    content="Here's the Python code you requested:\n\ndef factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
    context_type="code",
    model="mistral-small",
    success=True
)

print(formatted_response)
```

## Integration with Self-Awareness

The Charisma Engine integrates with the Self-Awareness Module to ensure consistent identity:

```python
# In CharismaEngine.__init__
try:
    from personality.self_awareness import SelfAwarenessEngine
    self.self_awareness = SelfAwarenessEngine()
    logger.info("Self-awareness engine initialized")
except ImportError:
    self.self_awareness = None
    logger.warning("Self-awareness engine not available")

# In CharismaEngine.format_response
if self.self_awareness:
    # Use self-awareness to ensure consistent identity
    if "I am Mistral" in clean_content or "I am an AI assistant" in clean_content:
        clean_content = clean_content.replace("I am Mistral", f"I am {self.self_awareness.pulse_info['name']}")
        clean_content = clean_content.replace("I am an AI assistant", f"I am {self.self_awareness.pulse_info['name']}")
```

## Future Improvements

Planned improvements for the Charisma Engine include:

1. **Advanced Mood Detection**: More sophisticated mood detection using sentiment analysis
2. **Personalized References**: Tailoring references to user preferences
3. **Dynamic Personality Adjustment**: Adjusting personality traits based on user feedback
4. **Multi-Language Support**: Adding support for multiple languages
5. **Voice Tone Adaptation**: Adapting tone for voice interfaces

## Related Documentation

- [Self-Awareness Module](self_awareness.md) - System introspection and status reporting
- [Identity System](../IDENTITY_SYSTEM.md) - Implementation of robust identity system
- [Chat Persistence](../chat_persistence.md) - Enhanced chat persistence implementation
