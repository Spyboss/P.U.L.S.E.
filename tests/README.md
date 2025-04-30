# Tests Directory

This directory contains test files for the P.U.L.S.E. (Prime Uminda's Learning System Engine) application.

## Subdirectories

- `integrations/` - Tests for external API integrations (GitHub, Notion, etc.)
- `routing/` - Tests for neural routing and query routing
- `skills/` - Tests for agent skills and model orchestration
- `tools/` - Tests for external tools and utilities
- `utils/` - Tests for utility functions and components

## Core Test Files

- `test_ask_code.py` - Tests for the "ask code" command
- `test_imports.py` - Tests for import compatibility
- `test_local_models.py` - Tests for local model loading
- `test_model_mappings.py` - Tests for model ID mappings
- `test_model_routing.py` - Tests for model routing with rich context data
- `test_models.py` - Tests for model configuration and orchestrator
- `test_pulse_core.py` - Tests for the P.U.L.S.E. core functionality
- `test_pulse_timeout.py` - Tests for timeout handling
- `test_shutdown.py` - Tests for shutdown process
- `test_simple_shutdown.py` - Tests for simplified shutdown
- `test_specialized_models.py` - Tests for specialized models

## Utility Test Files

- `utils/test_intent_handler.py` - Tests for the intent handler
- `utils/test_lancedb_fix.py` - Tests for LanceDB compatibility fixes
- `utils/test_model_interface.py` - Tests for the model interface
- `utils/test_ollama.py` - Tests for basic Ollama integration
- `utils/test_ollama_comprehensive.py` - Comprehensive tests for Ollama
- `utils/test_ollama_status.py` - Tests for Ollama status checking
- `utils/test_vector_db.py` - Tests for vector database functionality

## Skills Test Files

- `skills/test_model_orchestrator.py` - Tests for the model orchestrator
- `skills/test_model_orchestrator_script.py` - Script-based tests for model orchestrator

## Routing Test Files

- `routing/test_router.py` - Tests for the neural router

## Running Tests

You can run tests using the test runner script:

```bash
# Run all tests
python scripts/run_tests.py --all

# Run specific test categories
python scripts/run_tests.py --utils        # Run utility tests
python scripts/run_tests.py --skills       # Run skills tests
python scripts/run_tests.py --tools        # Run tools tests
python scripts/run_tests.py --routing      # Run routing tests
python scripts/run_tests.py --integrations # Run integration tests
python scripts/run_tests.py --root         # Run tests in the root tests directory

# Run with verbose output
python scripts/run_tests.py --verbose

# Run with fail-fast option (stop on first failure)
python scripts/run_tests.py --failfast
```

Or you can use unittest directly:

```bash
# Run all tests
python -m unittest discover tests

# Run tests in a specific directory
python -m unittest discover tests/utils
python -m unittest discover tests/skills
python -m unittest discover tests/routing

# Run a specific test file
python -m unittest tests.utils.test_vector_db
python -m unittest tests.skills.test_model_orchestrator
python -m unittest tests.routing.test_router
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
