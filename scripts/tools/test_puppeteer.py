#!/usr/bin/env python3
"""
Test script for Puppeteer MCP server
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add parent directories to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.append(root_dir)

def test_puppeteer():
    """Test Puppeteer MCP server."""
    print("Testing Puppeteer MCP server...")

    # Define the MCP server endpoint
    mcp_endpoint = "http://localhost:8000"

    # Define the navigate request
    navigate_request = {
        "name": "puppeteer_navigate",
        "parameters": {
            "url": "https://github.com/Spyboss/P.U.L.S.E."
        }
    }

    try:
        # Send the request to the MCP server
        response = requests.post(
            f"{mcp_endpoint}/tools",
            json=navigate_request,
            headers={"Content-Type": "application/json"}
        )

        # Check the response
        if response.status_code == 200:
            print("Successfully navigated to the URL!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Failed to navigate to the URL. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing Puppeteer MCP server: {str(e)}")
        return False

if __name__ == "__main__":
    test_puppeteer()
