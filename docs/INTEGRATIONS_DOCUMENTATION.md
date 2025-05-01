# P.U.L.S.E. Integrations Documentation

This document provides comprehensive information about the integrations available in P.U.L.S.E. (Prime Uminda's Learning System Engine).

## GitHub Integration

P.U.L.S.E. integrates with GitHub to provide repository management capabilities:

### Features

- **Repository Information** - Retrieves repository details
- **Issue Management** - Lists, creates, and updates issues
- **Commit Message Generation** - Generates AI-driven commit messages
- **Pull Request Summarization** - Summarizes pull requests
- **Repository Analysis** - Analyzes repository structure and content

### Usage

```
# List repositories
show my github repositories

# List issues
list issues for [username]/[repo]

# Generate commit message
create a commit message for file: [path]

# Summarize pull request
summarize pull request [PR URL]
```

### Implementation

The GitHub integration is implemented in the `tools/github_integration.py` file and uses the GitHub API to interact with repositories.

## Notion Integration

P.U.L.S.E. integrates with Notion to provide document management capabilities:

### Features

- **Page Creation** - Creates new Notion pages
- **Journal Entries** - Adds entries to a journal
- **To-Do Lists** - Creates and manages to-do lists
- **Page Analysis** - Analyzes Notion pages for insights
- **Content Generation** - Generates content for Notion pages

### Usage

```
# Create a page
create a notion page titled "[title]"

# Add journal entry
add a journal entry to my notion journal

# Create to-do list
create a to-do list in notion called "[name]"

# Analyze journal
analyze my notion journal
```

### Implementation

The Notion integration is implemented in the `tools/notion_integration.py` file and uses the Notion API to interact with Notion pages and databases.

## GitHub-Notion Sync

P.U.L.S.E. provides bidirectional synchronization between GitHub and Notion:

### Features

- **Issue Sync** - Syncs GitHub issues to Notion
- **Task Sync** - Syncs Notion tasks to GitHub issues
- **Status Updates** - Updates status across platforms
- **Comment Sync** - Syncs comments between platforms
- **Automated Workflows** - Automates workflows across platforms

### Usage

```
# Sync GitHub issues to Notion
sync github issues to notion for [username]/[repo]

# Sync Notion tasks to GitHub
sync notion tasks to github for [page_id]

# Check sync status
check github-notion sync status
```

### Implementation

The GitHub-Notion sync is implemented in the `integrations/sync.py` file and uses both the GitHub and Notion APIs to synchronize data.

## OpenRouter Integration

P.U.L.S.E. integrates with OpenRouter to access multiple AI models:

### Models

| Intent | Model | Description |
|--------|-------|-------------|
| debug | DeepSeek | Debugging and troubleshooting issues |
| code | DeepCoder | Code generation and optimization |
| docs | Llama-Doc | Documentation and explanations |
| explain | Llama-Doc | Detailed explanations of concepts |
| troubleshoot | DeepSeek | Troubleshooting technical issues |
| trends | Mistral-Small | Analysis of trends and market data |
| content | Llama-Content | Content creation for blogs, articles, etc. |
| technical | Llama-Technical | Technical writing and translation |
| brainstorm | Hermes | Creative brainstorming and idea generation |
| ethics | Olmo | Ethical considerations and analysis |
| automate | MistralAI | Task automation and workflow optimization |

### Usage

```
# Use a specific model
use deepseek to debug this code: [code]

# Test OpenRouter connection
test openrouter
```

### Implementation

The OpenRouter integration is implemented in the `skills/model_orchestrator.py` file and uses the OpenRouter API to access multiple AI models.

## MongoDB Integration

P.U.L.S.E. integrates with MongoDB Atlas for cloud-based persistent storage:

### Features

- **Chat History Storage** - Stores chat history in MongoDB
- **Vector Storage** - Stores vector embeddings
- **User Preferences** - Stores user preferences
- **Task Management** - Stores and manages tasks
- **Analytics Data** - Stores analytics data

### Usage

MongoDB integration is used internally by P.U.L.S.E. and doesn't have direct user commands.

### Implementation

The MongoDB integration is implemented in the `utils/mongodb_client.py` file and uses the MongoDB Atlas API to store and retrieve data.

## Ollama Integration

P.U.L.S.E. integrates with Ollama for local model inference:

### Features

- **Local Model Inference** - Uses local models for inference
- **Offline Operation** - Enables operation without internet
- **Custom Models** - Supports custom Ollama models
- **Model Management** - Manages local model downloads and updates
- **Performance Optimization** - Optimizes for local hardware

### Usage

```
# Check Ollama status
ollama status

# Use a specific Ollama model
use ollama model [model_name] for [query]

# Enable offline mode
enable offline mode
```

### Implementation

The Ollama integration is implemented in the `utils/ollama_client.py` file and uses the Ollama API to interact with local models.
