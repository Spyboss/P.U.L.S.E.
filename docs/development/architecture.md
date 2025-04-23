# Architecture Overview

This document provides an overview of the General Pulse architecture and how the different components interact.

## System Architecture

General Pulse is built with a modular architecture that separates concerns and allows for easy extension and maintenance:

```
                                 ┌─────────────────┐
                                 │                 │
                                 │  Main Agent     │
                                 │                 │
                                 └────────┬────────┘
                                          │
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 │                        │                        │
                 │                        │                        │
        ┌────────▼────────┐     ┌─────────▼─────────┐    ┌─────────▼─────────┐
        │                 │     │                   │    │                   │
        │  Skills         │     │  Tools            │    │  Utils            │
        │                 │     │                   │    │                   │
        └────────┬────────┘     └─────────┬─────────┘    └─────────┬─────────┘
                 │                        │                        │
                 │                        │                        │
┌────────────────┼────────────────────────┼────────────────────────┼────────────────┐
│                │                        │                        │                │
│                │                        │                        │                │
│    ┌───────────▼──────────┐  ┌──────────▼───────────┐  ┌─────────▼────────────┐  │
│    │                      │  │                      │  │                      │  │
│    │  GitHub Skills       │  │  GitHub Integration  │  │  Command Parser      │  │
│    │                      │  │                      │  │                      │  │
│    └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │
│                                                                                  │
│    ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│    │                      │  │                      │  │                      │  │
│    │  Notion Skills       │  │  Notion Integration  │  │  Intent Handler      │  │
│    │                      │  │                      │  │                      │  │
│    └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │
│                                                                                  │
│    ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│    │                      │  │                      │  │                      │  │
│    │  Model Interface     │  │  Bug Bounty Hunter   │  │  Timezone Utils      │  │
│    │                      │  │                      │  │                      │  │
│    └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Core Components

1. **Main Agent** (`skills/agent.py`)
   - Central controller that orchestrates all functionality
   - Processes user input and delegates to appropriate skills
   - Manages conversation context and memory

2. **Skills** (`skills/`)
   - High-level capabilities that implement specific functionality
   - Examples: GitHub skills, Notion skills, task management

3. **Tools** (`tools/`)
   - External integrations with APIs and services
   - Examples: GitHub API, Notion API

4. **Utils** (`utils/`)
   - Utility functions and helpers used across the application
   - Examples: Command parsing, logging, timezone utilities

### Key Modules

#### Agent System

- **Agent** (`skills/agent.py`) - Main agent implementation
- **Personality Engine** (`utils/agent_personality.py`) - Manages agent personality traits
- **Conversation Manager** (`utils/conversation_manager.py`) - Handles conversation history

#### Command Processing

- **Command Parser** (`utils/command_parser.py`) - Parses natural language commands
- **Intent Handler** (`utils/intent_handler.py`) - Processes user intents
- **Intent Classifier** (`utils/intent_classifier.py`) - Classifies user input into intents

#### AI Model Integration

- **Model Interface** (`skills/model_interface.py`) - Interface to AI models
- **OpenRouter Client** (`utils/openrouter_client.py`) - Client for OpenRouter API
- **Execution Flow** (`utils/execution_flow.py`) - Manages AI model execution flow

#### External Integrations

- **GitHub Integration** (`tools/github_integration.py`) - GitHub API integration
- **Notion Integration** (`tools/notion_integration.py`) - Notion API integration
- **GitHub Skills** (`skills/github_skills.py`) - High-level GitHub functionality
- **Notion Skills** (`skills/notion_skills.py`) - High-level Notion functionality

#### Utilities

- **Logger** (`utils/logger.py`) - Centralized logging
- **Cache Manager** (`utils/cache_manager.py`) - Caching for API responses
- **Timezone Utils** (`utils/timezone_utils.py`) - Timezone conversion utilities

## Data Flow

1. User input is received by the Agent
2. Command Parser identifies the command type and extracts parameters
3. Agent delegates to the appropriate skill
4. Skill uses tools to interact with external services
5. Results are processed and formatted
6. Agent returns the response to the user

## Memory System

General Pulse uses a persistent memory system to store:

- Conversation history
- Task data
- User preferences
- API response cache

Memory is stored in the `memory/` directory with appropriate subdirectories for different types of data.

## Configuration System

Configuration is managed through:

- Environment variables (`.env` file)
- YAML configuration files in the `configs/` directory
- Command-line arguments

## Extension Points

General Pulse is designed to be easily extended:

1. Add new skills in the `skills/` directory
2. Add new tools in the `tools/` directory
3. Add new utilities in the `utils/` directory
4. Update command patterns in `configs/command_patterns.yaml`
