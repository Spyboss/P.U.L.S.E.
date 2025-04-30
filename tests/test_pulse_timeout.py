"""
Test script to run the Pulse application with a timeout
"""

import asyncio
import sys
import time
import subprocess
import signal
import os

async def run_pulse_with_timeout(timeout_seconds=10):
    """Run the Pulse application with a timeout"""
    print(f"Running Pulse application with a {timeout_seconds} second timeout...")
    
    # Start the Pulse application
    process = subprocess.Popen(["python", "pulse.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Wait for the timeout
    print(f"Waiting for {timeout_seconds} seconds...")
    await asyncio.sleep(timeout_seconds)
    
    # Send Ctrl+C to the process
    print("Sending Ctrl+C to the process...")
    if os.name == 'nt':  # Windows
        process.send_signal(signal.CTRL_C_EVENT)
    else:  # Unix/Linux
        process.send_signal(signal.SIGINT)
    
    # Wait for the process to exit
    print("Waiting for the process to exit...")
    try:
        stdout, _ = process.communicate(timeout=10)
        print("Process exited with code:", process.returncode)
        print("Output:")
        print(stdout)
    except subprocess.TimeoutExpired:
        print("Process did not exit within the timeout period. Killing it...")
        process.kill()
        stdout, _ = process.communicate()
        print("Process killed.")
        print("Output:")
        print(stdout)
    
    return process.returncode

if __name__ == "__main__":
    exit_code = asyncio.run(run_pulse_with_timeout(15))
    sys.exit(exit_code)
