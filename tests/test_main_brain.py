import asyncio
import logging
from skills.model_orchestrator import ModelOrchestrator
from utils.api_key_manager import APIKeyManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-8s] %(message)s')
logger = logging.getLogger(__name__)

async def test_main_brain():
    """Test the Mistral-Small model via OpenRouter"""
    logger.info("Initializing API Key Manager...")
    api_key_manager = APIKeyManager()

    logger.info("Initializing Model Orchestrator...")
    model_orchestrator = ModelOrchestrator()
    # No need to call initialize() as it's done in the constructor

    logger.info("Testing OpenRouter API key...")
    result = await model_orchestrator.check_openrouter_api_key()

    if result["success"]:
        logger.info(f"✅ OpenRouter API key is valid!")
        logger.info(f"Response: {result.get('response', 'No response')}")

        # Now test Mistral-Small model with a query
        logger.info("\nTesting Mistral-Small model with query: What is machine learning? Keep it brief.")

        # Call Mistral-Small directly through the model orchestrator
        test_query = "What is machine learning? Keep it brief."
        try:
            mistral_result = await asyncio.wait_for(
                model_orchestrator.test_main_brain(test_query),
                timeout=30  # 30 second timeout
            )

            if mistral_result and mistral_result.get("success", False):
                logger.info("Test successful!")
                logger.info(f"Query: {test_query}")
                logger.info(f"Response: {mistral_result.get('content', '')}")
                logger.info(f"Model: {mistral_result.get('model_id', 'mistralai/mistral-small-3.1-24b-instruct:free')}")
            else:
                logger.error("Test failed!")
                logger.error(f"Query: {test_query}")
                logger.error(f"Error: {mistral_result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error testing Mistral-Small: {str(e)}")
    else:
        logger.error(f"❌ OpenRouter API key test failed!")
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
        logger.error(f"Message: {result.get('message', 'No message')}")

if __name__ == "__main__":
    asyncio.run(test_main_brain())
