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

### AI Crew System

P.U.L.S.E. uses a dynamic AI crew system where multiple specialized AI models work together:

- **Mistral-Small**: The crew leader, orchestrating other models and maintaining a personal relationship with you
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
- **Claude**: Paid fallback model for complex tasks (requires paid API access)
- **Grok**: Paid fallback model with real-time knowledge (requires paid API access)

Each model has a specific role, personality, and prompt, allowing them to maintain consistent character and collaborate effectively. The system automatically routes queries to the appropriate specialist based on the query type.

### Context & Memory

- **Short-Term Context**: Maintains conversation history for coherent interactions
- **Long-Term Memory**: SQLite database for persistent storage of:
  - User identity and preferences
  - Projects and interests
  - Goals and priorities
  - Important interactions
- **AugmentCode Integration**: Leverages AugmentCode's context engine for deeper understanding

### Personality & Workflow

- **Adaptive Personality**: Adjustable traits like informative, courageous, positive, casual, and strict
- **Anime-Inspired**: References anime like Jujutsu Kaisen and Solo Leveling for motivation
- **Goal Tracking**: Reminds you of your goals and helps you stay on track
- **AI Hustle Army Integration**: Syncs with your AI workflow (Claude, DeepSeek, Grok, Luminar)

### Hardware Optimization

- **Memory Management**: Careful memory usage with garbage collection
- **GPU Optimization**: Limited VRAM usage for GPU acceleration
- **SQLite Optimization**: WAL mode and other optimizations for better performance
- **SSD Detection**: Automatically uses SSD for temp files if available

## Recently Implemented

