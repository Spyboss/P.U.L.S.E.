"""
General Pulse utilities
Contains commonly used functions across the application
"""

import os
import json
import yaml
from datetime import datetime
import structlog

# Don't import logger here to avoid circular imports
# Use get_logger() function instead

def get_logger(name="general_pulse"):
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name for component identification
        
    Returns:
        structlog.BoundLogger: A configured logger instance
    """
    return structlog.get_logger(name)

def load_yaml_config(config_path):
    """Load YAML configuration file."""
    logger = get_logger()
    try:
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found: {config_path}")
            return {}
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.debug(f"Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {str(e)}", exc_info=True)
        return {}

def save_yaml_config(config_data, config_path):
    """Save configuration data to YAML file."""
    logger = get_logger()
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False)
            logger.debug(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {str(e)}", exc_info=True)
        return False

def load_json_data(file_path, default=None):
    """Load JSON data from file."""
    logger = get_logger()
    try:
        if default is None:
            default = {}
            
        if not os.path.exists(file_path):
            logger.warning(f"JSON file not found: {file_path}")
            return default
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Loaded JSON data from {file_path}")
            return data
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {file_path}", exc_info=True)
        return default
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {str(e)}", exc_info=True)
        return default

def save_json_data(data, file_path):
    """Save data as JSON."""
    logger = get_logger()
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            logger.debug(f"Saved JSON data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {str(e)}", exc_info=True)
        return False

def get_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def get_formatted_date():
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%B %d, %Y")

def ensure_directory_exists(directory_path):
    """
    Ensure that a directory exists, creating it if necessary
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        bool: True if the directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {str(e)}")
        return False 