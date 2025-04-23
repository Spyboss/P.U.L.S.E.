"""
Optimization utilities for General Pulse
Provides memory management and hardware optimization
"""

import os
import gc
import psutil
import sqlite3
import time
import functools
import structlog
from typing import Callable, Any
import platform

# Configure logger
logger = structlog.get_logger("optimization")

# Check if CUDA is available
try:
    import torch
    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False

# System information
SYSTEM_INFO = {
    "platform": platform.system(),
    "processor": platform.processor(),
    "python_version": platform.python_version(),
    "total_ram": psutil.virtual_memory().total,
    "total_disk": psutil.disk_usage('/').total,
    "cuda_available": CUDA_AVAILABLE
}

# Memory thresholds
LOW_MEMORY_THRESHOLD = 800_000_000  # 800MB
CRITICAL_MEMORY_THRESHOLD = 400_000_000  # 400MB

def memory_guard(func: Callable) -> Callable:
    """
    Decorator to guard against low memory conditions
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check available memory
        available_memory = psutil.virtual_memory().available
        
        if available_memory < CRITICAL_MEMORY_THRESHOLD:
            # Critical memory condition - take emergency measures
            logger.warning(f"Critical memory condition: {available_memory / 1_000_000:.2f}MB available")
            emergency_memory_cleanup()
            
            # If still critical, return error
            if psutil.virtual_memory().available < CRITICAL_MEMORY_THRESHOLD:
                logger.error("Memory still critical after cleanup, aborting operation")
                return "⚠️ System memory critically low. Please close other applications and try again."
        
        elif available_memory < LOW_MEMORY_THRESHOLD:
            # Low memory condition - perform cleanup
            logger.warning(f"Low memory condition: {available_memory / 1_000_000:.2f}MB available")
            gc.collect()
            
            # Optimize SQLite if using it
            try:
                sqlite3.connect("pulse_memory.db").execute("PRAGMA journal_mode=WAL")
            except:
                pass
            
            # Log warning
            logger.info(f"Memory after cleanup: {psutil.virtual_memory().available / 1_000_000:.2f}MB")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return wrapper

def emergency_memory_cleanup() -> None:
    """
    Perform emergency memory cleanup
    """
    # Force garbage collection
    gc.collect()
    
    # Close SQLite connections
    try:
        for conn in sqlite3.Connection.__instances__:
            conn.close()
    except:
        pass
    
    # Clear CUDA cache if available
    if TORCH_AVAILABLE and CUDA_AVAILABLE:
        try:
            torch.cuda.empty_cache()
        except:
            pass
    
    # Sleep briefly to allow OS to reclaim memory
    time.sleep(0.5)
    
    # Force another garbage collection
    gc.collect()

def optimize_for_hardware() -> None:
    """
    Optimize settings for the current hardware
    """
    # Log system information
    logger.info(
        "System information",
        platform=SYSTEM_INFO["platform"],
        processor=SYSTEM_INFO["processor"],
        total_ram=f"{SYSTEM_INFO['total_ram'] / 1_000_000_000:.2f}GB",
        total_disk=f"{SYSTEM_INFO['total_disk'] / 1_000_000_000:.2f}GB",
        cuda_available=SYSTEM_INFO["cuda_available"]
    )
    
    # Optimize for CUDA if available
    if TORCH_AVAILABLE and CUDA_AVAILABLE:
        try:
            # Set CUDA device
            torch.cuda.set_device(0)
            
            # Limit GPU memory usage to 512MB (0.5GB)
            torch.cuda.set_per_process_memory_fraction(0.5)
            
            # Enable CUDNN benchmark mode for potentially faster runtime
            torch.backends.cudnn.benchmark = True
            
            logger.info("CUDA optimizations applied")
        except Exception as e:
            logger.error(f"Failed to apply CUDA optimizations: {str(e)}")
    
    # Optimize for CPU
    else:
        # Set environment variables for CPU optimization
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow logging
        os.environ["OMP_NUM_THREADS"] = "4"  # Limit OpenMP threads
        os.environ["MKL_NUM_THREADS"] = "4"  # Limit MKL threads
        
        logger.info("CPU optimizations applied")
    
    # Optimize SQLite for HDD
    try:
        conn = sqlite3.connect("pulse_memory.db")
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better performance
        conn.execute("PRAGMA synchronous=NORMAL")  # Less synchronous for better performance
        conn.execute("PRAGMA temp_store=MEMORY")  # Store temp files in memory
        conn.execute("PRAGMA cache_size=5000")  # Increase cache size
        conn.close()
        
        logger.info("SQLite optimizations applied")
    except Exception as e:
        logger.error(f"Failed to apply SQLite optimizations: {str(e)}")
    
    # Check for SSD and optimize if available
    if os.path.exists("/mnt/ssd"):
        try:
            os.environ["TMPDIR"] = "/mnt/ssd/tmp"
            os.makedirs("/mnt/ssd/tmp", exist_ok=True)
            
            conn = sqlite3.connect("pulse_memory.db")
            conn.execute("PRAGMA temp_store_directory='/mnt/ssd/tmp'")
            conn.close()
            
            logger.info("SSD optimizations applied")
        except Exception as e:
            logger.error(f"Failed to apply SSD optimizations: {str(e)}")

def get_system_status() -> dict:
    """
    Get current system status
    
    Returns:
        Dictionary with system status information
    """
    # Get memory information
    memory = psutil.virtual_memory()
    
    # Get disk information
    disk = psutil.disk_usage('/')
    
    # Get CPU information
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Get GPU information if available
    gpu_info = {}
    if TORCH_AVAILABLE and CUDA_AVAILABLE:
        try:
            gpu_info = {
                "name": torch.cuda.get_device_name(0),
                "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1_000_000:.2f}MB",
                "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1_000_000:.2f}MB",
                "max_memory_allocated": f"{torch.cuda.max_memory_allocated(0) / 1_000_000:.2f}MB"
            }
        except:
            pass
    
    return {
        "memory": {
            "total": f"{memory.total / 1_000_000_000:.2f}GB",
            "available": f"{memory.available / 1_000_000_000:.2f}GB",
            "used": f"{memory.used / 1_000_000_000:.2f}GB",
            "percent": memory.percent
        },
        "disk": {
            "total": f"{disk.total / 1_000_000_000:.2f}GB",
            "free": f"{disk.free / 1_000_000_000:.2f}GB",
            "used": f"{disk.used / 1_000_000_000:.2f}GB",
            "percent": disk.percent
        },
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True)
        },
        "gpu": gpu_info,
        "processes": len(psutil.pids())
    }

def configure_hardware() -> None:
    """
    Configure hardware settings based on detected hardware
    """
    # Create hardware configuration file
    config = {
        "system": SYSTEM_INFO,
        "memory": {
            "low_threshold_mb": LOW_MEMORY_THRESHOLD / 1_000_000,
            "critical_threshold_mb": CRITICAL_MEMORY_THRESHOLD / 1_000_000
        },
        "gpu": {
            "enabled": CUDA_AVAILABLE,
            "memory_limit_fraction": 0.5
        },
        "optimizations": {
            "sqlite_wal": True,
            "reduce_logging": True,
            "limit_threads": True,
            "ssd_temp": os.path.exists("/mnt/ssd")
        }
    }
    
    # Save configuration
    try:
        import json
        with open("configs/hardware.json", "w") as f:
            json.dump(config, f, indent=2)
        logger.info("Hardware configuration saved")
    except Exception as e:
        logger.error(f"Failed to save hardware configuration: {str(e)}")
    
    # Apply optimizations
    optimize_for_hardware()
