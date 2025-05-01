#!/usr/bin/env python3
"""
Test script to verify model routing fix
"""

import os
import sys
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routing.router import AdaptiveRouter
from utils.neural_router import NeuralRouter
from skills.model_orchestrator import ModelOrchestrator

async def test_adaptive_router():
    """Test the adaptive router"""
    print("\n=== Testing Adaptive Router ===")
    
    # Initialize the adaptive router
    router = AdaptiveRouter()
    
    # Test routing for different query types
    test_queries = [
        "Hello, how are you today?",
        "What's the weather like?",
        "Write a Python function to calculate factorial",
        "Debug this code: print(1/0)",
        "Explain how databases work",
        "help",
        "status",
        "test"
    ]
    
    for query in test_queries:
        result = await router.route(query)
        print(f"\nQuery: {query}")
        print(f"Routed to: {result['model']} ({result['provider']})")
        print(f"Model name: {result['model_name']}")
        print(f"Offline compatible: {result['offline_compatible']}")
        print(f"System status: {result['system_status']}")

async def test_neural_router():
    """Test the neural router"""
    print("\n=== Testing Neural Router ===")
    
    # Initialize the model orchestrator (needed for neural router)
    orchestrator = ModelOrchestrator(simulate_responses=True)
    
    # Initialize the neural router
    router = NeuralRouter(model_interface=orchestrator)
    
    # Test routing for different query types
    test_queries = [
        "Hello, how are you today?",
        "What's the weather like?",
        "Write a Python function to calculate factorial",
        "Debug this code: print(1/0)",
        "Explain how databases work",
        "help",
        "status",
        "test"
    ]
    
    for query in test_queries:
        model, confidence = await router.route_query(query)
        print(f"\nQuery: {query}")
        print(f"Routed to: {model}")
        print(f"Confidence: {confidence}")

async def test_model_orchestrator():
    """Test the model orchestrator"""
    print("\n=== Testing Model Orchestrator ===")
    
    # Initialize the model orchestrator
    orchestrator = ModelOrchestrator(simulate_responses=True)
    
    # Test handling for different query types
    test_queries = [
        "Hello, how are you today?",
        "What's the weather like?",
        "Write a Python function to calculate factorial",
        "Debug this code: print(1/0)",
        "Explain how databases work",
        "help",
        "status",
        "test"
    ]
    
    for query in test_queries:
        result = await orchestrator.handle_query(query)
        print(f"\nQuery: {query}")
        print(f"Model: {result['model']}")
        print(f"Success: {result['success']}")
        print(f"Content preview: {result['content'][:100]}...")

async def run_tests():
    """Run all tests"""
    try:
        await test_adaptive_router()
        await test_neural_router()
        await test_model_orchestrator()
        print("\nAll model routing tests completed successfully!")
    except Exception as e:
        print(f"\nError during tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_tests())
