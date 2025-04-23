# Model Mappings

This document describes the model mappings used in General Pulse for routing queries to the appropriate AI models.

## Overview

General Pulse uses a variety of AI models for different tasks, each with its own strengths and specializations. The model mappings define which model is used for each type of query, based on the detected intent.

## Model IDs

The following model IDs are used in General Pulse:

| Model Name | Model ID | Source | Role |
|------------|----------|--------|------|
| Gemini | gemini-2.0-flash-thinking-exp-01-21 | Direct API | Default chat model, orchestrator |
| DeepSeek | deepseek/deepseek-r1-zero:free | OpenRouter | Troubleshooting, debugging |
| DeepCoder | agentica-org/deepcoder-14b-preview:free | OpenRouter | Code generation, optimization |
| Llama-Doc | meta-llama/llama-4-scout:free | OpenRouter | Documentation, explanations |
| Mistral-Small | mistralai/mistral-small-24b-instruct-2501:free | OpenRouter | Trends analysis |
| Llama-Content | meta-llama/llama-3.2-11b-vision-instruct:free | OpenRouter | Content creation |
| Llama-Technical | meta-llama/llama-3.3-70b-instruct:free | OpenRouter | Technical writing |
| Hermes | nousresearch/nous-hermes-2-mixtral-8x7b-sft:free | OpenRouter | Brainstorming, creative ideas |
| Olmo | allenai/olmo-7b:free | OpenRouter | Ethical considerations |
| MistralAI | mistralai/mixtral-8x7b-instruct:free | OpenRouter | Task automation |
| Kimi | moonshot/kimi:free | OpenRouter | Visual reasoning |
| Nemotron | nvidia/nemotron-4-340b-instruct:free | OpenRouter | Advanced reasoning |
| Phi | microsoft/phi-2:free | Ollama | Offline mode, low-resource scenarios |

## Intent to Model Mapping

The following intents are mapped to specific models:

| Intent | Model | Description |
|--------|-------|-------------|
| debug | DeepSeek | Debugging and troubleshooting issues |
| code | DeepCoder | Code generation and optimization |
| docs | Llama-Doc | Documentation and explanations |
| explain | Llama-Doc | Detailed explanations of concepts |
| troubleshoot | DeepSeek | Troubleshooting technical issues |
| trends | Mistral-Small | Analysis of trends and market data |
| content | Llama-Content | Content creation for blogs, articles, etc. |
| technical | Llama-Technical | Technical writing and translation |
| brainstorm | Hermes | Creative brainstorming and idea generation |
| ethics | Olmo | Ethical considerations and analysis |
| automate | MistralAI | Task automation and workflow optimization |
| visual | Kimi | Visual reasoning and design |
| reasoning | Nemotron | Advanced reasoning and problem-solving |

## Offline Mode

In offline mode, all queries are routed through Ollama using the Phi model (`microsoft/phi-2:free`). This allows General Pulse to function without an internet connection, using local models for all tasks.

## Handoff Mechanism

For specialized intents, General Pulse uses a handoff mechanism:

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
