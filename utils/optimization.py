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
    # Force garbage collection with all generations
    gc.collect(generation=0)  # Collect youngest generation
    gc.collect(generation=1)  # Collect middle generation
    gc.collect(generation=2)  # Collect oldest generation

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

    # Try to terminate unnecessary background processes
    try:
        # Get all processes
        processes = psutil.process_iter(['pid', 'name', 'username', 'memory_percent'])

        # Find memory-intensive processes that might be related to our application
        for proc in processes:
            try:
                # Skip system processes
                if proc.info['username'] == 'SYSTEM' or proc.info['username'] == 'NT AUTHORITY\\SYSTEM':
                    continue

                # Check if it's a Python process using a lot of memory (but not our main process)
                proc_name = proc.info['name'].lower()
                if (proc_name.startswith('python') or 'torch' in proc_name or 'tensorflow' in proc_name) and \
                   proc.info['memory_percent'] > 5.0 and \
                   proc.pid != os.getpid():
                    logger.warning(f"Terminating memory-intensive process: {proc.info['name']} (PID: {proc.pid})")
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Error terminating processes: {str(e)}")

    # Sleep briefly to allow OS to reclaim memory
    time.sleep(0.5)

    # Force another garbage collection
    gc.collect()

    # Log memory after cleanup
    logger.info(f"Memory after emergency cleanup: {psutil.virtual_memory().available / 1_000_000:.2f}MB")

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

    # Get CPU information - use a robust approach with multiple fallbacks
    cpu_percent = 0  # Default value in case all methods fail

    try:
        # Method 1: Try with a very short interval (most accurate but can fail)
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except Exception as cpu_err:
        logger.warning(f"Error getting CPU percent with interval=0.1: {str(cpu_err)}")
        try:
            # Method 2: Try with a longer interval
            cpu_percent = psutil.cpu_percent(interval=0.5)
        except Exception as cpu_err2:
            logger.warning(f"Error getting CPU percent with interval=0.5: {str(cpu_err2)}")
            try:
                # Method 3: Try without interval parameter (may return 0.0 on first call)
                cpu_percent = psutil.cpu_percent()
                # If we get 0.0, try one more time after a small sleep
                if cpu_percent == 0.0:
                    import time
                    time.sleep(0.2)
                    cpu_percent = psutil.cpu_percent()
            except Exception as cpu_err3:
                # Method 4: Try per-CPU and average them
                logger.warning(f"Error getting CPU percent without interval: {str(cpu_err3)}")
                try:
                    per_cpu = psutil.cpu_percent(percpu=True)
                    if per_cpu and len(per_cpu) > 0:
                        cpu_percent = sum(per_cpu) / len(per_cpu)
                    else:
                        cpu_percent = 0
                except Exception as cpu_err4:
                    # Last resort - use a fixed value
                    logger.error(f"All CPU percent methods failed: {str(cpu_err4)}")
                    cpu_percent = 50  # Use a reasonable default value instead of 0

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
        },
        "sync": {
            "github_notion_interval": 3600,  # 1 hour by default
            "memory_constrained_interval": 7200  # 2 hours when memory is constrained
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

def should_run_sync(last_sync_time: float, memory_constrained: bool = False) -> bool:
    """
    Determine if sync operations should run based on memory constraints and time since last sync

    Args:
        last_sync_time: Timestamp of the last sync operation
        memory_constrained: Whether the system is currently memory constrained

    Returns:
        True if sync should run, False otherwise
    """
    # Get current time
    current_time = time.time()

    # Default intervals
    default_interval = 3600  # 1 hour
    memory_constrained_interval = 7200  # 2 hours

    # Try to load from config
    try:
        import json
        if os.path.exists("configs/hardware.json"):
            with open("configs/hardware.json", "r") as f:
                config = json.load(f)
                default_interval = config.get("sync", {}).get("github_notion_interval", 3600)
                memory_constrained_interval = config.get("sync", {}).get("memory_constrained_interval", 7200)
    except Exception as e:
        logger.error(f"Error loading sync intervals from config: {str(e)}")

    # Determine interval based on memory constraints
    interval = memory_constrained_interval if memory_constrained else default_interval

    # Check if enough time has passed since last sync
    time_since_last_sync = current_time - last_sync_time

    # Log decision
    if time_since_last_sync >= interval:
        logger.info(f"Sync should run: {time_since_last_sync:.2f}s since last sync (interval: {interval}s)")
        return True
    else:
        logger.info(f"Sync should not run yet: {time_since_last_sync:.2f}s since last sync (interval: {interval}s)")
        return False
