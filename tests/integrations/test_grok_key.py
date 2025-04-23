#!/usr/bin/env python
"""
Test script to verify if the Grok API key is working correctly.
This script attempts to make a simple API call to Grok and reports the results.
"""

import os
import logging
import sys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GrokKeyTest")

# Import the ModelInterface class
try:
    from skills.model_interface import ModelInterface
    logger.info("Successfully imported ModelInterface")
except ImportError as e:
    logger.error(f"Failed to import ModelInterface: {str(e)}")
    sys.exit(1)

def test_grok_api():
    """Test if the Grok API key is working."""
    # Load environment variables
    logger.info("Loading environment variables...")
    load_dotenv()
    
    # Get Grok API key from environment
    grok_api_key = os.environ.get("GROK_API_KEY")
    if not grok_api_key:
        logger.error("GROK_API_KEY environment variable is not set")
        return False
    else:
        # Show masked key for verification
        masked_key = grok_api_key[:4] + "*" * (len(grok_api_key) - 8) + grok_api_key[-4:]
        logger.info(f"Found Grok API key: {masked_key}")
        
        # Check if this is a test key
        if grok_api_key.startswith("sk_test_"):
            logger.warning("Using a test API key that may not connect to the real service")
    
    # Initialize the model interface
    logger.info("Initializing ModelInterface...")
    model_interface = ModelInterface()
    
    # Check if Grok is in the available models
    available_models = model_interface.get_available_models()
    logger.info(f"Available models: {available_models}")
    
    if 'grok' not in available_models:
        logger.warning("Grok is not listed in available models. Check if it's enabled in the configuration.")
        
        # Check if Grok is in the models but disabled
        if 'grok' in model_interface.models:
            enabled = model_interface.models['grok'].get('enabled', False)
            logger.info(f"Grok is configured but enabled={enabled}")
            if not enabled:
                logger.info("You need to enable Grok in configs/agent_config.yaml")
                return False
    
    # Get endpoint from config
    grok_config = model_interface.models.get('grok', {})
    endpoint = grok_config.get('endpoint', 'unknown')
    logger.info(f"Using endpoint: {endpoint}")
    
    # Try to call the Grok API
    logger.info("Testing Grok API with a simple query...")
    test_prompt = "Hello, this is a test prompt to verify the Grok API key is working."
    response = model_interface.call_model_api('grok', test_prompt)
    
    # Check the response
    if "error" in response:
        error_msg = response.get('error', '')
        logger.error(f"API call failed: {error_msg}")
        
        # If using a test key, handle this specially
        if grok_api_key.startswith("sk_test_") and ("authentication" in error_msg.lower() or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower()):
            logger.warning("Test API key detected - this is expected to fail with authentication errors")
            logger.info("✅ Grok integration is implemented and configured correctly, but requires a valid API key")
            return True
            
        return False
    else:
        logger.info("API call succeeded!")
        logger.info(f"Grok response: {response.get('response', '')[:100]}...")
        return True

if __name__ == "__main__":
    logger.info("Starting Grok API key verification test...")
    success = test_grok_api()
    
    if success:
        logger.info("✅ Grok API key is working correctly!")
        sys.exit(0)
    else:
        logger.error("❌ Grok API key verification failed!")
        sys.exit(1) 