# Model Routing System

## Overview

The Model Routing System in General Pulse enables intelligent routing of user queries to the most appropriate AI model based on intent, context, and system status. This system ensures that each query is handled by the model best suited for the task, while providing rich context data to all models for more informed responses.

## Key Features

1. **Intent-Based Routing**: Routes queries to specialized models based on detected intent
2. **Rich Context Data**: Provides system status, conversation history, and metadata to all models
3. **Handoff Mechanism**: Gemini introduces specialized models and hands off for expert responses
4. **Offline Mode Support**: Automatically routes to local models when offline
5. **Memory Optimization**: Monitors and manages memory usage for low-spec hardware
6. **Fallback Mechanisms**: Gracefully handles API failures with alternative models

## AI Crew Members

General Pulse uses a crew of specialized AI models, each with a specific role:

| Model | Role | Specialization | Source |
|-------|------|----------------|--------|
| Gemini | Leader | General queries, orchestration | Direct API |
| DeepSeek | Troubleshooter | Debugging, error diagnosis | OpenRouter |
| DeepCoder | Code Expert | Code generation, optimization | OpenRouter |
| Llama-Doc | Documentation | Explanations, documentation | OpenRouter |
| Mistral-Small | Trends Analyst | Market and AI trends | OpenRouter |
| Llama-Content | Content Creator | Blog posts, articles | OpenRouter |
| Llama-Technical | Technical Writer | Technical explanations | OpenRouter |
| Hermes | Brainstormer | Creative ideas, innovation | OpenRouter |
| Olmo | Ethics Expert | Ethical considerations | OpenRouter |
| MistralAI | Automation Expert | Task automation | OpenRouter |
| Kimi | Visual Reasoner | UI/UX, visual design | OpenRouter |
| Nemotron | Reasoning Expert | Complex problem-solving | OpenRouter |
| Phi | Local Model | Offline support | Ollama |

## Intent to Model Mapping

The system maps intents to specialized models:

```
debug → DeepSeek
code → DeepCoder
docs/explain → Llama-Doc
troubleshoot → DeepSeek
trends → Mistral-Small
content → Llama-Content
technical → Llama-Technical
brainstorm → Hermes
ethics → Olmo
automate → MistralAI
visual → Kimi
reasoning → Nemotron
```

## Rich Context Data

All models receive rich context data to provide more informed responses:

1. **System Status**:
   - Memory usage (total, available, percent used)
   - CPU usage
   - Disk usage

2. **Ollama Status**:
   - Running status
   - Offline mode status

3. **Conversation History**:
   - Recent messages (up to 5 turns)
   - User and assistant roles clearly marked

4. **Metadata**:
   - Session start time
   - Interaction count
   - Last updated timestamp

## Handoff Mechanism

For specialized intents, the system implements a handoff mechanism:

1. Gemini provides an initial response to the query
2. Gemini introduces the specialized model with a handoff message
3. The specialized model provides its expert response
4. Both responses are combined and returned to the user

Example handoff:
```
[Gemini's initial response to the query]

Handing off to DeepSeek for specialized debugging assistance...

[DeepSeek's expert response to the query]
```

## Offline Mode

When offline or when Ollama is running:

1. All queries are routed to local models via Ollama
2. Phi is used as the default model
3. Rich context data is still provided to local models
4. The system automatically detects internet connectivity and enables offline mode when needed

## Implementation Details

The model routing system is implemented in the `ModelInterface` class with these key methods:

1. `generate_response()`: Main entry point for generating responses
2. `_route_by_intent()`: Routes queries based on intent
3. `_call_gemini_model()`: Calls the Gemini API
4. `_call_openrouter_model()`: Calls models via OpenRouter
5. `_call_ollama_model()`: Calls local models via Ollama
6. `_get_rich_context_data()`: Gathers rich context data
7. `_format_context_data()`: Formats context data for models

## Usage Examples

### Debug Intent

```python
response = await model_interface.generate_response(
    prompt="Low memory detected, how can I fix this?",
    intent="debug"
)
```

### Direct Model Call

```python
response = await model_interface.generate_response(
    prompt="Write a Python script",
    model="deepcoder"
)
```

### Offline Mode

```python
# Enable offline mode
await model_interface.toggle_offline_mode(True)

# Generate response (will use local models)
response = await model_interface.generate_response(
    prompt="What's the time in Tokyo?",
    intent="time"
)
```

## Future Enhancements

1. **Dynamic Model Selection**: Use machine learning to improve model selection based on past performance
2. **Context Optimization**: Intelligently trim context data based on model capabilities and query needs
3. **Multi-Model Collaboration**: Allow multiple specialized models to collaborate on complex queries
4. **User Feedback Integration**: Incorporate user feedback to improve model routing decisions
5. **Custom Model Roles**: Allow users to define custom roles and model assignments
