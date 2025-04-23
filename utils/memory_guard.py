"""
Memory Guard utility for General Pulse
Helps protect against memory leaks and excessive resource usage
"""

import gc
import contextlib
import os
import psutil
import logging
import structlog

logger = structlog.get_logger("memory_guard")

@contextlib.contextmanager
def memory_guard(threshold_mb=100, force_gc=True):
    """
    Context manager to monitor memory usage and trigger cleanup when necessary
    
    Args:
        threshold_mb: Memory increase threshold in MB to trigger warnings
        force_gc: Whether to force garbage collection after the operation
    """
    # Get current process
    process = psutil.Process(os.getpid())
    
    # Record starting memory
    start_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Log starting memory if high
    if start_memory > 500:  # 500 MB threshold
        logger.warning(f"High memory usage before operation: {start_memory:.2f} MB")
    
    try:
        # Start operation
        yield
    finally:
        # Explicitly run garbage collection
        if force_gc:
            collected = gc.collect()
            logger.debug(f"Garbage collector: collected {collected} objects")
        
        # Check memory after operation
        end_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
        delta = end_memory - start_memory
        
        # Log memory usage
        if delta > threshold_mb:
            logger.warning(f"High memory increase: {delta:.2f} MB (from {start_memory:.2f} to {end_memory:.2f} MB)")
            
            # If memory is critically high, take more aggressive action
            if end_memory > 1000:  # Over 1 GB of memory usage
                logger.error(f"Critical memory usage: {end_memory:.2f} MB. Taking emergency measures.")
                
                # Force more aggressive garbage collection
                gc.collect(2)  # Full collection
                
                # Check memory after aggressive GC
                post_gc_memory = process.memory_info().rss / (1024 * 1024)
                logger.info(f"Memory after emergency GC: {post_gc_memory:.2f} MB (freed {end_memory - post_gc_memory:.2f} MB)")
                
                # If still high, provide guidance
                if post_gc_memory > 800:  # Still over 800 MB
                    logger.critical("Memory remains critical after GC. Consider restarting the application.")
        else:
            logger.debug(f"Memory usage stable. Change: {delta:.2f} MB (from {start_memory:.2f} to {end_memory:.2f} MB)")

def check_system_memory():
    """
    Check overall system memory and return status
    
    Returns:
        tuple: (available_mb, total_mb, percent_used)
    """
    memory = psutil.virtual_memory()
    available_mb = memory.available / (1024 * 1024)
    total_mb = memory.total / (1024 * 1024)
    percent_used = memory.percent
    
    # Log warning if available memory is low
    if available_mb < 1000:  # Less than 1 GB available
        logger.warning(f"Low system memory: {available_mb:.2f} MB available ({percent_used}% used)")
    
    return (available_mb, total_mb, percent_used) 