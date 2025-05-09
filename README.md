# P.U.L.S.E.

<p align="center">
  <strong>Prime Uminda's Learning System Engine</strong><br>
  Your Loyal AI Companion for coding, freelancing, and leveling up in life!
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#development">Development</a>
</p>

## Overview

P.U.L.S.E. (Prime Uminda's Learning System Engine) is a powerful AI assistant designed to be your loyal companion, helping you with coding, freelancing, and personal growth. Inspired by J.A.R.V.I.S. (Just A Rather Very Intelligent System) from Iron Man, it combines multiple AI models, a robust memory system, and a personality that adapts to your needs and preferences, with a special focus on anime-inspired motivation and hustle-coding mindset.

## Quick Reference Guide

| If you want to...             | Go to...                                      |
| ----------------------------- | --------------------------------------------- |
| **Install P.U.L.S.E.**        | [Installation](#installation)                 |
| **Use P.U.L.S.E.**            | [Usage](#usage)                               |
| **Learn about features**      | [Features](#features)                         |
| **Understand the AI crew**    | [AI Crew System](#ai-crew-system)             |
| **Explore the documentation** | [Documentation](#documentation)               |
| **Contribute to development** | [Development](#development)                   |
| **See recent changes**        | [Recently Implemented](#recently-implemented) |

## Features

### Core Capabilities

- 🧠 **Multi-Model AI System** - Leverages specialized AI models for different tasks (Mistral-Small as primary brain, with specialized OpenRouter free models for specific tasks)
- 💬 **Natural Language Interface** - Communicate with the assistant using conversational language
- 🛡️ **Robust Error Handling** - Comprehensive error handling with monitoring, retry logic, and user-friendly messages
- 🔄 **Self-Healing Protocols** - Automatically recovers from API failures and errors
- 🧩 **Personality Engine** - Adapts responses based on configurable personality traits
- 💾 **Long-Term Memory** - Remembers your projects, goals, and preferences
- ⚡ **Hardware Optimization** - Designed to run efficiently on limited hardware
- 🚀 **Offline Mode** - Work offline with local models using Ollama
- 🔍 **Intent Classification** - Ultra-lightweight intent classification using MiniLM
- 🔌 **MCP Integration** - Interact with external tools and services through Model Context Protocol servers
- 🔄 **Repository Pattern** - Flexible and resilient data storage with primary-backup architecture

### AI Crew System

P.U.L.S.E. uses a dynamic AI crew system where multiple specialized AI models work together:

- **Mistral-Small** (mistralai/mistral-small-3.1-24b-instruct:free): The crew leader, orchestrating other models and maintaining a personal relationship with you
- **DeepCoder** (agentica-org/deepcoder-14b-preview:free): Code generation specialist for writing, debugging, and optimizing code
- **DeepSeek** (deepseek/deepseek-r1-zero:free): Troubleshooting expert for diagnosing errors and providing DevOps fixes
- **Llama-Doc** (meta-llama/llama-4-scout:free): Documentation expert for creating clear, concise documentation
- **Llama-Technical** (meta-llama/llama-3.3-70b-instruct:free): Technical translation expert for explaining complex concepts
- **Hermes** (nousresearch/deephermes-3-llama-3-8b-preview:free): Brainstorming specialist for generating creative ideas
- **Molmo** (allenai/molmo-7b-d:free): Ethical AI specialist for providing ethical considerations
- **Kimi** (moonshotai/moonlight-16b-a3b-instruct:free): Visual reasoning and design specialist
- **Nemotron** (nvidia/llama-3.1-nemotron-ultra-253b-v1:free): Advanced reasoning and problem-solving specialist
- **Gemma** (google/gemma-3-27b-it:free): Mathematical and chemical problem-solving specialist
- **Dolphin** (cognitivecomputations/dolphin3.0-mistral-24b:free): Script optimization and automation specialist
- **MiniLM** (local): Ultra-lightweight intent classification for minimal memory usage
- **Phi** (microsoft/phi-2:free via Ollama): Low-resource specialist for offline operation

Each model has a specific role, personality, and prompt, allowing them to maintain consistent character and collaborate effectively. The system automatically routes queries to the appropriate specialist based on the query type.

### Context & Memory

- **Short-Term Context**: Maintains conversation history for coherent interactions
- **Long-Term Memory**: SQLite database for persistent storage of:
  - User identity and preferences
  - Projects and interests
  - Goals and priorities
  - Important interactions
- **Vector Database**: Uses LanceDB for semantic search and context retrieval
- **MongoDB Integration**: Stores interactions in MongoDB Atlas for cloud persistence
- **Chat History Manager**: Provides persistent chat history with memory summarization
- **Repository Pattern**: Flexible data access with:
  - Primary-backup architecture for reliability
  - Circuit breaker pattern for failure handling
  - Redis caching for performance
  - Comprehensive error handling
- **Transaction Support**: ACID transactions for data integrity

### Adaptive Neural Router

- **Hardware-Aware Routing**: Automatically selects models based on available system resources
- **Neural Intent Classification**: Uses neural networks to determine query intent
- **Keyword Detection**: Identifies specialized queries through keyword analysis
- **Memory-Constrained Mode**: Falls back to lightweight models when system resources are limited
- **Offline Mode Detection**: Automatically switches to local models when internet connectivity is lost
- **Caching**: Caches routing decisions to reduce overhead and improve response time

### Personality & Workflow

- **Adaptive Personality**: Adjustable traits like informative, courageous, positive, casual, and strict
- **Anime-Inspired**: References anime like Jujutsu Kaisen and Solo Leveling for motivation
- **Goal Tracking**: Reminds you of your goals and helps you stay on track
- **Self-Awareness Module**: System introspection and status reporting capabilities
- **Charisma Engine**: Provides engaging, lively responses with anime-inspired wit
- **Mood Tracking**: Detects and adapts to user mood from conversation context

### GitHub-Notion Integration

- **Bidirectional Sync**: Synchronizes data between GitHub repositories and Notion databases
- **Memory-Aware Scheduling**: Intelligently schedules sync operations based on system resources
- **MongoDB Tracking**: Tracks sync status and history in MongoDB Atlas
- **Error Handling**: Robust error handling for API rate limits and connection issues
- **Customizable Sync Interval**: Configurable sync interval with adaptive adjustment

### Hardware Optimization

- **Memory Management**: Careful memory usage with garbage collection
- **GPU Optimization**: Limited VRAM usage for GPU acceleration
- **SQLite Optimization**: WAL mode and other optimizations for better performance
- **SSD Detection**: Automatically uses SSD for temp files if available

## Recently Implemented

### Phase 1: Foundation Improvements (Completed)

🔧 **Vector Database Fix** - Fixed LanceDB compatibility issues with proper version detection and fallback to SQLite
🔄 **Model Routing Enhancement** - Ensured Mistral-Small is consistently used as the main brain for general queries
🏗️ **Chat Persistence Architecture** - Implemented repository pattern with primary-backup architecture and circuit breaker
🔌 **MCP Integration** - Added Model Context Protocol integration for external tools and services
🛡️ **Error Handling Framework** - Implemented comprehensive error handling with classification and recovery
📊 **Implementation Plan** - Created a detailed implementation plan with phases, metrics, and timelines
📝 **Documentation** - Added comprehensive documentation for all Phase 1 components

### Previous Improvements

🗂️ **Codebase Organization** - Organized codebase with proper directory structure, moved test files to tests directory, and organized scripts
🔒 **Enhanced Identity System** - Implemented robust identity filtering to ensure P.U.L.S.E. maintains its unique identity
🧠 **Advanced Post-Processing** - Added regex-based post-processing to filter out incorrect model identifications
💬 **Improved Chat Persistence** - Enhanced session tracking for more natural conversations with fewer repetitive greetings
⚠️ **Fixed LanceDB Compatibility** - Resolved compatibility issues with LanceDB 0.3.0 while maintaining vector search capabilities
🚀 **Expanded Specialized Models** - Added more specialized models for different tasks (DeepCoder, Llama-Doc, Kimi, Nemotron, Gemma, Dolphin)
🧠 **Self-Awareness Module** - Added a self-awareness module for system introspection and status reporting
⚡ **Memory Optimization** - Enhanced memory optimization with aggressive cleanup and adaptive scheduling
🔄 **GitHub-Notion Sync** - Added GitHub-Notion synchronization with memory-aware scheduling
🎭 **Enhanced Charisma Engine** - Updated charisma engine to use the self-awareness module for better personality
🧪 **Specialized Model Testing** - Added test script for specialized models
🚀 **Rebranding to P.U.L.S.E.** - Renamed from General Pulse to P.U.L.S.E. (Prime Uminda's Learning System Engine)
🎨 **New CLI Header** - Updated CLI header with system vitals and version information
💬 **New Welcome Message** - Implemented time-aware welcome message with pending tasks
🚀 **Mistral-Small Integration** - Replaced Gemini with Mistral-Small (24B parameters) as the main brain
🛡️ **Enhanced Error Handling** - Improved retry logic and error reporting for API calls
🔍 **Neural Router** - Implemented neural router in dedicated routing module for better query routing
📝 **Intent Classification** - Added intent preprocessor for better query understanding
💡 **Testing Infrastructure** - Enhanced testing capabilities with organized test directories
🧹 **Codebase Cleanup** - Removed duplicate files and consolidated implementations for better maintainability
⚡ **Optimized Model Interface** - Enhanced model interface with better memory management and resource optimization
🚀 **Improved Ollama Integration** - Better Ollama management with automatic startup/shutdown and resource monitoring
🔍 **Ultra-Lightweight Intent Classification** - Implemented MiniLM-based intent classification for minimal memory usage and faster inference
🤖 **AI Crew System** - Dynamic AI crew with specialized models, each with a specific role and personality
🧠 **Role-Specific Prompts** - Custom prompts for each AI model to maintain consistent character
🔄 **Improved Shutdown Process** - Enhanced shutdown process with better error handling and resource cleanup
🖥️ **Fixed Character Encoding** - Resolved character encoding issues for better compatibility across platforms
📊 **Vector Database** - Implemented vector database for semantic search and context retrieval

## Getting Started

### Prerequisites

- Python 3.9+
- GitHub account (for GitHub integration)
- OpenRouter API key (for AI model access)
- Notion API key (for Notion integration)

### Installation

1. Clone the repository

```bash
git clone https://github.com/Spyboss/P.U.L.S.E..git
cd P.U.L.S.E.
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Download model files

The repository does not include large model files. You can download them from the following sources:

```bash
# Create a directory for model files
mkdir -p models/distilbert-intent/models--distilbert-base-uncased/

# Download the model files from Hugging Face
python -c "from transformers import AutoTokenizer, AutoModel; tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased'); model = AutoModel.from_pretrained('distilbert-base-uncased')"

# Or use the provided script
python scripts/prep_distilbert.py
```

Alternatively, you can use the MiniLM classifier which is more lightweight and doesn't require downloading large model files.

### Usage

#### Running the Application

```bash
# Run the application
python pulse.py

# Run in simulation mode (without API calls)
python pulse.py --simulate

# Run with debug logging
python pulse.py --debug
```

#### Using the AI Crew

Ask a specific AI crew member:

```
ask mistral what's the weather today?
ask deepcoder to write a Python function to calculate factorial
ask deepseek why my Docker container keeps crashing
```

Use specialized query types:

```
ask code how to implement a binary search tree
ask troubleshoot why my Python script is giving a NameError
ask docs how to document a REST API
ask technical how to explain OAuth to a junior developer
ask brainstorm ideas for a personal finance app
ask ethics considerations for facial recognition in public spaces
ask visual how to design a user-friendly dashboard
ask reasoning how to solve the traveling salesman problem
ask math how to solve a quadratic equation
ask script how to optimize a Python script for memory usage
```

Check the system status:

```
status
```

Manage Ollama for offline mode:

```
ollama status  # Check Ollama status
ollama on      # Start Ollama service
ollama off     # Stop Ollama service
ollama pull phi-2  # Pull a model from Ollama
```

Get help with available commands:

```
help
```

#### AI-Driven Commit Messages

Generate commit messages for GitHub:

```bash
python tests/tools/test_ai_commit.py --owner username --repo reponame --file path/to/file
```

Using the agent:

```
github username/repo commit message file: path/to/file.py
```

## Development

### Project Structure

```
P.U.L.S.E./
├── configs/           # Configuration files
│   ├── logging_config.yaml  # Logging configuration
│   ├── model_api_config.yaml  # Model API configuration
│   ├── model_roles.yaml  # Model role assignments
│   ├── personality_traits.yaml  # Personality configuration
│   ├── command_patterns.yaml  # Command recognition patterns
│   └── mcp_config.yaml  # MCP server configuration
├── context/           # Context management
│   └── history.py     # Conversation history management
├── data/              # Data storage
│   ├── vector_db/     # Vector database storage
│   └── sqlite/        # SQLite database files
├── docs/              # Documentation
│   ├── advanced/      # Advanced feature documentation
│   ├── development/   # Development documentation
│   ├── features/      # Feature documentation
│   ├── integrations/  # Integration documentation
│   ├── personality/   # Personality documentation
│   └── tasks/         # Task management documentation
├── integrations/      # External integrations
│   ├── github_api.py  # GitHub API integration
│   ├── notion_api.py  # Notion API integration
│   └── sync.py        # GitHub-Notion synchronization
├── logs/              # Log files
│   ├── *.log          # Log files
│   └── mcp_servers/   # MCP server logs
├── mcp-servers/       # MCP server submodule
├── models/            # Model files
│   ├── distilbert-intent/  # DistilBERT model files
│   └── keyword_classifier/  # Keyword classifier files
├── personality/       # Personality engine
│   ├── charisma.py    # Charisma engine
│   └── self_awareness.py  # Self-awareness module
├── routing/           # Query routing
│   └── router.py      # Neural router
├── scripts/           # Utility scripts
│   ├── prep_distilbert.py  # DistilBERT preparation
│   ├── run_tests.py   # Test runner
│   ├── fix_compatibility.py  # Compatibility fixes
│   └── tools/         # Tool scripts
│       ├── mcp_server_manager.py  # MCP server management
│       └── test_puppeteer.py  # Puppeteer MCP test
├── skills/            # Core agent skills
│   ├── marketplace.py  # Skill marketplace
│   ├── pulse_agent.py  # Main agent implementation
│   └── model_orchestrator.py  # Model management
├── tests/             # Test suite
│   ├── integrations/  # Integration tests
│   ├── routing/       # Routing tests
│   ├── skills/        # Skills tests
│   ├── tools/         # Tools tests
│   ├── utils/         # Utility tests
│   └── test_*.py      # Core tests
├── tools/             # Integration tools
│   ├── bug_bounty_hunter.py  # Bug bounty hunter
│   ├── github_integration.py  # GitHub integration
│   ├── notion_integration.py  # Notion integration
│   └── mcp_integration.py  # MCP integration
├── utils/             # Utility functions
│   ├── context_manager.py  # Context management
│   ├── intent_preprocessor.py  # Intent preprocessing
│   ├── integration_error_handler.py  # Integration error handling
│   ├── model_error_handler.py  # Model error handling
│   ├── error_monitoring.py  # Error monitoring
│   ├── circuit_breaker.py  # Circuit breaker pattern
│   ├── error_handler.py  # Error handling framework
│   ├── error_taxonomy.py  # Error classification
│   ├── log.py         # Logging utilities
│   ├── mcp_manager.py  # MCP server manager
│   ├── memory.py      # Memory management
│   ├── neural_router.py  # Neural routing
│   ├── optimization.py  # Hardware optimizations
│   ├── repository/    # Repository pattern implementation
│   │   ├── base.py    # Base repository interfaces
│   │   ├── chat.py    # Chat entities and repositories
│   │   ├── factory.py  # Repository factory
│   │   ├── mongodb.py  # MongoDB implementation
│   │   ├── redis.py   # Redis caching implementation
│   │   ├── sqlite.py  # SQLite implementation
│   │   └── transaction.py  # Transaction support
│   ├── retry.py       # Retry mechanisms
│   ├── security.py    # Security utilities
│   ├── system_utils.py  # System utilities
│   ├── telemetry.py   # Telemetry collection
│   ├── unified_logger.py  # Unified logging
│   └── vector_db.py   # Vector database utilities
├── .env               # Environment variables
├── .env.example       # Example environment variables
├── .gitignore         # Git ignore file
├── .gitmodules        # Git submodules
├── pulse.py           # Main entry point
├── pulse_core.py      # Core functionality
├── cli_ui_launcher.py  # CLI UI launcher
├── README.md          # This file
└── requirements.txt   # Python dependencies
```

### Running Tests

```bash
# Run all tests using the test runner script
python scripts/run_tests.py --all

# Run specific test categories
python scripts/run_tests.py --utils    # Run utility tests
python scripts/run_tests.py --skills   # Run skills tests
python scripts/run_tests.py --tools    # Run tools tests
python scripts/run_tests.py --routing  # Run routing tests
python scripts/run_tests.py --integrations # Run integration tests

# Run with verbose output
python scripts/run_tests.py --verbose

# Run specific test file
python -m unittest tests/utils/test_vector_db.py

# Or use unittest directly for all tests
python -m unittest discover tests
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

Comprehensive documentation is available in the [docs](docs) directory. We've organized the documentation into consolidated files for easier navigation.

### Core Documentation

- [Core Documentation](docs/CORE_DOCUMENTATION.md) - System architecture, error handling, model integration, installation and configuration
- [Features Documentation](docs/FEATURES_DOCUMENTATION.md) - Core features, advanced features, and functionality
- [Integrations Documentation](docs/INTEGRATIONS_DOCUMENTATION.md) - GitHub, Notion, MongoDB, OpenRouter, and Ollama integrations
- [Development Guide](docs/DEVELOPMENT_GUIDE.md) - Setup, coding standards, testing, contributing, and roadmap
- [Identity and Personality](docs/IDENTITY_AND_PERSONALITY.md) - Identity system, personality engine, and self-awareness
- [Model Routing System](docs/MODEL_ROUTING_SYSTEM.md) - Adaptive router, neural intent classification, and model mapping
- [Memory and Persistence](docs/MEMORY_AND_PERSISTENCE.md) - Chat persistence, vector database, and memory management
- [MCP Servers](docs/MCP_SERVERS.md) - Model Context Protocol server integration
- [Error Handling](docs/ERROR_HANDLING.md) - Comprehensive error handling framework

### User and Installation Guides

- [Installation and Configuration Guide](docs/INSTALLATION_AND_CONFIGURATION.md) - How to install and configure P.U.L.S.E.
- [User Guide](docs/USER_GUIDE.md) - How to use P.U.L.S.E. and its features

### Development and Planning

- [Roadmap and Future Plans](docs/ROADMAP_AND_FUTURE_PLANS.md) - Comprehensive roadmap and future plans
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Detailed implementation plan with phases, metrics, and timelines
- [Phase 1 Summary](docs/PHASE1_SUMMARY.md) - Summary of Phase 1 implementation
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - Summary of implementation details
- [P.U.L.S.E. Rebranding](docs/PULSE_REBRANDING.md) - Information about the rebranding to P.U.L.S.E.
- [Mistral Integration](docs/MISTRAL_INTEGRATION.md) - Details about the Mistral-Small integration
- [Vector DB Fix](docs/VECTOR_DB_FIX.md) - Details about the vector database fix
- [Model Routing Fix](docs/MODEL_ROUTING_FIX.md) - Details about the model routing fix

### Feature-Specific Documentation

- [Advanced Features](docs/advanced/) - Documentation for advanced features like AI commit messages and bug detection
- [Feature Modules](docs/features/) - Documentation for specific features like datetime functionality and offline mode
- [Integration Details](docs/integrations/) - Documentation for external integrations with GitHub, Notion, and more

## License

MIT License

## Acknowledgments

- OpenRouter for simplifying access to multiple AI models
- GitHub API for repository integration capabilities
- Notion API for knowledge management integration
