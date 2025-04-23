#!/usr/bin/env python3
"""
Installation script for General Pulse
Sets up the environment and dependencies
"""

import os
import sys
import subprocess
import platform
import argparse
import shutil
from datetime import datetime

def check_python_version():
    """
    Check if Python version is compatible

    Returns:
        True if compatible, False otherwise
    """
    required_version = (3, 8)
    current_version = sys.version_info

    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required")
        print(f"Current version: {current_version[0]}.{current_version[1]}.{current_version[2]}")
        return False

    return True

def check_pip():
    """
    Check if pip is installed

    Returns:
        True if installed, False otherwise
    """
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print("Error: pip is not installed")
        return False

def create_virtual_environment(venv_dir):
    """
    Create a virtual environment

    Args:
        venv_dir: Directory for the virtual environment

    Returns:
        True if successful, False otherwise
    """
    print(f"Creating virtual environment in {venv_dir}...")

    try:
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False

def install_dependencies(venv_dir, requirements_file, upgrade=False):
    """
    Install dependencies in the virtual environment

    Args:
        venv_dir: Directory of the virtual environment
        requirements_file: Path to requirements.txt
        upgrade: Whether to upgrade existing packages

    Returns:
        True if successful, False otherwise
    """
    print("Installing dependencies...")

    # Get path to pip in virtual environment
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")

    # Build command
    cmd = [pip_path, "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.extend(["-r", requirements_file])

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_env_file():
    """
    Create .env file if it doesn't exist

    Returns:
        True if successful, False otherwise
    """
    env_file = ".env"

    if os.path.exists(env_file):
        print(f"{env_file} already exists, skipping")
        return True

    print(f"Creating {env_file}...")

    try:
        with open(env_file, "w") as f:
            f.write("# General Pulse environment variables\n")
            f.write("# Created by install.py on {}\n\n".format(datetime.now().isoformat()))
            f.write("# API Keys\n")
            f.write("OPENROUTER_API_KEY=\n")
            f.write("MISTRAL_SMALL_API_KEY=\n\n")
            f.write("# Optional Settings\n")
            f.write("# LOG_LEVEL=INFO\n")
            f.write("# SIMULATE_RESPONSES=false\n")

        print(f"{env_file} created. Please edit it to add your API keys.")
        return True
    except Exception as e:
        print(f"Error creating {env_file}: {e}")
        return False

def create_directories():
    """
    Create required directories

    Returns:
        True if successful, False otherwise
    """
    directories = ["logs", "backups", "configs"]

    for directory in directories:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            try:
                os.makedirs(directory)
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return False

    return True

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install General Pulse")
    parser.add_argument("--venv", type=str, default="venv", help="Virtual environment directory")
    parser.add_argument("--requirements", type=str, default="requirements.txt", help="Requirements file")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade existing packages")
    parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment creation")
    args = parser.parse_args()

    # Print welcome message
    print("=" * 70)
    print("General Pulse Installation")
    print("=" * 70)

    # Check Python version
    if not check_python_version():
        return 1

    # Check pip
    if not check_pip():
        return 1

    # Create directories
    if not create_directories():
        return 1

    # Create virtual environment
    if not args.no_venv:
        if not create_virtual_environment(args.venv):
            return 1

        # Install dependencies
        if not install_dependencies(args.venv, args.requirements, args.upgrade):
            return 1
    else:
        print("Skipping virtual environment creation")

        # Install dependencies globally
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if args.upgrade:
                cmd.append("--upgrade")
            cmd.extend(["-r", args.requirements])

            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            return 1

    # Create .env file
    if not create_env_file():
        return 1

    # Print success message
    print("\n" + "=" * 70)
    print("Installation completed successfully!")
    print("=" * 70)

    if not args.no_venv:
        if platform.system() == "Windows":
            activate_cmd = f"{args.venv}\\Scripts\\activate"
        else:
            activate_cmd = f"source {args.venv}/bin/activate"

        print(f"\nTo activate the virtual environment, run:")
        print(f"  {activate_cmd}")

    print("\nBefore running General Pulse, edit the .env file to add your API keys.")
    print("\nTo run General Pulse, use:")
    print("  python pulse.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
