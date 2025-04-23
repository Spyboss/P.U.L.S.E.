#!/usr/bin/env python3
"""
Test script for ONNX-optimized intent classifier
"""

import asyncio
import time
import logging
import sys
from pathlib import Path
import psutil
import gc

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_onnx_classifier():
    """Test the ONNX intent classifier performance and memory usage"""
    try:
        # Pre-test memory usage
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Force GC before test
        gc.collect()
        
        # Import after GC to measure accurate memory impact
        logger.info("Importing ONNX classifier...")
        from utils.intent_classifier_onnx import get_intent_classifier
        
        # Record import memory
        import_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        logger.info(f"Memory after import: {import_memory:.2f} MB (delta: {import_memory - initial_memory:.2f} MB)")
        
        # Check if ONNX model exists
        onnx_model_path = Path("models/onnx/distilbert.onnx")
        if not onnx_model_path.exists():
            logger.warning(f"ONNX model not found at {onnx_model_path}")
            logger.info("You need to run the conversion script first: python scripts/convert_to_onnx.py")
            return
            
        # Initialize classifier
        logger.info("Initializing ONNX classifier...")
        start_time = time.time()
        classifier = get_intent_classifier()
        init_time = time.time() - start_time
        
        # Record memory after initialization
        init_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        logger.info(f"Memory after initialization: {init_memory:.2f} MB (delta: {init_memory - import_memory:.2f} MB)")
        logger.info(f"Initialization time: {init_time:.2f} seconds")
        
        # Test queries
        test_queries = [
            "What time is it?",
            "Help me with the commands",
            "Create a new repository on GitHub",
            "Show me the system status",
            "Write a blog post about Python",
            "Create a new note in Notion",
            "Add a task to my list",
            "Ask Claude about the future of AI",
            "Hello, how are you today?"
        ]
        
        # Run classification tests
        logger.info("Running classification tests...")
        for i, query in enumerate(test_queries):
            # Measure single query performance
            start_time = time.time()
            intent = classifier.classify(query)
            query_time = time.time() - start_time
            
            # Log results
            logger.info(f"Query {i+1}: '{query}'")
            logger.info(f"  → Intent: {intent}")
            logger.info(f"  → Time: {query_time*1000:.2f} ms")
            
            # Check memory after each query
            current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            logger.info(f"  → Memory: {current_memory:.2f} MB (delta: {current_memory - init_memory:.2f} MB)")
            
        # Test async classification
        logger.info("\nTesting async classification...")
        start_time = time.time()
        async_results = await asyncio.gather(*[classifier.classify_async(query) for query in test_queries])
        async_time = time.time() - start_time
        
        # Log async results
        logger.info(f"Async classification of {len(test_queries)} queries: {async_time:.2f} seconds")
        logger.info(f"Average time per query: {(async_time*1000)/len(test_queries):.2f} ms")
        
        # Force cleanup and measure final memory
        classifier.cleanup()
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        logger.info(f"Final memory usage: {final_memory:.2f} MB (net change: {final_memory - initial_memory:.2f} MB)")
        
        # Compare with regex-only classification
        logger.info("\nTesting regex-only fallback...")
        start_time = time.time()
        for query in test_queries:
            intent = classifier._classify_with_regex(query)
        regex_time = time.time() - start_time
        
        logger.info(f"Regex classification time: {regex_time:.2f} seconds")
        logger.info(f"Speedup with ONNX vs regex: {regex_time/async_time:.2f}x")
        
        # Summary
        logger.info("\nPerformance summary:")
        logger.info(f"Memory overhead: {init_memory - initial_memory:.2f} MB")
        logger.info(f"Average inference time: {(async_time*1000)/len(test_queries):.2f} ms per query")
        logger.info(f"Model file size: {onnx_model_path.stat().st_size / (1024*1024):.2f} MB")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the test
    asyncio.run(test_onnx_classifier()) 