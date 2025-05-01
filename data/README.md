# Data Directory

This directory contains data files used by the P.U.L.S.E. (Prime Uminda's Learning System Engine) application.

## Contents

### Database Files

- `cache.db` - SQLite database for caching API responses
- `memory.db` - Memory database for storing long-term memory
- `pulse_memory.db` - Main memory database for the Pulse Agent

### Configuration Files

- `models.json` - Configuration for AI models
- `deepseek_prompt.txt` - Prompt template for DeepSeek model
- Other data files used by the application

## Note

Most files in this directory are ignored by Git to avoid committing sensitive or large data files. See the `.gitignore` file in the project root for details.

## Backup

It's recommended to regularly backup the database files in this directory. You can use the `scripts/backup_memory.py` script to create backups:

```bash
# List all backups
python scripts/backup_memory.py list

# Create a backup of the memory database
python scripts/backup_memory.py backup data/pulse_memory.db

# Restore a backup
python scripts/backup_memory.py restore backups/pulse_memory.db.20250419_080000.bak data/pulse_memory.db
```
