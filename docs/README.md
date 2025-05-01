# P.U.L.S.E. Documentation

Welcome to the P.U.L.S.E. (Prime Uminda's Learning System Engine) documentation. This directory contains comprehensive documentation for all aspects of the P.U.L.S.E. AI Personal Workflow Ops Assistant.

## Quick Reference Guide

| If you want to...                      | Go to...                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------- |
| **Install P.U.L.S.E.**                 | [Installation and Configuration Guide](INSTALLATION_AND_CONFIGURATION.md) |
| **Learn how to use P.U.L.S.E.**        | [User Guide](USER_GUIDE.md)                                               |
| **Understand the system architecture** | [Core Documentation](CORE_DOCUMENTATION.md)                               |
| **Learn about features**               | [Features Documentation](FEATURES_DOCUMENTATION.md)                       |
| **Explore integrations**               | [Integrations Documentation](INTEGRATIONS_DOCUMENTATION.md)               |
| **Contribute to development**          | [Development Guide](DEVELOPMENT_GUIDE.md)                                 |
| **Understand the AI models**           | [Model Routing System](MODEL_ROUTING_SYSTEM.md)                           |
| **Learn about memory and persistence** | [Memory and Persistence](MEMORY_AND_PERSISTENCE.md)                       |
| **Explore the personality system**     | [Identity and Personality](IDENTITY_AND_PERSONALITY.md)                   |
| **See the roadmap**                    | [Roadmap and Future Plans](ROADMAP_AND_FUTURE_PLANS.md)                   |

## Documentation Structure

We've organized the documentation into consolidated files for easier navigation, with specialized subdirectories for specific features and components.

## Core Documentation

These files provide comprehensive information about the core aspects of P.U.L.S.E.:

- [Core Documentation](CORE_DOCUMENTATION.md) - System architecture, error handling, model integration, installation and configuration
- [Features Documentation](FEATURES_DOCUMENTATION.md) - Core features, advanced features, and functionality
- [Integrations Documentation](INTEGRATIONS_DOCUMENTATION.md) - GitHub, Notion, MongoDB, OpenRouter, and Ollama integrations
- [Development Guide](DEVELOPMENT_GUIDE.md) - Setup, coding standards, testing, contributing, and roadmap
- [Identity and Personality](IDENTITY_AND_PERSONALITY.md) - Identity system, personality engine, and self-awareness
- [Model Routing System](MODEL_ROUTING_SYSTEM.md) - Adaptive router, neural intent classification, and model mapping
- [Memory and Persistence](MEMORY_AND_PERSISTENCE.md) - Chat persistence, vector database, and memory management

## User and Installation Guides

These files provide information for users and administrators:

- [Installation and Configuration Guide](INSTALLATION_AND_CONFIGURATION.md) - How to install and configure P.U.L.S.E.
- [User Guide](USER_GUIDE.md) - How to use P.U.L.S.E. and its features

## Development and Planning

These files provide information for developers and project planning:

- [Roadmap and Future Plans](ROADMAP_AND_FUTURE_PLANS.md) - Comprehensive roadmap and future plans
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Summary of implementation details
- [P.U.L.S.E. Rebranding](PULSE_REBRANDING.md) - Information about the rebranding to P.U.L.S.E.
- [Mistral Integration](MISTRAL_INTEGRATION.md) - Details about the Mistral-Small integration

## Feature-Specific Documentation

### Advanced Features

The `advanced/` directory contains documentation for advanced features:

- [AI Commit Messages](advanced/ai_commit_messages.md) - AI-driven commit message generation
- [Bug Bounty Hunter](advanced/bug_bounty_hunter.md) - AI-powered bug detection (in development)

### Feature Modules

The `features/` directory contains documentation for specific features:

- [DateTime Functionality](features/datetime_functionality.md) - Date, time, and timezone features
- [Intent Classification](features/intent_classification.md) - Intent classification system
- [Offline Mode](features/offline_mode.md) - Working offline with Ollama and DistilBERT
- [Ollama Integration](features/ollama_integration.md) - Integration with Ollama for local models
- [Optimized Model Interface](features/optimized_model_interface.md) - Optimized interface for AI models

### Integration Details

The `integrations/` directory contains documentation for external integrations:

- [GitHub Integration](integrations/github_integration.md) - Working with GitHub repositories
- [GitHub-Notion Sync](integrations/github_notion_sync.md) - Bidirectional synchronization between GitHub and Notion
- [Notion Integration](integrations/notion_integration.md) - Working with Notion documents
- [OpenRouter Integration](integrations/openrouter_integration.md) - Multi-model AI capabilities

### Personality Components

The `personality/` directory contains documentation for personality components:

- [Charisma Engine](personality/charisma.md) - Charisma engine for engaging responses
- [Self-Awareness Module](personality/self_awareness.md) - Self-awareness module for system introspection

## Project Structure

```
P.U.L.S.E./
├── configs/           # Configuration files
│   ├── logging_config.yaml  # Logging configuration
│   ├── model_api_config.yaml  # Model API configuration
│   ├── model_roles.yaml  # Model role assignments
│   ├── personality_traits.yaml  # Personality configuration
│   └── command_patterns.yaml  # Command recognition patterns
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
│   └── *.log          # Log files
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
│   └── fix_compatibility.py  # Compatibility fixes
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
│   └── notion_integration.py  # Notion integration
├── utils/             # Utility functions
│   ├── context_manager.py  # Context management
│   ├── intent_preprocessor.py  # Intent preprocessing
│   ├── integration_error_handler.py  # Integration error handling
│   ├── model_error_handler.py  # Model error handling
│   ├── error_monitoring.py  # Error monitoring
│   ├── log.py         # Logging utilities
│   ├── memory.py      # Memory management
│   ├── neural_router.py  # Neural routing
│   ├── optimization.py  # Hardware optimizations
│   ├── system_utils.py  # System utilities
│   ├── unified_logger.py  # Unified logging
│   └── vector_db.py   # Vector database utilities
├── .env               # Environment variables
├── .env.example       # Example environment variables
├── .gitignore         # Git ignore file
├── pulse.py           # Main entry point
├── pulse_core.py      # Core functionality
├── cli_ui_launcher.py  # CLI UI launcher
├── README.md          # Main README file
└── requirements.txt   # Python dependencies
```

## Getting Started

To get started with P.U.L.S.E., see the [Installation and Configuration Guide](INSTALLATION_AND_CONFIGURATION.md) for detailed setup instructions, and the [User Guide](USER_GUIDE.md) for information on how to use the system effectively.
