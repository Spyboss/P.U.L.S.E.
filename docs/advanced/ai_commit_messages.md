# AI-Driven Commit Messages

## Overview

The AI-Driven Commit Messages feature leverages language models to generate descriptive, informative, and slightly snarky commit messages based on code changes. This feature helps developers maintain a clean and informative git history without the mental overhead of writing descriptive commit messages.

## Implementation Status
✅ **IMPLEMENTED** - June 2025

## How It Works

1. The system analyzes the diff (changes) between the current and new version of a file
2. The diff is sent to an AI model via OpenRouter (typically DeepSeek for code-related tasks)
3. The AI generates a concise, informative, and slightly humorous commit message
4. The message can be used directly for committing changes to a GitHub repository

## Usage

### Through the Agent Interface

You can use the General Pulse agent to generate commit messages:

```
github [owner]/[repo] commit message file: [file_path]
```

Optional parameters:
- `branch: [branch_name]` (default: main)
- `model: [model_name]` (default: deepseek)

Example:
```
github username/myrepo commit message file: src/main.py branch: feature/new-login
```

### Using the Test Script

A dedicated test script is provided for quick testing and real-world usage:

```bash
python test_ai_commit.py --owner [username] --repo [repo_name] --file [file_path]
```

For testing with a sample diff:
```bash
python test_ai_commit.py --sample
```

## Examples

### Sample Input (Diff)

```diff
--- a/README.md
+++ b/README.md
@@ -4,7 +4,9 @@
 
 ## Features
 
-* Task tracking and management
+* Comprehensive task tracking and management
+* AI-driven commit message generation
+* OpenRouter integration for multiple AI models
 * GitHub API integration
 * Automated workflows
```

### Sample Output (Commit Message)

```
Add AI commit generation and OpenRouter integration to features list 🚀
```

### Real-World Example

When used with the DeepSeek model, the feature generated this commit message for a README update:

```
Updated README.md to flex our fancy new AI-driven features. Because who writes commit messages manually anymore? 🤖
```

## Implementation Details

### Components

1. **GitHubSkills Class**: 
   - `create_commit_message()`: Generates a commit message from a diff
   - `extract_repo_info_from_url()`: Parses GitHub URLs to extract owner and repo

2. **GitHubIntegration Class**:
   - `get_repo_info()`: Retrieves repository information
   - `list_issues()`: Lists issues in a repository

3. **ModelInterface Class**:
   - Uses OpenRouter to route requests to DeepSeek or other AI models
   - Handles API communication and error fallbacks

4. **Intent Handlers**:
   - `github_intent()`: Processes commit message requests via natural language
   - Parses parameters like file path, branch, and model selection

### AI Prompt Design

The AI is instructed to generate commit messages that:
1. Clearly describe what changed
2. Are concise (1-2 lines, max 72 chars per line)
3. Include a bit of personality/humor
4. Focus on the "what" and "why", not the "how"

### Model Selection

After testing multiple models, DeepSeek was selected as the default model for code-related tasks due to its:
- Strong understanding of code contexts
- Ability to generate concise yet descriptive messages
- Appropriate level of humor in responses

## Benefits

1. **Consistency**: Ensures commit messages maintain a consistent style and level of detail
2. **Time-saving**: Reduces the mental overhead of writing descriptive commit messages
3. **Engagement**: Adds a touch of personality to git history, making it more engaging
4. **Focus**: Lets developers focus on coding instead of commit message wording

## Future Enhancements

1. Pre-commit hooks for automatic message generation
2. Support for bulk commits across multiple files
3. Custom personality profiles for different types of messages
4. Integration with pull request descriptions
5. Advanced diff analysis to detect refactoring vs. new features vs. bug fixes

## Potential Cursor CLI Integration

Based on recent research, there's potential to integrate this feature with the Cursor CLI:

1. **Automated PR Review System**:
   - Extend the commit message generation to full PR reviews
   - Use Cursor CLI's `analyze` command to scan PR diffs
   - Generate both technical feedback and style suggestions
   
2. **In-Editor Commit Message Generation**:
   - Integrate directly with the Cursor IDE
   - Provide commit message suggestions as you stage changes
   - Allow one-click acceptance of generated messages 