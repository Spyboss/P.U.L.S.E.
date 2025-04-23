#!/usr/bin/env python3
"""
Test script for General Pulse Agent
"""

import asyncio
import sys
import os
from skills.agent import Agent

async def test_agent_models():
    """Test the agent's ability to query AI models"""
    
    print("Testing Agent model queries...")
    
    # Create agent
    agent = Agent(simulate_responses=False)
    
    # Test model queries
    models = ["claude", "gpt-3.5-turbo", "deepseek"]
    for model in models:
        print(f"\nTesting model: {model}")
        response = await agent._handle_ai_command(f"ask {model} What is artificial intelligence?")
        print(f"Response: {response[:150]}...")
    
    print("\nTest completed.")

if __name__ == "__main__":
    # Set up Windows policy if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the test
    asyncio.run(test_agent_models()) 