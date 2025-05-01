"""
LanceDB Patch Module

This module provides monkey patches for LanceDB to fix warnings and compatibility issues.
"""

import logging
import importlib.util
import sys
import warnings
from functools import wraps

# Configure logger
logger = logging.getLogger("lancedb_patch")

def apply_patches():
    """Apply all LanceDB patches"""
    try:
        # Check if LanceDB is installed
        if importlib.util.find_spec("lance") is None:
            logger.info("LanceDB not installed, skipping patches")
            return False
            
        # Apply patch for field_by_name warning
        patch_field_by_name_warning()
        
        logger.info("Applied LanceDB patches successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to apply LanceDB patches: {str(e)}")
        return False

def patch_field_by_name_warning():
    """
    Patch the field_by_name warning in LanceDB
    
    This patch suppresses the FutureWarning about the deprecated field_by_name method
    by filtering out the specific warning.
    """
    try:
        # Filter out the specific FutureWarning about field_by_name
        warnings.filterwarnings(
            "ignore", 
            message="The 'field_by_name' method is deprecated, use 'field' instead",
            category=FutureWarning
        )
        
        logger.info("Applied patch for field_by_name warning")
        return True
    except Exception as e:
        logger.error(f"Failed to patch field_by_name warning: {str(e)}")
        return False
