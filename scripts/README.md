# Scripts Directory

This directory contains utility scripts for the General Pulse application.

## Subdirectories

- `maintenance/` - Scripts for maintenance tasks (e.g., installing dependencies)
- `tools/` - Scripts for working with external tools and integrations
- `utils/` - Utility scripts for various tasks

## Key Scripts

### Runner Scripts

- `run_tests.py` - Script to run tests with various options
- `cli_ui.py` - Script to launch the CLI UI in a standalone window
- `cli_ui_launcher.py` - Simplified script to launch the CLI UI

### Maintenance Scripts

- `install.py` - Script to install General Pulse and its dependencies
- `backup_memory.py` - Script to backup and restore memory databases
- `maintenance/install_spacy.py` - Script to install spaCy and its dependencies

### Tool Scripts

- `tools/analyze_notion_page.py` - Script to analyze Notion pages
- `tools/daily_journal.py` - Script to create daily journal entries in Notion
- `tools/notion_document_creator.py` - Script to create Notion documents

### Utility Scripts

- `utils/check_api_key.py` - Script to check API key validity
- `utils/check_models.py` - Script to check available AI models
- `utils/openrouter_test.py` - Script to test OpenRouter integration

## Usage

Most scripts can be run directly from the command line:

```bash
python scripts/run_tests.py --all
python scripts/cli_ui.py
python scripts/backup_memory.py list
python scripts/install.py --upgrade
```

See the individual script files for specific usage instructions.
