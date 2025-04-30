# P.U.L.S.E. Documentation

Welcome to the P.U.L.S.E. (Prime Uminda's Learning System Engine) documentation. This directory contains comprehensive documentation for all aspects of the P.U.L.S.E. AI Personal Workflow Ops Assistant.

## Documentation Index

### Core Documentation

- [Usage Guide](USAGE_GUIDE.md) - Detailed instructions on how to use P.U.L.S.E.
- [AI Crew](AI_CREW.md) - Information about the AI crew system
- [Architecture](ARCHITECTURE.md) - Overview of the system architecture
- [Error Handling](ERROR_HANDLING.md) - Comprehensive error handling and monitoring
- [Mistral Integration](MISTRAL_INTEGRATION.md) - Details about the Mistral-Small integration
- [Gemini to Mistral Migration](GEMINI_TO_MISTRAL_MIGRATION.md) - Migration process from Gemini to Mistral-Small
- [Identity System](IDENTITY_SYSTEM.md) - Implementation of robust identity system for P.U.L.S.E.
- [Developer Guide](DEVELOPER_GUIDE.md) - Guide for developers working on P.U.L.S.E.
- [P.U.L.S.E. Rebranding](PULSE_REBRANDING.md) - Information about the rebranding to P.U.L.S.E.
- [Installation Guide](installation.md) - How to install and set up P.U.L.S.E.
- [Configuration Guide](configuration.md) - How to configure P.U.L.S.E.

### Feature Documentation

- [Chat Persistence](chat_persistence.md) - Enhanced chat persistence implementation
- [Vector Database](vector_database.md) - Vector database for semantic search
- [LanceDB Upgrade](lancedb_upgrade.md) - Information about LanceDB integration
- [Enhancements](ENHANCEMENTS.md) - Planned and implemented enhancements
- [Local Models](LOCAL_MODELS.md) - Information about local model usage
- [Model Mappings](MODEL_MAPPINGS.md) - Model ID mappings and configurations
- [Model Routing](MODEL_ROUTING.md) - Neural routing between different models
- [Timezone Feature](TIMEZONE_FEATURE.md) - Timezone functionality

### Feature Modules

- [DateTime Functionality](features/datetime_functionality.md) - Date, time, and timezone features
- [Offline Mode](features/offline_mode.md) - Working offline with Ollama and DistilBERT
- [Intent Classification](features/intent_classification.md) - Intent classification system
- [Ollama Integration](features/ollama_integration.md) - Integration with Ollama for local models
- [Optimized Model Interface](features/optimized_model_interface.md) - Optimized interface for AI models

### Integrations

- [GitHub Integration](integrations/github_integration.md) - Working with GitHub repositories
- [Notion Integration](integrations/notion_integration.md) - Working with Notion documents
- [OpenRouter Integration](integrations/openrouter_integration.md) - Multi-model AI capabilities

### Advanced Features

- [AI Commit Messages](advanced/ai_commit_messages.md) - AI-driven commit message generation
- [Bug Bounty Hunter](advanced/bug_bounty_hunter.md) - AI-powered bug detection (in development)

### Development and Testing

- [Contributing](development/contributing.md) - Guidelines for contributing to P.U.L.S.E.
- [Architecture](development/architecture.md) - Detailed architecture documentation
- [Roadmap](development/roadmap.md) - Development roadmap
- [Enhancements](development/enhancements.md) - Planned enhancements
- [Improvement Plan](development/improvement_plan.md) - Improvement plans
- [Testing](tests/README.md) - Testing procedures and scripts

## Project Structure

```
P.U.L.S.E./
├── configs/           # Configuration files
│   └── models.py      # Model configurations
├── context/           # Context management
│   └── history.py     # Conversation history management
├── data/              # Data storage
│   ├── vector_db/     # Vector database storage
│   └── *.db           # SQLite database files
├── docs/              # Documentation
│   ├── advanced/      # Advanced feature documentation
│   ├── development/   # Development documentation
│   ├── features/      # Feature documentation
│   ├── integrations/  # Integration documentation
│   └── tests/         # Test documentation
├── integrations/      # External integrations
│   └── sync.py        # GitHub-Notion synchronization
├── logs/              # Log files
│   └── *.log          # Log files
├── memory/            # Memory storage
│   └── tasks.db       # Task memory database
├── personality/       # Personality engine
│   ├── charisma.py    # Charisma engine
│   └── self_awareness.py # Self-awareness module
├── routing/           # Query routing
│   └── router.py      # Neural router
├── scripts/           # Utility scripts
│   ├── fix_compatibility.py # Compatibility fixes
│   ├── fix_numpy.py   # NumPy fixes
│   ├── fix_pytorch.py # PyTorch fixes
│   └── test_vector_db.py # Vector database test script
├── skills/            # Core agent skills
│   ├── marketplace.py # Skill marketplace
│   ├── pulse_agent.py # Main agent implementation
│   └── model_orchestrator.py # Model management
├── tests/             # Test suite
│   ├── integrations/  # Integration tests
│   ├── routing/       # Routing tests
│   ├── skills/        # Skills tests
│   ├── tools/         # Tools tests
│   ├── utils/         # Utility tests
│   └── test_*.py      # Core tests
├── tools/             # Integration tools
│   ├── bug_bounty_hunter.py # Bug bounty hunter
│   ├── github_integration.py # GitHub integration
│   └── notion_overplanning_detector.py # Notion overplanning detector
├── utils/             # Utility functions
│   ├── context_manager.py # Context management
│   ├── intent_preprocessor.py # Intent preprocessing
│   ├── log.py         # Logging utilities
│   ├── memory.py      # Memory management
│   ├── neural_router.py # Neural routing
│   ├── optimization.py # Hardware optimizations
│   ├── personality_engine.py # Personality traits
│   ├── sqlite_utils.py # SQLite utilities
│   ├── system_utils.py # System utilities
│   ├── unified_logger.py # Unified logging
│   └── vector_db.py   # Vector database utilities
├── pulse.py           # Main entry point
├── pulse_core.py      # Core functionality
└── cli_ui_launcher.py # CLI UI launcher
```

## Getting Started

To get started with P.U.L.S.E., see the [Installation Guide](installation.md) and [User Guide](user_guide.md).
