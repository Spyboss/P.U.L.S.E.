"""
Test script for the AI Bug Bounty Hunter
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

from tools.bug_bounty_hunter import AIBugBountyHunter

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the AI Bug Bounty Hunter')
    parser.add_argument('--file', help='Path to a specific file to analyze')
    parser.add_argument('--repo', help='Path to a repository to analyze')
    parser.add_argument('--diff', action='store_true', help='Analyze git diff in the specified repo')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the Bug Bounty Hunter
    bug_hunter = AIBugBountyHunter()
    
    if not bug_hunter.is_configured():
        print("AI Bug Bounty Hunter is not properly configured.")
        print("Make sure the AI models (DeepSeek and Claude) are configured.")
        sys.exit(1)
    
    print("AI Bug Bounty Hunter Test")
    print("========================")
    
    # Decide what to analyze based on arguments
    if args.file:
        analyze_file(bug_hunter, args.file)
    elif args.repo and args.diff:
        analyze_diff(bug_hunter, args.repo)
    elif args.repo:
        analyze_repo(bug_hunter, args.repo)
    else:
        # No specific file or repo provided, create a test file with intentional bugs
        test_file = create_test_file()
        analyze_file(bug_hunter, test_file)
        # Clean up the test file
        os.remove(test_file)

def analyze_file(bug_hunter, file_path):
    """Analyze a single file for bugs."""
    print(f"\nAnalyzing file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    # Run the analysis
    result = bug_hunter.analyze_file(file_path)
    
    # Display results
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\nAnalysis Results:")
    print(f"Found {result['total_issues']} potential issues")
    
    if result['total_issues'] > 0:
        print("\nIssues:")
        for i, issue in enumerate(result.get('issues', []), 1):
            severity = issue.get('severity', 'medium').upper()
            line = issue.get('line', 'Unknown')
            description = issue.get('description', 'No description provided')
            
            print(f"\n{i}. [Line {line}] {severity}: {description}")
            
            if "humorous_comment" in issue:
                print(f"   💬 {issue['humorous_comment']}")
                
            if "fix_suggestion" in issue and issue["fix_suggestion"] != "Not provided":
                print(f"   Suggestion: {issue['fix_suggestion']}")
    else:
        print("\nNo issues found. Your code looks good!")

def analyze_diff(bug_hunter, repo_path):
    """Analyze git diff in a repository."""
    print(f"\nAnalyzing git diff in repository: {repo_path}")
    
    if not os.path.exists(repo_path):
        print(f"Error: Repository not found: {repo_path}")
        return
    
    # Run the analysis
    result = bug_hunter.analyze_git_diff(repo_path=repo_path)
    
    # Display results
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\nAnalysis Results:")
    print(f"Found {result['total_issues']} potential issues in the changes")
    
    if result['total_issues'] > 0:
        print("\nIssues:")
        for i, issue in enumerate(result.get('issues', []), 1):
            severity = issue.get('severity', 'medium').upper()
            file = issue.get('file', 'Unknown file')
            line = issue.get('line', 'Unknown')
            description = issue.get('description', 'No description provided')
            
            print(f"\n{i}. [{file}:{line}] {severity}: {description}")
            
            if "humorous_comment" in issue:
                print(f"   💬 {issue['humorous_comment']}")
                
            if "fix_suggestion" in issue and issue["fix_suggestion"] != "Not provided":
                print(f"   Suggestion: {issue['fix_suggestion']}")
    else:
        print("\nNo issues found in the changes. Looking good!")

def analyze_repo(bug_hunter, repo_path, max_files=5):
    """Analyze a repository for bugs."""
    print(f"\nAnalyzing repository: {repo_path}")
    print(f"(Limited to {max_files} files)")
    
    if not os.path.exists(repo_path):
        print(f"Error: Repository not found: {repo_path}")
        return
    
    # Run the analysis
    result = bug_hunter.analyze_repo(repo_path, max_files=max_files)
    
    # Display results
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\nAnalysis Results:")
    print(f"Analyzed {result['files_analyzed']} files")
    print(f"Found {result['total_issues']} potential issues total")
    
    if result['total_issues'] > 0:
        for file_result in result.get('file_results', []):
            file_issues = file_result.get('total_issues', 0)
            if file_issues > 0:
                file_path = file_result.get('file', 'Unknown file')
                print(f"\n\nFile: {file_path}")
                print(f"Issues: {file_issues}")
                
                for i, issue in enumerate(file_result.get('issues', []), 1):
                    severity = issue.get('severity', 'medium').upper()
                    line = issue.get('line', 'Unknown')
                    description = issue.get('description', 'No description provided')
                    
                    print(f"\n  {i}. [Line {line}] {severity}: {description}")
                    
                    if "humorous_comment" in issue:
                        print(f"     💬 {issue['humorous_comment']}")
                        
                    if "fix_suggestion" in issue and issue["fix_suggestion"] != "Not provided":
                        print(f"     Suggestion: {issue['fix_suggestion']}")
    else:
        print("\nNo issues found. The repository looks clean!")

def create_test_file():
    """Create a Python file with intentional bugs for testing."""
    print("\nCreating a test file with intentional bugs...")
    
    file_path = "test_buggy_code.py"
    
    # Code with intentional bugs
    code = """
# This is a test file with intentional bugs

def divide_numbers(a, b):
    # Bug 1: No check for division by zero
    return a / b

def get_item_from_list(my_list, index):
    # Bug 2: No check for index out of bounds
    return my_list[index]

def read_file_content(file_path):
    # Bug 3: No error handling for file not found
    with open(file_path, 'r') as file:
        return file.read()

# Bug 4: Unused import
import random

# Bug 5: SQL Injection vulnerability
def get_user(username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    # Execute query...
    
# Bug 6: Infinite loop potential
def process_data(data):
    i = 0
    while i < len(data):
        # Bug: if the processing removes items from data,
        # this could run indefinitely
        process_item(data[i])
        # No increment of i

def process_item(item):
    # Just a placeholder
    pass

# Bug 7: Memory leak potential
def create_large_list():
    large_list = [i for i in range(10000000)]  
    # large_list is never released

# Bug 8: Race condition
shared_counter = 0
def increment_counter():
    global shared_counter
    # Bug: Read and increment without synchronization
    current = shared_counter
    # Some delay could occur here in a real scenario
    shared_counter = current + 1
    
# Main execution
if __name__ == "__main__":
    result = divide_numbers(10, 2)  # This will work
    
    # Bug 9: Will throw an exception
    result = divide_numbers(10, 0)  
    
    my_list = [1, 2, 3]
    # Bug 10: Index error
    item = get_item_from_list(my_list, 10)
"""
    
    with open(file_path, 'w') as f:
        f.write(code)
    
    print(f"Created test file: {file_path}")
    return file_path

if __name__ == "__main__":
    main() 