🚀 **Rebranding to P.U.L.S.E.** - Renamed from General Pulse to P.U.L.S.E. (Prime Uminda's Learning System Engine)
🎨 **New CLI Header** - Updated CLI header with system vitals and version information
💬 **New Welcome Message** - Implemented time-aware welcome message with pending tasks
🚀 **Mistral-Small Integration** - Replaced Gemini with Mistral-Small (24B parameters) as the main brain
🛡️ **Enhanced Error Handling** - Improved retry logic and error reporting for API calls
🔍 **Neural Router Updates** - Updated neural router to use Mistral-Small for routing decisions
📝 **Intent Classification Improvements** - Modified natural intent handler to use Mistral-Small
💡 **Testing Infrastructure** - Enhanced testing capabilities for the main brain
🧹 **Codebase Cleanup** - Removed duplicate files and consolidated implementations for better maintainability
⚡ **Optimized Model Interface** - Enhanced model interface with better memory management and resource optimization
🚀 **Improved Ollama Integration** - Better Ollama management with automatic startup/shutdown and resource monitoring
🔍 **Ultra-Lightweight Intent Classification** - Implemented MiniLM-based intent classification for minimal memory usage and faster inference
🤖 **AI Crew System** - Dynamic AI crew with specialized models, each with a specific role and personality
🧠 **Role-Specific Prompts** - Custom prompts for each AI model to maintain consistent character
🔄 **Improved Shutdown Process** - Enhanced shutdown process with better error handling and resource cleanup
🖥️ **Fixed Character Encoding** - Resolved character encoding issues for better compatibility across platforms

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
ask mistral-small about the latest AI trends
```

Use specialized query types:

```
ask code how to implement a binary search tree
ask troubleshoot why my Docker container keeps crashing
ask write a blog post about AI ethics
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
│   ├── models.yaml    # Model configurations
│   └── hardware.yaml  # Hardware optimizations
├── data/              # Data storage
│   └── *.db           # SQLite database files
├── docs/              # Documentation
│   ├── ARCHITECTURE.md # Architecture overview
│   ├── USER_GUIDE.md  # User guide
│   ├── DEVELOPER_GUIDE.md # Developer guide
│   ├── ERROR_HANDLING.md # Error handling documentation
│   ├── features/      # Feature documentation
│   └── integrations/  # Integration documentation
├── logs/              # Log files
│   └── *.log          # Log files
├── memory/            # Memory storage
│   └── tasks.db       # Task memory database
├── scripts/           # Utility scripts
│   ├── tools/         # Tool scripts
│   └── utils/         # Utility scripts
├── skills/            # Core agent skills
│   ├── github_skills.py # GitHub integration skills
│   ├── optimized_model_interface.py # Optimized model interface
│   ├── pulse_agent.py # Main agent implementation
│   ├── model_orchestrator.py # Model management
│   └── task_memory_manager.py # Task memory management
├── tests/             # Test suite
│   ├── test_context_manager.py # Context tests
│   ├── test_memory_manager.py # Memory tests
│   ├── test_model_mappings.py # Model mapping tests
│   ├── test_model_routing.py # Model routing tests
│   ├── test_offline_mode.py # Offline mode tests
│   └── test_pulse_agent.py # Agent tests
├── tools/             # Integration tools
│   ├── bug_bounty_hunter.py # Bug bounty hunter
│   ├── github_integration.py # GitHub integration
│   └── notion_overplanning_detector.py # Notion overplanning detector
├── utils/             # Utility functions
│   ├── cli_ui.py      # CLI user interface
│   ├── context_manager.py # Context management
│   ├── distilbert_classifier.py # DistilBERT intent classifier
│   ├── execution_flow.py # Execution flow management
│   ├── intent_handler.py # Intent recognition
│   ├── memory_manager.py # Memory storage
│   ├── ollama_manager.py # Ollama service management
│   ├── optimization.py # Hardware optimizations
│   ├── personality_engine.py # Personality traits
│   └── task_orchestrator.py # Task orchestration
├── .env               # Environment variables
├── .gitignore         # Git ignore file
├── pulse.py           # Main entry point
├── run_tests.py       # Test runner
├── README.md          # This file
└── requirements.txt   # Python dependencies
```

### Running Tests

```bash
# Run all tests using the test runner script
python run_tests.py

# Run specific test file
python run_tests.py tests/test_context_manager.py

# Run with verbose output
python run_tests.py --verbose

# Or use unittest directly
python -m unittest discover tests
python -m unittest tests.test_pulse_agent
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

Comprehensive documentation is available in the [docs](docs) directory:

- [Usage Guide](docs/USAGE_GUIDE.md) - Detailed instructions on how to use P.U.L.S.E.
- [AI Crew](docs/AI_CREW.md) - Information about the AI crew system
- [Architecture](docs/ARCHITECTURE.md) - Overview of the system architecture
- [Error Handling](docs/ERROR_HANDLING.md) - Comprehensive error handling and monitoring
- [Mistral Integration](docs/MISTRAL_INTEGRATION.md) - Details about the Mistral-Small integration
- [Gemini to Mistral Migration](docs/GEMINI_TO_MISTRAL_MIGRATION.md) - Migration process from Gemini to Mistral-Small

### Feature Documentation

- [AI Crew System](docs/AI_CREW.md) - Dynamic AI crew with specialized models
- [DateTime Functionality](docs/features/datetime_functionality.md) - Date, time, and timezone features
- [Offline Mode](docs/features/offline_mode.md) - Working offline with Ollama and DistilBERT
- [GitHub Integration](docs/integrations/github_integration.md) - Working with GitHub repositories
- [Notion Integration](docs/integrations/notion_integration.md) - Working with Notion documents
- [OpenRouter Integration](docs/integrations/openrouter_integration.md) - Multi-model AI capabilities
- [AI Commit Messages](docs/advanced/ai_commit_messages.md) - AI-driven commit message generation
- [Testing](docs/tests/README.md) - Testing procedures and scripts

## License

MIT License

## Acknowledgments

- OpenRouter for simplifying access to multiple AI models
- GitHub API for repository integration capabilities
- Notion API for knowledge management integration
