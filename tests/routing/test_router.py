#!/usr/bin/env python3
"""
Test script for the neural router
"""

import asyncio
from utils.neural_router import NeuralRouter

class MockModelInterface:
    """Mock model interface for testing"""
    async def call_mistral(self, query, max_tokens=1000):
        return {"success": True, "content": "This is a mock response"}

    async def call_openrouter(self, model_id, query, max_tokens=1000):
        return {"success": True, "content": "This is a mock response"}

    async def check_status(self):
        return {
            "main_brain": {"available": True, "api_key": True, "api_key_valid": True},
            "mistral": {"available": True, "api_key": True, "api_key_valid": True},
            "openrouter": {"available": True, "api_key": True, "models": []},
            "local": {"available": True},
            "ollama": {"available": False, "running": False},
            "timestamp": "2025-04-26T06:05:00"
        }

    async def check_internet(self):
        return True

async def main():
    # Initialize the neural router with a mock model interface
    neural_router = NeuralRouter(model_interface=MockModelInterface())

    # Test queries
    test_queries = [
        "ask code how to implement a binary search tree in Python",
        "ask debug why my Python code is crashing",
        "ask algorithm how to implement quicksort",
        "ask docs how to document my Python code",
        "ask explain what is a binary search tree",
        "ask summarize this article about AI",
        "ask troubleshoot why my computer is slow",
        "ask solve this math problem",
        "ask trends what's new in AI",
        "ask research the latest in quantum computing",
        "ask content write a blog post about AI",
        "ask creative write a short story",
        "ask write an email to my boss",
        "ask technical explain how a CPU works",
        "ask math solve this equation",
        "ask brainstorm ideas for a new app",
        "ask ideas for a new business",
        "ask ethics is AI dangerous"
    ]

    # Test each query
    for query in test_queries:
        model, confidence = await neural_router.route_query(query)
        print(f"Query: {query}")
        print(f"Model: {model}")
        print(f"Confidence: {confidence}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
