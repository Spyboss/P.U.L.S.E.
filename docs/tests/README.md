# Testing Documentation

This directory contains test scripts and documentation for testing General Pulse components.

## Available Tests

### Main Brain Tests

- `test_main_brain.py`: Tests the Mistral-Small integration via OpenRouter

## Running Tests

### Main Brain Test

To test the Mistral-Small integration:

```bash
python docs/tests/test_main_brain.py
```

This script tests:
1. OpenRouter API key validation
2. Mistral-Small model response
3. Error handling and timeouts

### CLI UI Tests

You can also test the main brain using the CLI UI:

```bash
python pulse.py
# Then in the CLI:
test main_brain_api_key
```

This will:
1. Verify that your OpenRouter API key is valid
2. Test Mistral-Small with a simple query
3. Display the response

## Test Development Guidelines

When creating new tests:

1. Place test scripts in the `docs/tests` directory
2. Use descriptive names for test files and functions
3. Include proper error handling and logging
4. Document the test purpose and usage in this README
5. Keep tests focused on a single component or feature

## Test Output

Test output is logged to the console and to the log files in the `logs` directory. Check these logs for detailed information about test execution and results.
