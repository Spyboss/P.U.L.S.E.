#!/usr/bin/env python3
"""
Test script for the model orchestrator
"""

import asyncio
from skills.model_orchestrator import ModelOrchestrator

async def main():
    # Initialize the model orchestrator
    model_orchestrator = ModelOrchestrator()
    
    # Test query
    query = "ask code how to implement a binary search tree in Python"
    
    # Get the model from the neural router
    model, confidence = await model_orchestrator.neural_router.route_query(query)
    print(f"Query: {query}")
    print(f"Model: {model}")
    print(f"Confidence: {confidence}")
    
    # Call the model
    response = await model_orchestrator.handle_query(
        input_text=query,
        model_preference=model
    )
    
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
