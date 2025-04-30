#!/usr/bin/env python3
"""
Test script for specialized models in P.U.L.S.E.
Tests the routing and response generation for specialized models like DeepCoder.
"""

import os
import sys
import asyncio
import logging

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_specialized_models")

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the model orchestrator directly
try:
    from skills.model_orchestrator import ModelOrchestrator
    logger.info("Successfully imported ModelOrchestrator")
except ImportError as e:
    logger.error(f"Error importing ModelOrchestrator: {e}")
    # Try an alternative import approach
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_orchestrator",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "model_orchestrator.py")
    )
    model_orchestrator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_orchestrator)
    ModelOrchestrator = model_orchestrator.ModelOrchestrator
    logger.info("Successfully imported ModelOrchestrator using alternative method")

async def test_specialized_model(orchestrator, query, expected_model):
    """
    Test a specialized model with a query

    Args:
        orchestrator: ModelOrchestrator instance
        query: Query to test
        expected_model: Expected model to be routed to
    """
    print(f"\n\n=== Testing query: {query} ===")
    print(f"Expected model: {expected_model}")

    # Process the query
    response = await orchestrator.handle_query(
        input_text=query,
        context={"system_prompt": "You are a helpful AI assistant."},
        model_preference=expected_model
    )

    # Print the response
    if response.get("success", False):
        print(f"Response from {response.get('model', 'unknown')}:")
        content = response.get("content", "No content")
        print(f"{content[:200]}..." if len(content) > 200 else content)
    else:
        print(f"Error: {response.get('error', 'Unknown error')}")

    print("=" * 50)

    return response

async def main():
    """Main test function"""
    print("Initializing Model Orchestrator...")
    orchestrator = ModelOrchestrator(simulate_responses=True)  # Use simulation mode for testing
    print("Model Orchestrator initialized!")

    # Test queries for specialized models
    test_queries = [
        ("ask code how to implement a binary search tree in Python", "code"),
        ("ask troubleshoot why my Python script is giving a NameError", "troubleshoot"),
        ("ask docs how to document a REST API", "docs"),
        ("ask technical how to explain OAuth to a junior developer", "technical"),
        ("ask brainstorm ideas for a personal finance app", "brainstorm"),
        ("ask ethics considerations for facial recognition in public spaces", "ethics"),
        ("ask visual how to design a user-friendly dashboard", "visual"),
        ("ask reasoning how to solve the traveling salesman problem", "reasoning"),
        ("ask math how to solve a quadratic equation", "math"),
        ("ask script how to optimize a Python script for memory usage", "script"),
        ("what's the weather today", "mistral")  # General query should go to Mistral-Small
    ]

    # Run tests
    for query, expected_model in test_queries:
        await test_specialized_model(orchestrator, query, expected_model)

    print("\nShutting down Model Orchestrator...")
    await orchestrator.shutdown()
    print("Model Orchestrator shutdown complete!")

if __name__ == "__main__":
    asyncio.run(main())
