#!/usr/bin/env python3
"""
Memory backup script for General Pulse
Creates a backup of the memory database
"""

import os
import sys
import argparse
import sqlite3
import shutil
from datetime import datetime
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger("backup")

def backup_memory(source_path, backup_dir=None, backup_name=None):
    """
    Backup the memory database
    
    Args:
        source_path: Path to the memory database
        backup_dir: Directory to store the backup
        backup_name: Name of the backup file
        
    Returns:
        Path to the backup file
    """
    # Check if source file exists
    if not os.path.exists(source_path):
        logger.error(f"Source file not found: {source_path}")
        return None
    
    # Create backup directory if it doesn't exist
    if not backup_dir:
        backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logger.info(f"Created backup directory: {backup_dir}")
    
    # Generate backup filename
    if not backup_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_filename = os.path.basename(source_path)
        backup_name = f"{source_filename}.{timestamp}.bak"
    
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Create backup
    try:
        # Method 1: SQLite backup API (preferred)
        source_conn = sqlite3.connect(source_path)
        backup_conn = sqlite3.connect(backup_path)
        
        with backup_conn:
            source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        logger.info(f"Backup created successfully: {backup_path}")
        return backup_path
    
    except Exception as e:
        logger.error(f"SQLite backup API failed: {str(e)}")
        
        try:
            # Method 2: File copy (fallback)
            shutil.copy2(source_path, backup_path)
            logger.info(f"Backup created successfully (file copy): {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"File copy backup failed: {str(e)}")
            return None

def list_backups(backup_dir=None):
    """
    List all backups
    
    Args:
        backup_dir: Directory containing backups
        
    Returns:
        List of backup files
    """
    if not backup_dir:
        backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        logger.warning(f"Backup directory not found: {backup_dir}")
        return []
    
    # Get all backup files
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith(".bak"):
            file_path = os.path.join(backup_dir, filename)
            file_size = os.path.getsize(file_path)
            file_time = os.path.getmtime(file_path)
            file_date = datetime.fromtimestamp(file_time).strftime("%Y-%m-%d %H:%M:%S")
            
            backups.append({
                "filename": filename,
                "path": file_path,
                "size": file_size,
                "date": file_date
            })
    
    # Sort by date (newest first)
    backups.sort(key=lambda x: x["date"], reverse=True)
    
    return backups

def restore_backup(backup_path, target_path):
    """
    Restore a backup
    
    Args:
        backup_path: Path to the backup file
        target_path: Path to restore to
        
    Returns:
        True if successful, False otherwise
    """
    # Check if backup file exists
    if not os.path.exists(backup_path):
        logger.error(f"Backup file not found: {backup_path}")
        return False
    
    # Create target directory if it doesn't exist
    target_dir = os.path.dirname(target_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir)
        logger.info(f"Created target directory: {target_dir}")
    
    # Create backup of current file if it exists
    if os.path.exists(target_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_before_restore = f"{target_path}.{timestamp}.before_restore"
        try:
            shutil.copy2(target_path, backup_before_restore)
            logger.info(f"Created backup of current file: {backup_before_restore}")
        except Exception as e:
            logger.warning(f"Failed to backup current file: {str(e)}")
    
    # Restore backup
    try:
        # Method 1: SQLite backup API (preferred)
        backup_conn = sqlite3.connect(backup_path)
        target_conn = sqlite3.connect(target_path)
        
        with target_conn:
            backup_conn.backup(target_conn)
        
        backup_conn.close()
        target_conn.close()
        
        logger.info(f"Backup restored successfully: {backup_path} -> {target_path}")
        return True
    
    except Exception as e:
        logger.error(f"SQLite backup API restore failed: {str(e)}")
        
        try:
            # Method 2: File copy (fallback)
            shutil.copy2(backup_path, target_path)
            logger.info(f"Backup restored successfully (file copy): {backup_path} -> {target_path}")
            return True
        
        except Exception as e:
            logger.error(f"File copy restore failed: {str(e)}")
            return False

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Memory backup utility for General Pulse")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument("source", help="Path to the memory database")
    backup_parser.add_argument("--dir", help="Directory to store the backup")
    backup_parser.add_argument("--name", help="Name of the backup file")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all backups")
    list_parser.add_argument("--dir", help="Directory containing backups")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("backup", help="Path to the backup file")
    restore_parser.add_argument("target", help="Path to restore to")
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == "backup":
        backup_path = backup_memory(args.source, args.dir, args.name)
        if backup_path:
            print(f"Backup created successfully: {backup_path}")
            return 0
        else:
            print("Backup failed")
            return 1
    
    elif args.command == "list":
        backups = list_backups(args.dir)
        if backups:
            print(f"Found {len(backups)} backups:")
            for i, backup in enumerate(backups):
                print(f"{i+1}. {backup['filename']} ({backup['size']} bytes, {backup['date']})")
            return 0
        else:
            print("No backups found")
            return 0
    
    elif args.command == "restore":
        success = restore_backup(args.backup, args.target)
        if success:
            print(f"Backup restored successfully: {args.backup} -> {args.target}")
            return 0
        else:
            print("Restore failed")
            return 1
    
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
