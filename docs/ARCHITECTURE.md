# General Pulse Architecture

This document describes the architecture of General Pulse, a loyal AI companion designed to assist with coding, freelancing, and personal growth.

## Overview

General Pulse is built with a modular architecture that integrates multiple AI models, context management, memory storage, and personality traits. The system is designed to be:

- **Efficient**: Optimized for limited hardware resources
- **Extensible**: Easy to add new features and capabilities
- **Personal**: Adapts to the user's preferences and needs
- **Reliable**: Handles errors gracefully and provides consistent responses
- **Collaborative**: Uses an AI crew system where specialized models work together

### AI Crew System

A key feature of General Pulse is its AI crew system, where multiple specialized AI models work together:

- **Gemini**: The crew leader, orchestrating other models and maintaining a personal relationship with the user
- **DeepSeek**: Troubleshooting expert for diagnosing errors and providing DevOps fixes
- **DeepCoder**: Code generation specialist for writing, debugging, and optimizing code
- **Llama-Doc**: Documentation expert for creating clear, concise documentation
- **Mistral-Small**: Trends analyst for tracking market and AI trends
- **Llama-Content**: Content creation specialist for generating engaging content
- **Llama-Technical**: Technical translation expert for explaining complex concepts
- **Hermes**: Brainstorming specialist for generating creative ideas
- **Olmo**: Ethical AI specialist for providing ethical considerations
- **Phi**: Low-resource specialist optimized for simple queries
- **MistralAI**: Task automation specialist for streamlining workflows

Each model has a specific role, personality, and prompt, allowing them to maintain consistent character and collaborate effectively. The system automatically routes queries to the appropriate specialist based on the query type.

## Core Components

### 1. Optimized Model Interface & AI Crew System

The Optimized Model Interface manages the AI crew system, where multiple specialized AI models work together:

- **Leader**: Gemini 2.0 Flash Thinking (direct API) - Orchestrates the crew and knows the user personally
- **Specialists**: Free OpenRouter models for specific tasks, each with a defined role and personality
- **Paid Fallbacks**: Claude and Grok models available as paid fallbacks
- **Local Models**: MiniLM for intent classification (with DistilBERT as fallback) and Ollama models for offline operation

Key features:

- Memory optimization with proactive garbage collection and resource monitoring
- Ollama integration with on-demand startup and automatic shutdown
- Robust fallback mechanisms for API failures and resource constraints
- Intelligent query routing to appropriate models based on query type
- Performance monitoring and adaptive throttling
- AI crew with defined roles, relationships, and personalities
- Role-specific prompts for each model to maintain consistent character
- Usage tracking and optimization to stay within free tiers

Files:

- `skills/optimized_model_interface.py` - Core model interface with optimization features
- `skills/model_orchestrator.py` - Model orchestration logic
- `utils/ollama_manager.py` - Ollama service management
- `configs/models.yaml` - Model definitions, roles, and relationships
- `configs/prompts.yaml` - Role-specific prompts for each model

### 2. Context Manager

The Context Manager maintains conversation context and integrates with AugmentCode's context engine:

- **Short-term Context**: Recent conversation history stored in a deque
- **AugmentCode Integration**: Deep context understanding without token limits
- **Mood Inference**: Detects user mood from input text
- **Metadata Tracking**: Stores interaction metadata for better context

File: `utils/context_manager.py`

### 3. Memory Manager

The Memory Manager provides long-term storage using SQLite:

- **Identity Storage**: Core system identity and personality traits
- **User Data**: Projects, interests, and preferences
- **Goals**: User goals with priority and status tracking
- **Interactions**: Important conversations and insights
- **Search Capabilities**: Full-text search across all memory types

File: `utils/memory_manager.py`

### 4. Personality Engine

The Personality Engine manages the assistant's tone, style, and responses:

- **Personality Traits**: Configurable traits like informative, courageous, positive
- **Response Formatting**: Adapts responses based on context and personality
- **Mood Tracking**: Adjusts energy level and tone based on user interactions
- **Anime References**: Incorporates references to anime like Jujutsu Kaisen and Solo Leveling
- **Goal Reminders**: Occasionally reminds the user of their goals

File: `utils/personality_engine.py`

### 5. Ollama Integration

The Ollama integration provides offline AI capabilities:

- **Service Lifecycle**: Manages the Ollama service lifecycle with automatic discovery
- **Resource Optimization**: Monitors memory and CPU usage to prevent system slowdowns
- **Model Management**: Discovers, pulls, and caches models from Ollama's library
- **Offline Mode**: Provides seamless transition between online and offline operation
- **Integration**: Integrates with the Optimized Model Interface for consistent API

