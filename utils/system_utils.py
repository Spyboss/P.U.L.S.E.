"""
System utilities for General Pulse
Provides functions for getting system information and status
"""

import os
import sys
import platform
import psutil
import structlog
from typing import Dict, Any

# Configure logger
logger = structlog.get_logger("system_utils")

def get_system_info() -> Dict[str, Any]:
    """
    Get system information
    
    Returns:
        Dictionary with system information
    """
    try:
        # Get platform information
        platform_name = platform.system()
        processor = platform.processor()
        
        # Get memory information
        memory = psutil.virtual_memory()
        total_ram = memory.total / (1024 * 1024 * 1024)  # Convert to GB
        
        # Get disk information
        disk = psutil.disk_usage('/')
        total_disk = disk.total / (1024 * 1024 * 1024)  # Convert to GB
        
        # Check for CUDA availability
        cuda_available = False
        try:
            import torch
            cuda_available = torch.cuda.is_available()
        except ImportError:
            pass
        
        # Log system information
        logger.info("System information", 
                    platform=platform_name, 
                    processor=processor, 
                    total_ram=f"{total_ram:.2f}GB", 
                    total_disk=f"{total_disk:.2f}GB",
                    cuda_available=cuda_available)
        
        return {
            "platform": platform_name,
            "processor": processor,
            "total_ram": f"{total_ram:.2f}GB",
            "total_disk": f"{total_disk:.2f}GB",
            "cuda_available": cuda_available
        }
    except Exception as e:
        logger.error(f"Error getting system information: {str(e)}")
        return {
            "platform": "Unknown",
            "processor": "Unknown",
            "total_ram": "Unknown",
            "total_disk": "Unknown",
            "cuda_available": False
        }

def get_system_status() -> Dict[str, Any]:
    """
    Get current system status
    
    Returns:
        Dictionary with system status
    """
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_used = memory.used / (1024 * 1024 * 1024)  # Convert to GB
        memory_total = memory.total / (1024 * 1024 * 1024)  # Convert to GB
        memory_percent = memory.percent
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_used = disk.used / (1024 * 1024 * 1024)  # Convert to GB
        disk_total = disk.total / (1024 * 1024 * 1024)  # Convert to GB
        disk_percent = disk.percent
        
        # Get processor information
        processor = platform.processor()
        
        # Log system status
        logger.info("System status", 
                    cpu_percent=cpu_percent, 
                    memory_used=f"{memory_used:.2f}GB", 
                    memory_percent=memory_percent,
                    disk_used=f"{disk_used:.2f}GB", 
                    disk_percent=disk_percent)
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "processor": processor
            },
            "memory": {
                "used": f"{memory_used:.2f}GB",
                "total": f"{memory_total:.2f}GB",
                "percent": memory_percent
            },
            "disk": {
                "used": f"{disk_used:.2f}GB",
                "total": f"{disk_total:.2f}GB",
                "percent": disk_percent
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "cpu": {
                "percent": 0,
                "processor": "Unknown"
            },
            "memory": {
                "used": "0GB",
                "total": "0GB",
                "percent": 0
            },
            "disk": {
                "used": "0GB",
                "total": "0GB",
                "percent": 0
            }
        }

def check_low_memory(threshold_gb: float = 2.0) -> bool:
    """
    Check if system memory is low
    
    Args:
        threshold_gb: Threshold in GB for low memory warning
        
    Returns:
        True if memory is low, False otherwise
    """
    try:
        # Get available memory
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024 * 1024 * 1024)  # Convert to GB
        
        # Check if available memory is below threshold
        if available_gb < threshold_gb:
            logger.warning(f"Low memory detected ({available_gb:.1f}GB available). Forcing CPU mode.")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking memory: {str(e)}")
        return False

def get_available_models() -> Dict[str, bool]:
    """
    Get available AI models
    
    Returns:
        Dictionary with model availability
    """
    models = {
        "gemini": False,
        "openrouter": False,
        "local": False
    }
    
    # Check for Gemini
    try:
        import google.generativeai
        models["gemini"] = True
    except ImportError:
        pass
    
    # Check for OpenRouter
    try:
        from openai import OpenAI
        models["openrouter"] = True
    except ImportError:
        pass
    
    # Check for local models
    try:
        import torch
        import transformers
        models["local"] = True
    except ImportError:
        pass
    
    return models
