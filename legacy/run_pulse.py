#!/usr/bin/env python3
"""
Run script for General Pulse
Runs the application with hardware optimization
"""

import os
import sys
import argparse
import subprocess
import platform
import psutil
import time
import signal
import structlog
from datetime import datetime

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger("runner")

# Global variables
pulse_process = None
running = True

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    global running
    print("\nShutting down Pulse...")
    running = False
    if pulse_process:
        pulse_process.terminate()

def get_system_info():
    """
    Get system information
    
    Returns:
        Dictionary with system information
    """
    # Get CPU information
    cpu_count = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Get memory information
    memory = psutil.virtual_memory()
    
    # Get disk information
    disk = psutil.disk_usage('/')
    
    # Get platform information
    system = platform.system()
    release = platform.release()
    version = platform.version()
    processor = platform.processor()
    
    # Check for CUDA
    cuda_available = False
    try:
        import torch
        cuda_available = torch.cuda.is_available()
    except ImportError:
        pass
    
    return {
        "cpu": {
            "cores": cpu_count,
            "threads": cpu_threads,
            "percent": cpu_percent,
            "processor": processor
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent
        },
        "disk": {
            "total": disk.total,
            "free": disk.free,
            "percent": disk.percent
        },
        "platform": {
            "system": system,
            "release": release,
            "version": version
        },
        "cuda_available": cuda_available
    }

def optimize_environment():
    """
    Optimize environment variables for better performance
    
    Returns:
        Dictionary with optimized environment variables
    """
    # Start with current environment
    env = os.environ.copy()
    
    # Get system info
    system_info = get_system_info()
    
    # Set environment variables based on system info
    
    # Optimize Python
    env["PYTHONUNBUFFERED"] = "1"  # Unbuffered output
    env["PYTHONIOENCODING"] = "utf-8"  # UTF-8 encoding
    
    # Optimize OpenMP
    cpu_threads = system_info["cpu"]["threads"]
    recommended_threads = max(1, min(4, cpu_threads - 1))  # Leave at least 1 thread for OS
    env["OMP_NUM_THREADS"] = str(recommended_threads)
    env["MKL_NUM_THREADS"] = str(recommended_threads)
    
    # Optimize TensorFlow logging
    env["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Only show warnings and errors
    
    # Optimize PyTorch
    if system_info["cuda_available"]:
        env["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU
    else:
        env["CUDA_VISIBLE_DEVICES"] = ""  # Disable GPU
    
    # Optimize for Windows
    if system_info["platform"]["system"] == "Windows":
        env["PYTHONUTF8"] = "1"  # UTF-8 encoding on Windows
    
    # Log optimizations
    logger.info(
        "Environment optimized",
        omp_threads=env["OMP_NUM_THREADS"],
        mkl_threads=env["MKL_NUM_THREADS"],
        cuda_devices=env["CUDA_VISIBLE_DEVICES"]
    )
    
    return env

def run_pulse(args):
    """
    Run the Pulse application
    
    Args:
        args: Command line arguments
    """
    global pulse_process
    
    # Get optimized environment
    env = optimize_environment()
    
    # Build command
    cmd = [sys.executable, "pulse.py"]
    
    # Add arguments
    if args.simulate:
        cmd.append("--simulate")
    if args.user:
        cmd.extend(["--user", args.user])
    if args.memory:
        cmd.extend(["--memory", args.memory])
    
    # Log command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Run the process
    pulse_process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE if args.log else None,
        stderr=subprocess.PIPE if args.log else None,
        text=True,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Log process ID
    logger.info(f"Pulse process started with PID {pulse_process.pid}")
    
    # Monitor process if logging
    if args.log:
        log_file = f"logs/pulse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, "w") as f:
            # Write header
            f.write(f"=== Pulse Log - {datetime.now().isoformat()} ===\n\n")
            
            # Monitor process output
            while running and pulse_process.poll() is None:
                # Read stdout
                stdout_line = pulse_process.stdout.readline()
                if stdout_line:
                    sys.stdout.write(stdout_line)
                    f.write(stdout_line)
                    f.flush()
                
                # Read stderr
                stderr_line = pulse_process.stderr.readline()
                if stderr_line:
                    sys.stderr.write(stderr_line)
                    f.write(f"ERROR: {stderr_line}")
                    f.flush()
                
                # Small delay to reduce CPU usage
                time.sleep(0.01)
            
            # Write footer
            f.write(f"\n=== End of Log - {datetime.now().isoformat()} ===\n")
        
        logger.info(f"Log saved to {log_file}")
    
    else:
        # Wait for process to complete
        pulse_process.wait()
    
    # Get return code
    return_code = pulse_process.returncode
    logger.info(f"Pulse process exited with code {return_code}")
    
    return return_code

def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run General Pulse with hardware optimization")
    parser.add_argument("--simulate", action="store_true", help="Simulate AI responses (for testing)")
    parser.add_argument("--user", type=str, default="uminda", help="User identifier")
    parser.add_argument("--memory", type=str, default="pulse_memory.db", help="Path to memory database")
    parser.add_argument("--log", action="store_true", help="Log output to file")
    args = parser.parse_args()
    
    # Print system information
    system_info = get_system_info()
    logger.info(
        "System information",
        cpu_cores=system_info["cpu"]["cores"],
        cpu_threads=system_info["cpu"]["threads"],
        memory_total=f"{system_info['memory']['total'] / (1024**3):.2f} GB",
        memory_available=f"{system_info['memory']['available'] / (1024**3):.2f} GB",
        memory_percent=f"{system_info['memory']['percent']}%",
        platform=system_info["platform"]["system"],
        cuda_available=system_info["cuda_available"]
    )
    
    # Run Pulse
    try:
        return_code = run_pulse(args)
        return return_code
    except KeyboardInterrupt:
        print("\nShutting down Pulse...")
        if pulse_process:
            pulse_process.terminate()
        return 0
    except Exception as e:
        logger.error(f"Error running Pulse: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
