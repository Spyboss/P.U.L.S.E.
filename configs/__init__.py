"""
Configuration module for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Handles loading and managing configuration from various sources
"""

import os
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "agent_config.yaml"

def load_config(config_path=None):
    """
    Load configuration from the specified path or the default path.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}