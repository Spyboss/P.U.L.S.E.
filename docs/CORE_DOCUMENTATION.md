# P.U.L.S.E. Core Documentation

This document provides comprehensive information about the core components and architecture of P.U.L.S.E. (Prime Uminda's Learning System Engine).

## System Architecture

P.U.L.S.E. is built with a modular architecture that integrates multiple AI models, context management, memory storage, and personality traits. The system is designed to be:

- **Efficient**: Optimized for limited hardware resources
- **Extensible**: Easy to add new features and capabilities
- **Personal**: Adapts to the user's preferences and needs
- **Reliable**: Handles errors gracefully and provides consistent responses
- **Collaborative**: Uses an AI crew system where specialized models work together

### Core Components

1. **Optimized Model Interface & AI Crew System** - Manages AI model interactions and routing
2. **Neural Router** - Routes queries to appropriate models based on intent
3. **Intent Handler** - Classifies user intents using MiniLM for quick commands and Mistral-Small for complex intents
4. **Context Manager** - Maintains conversation context and history
5. **Memory System** - Provides persistent storage for conversations and data
6. **Vector Database** - Enables semantic search capabilities
7. **Personality Engine** - Implements the system's unique personality

### Data Flow

1. User input is received by the Pulse Agent
2. The Intent Handler checks for specific commands
3. If a command is recognized, it's handled by the appropriate handler
4. Otherwise, the input is processed by the Model Orchestrator
5. The Model Orchestrator selects the appropriate model and generates a response
6. The response is formatted by the Personality Engine
7. The interaction is stored in the Context Manager and Memory Manager
8. The formatted response is returned to the user

### Detailed Component Descriptions

#### 1. Optimized Model Interface & AI Crew System

The Optimized Model Interface manages the AI crew system, where multiple specialized AI models work together:

- **Leader**: Mistral-Small (via OpenRouter) - Orchestrates the crew and knows the user personally
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

#### 2. Context Manager

The Context Manager maintains conversation context and provides historical context:

- **Short-term Context**: Recent conversation history stored in a deque
- **Vector Database**: Semantic search for relevant historical context
- **Mood Inference**: Detects user mood from input text
- **Metadata Tracking**: Stores interaction metadata for better context

File: `utils/context_manager.py`

#### 3. Memory Manager

The Memory Manager provides long-term storage using SQLite:

- **Identity Storage**: Core system identity and personality traits
- **User Data**: Projects, interests, and preferences
- **Goals**: User goals with priority and status tracking
- **Interactions**: Important conversations and insights
- **Search Capabilities**: Full-text search across all memory types

File: `utils/memory_manager.py`

#### 4. Personality Engine

The Personality Engine manages the assistant's tone, style, and responses:

- **Personality Traits**: Configurable traits like informative, courageous, positive
- **Response Formatting**: Adapts responses based on context and personality
- **Mood Tracking**: Adjusts energy level and tone based on user interactions
- **Anime References**: Incorporates references to anime like Jujutsu Kaisen and Solo Leveling
- **Goal Reminders**: Occasionally reminds the user of their goals

File: `utils/personality_engine.py`

#### 5. Ollama Integration

The Ollama integration provides offline AI capabilities:

- **Service Lifecycle**: Manages the Ollama service lifecycle with automatic discovery
- **Resource Optimization**: Monitors memory and CPU usage to prevent system slowdowns
- **Model Management**: Discovers, pulls, and caches models from Ollama's library
- **Offline Mode**: Provides seamless transition between online and offline operation
- **Integration**: Integrates with the Optimized Model Interface for consistent API

File: `utils/ollama_manager.py`

#### 6. Pulse Agent & Intent Handler

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

## Identity System

P.U.L.S.E. has a unique identity inspired by J.A.R.V.I.S. with anime and Sri Lankan cultural references:

- **Personality Traits**: Helpful, slightly sarcastic, knowledgeable
- **Self-Awareness**: Ability to report on its own status and capabilities
- **Charisma Engine**: Provides engaging and personalized responses

## Error Handling

P.U.L.S.E. implements comprehensive error handling:

1. **Graceful Degradation** - Falls back to simpler models when advanced models fail
2. **Retry Mechanisms** - Automatically retries failed API calls with exponential backoff
3. **Detailed Logging** - Logs errors with context for debugging
4. **User-Friendly Messages** - Translates technical errors into understandable messages

### Error Handling System

The error handling system provides a standardized way to handle errors across different parts of the application. It includes:

1. **Standardized Error Responses**: Consistent error response format across all components
2. **Error Monitoring**: Centralized error logging, aggregation, and analysis
3. **User-Friendly Error Messages**: Clear, actionable error messages for users
4. **Retry Logic**: Automatic retry for transient errors
5. **Error Categorization**: Classification of errors by type, source, and severity

### Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error_type": "error_category",
  "message": "Technical error message for logging",
  "user_message": "User-friendly error message",
  "status_code": 404, // Optional HTTP status code
  "detailed_error": "Detailed technical information",
  "operation": "operation_being_performed",
  "timestamp": "2023-04-15T12:34:56"
}
```

### Error Handlers

#### Integration Error Handler

Located in `utils/integration_error_handler.py`, this module handles errors from external API integrations:

- GitHub API errors
- Notion API errors
- Other third-party service errors

It provides:

- Error classification
- Standardized error responses
- Retry logic for transient errors
- User-friendly error messages

#### Model Error Handler

Located in `utils/model_error_handler.py`, this module handles errors from AI model interactions:

- Authentication errors
- Rate limit errors
- Context length errors
- Content policy violations
- Network errors

It provides:

- Error classification by model type
- Standardized error responses
- Retry logic for transient errors
- User-friendly error messages
- Decorator for easy application to model interface methods

### Error Monitoring System

Located in `utils/error_monitoring.py`, this system provides:

- Centralized error logging
- Error aggregation and categorization
- Error trend analysis
- Notification capabilities for critical errors
- Export/import functionality for error logs

### Error Severity Levels

The system uses the following severity levels:

- **DEBUG**: Minor issues that don't affect functionality
- **INFO**: Informational messages about potential issues
- **WARNING**: Issues that might affect functionality but don't cause failure
- **ERROR**: Issues that cause a specific operation to fail
- **CRITICAL**: Severe issues that might affect system stability

### Retryable Errors

The system automatically identifies and retries the following types of errors:

- Network connectivity issues
- Rate limiting errors
- Temporary service unavailability (HTTP 503)
- Gateway timeouts (HTTP 504)
- Other transient errors

## AI Crew System

P.U.L.S.E. uses a dynamic AI crew system where multiple specialized AI models work together to provide the best possible assistance. Each model has a specific role and personality, and they can collaborate to solve complex problems.

### Crew Structure

The AI crew is structured as follows:

- **Leader**: Mistral-Small is the crew leader, orchestrating the other models and maintaining a personal relationship with the user.
- **Specialists**: Each specialist model has a specific role and expertise.
- **Paid Fallbacks**: These models are available as fallbacks when needed, but require paid API access.

### Crew Members

#### Leader

- **Mistral-Small** - Default Chat - Main orchestrator that knows the user personally and delegates to specialists.

#### Specialists

- **DeepSeek** - Troubleshooting - Diagnoses errors, provides DevOps fixes, and solves technical problems.
- **DeepCoder** - Code Generation - Writes, debugs, and optimizes code with clean, efficient implementations.
- **Llama-Doc** - Documentation - Creates clear, concise documentation and explains complex concepts.
- **Mistral-Small** - Trends Analyst - Tracks market and AI trends, providing up-to-date information.
- **Llama-Content** - Content Creation - Generates engaging content for blogs, marketing, and more.
- **Llama-Technical** - Technical Translation - Translates technical jargon into understandable language.
- **Hermes** - Brainstorming - Generates creative ideas and innovative solutions.
- **Olmo** - Ethical AI - Provides ethical considerations and detects bias in AI systems.
- **MistralAI** - Task Automation - Automates workflows and streamlines processes.
- **Kimi** - Visual Reasoning - Analyzes images and provides visual content assistance.
- **Nemotron** - Advanced Reasoning - Handles complex reasoning tasks and in-depth analysis.

#### Paid Fallbacks

- **Claude** - Fallback (Paid) - Paid fallback model for complex tasks requiring nuanced understanding.
- **Grok** - Fallback (Paid) - Paid fallback model with real-time knowledge and witty responses.

### Query Types and Routing

P.U.L.S.E. automatically routes queries to the appropriate specialist based on the query type:

#### Code-related Queries (DeepCoder)

- `code`: General coding help
- `debug`: Debugging code issues
- `algorithm`: Algorithm design and optimization

#### Documentation-related Queries (Llama-Doc)

- `docs`: Documentation creation and management
- `explain`: Detailed explanations of concepts
- `summarize`: Summarizing complex information

#### Problem-solving Queries (DeepSeek)

- `troubleshoot`: Diagnosing and fixing issues
- `solve`: Finding solutions to problems

#### Information and Research Queries (Mistral-Small)

- `trends`: Information about current trends
- `research`: In-depth research on topics

#### Content Creation Queries (Llama-Content)

- `content`: General content creation
- `creative`: Creative writing and ideas
- `write`: Writing assistance

#### Technical Queries (Llama-Technical)

- `technical`: Technical information and explanations
- `math`: Mathematical problems and concepts

#### Brainstorming Queries (Hermes)

- `brainstorm`: Generating multiple ideas
- `ideas`: Creative ideation

#### Ethics Queries (Olmo)

- `ethics`: Ethical considerations and analysis

#### Task Automation Queries (MistralAI)

- `automate`: Automating repetitive tasks
- `workflow`: Optimizing workflows
- `process`: Improving processes

### How to Use the AI Crew

You can interact with the AI crew in several ways:

1. **Direct Model Queries**: Ask a specific model directly.

   ```
   ask mistral-small what's the weather today?
   ask deepcoder to write a Python function to calculate factorial
   ask mistral-small about the latest AI trends
   ```

2. **Query Type Routing**: Use specialized query types to automatically route to the right model.

   ```
   ask code how to implement a binary search tree
   ask troubleshoot why my Docker container keeps crashing
   ask write a blog post about AI ethics
   ```

3. **Default Queries**: If you don't specify a model or query type, Mistral-Small (the leader) will handle your query.
   ```
   what's the capital of France?
   how do I improve my coding skills?
   ```

### Crew Dynamics

The AI crew members are aware of each other and can suggest other specialists when appropriate. For example:

- If you ask DeepCoder about troubleshooting a server issue, it might suggest consulting DeepSeek.
- If you ask Mistral-Small about code optimization, it might suggest DeepCoder.
- If you ask Mistral-Small about ethical considerations, it might delegate to Olmo.

This collaborative approach ensures you always get the best possible assistance for your specific needs.

### Model Availability

The availability of models depends on your API keys and the current status of the services:

- **Mistral-Small**: Requires a valid OpenRouter API key.
- **OpenRouter Models**: All specialist models require a valid OpenRouter API key.
- **Paid Fallbacks**: Claude and Grok require paid API access.

You can check the current status of all models with the `status` command.

## Model Integration

P.U.L.S.E. integrates with multiple AI models:

1. **Mistral-Small** - Primary model for general queries via OpenRouter
2. **MiniLM** - Local model for quick intent classification
3. **Ollama Models** - Local models for offline operation

### Model Routing

The Neural Router determines which model to use based on:

1. **Intent Classification** - What the user is trying to accomplish
2. **Hardware Availability** - Available computational resources
3. **Online Status** - Whether the system is online or offline
4. **Query Complexity** - Complexity of the user's request

## Installation and Configuration

### Installation

1. Clone the repository
2. Create a virtual environment
3. Install dependencies from requirements.txt
4. Set up environment variables

### Configuration

Configuration files are located in the `configs/` directory:

- `model_api_config.yaml` - AI model configuration
- `personality_traits.yaml` - Agent personality settings
- `command_patterns.yaml` - Command recognition patterns
- `logging_config.yaml` - Logging configuration

Environment variables are stored in the `.env` file:

```
# OpenRouter API key (for AI capabilities)
OPENROUTER_API_KEY=your_openrouter_api_key

# GitHub personal access token
GITHUB_TOKEN=your_github_token

# Notion API key
NOTION_API_KEY=your_notion_api_key

# MongoDB connection string
MONGODB_URI=your_mongodb_connection_string
```

## Migration from Gemini to Mistral

P.U.L.S.E. has migrated from using Google's Gemini model to Mistral-Small via OpenRouter:

1. **API Changes** - Updated API calls to use OpenRouter format
2. **Prompt Engineering** - Adjusted prompts for Mistral-Small's capabilities
3. **Error Handling** - Updated error handling for OpenRouter-specific errors
4. **Performance Tuning** - Optimized for Mistral-Small's response characteristics
