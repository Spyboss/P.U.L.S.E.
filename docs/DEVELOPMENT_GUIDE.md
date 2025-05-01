# P.U.L.S.E. Development Guide

This document provides comprehensive information for developers working on P.U.L.S.E. (Prime Uminda's Learning System Engine).

## Architecture Overview

P.U.L.S.E. follows a modular architecture with the following key components:

1. **Pulse Agent**: The main controller that integrates all components
2. **Model Orchestrator**: Manages multiple AI models
3. **Context Manager**: Handles conversation context
4. **Memory Manager**: Provides long-term storage
5. **Personality Engine**: Manages the assistant's personality
6. **Optimization Utilities**: Optimizes performance for different hardware

For a detailed architecture overview, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- Git
- SQLite
- (Optional) CUDA-compatible GPU for accelerated inference

### Setup Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/pulse.git
   cd pulse
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file with the following variables:

   ```
   OPENROUTER_API_KEY=your_openrouter_api_key
   GITHUB_TOKEN=your_github_token
   NOTION_API_KEY=your_notion_api_key
   MONGODB_URI=your_mongodb_connection_string
   ```

5. Run tests to verify setup:
   ```bash
   python -m unittest discover tests
   ```

## Project Structure

```
P.U.L.S.E./
├── configs/           # Configuration files
│   └── models.py      # Model configurations
├── context/           # Context management
│   └── history.py     # Conversation history management
├── data/              # Data storage
│   ├── vector_db/     # Vector database storage
│   └── *.db           # SQLite database files
├── docs/              # Documentation
│   ├── advanced/      # Advanced feature documentation
│   ├── development/   # Development documentation
│   ├── features/      # Feature documentation
│   ├── integrations/  # Integration documentation
├── integrations/      # External integrations
│   └── sync.py        # GitHub-Notion synchronization
├── logs/              # Log files
│   └── *.log          # Log files
├── memory/            # Memory storage
│   └── tasks.db       # Task memory database
├── personality/       # Personality engine
│   ├── charisma.py    # Charisma engine
│   └── self_awareness.py # Self-awareness module
├── routing/           # Query routing
│   └── router.py      # Neural router
├── scripts/           # Utility scripts
├── skills/            # Core agent skills
│   ├── marketplace.py # Skill marketplace
│   ├── pulse_agent.py # Main agent implementation
│   └── model_orchestrator.py # Model management
├── tests/             # Test suite
│   ├── integrations/  # Integration tests
│   ├── routing/       # Routing tests
│   ├── skills/        # Skills tests
│   ├── tools/         # Tools tests
│   ├── utils/         # Utility tests
│   └── test_*.py      # Core tests
├── tools/             # Integration tools
│   ├── bug_bounty_hunter.py # Bug bounty hunter
│   ├── github_integration.py # GitHub integration
│   └── notion_overplanning_detector.py # Notion overplanning detector
├── utils/             # Utility functions
│   ├── context_manager.py # Context management
│   ├── intent_preprocessor.py # Intent preprocessing
│   ├── log.py         # Logging utilities
│   ├── memory.py      # Memory management
│   ├── neural_router.py # Neural routing
│   ├── optimization.py # Hardware optimizations
│   ├── personality_engine.py # Personality traits
│   ├── sqlite_utils.py # SQLite utilities
│   ├── system_utils.py # System utilities
│   ├── unified_logger.py # Unified logging
│   └── vector_db.py   # Vector database utilities
├── pulse.py           # Main entry point
├── pulse_core.py      # Core functionality
└── cli_ui_launcher.py # CLI UI launcher
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 100 characters
- Use docstrings for all public functions, classes, and methods

### Documentation

- Update documentation for any changes to functionality
- Use Markdown for documentation files
- Keep documentation clear, concise, and up-to-date

### Testing

- Write unit tests for all new functionality
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage

## Testing

### Running Tests

Run all tests:

```bash
python -m unittest discover tests
```

Run a specific test:

```bash
python -m unittest tests.test_pulse_agent
```

### Writing Tests

1. Create a new test file in the `tests/` directory
2. Import the module to test
3. Create a test class that inherits from `unittest.TestCase`
4. Write test methods that start with `test_`
5. Use assertions to verify behavior

Example:

```python
import unittest
from utils.context_manager import PulseContext

class TestContextManager(unittest.TestCase):
    def setUp(self):
        # Set up test environment
        self.context = PulseContext()

    def test_add_message(self):
        # Test adding a message to the context
        self.context.add_message("user", "Hello")
        self.context.add_message("assistant", "Hi there")

        messages = self.context.get_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")

    def tearDown(self):
        # Clean up after tests
        pass

if __name__ == '__main__':
    unittest.main()
```

## Contributing

### Contribution Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests
5. Update documentation
6. Submit a pull request

### Pull Request Process

1. Ensure your code passes all tests
2. Update documentation if necessary
3. Add your changes to the CHANGELOG.md file
4. Submit the pull request
5. Address any feedback from reviewers

## Development Roadmap

### Current Focus

- Improving model routing and delegation
- Enhancing chat persistence
- Fixing LanceDB integration issues
- Improving error handling
- Enhancing GitHub-Notion sync

### Future Plans

- Skill marketplace implementation
- Advanced analytics dashboard
- Enhanced offline capabilities
- Multi-user support
- Mobile companion app

## Key Concepts

### Model Orchestration

The Model Orchestrator selects the most appropriate model for each query:

```python
# Example: Adding a new model to the orchestrator
self.free_models["new_task"] = "new-model-id:free"
```

### Context Management

The Context Manager maintains conversation history and provides historical context:

```python
# Example: Updating context
self.context.update(
    user_input="Hello",
    response="Hi there!",
    metadata={"mood": "positive"}
)
```

### Memory Storage

The Memory Manager provides persistent storage using SQLite:

```python
# Example: Saving user data
self.memory.save_user_data("projects", "New Project")
```

### Personality Engine

The Personality Engine manages the assistant's tone and style:

```python
# Example: Formatting a response
formatted_response = self.personality.format_response(
    content="This is a test",
    context="tech",
    success=True
)
```

### Intent Handling

The Intent Handler recognizes and processes specific commands:

```python
# Example: Handling an intent
intent_result = self.intent_handler.parse_command(user_input)
if intent_result and intent_result.get("command_type"):
    return await self._handle_intent(intent_result, user_input)
```

## Adding New Features

### Adding a New Command

1. Update the Intent Handler to recognize the new command:

```python
# In utils/intent_handler.py
def parse_command(self, text):
    # Add pattern for new command
    if re.match(r"new command (.+)", text, re.IGNORECASE):
        return {
            "command_type": "new_command",
            "parameter": re.match(r"new command (.+)", text, re.IGNORECASE).group(1)
        }
```

2. Add a handler method in the Pulse Agent:

```python
# In skills/pulse_agent.py
async def _handle_intent(self, intent_result, user_input):
    command_type = intent_result.get("command_type")

    # Add handler for new command
    if command_type == "new_command":
        parameter = intent_result.get("parameter")
        return self._format_response(f"Handling new command with parameter: {parameter}")
```

### Adding a New Model

1. Add the model to the free_models dictionary in the Model Orchestrator:

```python
# In skills/model_orchestrator.py
self.free_models["new_task"] = "new-model-id:free"
```

2. Update the query classification method:

```python
# In skills/model_orchestrator.py
async def _classify_query(self, input_text):
    # Add classification for new task
    if any(word in input_text.lower() for word in ["new", "task", "keywords"]):
        return "new_task"
```

### Adding a New Personality Trait

1. Add the trait to the traits dictionary in the Personality Engine:

```python
# In utils/personality_engine.py
traits = {
    # Existing traits...
    "new_trait": 0.5
}
```

2. Use the trait in response formatting:

```python
# In utils/personality_engine.py
def format_response(self, content, context="general", success=True):
    # Use new trait to influence response
    if random.random() < self.traits["new_trait"]:
        # Apply trait effect
        content = f"[New trait effect] {content}"
```

## Performance Optimization

### Memory Optimization

Use the memory_guard decorator to protect against low memory conditions:

```python
from utils.optimization import memory_guard

@memory_guard
def memory_intensive_function():
    # Function code here
```

### GPU Optimization

Configure GPU memory usage for PyTorch:

```python
import torch

if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.5)  # Use only 50% of GPU memory
    torch.backends.cudnn.benchmark = True  # Optimize for fixed input sizes
