# Installation Guide

This guide will help you install and set up General Pulse on your system.

## Prerequisites

General Pulse requires:
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Required Dependencies

The following Python packages are required:
- prompt_toolkit
- structlog
- python-dotenv
- pytz
- python-dateutil

## Recommended Dependencies

These packages enable additional features:
- transformers (for local intent classification)
- torch (for local AI models)
- openrouter (for multi-model AI capabilities)
- PyGithub (for GitHub integration)
- notion-client (for Notion integration)
- ollama (for local model support)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/general-pulse.git
cd general-pulse
```

### 2. Create a Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required dependencies
pip install -r requirements.txt

# Install optional dependencies for all features
pip install -r requirements-optional.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Required for AI capabilities
OPENROUTER_API_KEY=your_openrouter_api_key

# Required for GitHub integration
GITHUB_TOKEN=your_github_token

# Required for Notion integration
NOTION_API_KEY=your_notion_api_key

# Optional: Direct API keys (if not using OpenRouter)
CLAUDE_API_KEY=your_claude_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GEMINI_API_KEY=your_gemini_api_key
```

You can obtain these API keys from:
- [OpenRouter](https://openrouter.ai/keys)
- [GitHub Developer Settings](https://github.com/settings/tokens)
- [Notion Integrations](https://www.notion.so/my-integrations)

### 5. Verify Installation

Run the following command to verify your installation:

```bash
python main.py --debug
```

If everything is set up correctly, you should see the General Pulse banner and be able to interact with the agent.

## Troubleshooting

### Missing Dependencies

If you see errors about missing dependencies, install them manually:

```bash
pip install package_name
```

### API Key Issues

If you see warnings about missing API keys, make sure your `.env` file is properly configured and located in the project root directory.

### Simulation Mode

If you want to test General Pulse without API keys, use simulation mode:

```bash
python main.py --simulate
```

## Next Steps

After installation, check out the [User Guide](user_guide.md) to learn how to use General Pulse effectively.
