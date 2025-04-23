#!/usr/bin/env python
"""
Runner script for General Pulse.

This script provides a convenient way to run the General Pulse application
with various configuration options.

Usage:
    python scripts/run_app.py [options]

Options:
    --debug         Run in debug mode with additional logging
    --simulate      Run in simulation mode without making API calls
    --config FILE   Use a specific configuration file
"""

import argparse
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main module
import pulse as main

def parse_args():
    parser = argparse.ArgumentParser(description='Run General Pulse')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode with additional logging')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode without making API calls')
    parser.add_argument('--config', type=str, help='Use a specific configuration file')

    return parser.parse_args()

def main_runner():
    args = parse_args()

    # Set environment variables based on arguments
    if args.debug:
        os.environ['DEBUG'] = 'true'

    if args.simulate:
        os.environ['SIMULATE'] = 'true'

    if args.config:
        os.environ['CONFIG_FILE'] = args.config

    # Run the main application
    main.main()

if __name__ == '__main__':
    main_runner()
