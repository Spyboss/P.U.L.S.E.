# P.U.L.S.E. Installation and Configuration Guide

This guide provides comprehensive instructions for installing and configuring P.U.L.S.E. (Prime Uminda's Learning System Engine).

## Installation

### Prerequisites

P.U.L.S.E. requires:
- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Required Dependencies

The following Python packages are required:
- prompt_toolkit
- structlog
- python-dotenv
- pytz
- python-dateutil
- aiohttp
- lancedb==0.3.0 (specific version for stability)

### Recommended Dependencies

These packages enable additional features:
- transformers (for local intent classification)
- torch (for local AI models)
- openrouter (for multi-model AI capabilities)
- PyGithub (for GitHub integration)
- notion-client (for Notion integration)
- ollama (for local model support)
- pymongo (for MongoDB integration)

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/Spyboss/P.U.L.S.E..git
cd P.U.L.S.E.
```

#### 2. Create a Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
# Install required dependencies
pip install -r requirements.txt

# Install optional dependencies for all features
pip install -r requirements-optional.txt
```

#### 4. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Required for AI capabilities
OPENROUTER_API_KEY=your_openrouter_api_key

# Required for GitHub integration
GITHUB_TOKEN=your_github_token

# Required for Notion integration
NOTION_API_KEY=your_notion_api_key

# Required for MongoDB integration
MONGODB_URI=your_mongodb_connection_string
```

You can obtain these API keys from:
- [OpenRouter](https://openrouter.ai/keys)
- [GitHub Developer Settings](https://github.com/settings/tokens)
- [Notion Integrations](https://www.notion.so/my-integrations)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

#### 5. Verify Installation

Run the following command to verify your installation:

```bash
python pulse.py --debug
```

If everything is set up correctly, you should see the P.U.L.S.E. banner and be able to interact with the agent.

### Troubleshooting

#### Missing Dependencies

If you see errors about missing dependencies, install them manually:

```bash
pip install package_name
```

#### API Key Issues

If you see warnings about missing API keys, make sure your `.env` file is properly configured and located in the project root directory.

#### Simulation Mode

If you want to test P.U.L.S.E. without API keys, use simulation mode:

```bash
python pulse.py --simulate
```

## Configuration

### Configuration Files

P.U.L.S.E. uses several configuration files located in the `configs/` directory:

- `model_api_config.yaml` - AI model configuration
- `personality_traits.yaml` - Agent personality settings
- `command_patterns.yaml` - Command recognition patterns
- `logging_config.yaml` - Logging configuration

### Environment Variables

Environment variables are stored in the `.env` file in the project root. Here are the available options:

#### Required Variables

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

#### Optional Variables

```
# Direct API keys (if not using OpenRouter)
CLAUDE_API_KEY=your_claude_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Local model configuration
USE_LOCAL_MODELS=true
OLLAMA_BASE_URL=http://localhost:11434

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=pulse.log
```

### AI Model Configuration

You can configure AI model settings in `configs/model_api_config.yaml`:

```yaml
# Example configuration
models:
  default: mistral-small

  mistral-small:
    api_url: https://openrouter.ai/api/v1/chat/completions
    model_name: mistralai/mistral-small-3.1-24b-instruct:free
    temperature: 0.7
    max_tokens: 1000

  deepseek:
    api_url: https://openrouter.ai/api/v1/chat/completions
    model_name: deepseek-ai/deepseek-coder-33b-instruct:free
    temperature: 0.7
    max_tokens: 1000

openrouter:
  models:
    mistral_small: "mistralai/mistral-small-3.1-24b-instruct:free"
    debug_troubleshooting: "deepseek-ai/deepseek-coder-33b-instruct:free"
    code_generation: "deepseek-ai/deepseek-coder-33b-instruct:free"
    documentation: "meta-llama/llama-3-70b-instruct:free"
    default: "mistralai/mistral-small-3.1-24b-instruct:free"
```

### Personality Configuration

Configure the agent's personality in `configs/personality_traits.yaml`:

```yaml
# Example configuration
personality:
  name: P.U.L.S.E.
  traits:
    helpfulness: 0.9
    creativity: 0.7
    humor: 0.5
    conciseness: 0.6
    formality: 0.5
    anime_references: 0.4

  response_styles:
    default: balanced
    technical: detailed
    creative: imaginative
    business: professional
```

### Command Pattern Configuration

Configure command recognition patterns in `configs/command_patterns.yaml`:

```yaml
# Example configuration
commands:
  time:
    - "what(?:'s| is) the time"
    - "current time"
    - "time now"

  timezone:
    - "what(?:'s| is) the time in ([a-zA-Z\\s]+)"
    - "time (?:in|at) ([a-zA-Z\\s]+)"
    - "current time in ([a-zA-Z\\s]+)"

  github:
    - "github ([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)"
    - "show (?:my )?github repositories"
    - "list (?:github )?issues for ([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)"
```

### Logging Configuration

Configure logging in `configs/logging_config.yaml`:

```yaml
# Example configuration
version: 1
formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  structured:
    format: "%(message)s"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.FileHandler
    level: DEBUG
    formatter: structured
    filename: logs/pulse.log
    encoding: utf8

loggers:
  "": # Root logger
    level: DEBUG
    handlers: [console, file]
    propagate: no
```

### Memory Configuration

P.U.L.S.E. stores persistent data in several locations:

- `data/vector_db/` - Vector database for semantic search
- `data/sqlite/` - SQLite database for fallback storage
- MongoDB Atlas - Cloud storage for chat history and memories

You can configure memory settings in `configs/memory_config.yaml`:

```yaml
# Example configuration
memory:
  conversation_history_limit: 100
  cache_expiration: 3600 # seconds
  vector_db_path: data/vector_db
  sqlite_path: data/sqlite/pulse.db
```

### Advanced Configuration

#### Custom Command Handlers

You can create custom command handlers by adding Python files to the `utils/` directory and registering them in `utils/intent_handler.py`.

#### Model Role Specialization

Configure which models handle specific tasks in `configs/model_roles.yaml`:

```yaml
# Example configuration
roles:
  debug: deepseek
  code: deepcoder
  docs: llama-doc
  explain: llama-doc
  troubleshoot: deepseek
  trends: mistral-small
  content: llama-content
  technical: llama-technical
  brainstorm: hermes
  ethics: olmo
  automate: mistralai
  visual: kimi
  reasoning: nemotron
```

#### Integration Configuration

Configure integration settings in `configs/integration_config.yaml`:

```yaml
# Example configuration
github:
  cache_ttl: 300 # seconds
  rate_limit_buffer: 100

notion:
  default_parent_page_id: "your-notion-page-id"
  journal_template: "daily"
```

### Applying Configuration Changes

Most configuration changes take effect after restarting P.U.L.S.E. Some changes (like personality traits) can be applied dynamically during runtime.

## Next Steps

After installation and configuration, check out the [User Guide](USER_GUIDE.md) to learn how to use P.U.L.S.E. effectively.
