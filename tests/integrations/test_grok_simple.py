#!/usr/bin/env python
"""
Simple test script for Grok API
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("GROK_API_KEY")

if not api_key:
    print("Error: GROK_API_KEY not found in environment")
    exit(1)

print(f"API key found: {api_key[:5]}...{api_key[-5:]}")
print(f"Full API key for debugging: {api_key}")

# Try multiple possible endpoints
endpoints = [
    "https://api.xai.com/v1",
    "https://api.grok.ai/v1",
    "https://api.openai.com/v1"
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Test data
data = {
    "model": "grok-1.5",
    "messages": [
        {"role": "user", "content": "Say hello and identify yourself as Grok"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": False
}

# Try each endpoint
for endpoint in endpoints:
    print(f"\nTrying endpoint: {endpoint}")
    try:
        response = requests.post(
            f"{endpoint}/chat/completions", 
            headers=headers, 
            json=data,
            timeout=10
        )
        
        # Print status and response
        print(f"Status code: {response.status_code}")
        response_text = response.text[:300]
        print(f"Response: {response_text}...")
        
        # Check for authentication errors in the response body
        try:
            response_json = response.json()
            
            # Check for Chinese authentication error format
            if "msg" in response_json and "code" in response_json and response_json.get("code") == 401:
                print(f"Authentication failed: {response_json.get('msg')}")
                continue
                
            # Check for OpenAI-style errors
            if "error" in response_json:
                error_msg = response_json.get("error", {})
                if isinstance(error_msg, dict):
                    error_type = error_msg.get("type", "")
                    error_message = error_msg.get("message", "")
                    print(f"API Error: {error_type} - {error_message}")
                else:
                    print(f"API Error: {error_msg}")
                continue
                
            # If successful, format the content
            if response.status_code == 200 and "choices" in response_json:
                choices = response_json.get("choices", [])
                content = choices[0].get("message", {}).get("content", "") if choices else ""
                
                if content:
                    print("\nGrok says:")
                    print(f"{content}")
                    print("\nSuccess! Grok API is working with this endpoint.")
                    exit(0)
                else:
                    print("Warning: No content found in the response")
                    
            else:
                print("Response doesn't contain expected data format")
                
        except json.JSONDecodeError:
            print("Response is not valid JSON")
            
    except Exception as e:
        print(f"Error with {endpoint}: {str(e)}")

print("\nFailed to connect to Grok API with any of the attempted endpoints.")
print("\nAPI key may not be valid or service may be restricted in your region.")
print("The API is working but authentication is failing. You can still use the simulation mode.")
exit(1) 