```

### SQLite Optimization

Optimize SQLite for better performance:

```python
import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("PRAGMA journal_mode=WAL")  # Use Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")  # Less synchronous for better performance
conn.execute("PRAGMA cache_size=5000")  # Increase cache size
```

## Debugging

### Logging

Use structlog for structured logging:

```python
import structlog

logger = structlog.get_logger("module_name")
logger.info("Message", key1="value1", key2="value2")
```

### Error Handling

Use try-except blocks with detailed error messages:

```python
try:
    # Code that might raise an exception
except Exception as e:
    logger.error(
        "Error description",
        error=str(e),
        traceback=traceback.format_exc()
    )
    return {"success": False, "error": str(e)}
```

## Best Practices

1. **Follow the Modular Architecture**: Keep components separate and focused
2. **Use Type Hints**: Add type hints to function parameters and return values
3. **Write Unit Tests**: Test all new functionality
4. **Handle Errors Gracefully**: Provide helpful error messages
5. **Optimize for Performance**: Consider memory and CPU usage
6. **Document Your Code**: Add docstrings and comments
7. **Use Async Where Appropriate**: Use async/await for I/O-bound operations
8. **Respect User Privacy**: Don't store sensitive information
9. **Stay Within Free Tiers**: Avoid accidental usage of paid API features
10. **Keep It Simple**: Prefer simple solutions over complex ones

## Resources

- [Python Documentation](https://docs.python.org/3/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Notion API Documentation](https://developers.notion.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
