# Configuration Guide

This guide explains how to configure General Pulse to suit your needs.

## Configuration Files

General Pulse uses several configuration files located in the `configs/` directory:

- `model_api_config.yaml` - AI model configuration
- `personality_traits.yaml` - Agent personality settings
- `command_patterns.yaml` - Command recognition patterns
- `logging_config.yaml` - Logging configuration

## Environment Variables

Environment variables are stored in the `.env` file in the project root. Here are the available options:

### Required Variables

```
# OpenRouter API key (for AI capabilities)
OPENROUTER_API_KEY=your_openrouter_api_key

# GitHub personal access token
GITHUB_TOKEN=your_github_token

# Notion API key
NOTION_API_KEY=your_notion_api_key
```

### Optional Variables

```
# Direct API keys (if not using OpenRouter)
CLAUDE_API_KEY=your_claude_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GEMINI_API_KEY=your_gemini_api_key

# Local model configuration
USE_LOCAL_MODELS=true
OLLAMA_BASE_URL=http://localhost:11434

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=general_pulse.log
```

## AI Model Configuration

You can configure AI model settings in `configs/model_api_config.yaml`:

```yaml
# Example configuration
models:
  default: claude
  
  claude:
    api_url: https://api.anthropic.com/v1/messages
    model_name: claude-3-sonnet-20240229
    temperature: 0.7
    max_tokens: 1000
    
  gemini:
    api_url: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
    temperature: 0.7
    max_tokens: 1000
    
  deepseek:
    api_url: https://api.deepseek.com/v1/chat/completions
    model_name: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

openrouter:
  models:
    claude: "anthropic/claude-3-sonnet-20240229"
    grok: "mistralai/mistral-small"
    deepseek: "deepseek/deepseek-chat"
    default: "openai/gpt-3.5-turbo"
```

## Personality Configuration

Configure the agent's personality in `configs/personality_traits.yaml`:

```yaml
# Example configuration
personality:
  name: General Pulse
  traits:
    helpfulness: 0.9
    creativity: 0.7
    humor: 0.5
    conciseness: 0.6
    formality: 0.5
  
  response_styles:
    default: balanced
    technical: detailed
    creative: imaginative
    business: professional
```

## Command Pattern Configuration

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

## Logging Configuration

Configure logging in `configs/logging_config.yaml`:

```yaml
# Example configuration
version: 1
formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  structured:
    format: '%(message)s'

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
    filename: logs/general_pulse.log
    encoding: utf8

loggers:
  '':  # Root logger
    level: DEBUG
    handlers: [console, file]
    propagate: no
```

## Memory Configuration

General Pulse stores persistent data in the `memory/` directory:

- `memory/conversations/` - Conversation history
- `memory/tasks/` - Task data
- `memory/cache/` - API response cache

You can configure memory settings in `configs/memory_config.yaml`:

```yaml
# Example configuration
memory:
  conversation_history_limit: 100
  cache_expiration: 3600  # seconds
  task_storage: file  # file or database
```

## Advanced Configuration

### Custom Command Handlers

You can create custom command handlers by adding Python files to the `utils/` directory and registering them in `utils/command_parser.py`.

### Model Role Specialization

Configure which models handle specific tasks in `configs/model_roles.yaml`:

```yaml
# Example configuration
roles:
  strategy: gemini
  content: claude
  code: deepseek
```

### Integration Configuration

Configure integration settings in `configs/integration_config.yaml`:

```yaml
# Example configuration
github:
  cache_ttl: 300  # seconds
  rate_limit_buffer: 100
  
notion:
  default_parent_page_id: "your-notion-page-id"
  journal_template: "daily"
```

## Applying Configuration Changes

Most configuration changes take effect after restarting General Pulse. Some changes (like personality traits) can be applied dynamically during runtime.
