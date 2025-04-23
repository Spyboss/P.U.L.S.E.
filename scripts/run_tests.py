#!/usr/bin/env python
"""
Test runner script for General Pulse.

This script provides a convenient way to run tests for the General Pulse application.
It supports running all tests or specific test categories.

Usage:
    python scripts/run_tests.py [options]

Options:
    --all           Run all tests
    --utils         Run utility tests
    --skills        Run skills tests
    --tools         Run tools tests
    --integrations  Run integration tests
    --verbose       Run tests with verbose output
    --failfast      Stop on first failure
"""

import argparse
import unittest
import sys
import os
import time

def run_tests(test_path, verbose=False, failfast=False, pattern='test_*.py'):
    """Run tests from the specified path."""
    # Add the project root to the path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    print(f"Running tests from: {test_path} (pattern: {pattern})")
    start_time = time.time()

    # Discover and run tests
    loader = unittest.TestLoader()
    tests = loader.discover(test_path, pattern=pattern)

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1, failfast=failfast)
    result = runner.run(tests)

    elapsed_time = time.time() - start_time
    print(f"Completed in {elapsed_time:.2f} seconds")

    return result.wasSuccessful()

def main():
    parser = argparse.ArgumentParser(description='Run General Pulse tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--root', action='store_true', help='Run root directory tests')
    parser.add_argument('--utils', action='store_true', help='Run utility tests')
    parser.add_argument('--skills', action='store_true', help='Run skills tests')
    parser.add_argument('--tools', action='store_true', help='Run tools tests')
    parser.add_argument('--integrations', action='store_true', help='Run integration tests')
    parser.add_argument('--verbose', action='store_true', help='Run tests with verbose output')
    parser.add_argument('--failfast', action='store_true', help='Stop on first failure')

    args = parser.parse_args()

    # If no specific test category is specified, run all tests
    if not (args.root or args.utils or args.skills or args.tools or args.integrations):
        args.all = True

    success = True

    if args.all or args.root:
        print("\n=== Running Root Directory Tests ===\n")
        if not run_tests('tests', args.verbose, args.failfast, pattern='test_*.py'):
            success = False
            if args.failfast:
                return 1

    if args.all or args.utils:
        print("\n=== Running Utility Tests ===\n")
        if not run_tests('tests/utils', args.verbose, args.failfast):
            success = False
            if args.failfast:
                return 1

    if args.all or args.skills:
        print("\n=== Running Skills Tests ===\n")
        if not run_tests('tests/skills', args.verbose, args.failfast):
            success = False
            if args.failfast:
                return 1

    if args.all or args.tools:
        print("\n=== Running Tools Tests ===\n")
        if not run_tests('tests/tools', args.verbose, args.failfast):
            success = False
            if args.failfast:
                return 1

    if args.all or args.integrations:
        print("\n=== Running Integration Tests ===\n")
        if not run_tests('tests/integrations', args.verbose, args.failfast):
            success = False
            if args.failfast:
                return 1

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
