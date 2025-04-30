#!/usr/bin/env python3
"""
Test script for the "ask code" command
"""

import asyncio
import logging
import structlog
from pulse_core import PulseCore

# Configure logging
logging.basicConfig(level=logging.DEBUG)
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

async def main():
    print("Initializing P.U.L.S.E. Core...")
    core = PulseCore(user_id="test_user", debug_mode=True)
    print("P.U.L.S.E. Core initialized!")
    
    # Test the entire flow with the "ask code" command
    print("\nTesting the entire flow with the 'ask code' command...")
    
    # Step 1: Preprocess the query
    query = "ask code how to implement a binary search tree in Python"
    print(f"\nStep 1: Preprocessing query: {query}")
    preprocessed = await core.query_preprocessor.preprocess_query(query)
    print(f"Preprocessed query: {preprocessed}")
    
    # Step 2: Route the query
    print(f"\nStep 2: Routing query: {preprocessed['query']}")
    routing_result = await core.router.route(
        preprocessed["query"],
        intent=preprocessed.get("intent")
    )
    print(f"Routing result: {routing_result}")
    
    # Step 3: Get context for the model
    print(f"\nStep 3: Getting context for the model...")
    context_result = await core.history_manager.get_context_for_model()
    context = {}
    if context_result["success"]:
        context = context_result["context"]
    print(f"Context: {context}")
    
    # Step 4: Get the system prompt and add it to the context
    print(f"\nStep 4: Getting system prompt...")
    context["system_prompt"] = await core.charisma_engine.get_system_prompt(model=routing_result["model"])
    print(f"System prompt: {context['system_prompt'][:100]}...")
    
    # Step 5: Call the model
    print(f"\nStep 5: Calling the model...")
    response = await core.model_orchestrator.handle_query(
        input_text=preprocessed["query"],
        context=context,
        model_preference=routing_result["model"]
    )
    print(f"Response: {response}")
    
    # Step 6: Format the response
    print(f"\nStep 6: Formatting the response...")
    content = response.get("content", "I'm not sure how to respond to that.")
    formatted_response = core.charisma_engine.format_response(
        content=content,
        context_type=preprocessed.get("intent", "general"),
        model=routing_result["model"],
        success=response.get("success", False)
    )
    print(f"Formatted response: {formatted_response[:100]}...")
    
    print("\nShutting down P.U.L.S.E. Core...")
    await core.shutdown()
    print("P.U.L.S.E. Core shutdown complete!")

if __name__ == "__main__":
    asyncio.run(main())
