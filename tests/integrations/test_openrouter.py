#!/usr/bin/env python3
"""
Test script to directly call OpenRouter API
"""

import os
import sys
import json
import httpx
import asyncio
from dotenv import load_dotenv
import logging
from utils.execution_flow import ExecutionFlow

logging.basicConfig(level=logging.INFO)

async def test_openrouter_api():
    """Test the OpenRouter API directly"""
    # Load API key from .env
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("ERROR: No OpenRouter API key found in .env file")
        return False
    
    print(f"Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Set up headers and payload
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://general-pulse.app",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "anthropic/claude-3-opus",
        "messages": [
            {"role": "user", "content": "What is artificial intelligence?"}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    print("Sending request to OpenRouter API...")
    
    # Make the API call
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"API error: {response.text}")
                return False
            
            # Parse and print the response
            result = response.json()
            print(f"Full API response:\n{json.dumps(result, indent=2)}")
            
            # Check for error in the response JSON (even with status code 200)
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                error_code = result["error"].get("code", 0)
                print(f"\nAPI Error (code {error_code}): {error_msg}")
                return False
            
            # Extract content
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"\nContent: {content}")
            
            # Check token usage
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            print(f"\nToken usage: {prompt_tokens} prompt, {completion_tokens} completion")
            
            return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function"""
    print("Testing OpenRouter API...")
    
    # Run the async test
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    result = asyncio.run(test_openrouter_api())
    
    if result:
        print("\nSuccess! The OpenRouter API is working.")
    else:
        print("\nFailed to get a proper response from OpenRouter.")
        print("Please check your API key and OpenRouter account status.")
    
    return 0 if result else 1

async def test_model_execution_flow():
    """Test ModelExecutionFlow with Claude-3-Opus"""
    print("Testing ModelExecutionFlow with Claude-3-Opus...")
    
    flow = ExecutionFlow()
    
    # First test with an intentionally high max_tokens value to verify it's auto-adjusted
    print("\nTest 1: Testing with high max_tokens value (should be auto-adjusted)...")
    result = await flow.execute_query(
        'Generate a short explanation of how GPT models work',
        model_preference='claude-3-opus',
        system_prompt='',
        temperature=0.7,
        max_tokens=2000  # This is higher than our limit and should be auto-adjusted
    )
    
    print(f'Result status: {"Success" if result.get("success", False) else "Failed"}')
    print(f'Response excerpt: {result.get("content", "No content")[:100]}...')
    
    # Now test with a reasonable value that shouldn't trigger auto-adjustment
    print("\nTest 2: Testing with reasonable max_tokens value...")
    result2 = await flow.execute_query(
        'What are the three most important considerations when designing a CLI tool?',
        model_preference='claude-3-opus',
        system_prompt='',
        temperature=0.7,
        max_tokens=300  # This is within our limit and shouldn't need adjustment
    )
    
    print(f'Result status: {"Success" if result2.get("success", False) else "Failed"}')
    print(f'Response excerpt: {result2.get("content", "No content")[:100]}...')
    
    return result

if __name__ == "__main__":
    # Get command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "flow":
        # Windows policy if needed
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Run the flow test
        asyncio.run(test_model_execution_flow())
        sys.exit(0)
    else:
        # Run the regular test
        sys.exit(main()) 