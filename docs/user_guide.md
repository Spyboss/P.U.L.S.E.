# User Guide

This guide will help you get the most out of General Pulse, your AI Personal Workflow Ops Assistant.

## Getting Started

After [installing General Pulse](installation.md), you can start it by running:

```bash
python main.py
```

You'll see the General Pulse banner and a prompt where you can enter commands.

## Basic Commands

General Pulse understands a variety of natural language commands. Here are some examples:

### General Queries

```
hello
what can you do?
help
```

### Time and Date

```
what time is it?
what's the date today?
what time is it in Tokyo?
what's the time in London?
```

### Task Management

```
add a task to implement the new feature
show my tasks
mark task 3 as completed
what tasks are in progress?
```

### GitHub Integration

```
show my github repositories
list issues for username/repo
create a commit message for file: path/to/file
```

### Notion Integration

```
create a new notion page titled "Meeting Notes"
add a journal entry to my notion journal
create a to-do list in notion called "Project Tasks"
```

## Command Categories

### Time and Date Commands

General Pulse can provide current time, date, and timezone conversions:

- `what time is it?` - Shows the current local time
- `what's the date today?` - Shows the current date
- `what time is it in [location]?` - Shows the current time in the specified location
- `what's the time difference between [location1] and [location2]?` - Calculates time difference

### Task Management Commands

Manage your tasks directly from the command line:

- `add a task to [description]` - Creates a new task
- `show my tasks` - Lists all tasks
- `show completed tasks` - Lists completed tasks
- `mark task [number] as completed` - Marks a task as completed
- `what tasks are in progress?` - Shows tasks in progress

### GitHub Commands

Interact with GitHub repositories:

- `show my github repositories` - Lists your repositories
- `list issues for [username]/[repo]` - Lists issues for a repository
- `create a commit message for file: [path]` - Generates an AI commit message
- `summarize pull request [PR URL]` - Summarizes a pull request

### Notion Commands

Work with Notion pages and databases:

- `create a notion page titled "[title]"` - Creates a new Notion page
- `add a journal entry to my notion journal` - Adds an entry to your journal
- `create a to-do list in notion called "[name]"` - Creates a to-do list
- `analyze my notion journal` - Analyzes journal entries

## Advanced Usage

### AI Model Selection

You can specify which AI model to use for certain tasks:

```
use claude to summarize this text: [text]
use deepseek to analyze this code: [code]
use gemini to generate ideas for [topic]
```

### Personality Traits

General Pulse has a personality engine that adapts to your preferences:

```
be more concise in your responses
be more detailed in your explanations
be more professional/casual/humorous
```

### Workflow Automation

Combine multiple commands for workflow automation:

```
create a github issue for username/repo titled "Bug Fix" and then add a task to implement it
```

## Tips and Tricks

1. **Use natural language** - General Pulse understands conversational commands
2. **Be specific with locations** - For timezone queries, use specific city names
3. **Provide context** - When working with GitHub or Notion, provide specific repository or page information
4. **Check the logs** - If something isn't working, check the logs for more information

## Troubleshooting

### Common Issues

- **"I don't understand that command"** - Try rephrasing or using a more specific command
- **API errors** - Check your API keys in the `.env` file
- **Slow responses** - Some AI models may take longer to respond, especially for complex queries

### Debug Mode

Run General Pulse in debug mode to see more detailed logs:

```bash
python main.py --debug
```

### Simulation Mode

If you want to test without making API calls:

```bash
python main.py --simulate
```

## Next Steps

Check out the [Configuration Guide](configuration.md) to learn how to customize General Pulse to your needs.
