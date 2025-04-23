# GitHub Integration

General Pulse provides comprehensive integration with GitHub, allowing you to manage repositories, issues, and more directly from the command line.

## Features

The GitHub integration in General Pulse includes:

- Repository information retrieval
- Issue management (list, view, create)
- AI-driven commit message generation
- Pull request summarization
- Code search capabilities
- Repository statistics and metrics
- Cached responses for faster repeated queries

## Setup

To use the GitHub integration, you need to:

1. Create a GitHub personal access token with appropriate permissions
2. Set the `GITHUB_TOKEN` environment variable in your `.env` file

```
GITHUB_TOKEN=your_github_personal_access_token
```

You can create a personal access token in your [GitHub Developer Settings](https://github.com/settings/tokens).

## Usage Examples

### Repository Information

```
show my github repositories
github username/repo info
```

These commands display information about your repositories or a specific repository.

### Issue Management

```
list issues for username/repo
show open issues for username/repo
create issue for username/repo titled "Bug in login form"
```

These commands allow you to manage issues in GitHub repositories.

### Commit Message Generation

```
github username/repo commit message file: path/to/file
generate commit message for file: path/to/file
```

These commands use AI to generate descriptive commit messages based on code changes.

### Pull Request Management

```
summarize pull request https://github.com/username/repo/pull/123
list pull requests for username/repo
```

These commands help you manage and understand pull requests.

## Implementation Details

### Core Components

The GitHub integration is implemented in the following files:

- `tools/github_integration.py` - Core GitHub API integration
- `skills/github_skills.py` - GitHub-related agent skills
- `utils/github_parser.py` - Parsing GitHub URLs and data

### GitHubIntegration Class

The `GitHubIntegration` class in `tools/github_integration.py` provides the core functionality:

```python
class GitHubIntegration:
    def __init__(self, token=None):
        self.logger = structlog.get_logger("github_integration")
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.token) if self.token else None
        self.cache = CacheManager("github")
        
    def get_repo_info(self, owner, repo_name):
        """Get information about a repository"""
        # Implementation details...
        
    def list_issues(self, owner, repo_name, state="all"):
        """List issues in a repository"""
        # Implementation details...
        
    def create_issue(self, owner, repo_name, title, body=None, labels=None):
        """Create a new issue in a repository"""
        # Implementation details...
```

### GitHubSkills Class

The `GitHubSkills` class in `skills/github_skills.py` provides agent skills for GitHub:

```python
class GitHubSkills:
    def __init__(self, github_integration=None):
        self.logger = structlog.get_logger("github_skills")
        self.github = github_integration or GitHubIntegration()
        
    def handle_github_command(self, command):
        """Handle a GitHub-related command"""
        # Implementation details...
        
    def create_commit_message(self, repo_url, file_path, diff=None):
        """Generate a commit message from a diff"""
        # Implementation details...
```

## AI-Driven Commit Messages

One of the standout features of the GitHub integration is AI-driven commit message generation:

1. The system analyzes the diff (changes) between the current and new version of a file
2. The diff is sent to an AI model via OpenRouter (typically DeepSeek for code-related tasks)
3. The AI generates a concise, informative, and slightly humorous commit message
4. The message can be used directly for committing changes to a GitHub repository

Example usage:

```
github username/myrepo commit message file: src/main.py branch: feature/new-login
```

Optional parameters:
- `branch: [branch_name]` (default: main)
- `model: [model_name]` (default: deepseek)

## Error Handling

The GitHub integration includes robust error handling for:

- Authentication failures
- Rate limiting
- Network issues
- Permission errors
- Invalid repository or user names

When an error occurs, the system provides helpful error messages and suggestions for resolution.

## Caching

To improve performance and reduce API calls, the GitHub integration includes a caching system:

- Repository information is cached for 1 hour
- Issue lists are cached for 5 minutes
- User information is cached for 24 hours

You can configure cache TTL (time-to-live) values in the configuration file.

## Future Enhancements

Planned enhancements for the GitHub integration include:

- Pull request creation and management
- Code review assistance
- Repository statistics and analytics
- Webhook event handling
- Branch management
- Advanced search capabilities

For more details on planned enhancements, see the [Development Roadmap](../development/roadmap.md).
