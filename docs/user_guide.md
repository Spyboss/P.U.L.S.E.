# User Guide

This guide will help you get the most out of P.U.L.S.E. (Prime Uminda's Learning System Engine), your AI Personal Workflow Ops Assistant.

## Getting Started

After [installing P.U.L.S.E.](installation.md), you can start it by running:

```bash
python main.py
```

You'll see the P.U.L.S.E. banner and a prompt where you can enter commands.

## Basic Commands

P.U.L.S.E. understands a variety of natural language commands. Here are some examples:

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

P.U.L.S.E. can provide current time, date, and timezone conversions:

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

### Personality Customization

P.U.L.S.E. has a customizable personality that adapts to your preferences:

- `show personality`: Show current personality traits
- `adjust [trait] to [value]`: Adjust a personality trait (0.0 to 1.0)
  ```
  adjust informative to 0.8
  adjust casual to 0.6
  adjust humor to 0.9
  ```

Available traits:

- `informative`: How detailed and informative responses are
- `courageous`: Willingness to tackle difficult topics
- `positive`: Level of positivity in responses
- `casual`: How casual vs. formal the tone is
- `strict`: How strict or lenient the responses are
- `personal`: How personal vs. impersonal the responses are
- `honest`: Level of directness and honesty
- `humor`: Amount of humor in responses
- `anime_references`: Frequency of anime references

### Workflow Automation

Combine multiple commands for workflow automation:

```
create a github issue for username/repo titled "Bug Fix" and then add a task to implement it
```

## Tips and Tricks

1. **Use natural language** - P.U.L.S.E. understands conversational commands
2. **Be specific with locations** - For timezone queries, use specific city names
3. **Provide context** - When working with GitHub or Notion, provide specific repository or page information
4. **Check the logs** - If something isn't working, check the logs for more information

## Troubleshooting

### Common Issues

- **"I don't understand that command"** - Try rephrasing or using a more specific command
- **API errors** - Check your API keys in the `.env` file
- **Slow responses** - Some AI models may take longer to respond, especially for complex queries

### Debug Mode

Run P.U.L.S.E. in debug mode to see more detailed logs:

```bash
python main.py --debug
```

### Simulation Mode

If you want to test without making API calls:

```bash
python main.py --simulate
```

## Offline Mode

P.U.L.S.E. can operate offline using local models:

```
enable offline mode
```

In offline mode, all queries are routed through Ollama using the Phi model. This allows P.U.L.S.E. to function without an internet connection, using local models for all tasks.

## System Status

Check the system status with:

```
status
```

This shows:

- Hardware information (memory, disk, CPU)
- AI model usage statistics
- AI crew availability
- Specialized query types
- Session information

## Memory Commands

- `search memory [query]`: Search memory for a query
  ```
  search memory python
  ```
- `search memory`: Show recent memories
- `save to memory [text]`: Save a memory
  ```
  save to memory I prefer dark mode in my code editor
  ```
- `save to memory [category]: [data]`: Save categorized data to memory
  ```
  save to memory projects: Tourist Guide App
  save to memory interests: Machine Learning
  ```
- `recall [category]`: Recall data from memory
  ```
  recall projects
  recall interests
  ```

## Next Steps

Check out the [Core Documentation](CORE_DOCUMENTATION.md) to learn more about P.U.L.S.E.'s architecture and capabilities.
