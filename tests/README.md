# Tests Directory

This directory contains test files for the General Pulse application.

## Subdirectories

- `integrations/` - Tests for external API integrations
- `skills/` - Tests for agent skills
- `tools/` - Tests for external tools
- `utils/` - Tests for utility functions and components

## Test Files

- `test_model_mappings.py` - Tests for model ID mappings
- `test_model_routing.py` - Tests for model routing with rich context data
- `test_fixes.py` - Tests for fixes to model query and personality commands
- `utils/test_intent_handler.py` - Tests for the intent handler
- `utils/test_model_interface.py` - Tests for the model interface
- `utils/test_ollama.py` - Tests for Ollama integration
- `utils/test_distilbert.py` - Tests for DistilBERT intent classification

## Running Tests

You can run tests using the test runner script:

```bash
# Run all tests
python scripts/run_tests.py --all

# Run specific test categories
python scripts/run_tests.py --utils  # Run utility tests
python scripts/run_tests.py --skills  # Run skills tests
python scripts/run_tests.py --tools  # Run tools tests
python scripts/run_tests.py --integrations  # Run integration tests

# Run with verbose output
python scripts/run_tests.py --verbose
```

Or you can use unittest directly:

```bash
# Run all tests
python -m unittest discover tests

# Run a specific test file
python -m unittest tests.skills.test_github_skills
```

## Writing Tests

When adding new functionality, please add corresponding tests. Tests should be placed in the appropriate subdirectory and follow the naming convention `test_*.py`.

Example test file structure:

```python
import unittest
from skills.github_skills import GitHubSkills

class TestGitHubSkills(unittest.TestCase):
    def setUp(self):
        # Set up test environment
        self.github_skills = GitHubSkills()

    def test_create_commit_message(self):
        # Test the create_commit_message method
        result = self.github_skills.create_commit_message("repo_url", "file_path")
        self.assertIsNotNone(result)

    def tearDown(self):
        # Clean up after tests
        pass

if __name__ == '__main__':
    unittest.main()
```