File: `utils/ollama_manager.py`

### 6. Pulse Agent & Intent Handler

The Pulse Agent integrates all components and manages the overall system:

- **Input Processing**: Handles user input and generates responses
- **Intent Handling**: Recognizes and processes specific commands using DistilBERT
- **Error Handling**: Gracefully handles errors and provides helpful messages
- **System Commands**: Provides help, status, and other system functions
- **Resource Management**: Ensures efficient use of system resources
- **Offline Mode**: Manages transitions between online and offline operation

The Intent Handler uses a consolidated MiniLM-based classification system:

- **Ultra-Lightweight Model**: Uses MiniLM for extremely efficient intent classification (22.7M parameters)
- **Minimal Memory Footprint**: Only ~470MB vs DistilBERT's 1.1GB
- **Blazing Fast Inference**: 0.8ms per query on low-spec hardware
- **Offline Capability**: Works without internet connectivity
- **Command Categories**: Recognizes system commands, model commands, tool commands, and more
- **Confidence Scoring**: Uses thresholds to determine intent with fallback mechanisms

Files:

- `skills/pulse_agent.py` - Main agent implementation
- `utils/intent_handler.py` - Intent recognition and command routing
- `utils/minilm_classifier.py` - MiniLM-based intent classification (primary)
- `utils/distilbert_classifier.py` - DistilBERT-based intent classification (fallback)

## Data Flow

1. User input is received by the Pulse Agent
2. The Intent Handler checks for specific commands
3. If a command is recognized, it's handled by the appropriate handler
4. Otherwise, the input is processed by the Model Orchestrator
5. The Model Orchestrator selects the appropriate model and generates a response
6. The response is formatted by the Personality Engine
7. The interaction is stored in the Context Manager and Memory Manager
8. The formatted response is returned to the user

## Hardware Optimization

General Pulse is optimized for systems with limited resources:

- **Memory Management**: Careful memory usage with garbage collection
- **GPU Optimization**: Limited VRAM usage for GPU acceleration
- **SQLite Optimization**: WAL mode and other optimizations for better performance
- **SSD Detection**: Automatically uses SSD for temp files if available
- **Resource Monitoring**: Tracks system resource usage and adapts accordingly

File: `utils/optimization.py`

## Configuration

Configuration is stored in YAML files:

- **Models**: Model definitions, roles, and configurations
- **Hardware**: Hardware-specific settings and optimizations
- **Personality**: Default personality traits and response templates

Directory: `configs/`

## Extension Points

General Pulse can be extended in several ways:

1. **New AI Crew Members**: Add new specialized models to the AI crew system
   - Add model definitions to `configs/models.py`
   - Create role-specific prompts in `configs/prompts.py`
   - Define relationships with other crew members in `CREW_MANIFEST`
2. **New Query Types**: Add new query types to route to specific specialists
   - Add mappings in `QUERY_TYPE_TO_MODEL` in `configs/models.py`
3. **New Commands**: Add new command handlers to the Pulse Agent
   - Extend the Intent Handler in `utils/intent_handler.py`
4. **New Personality Traits**: Add new traits to the Personality Engine
   - Add traits in `utils/personality_engine.py`
5. **New Memory Types**: Add new memory storage types to the Memory Manager
   - Extend the Memory Manager in `utils/memory_manager.py`
6. **New Optimizations**: Add new hardware optimizations to the optimization utilities
   - Enhance the optimization utilities in `utils/optimization.py`

## Dependencies

- **Python 3.8+**: Core language
- **SQLite**: Memory storage
- **Google Generative AI**: Gemini API
- **OpenRouter**: Access to multiple AI models
- **Transformers**: Local models like DistilBERT
- **PyTorch**: Deep learning framework for local models
- **Structlog**: Structured logging
- **Dotenv**: Environment variable management
- **Pytz**: Timezone handling

## Future Enhancements

1. **Enhanced AI Crew Dynamics**:
   - Add more specialized crew members for specific domains
   - Implement more complex crew interactions and collaborations
   - Add crew member "personalities" that evolve based on user interactions
2. **Voice Interface**: Add speech recognition and synthesis
3. **Multimodal Support**: Handle images, audio, and other media
4. **Plugin System**: Allow third-party plugins for extended functionality
5. **Web Interface**: Add a web-based UI for easier interaction
6. **Mobile App**: Create a mobile companion app
7. **Advanced Analytics**: Track usage patterns and optimize accordingly
8. **Crew Visualization**: Visual representation of the AI crew and their relationships
