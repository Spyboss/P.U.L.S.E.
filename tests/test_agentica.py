"""
Test script for Agentica model
"""

import os
import sys
import asyncio

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from skills.model_orchestrator import ModelOrchestrator

async def test_agentica():
    print("Initializing ModelOrchestrator...")
    orchestrator = ModelOrchestrator()

    print("Testing Agentica model...")
    response = await orchestrator.query_specialized_model(
        'agentica',
        'Write a Python function to calculate the factorial of a number'
    )

    print("\nTesting Gemini model...")
    gemini_response = await orchestrator._call_gemini(
        'Write a Python function to calculate the factorial of a number',
        ''
    )

    print("\nAgentica Response:")
    print(response)

    if response and response.get("success", False):
        print("\nAgentica Content:")
        print(response.get("content", "No content"))
    else:
        print("\nAgentica Error:")
        print(response.get("error", "Unknown error"))

    print("\nGemini Response:")
    print(gemini_response)

    if gemini_response and gemini_response.get("success", False):
        print("\nGemini Content:")
        print(gemini_response.get("content", "No content"))
    else:
        print("\nGemini Error:")
        print(gemini_response.get("error", "Unknown error"))

if __name__ == "__main__":
    asyncio.run(test_agentica())
