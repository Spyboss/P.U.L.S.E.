# Contributing Guide

Thank you for your interest in contributing to General Pulse! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- A GitHub account

### Setting Up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/general-pulse.git
   cd general-pulse
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```
5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Development Workflow

### Branching Strategy

- `main` - Main development branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `release/*` - Release branches

### Creating a New Feature

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Implement your changes
3. Write tests for your changes
4. Run the tests:
   ```bash
   python -m unittest discover tests
   ```
5. Commit your changes:
   ```bash
   git commit -m "Add your descriptive commit message"
   ```
6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. Create a pull request on GitHub

### Pull Request Process

1. Ensure your code passes all tests
2. Update documentation if necessary
3. Add your changes to the CHANGELOG.md file
4. Submit the pull request
5. Address any feedback from reviewers

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

## Project Structure

```
General Pulse/
├── configs/           # Configuration files
├── docs/              # Documentation
├── memory/            # Persistent memory storage
├── scripts/           # Utility scripts
├── skills/            # Core agent skills
├── tests/             # Test suite
├── tools/             # External integrations
├── utils/             # Utility functions
└── main.py            # Main entry point
```

### Adding New Components

#### Adding a New Skill

1. Create a new file in the `skills/` directory
2. Implement the skill class with appropriate methods
3. Add tests in the `tests/` directory
4. Update documentation

#### Adding a New Tool

1. Create a new file in the `tools/` directory
2. Implement the tool class with appropriate methods
3. Add tests in the `tests/` directory
4. Update documentation

#### Adding a New Utility

1. Create a new file in the `utils/` directory
2. Implement the utility functions or classes
3. Add tests in the `tests/` directory
4. Update documentation

## Reporting Issues

### Bug Reports

When reporting a bug, please include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots or error messages (if applicable)
- Environment information (OS, Python version, etc.)

### Feature Requests

When requesting a feature, please include:

- A clear and descriptive title
- A detailed description of the proposed feature
- Any relevant use cases or examples
- Why this feature would be beneficial to the project

## Communication

- GitHub Issues: For bug reports, feature requests, and discussions
- Pull Requests: For code contributions

## License

By contributing to General Pulse, you agree that your contributions will be licensed under the project's MIT License.
