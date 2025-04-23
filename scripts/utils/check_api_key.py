#!/usr/bin/env python3
"""
Script to check if the OpenRouter API key is correctly loaded
"""

import os
from dotenv import load_dotenv

def main():
    """Check OpenRouter API key"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Try to get the API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if api_key:
        print(f"API key found: Yes")
        print(f"API key length: {len(api_key)} characters")
        print(f"First 10 chars: {api_key[:10]}...")
        
        # Check if it's still the placeholder
        if api_key == "your_api_key_here":
            print("WARNING: You're using the placeholder API key!")
            print("Please replace 'your_api_key_here' in the .env file with your actual OpenRouter API key.")
    else:
        print("API key found: No")
        print("The OPENROUTER_API_KEY environment variable is not set.")
        print("Make sure you have a .env file in the project root with your API key.")

if __name__ == "__main__":
    main() 