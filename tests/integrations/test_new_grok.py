#!/usr/bin/env python
"""
Test script for Grok API with the new key
"""

import os
import json
import requests
from dotenv import load_dotenv

# Force reload environment variables
os.environ.clear()
load_dotenv(override=True)

# Get API key
api_key = os.environ.get("GROK_API_KEY")

if not api_key:
    print("Error: GROK_API_KEY not found in environment")
    exit(1)

print(f"Using API key: {api_key}")

# Try different formats for the key
# Some APIs expect "Bearer token", others just the token
headers_formats = [
    {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    {"api-key": api_key, "Content-Type": "application/json"},
    {"x-api-key": api_key, "Content-Type": "application/json"}
]

# Try multiple possible endpoints
endpoints = [
    "https://api.xai.com/v1",
    "https://api.grok.ai/v1", 
    "https://api.openai.com/v1"
]

# Test data (using OpenAI format which xAI usually follows)
data = {
    "model": "grok-1.5",
    "messages": [
        {"role": "user", "content": "Say hello and identify yourself as Grok"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": False
}

# Try each endpoint with each header format
for endpoint in endpoints:
    print(f"\nTrying endpoint: {endpoint}")
    
    for headers in headers_formats:
        print(f"With headers: {headers}")
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
            
            # Try to parse the response as JSON
            try:
                response_json = response.json()
                
                # Check for Chinese error message format
                if "msg" in response_json and "code" in response_json:
                    print(f"Error message: {response_json.get('msg')}")
                    continue
                    
                # Check for OpenAI-style errors
                if "error" in response_json:
                    error = response_json.get("error", {})
                    if isinstance(error, dict):
                        print(f"Error type: {error.get('type')}")
                        print(f"Error message: {error.get('message')}")
                    else:
                        print(f"Error: {error}")
                    continue
                
                # If successful, format the content
                if response.status_code == 200 and "choices" in response_json:
                    choices = response_json.get("choices", [])
                    content = choices[0].get("message", {}).get("content", "") if choices else ""
                    
                    if content:
                        print("\nGrok says:")
                        print(f"{content}")
                        print("\nSuccess! Grok API is working with this configuration.")
                        exit(0)
                    else:
                        print("Warning: No content found in the response")
                        
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                
        except Exception as e:
            print(f"Error with request: {str(e)}")

print("\nFailed to connect to Grok API with any of the attempted configurations.")
print("The API key may not be valid or service may be restricted in your region.")
print("You may need to use a VPN if the API is restricted based on geography.")
exit(1) 