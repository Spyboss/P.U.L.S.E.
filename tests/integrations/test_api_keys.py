#!/usr/bin/env python
"""
Test script for API keys - tests Claude and DeepSeek
"""

import os
import json
import requests
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI colors for nice output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{YELLOW}{'=' * 50}{RESET}")
    print(f"{BOLD}{YELLOW}  {text}{RESET}")
    print(f"{BOLD}{YELLOW}{'=' * 50}{RESET}\n")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print an info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")

def test_claude_api():
    """Test if the Claude API key is working."""
    print_header("Testing Claude API")
    
    # Get Claude API key from environment
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print_error("CLAUDE_API_KEY environment variable is not set")
        return False
    
    # Show masked key
    masked_key = f"{api_key[:7]}...{api_key[-5:]}"
    print_info(f"Using Claude API key: {masked_key}")
    
    # Set up API request
    endpoint = "https://api.anthropic.com/v1/messages"
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": api_key
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say hello and identify yourself as Claude in one sentence."}
        ]
    }
    
    print_info("Sending request to Claude API...")
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        
        # Print status
        status_code = response.status_code
        if status_code == 200:
            print_success(f"Request successful (status {status_code})")
        else:
            print_error(f"Request failed with status {status_code}")
        
        # Process the response
        response_json = response.json()
        if status_code == 200:
            content = response_json.get("content", [])
            text = ""
            for item in content:
                if item.get("type") == "text":
                    text += item.get("text", "")
            
            print_info("Response:")
            print(text.strip())
            print_success("Claude API key is working correctly!")
            return True
        else:
            error = response_json.get("error", {})
            print_error(f"API Error: {error.get('type')}: {error.get('message')}")
            return False
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_deepseek_api():
    """Test if the DeepSeek API key is working."""
    print_header("Testing DeepSeek API")
    
    # Get DeepSeek API key from environment
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print_error("DEEPSEEK_API_KEY environment variable is not set")
        return False
    
    # Show masked key
    masked_key = f"{api_key[:7]}...{api_key[-5:]}" if len(api_key) > 12 else "***masked***"
    print_info(f"Using DeepSeek API key: {masked_key}")
    
    # Set up API request - using the correct endpoints from the documentation
    endpoint = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "Say hello and identify yourself as DeepSeek in one sentence."}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print_info("Sending request to DeepSeek API...")
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        
        # Print status
        status_code = response.status_code
        if status_code == 200:
            print_success(f"Request successful (status {status_code})")
        else:
            print_error(f"Request failed with status {status_code}")
        
        # Process the response
        try:
            response_json = response.json()
            if status_code == 200:
                choices = response_json.get("choices", [])
                content = choices[0].get("message", {}).get("content", "") if choices else ""
                
                print_info("Response:")
                print(content.strip())
                print_success("DeepSeek API key is working correctly!")
                return True
            else:
                error = response_json.get("error", {})
                if isinstance(error, dict):
                    print_error(f"API Error: {error.get('message')}")
                else:
                    print_error(f"API Error: {error}")
                return False
        except json.JSONDecodeError:
            print_error(f"Invalid JSON response: {response.text[:200]}...")
            return False
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print_header("API Key Verification Tests")
    
    claude_success = test_claude_api()
    print("\n")
    deepseek_success = test_deepseek_api()
    
    print_header("Test Results")
    print(f"Claude API: {'Success' if claude_success else 'Failed'}")
    print(f"DeepSeek API: {'Success' if deepseek_success else 'Failed'}")
    
    if claude_success and deepseek_success:
        print_success("All API keys are working correctly!")
        sys.exit(0)
    elif not claude_success and not deepseek_success:
        print_error("Both API keys failed verification.")
        sys.exit(2)
    else:
        print_info("Some API keys are working, some are not.")
        sys.exit(1) 