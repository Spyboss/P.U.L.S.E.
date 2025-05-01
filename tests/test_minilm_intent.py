import asyncio
from utils.intent_handler import IntentHandler

async def test():
    # Initialize the intent handler
    handler = IntentHandler()
    
    # Test queries
    test_queries = [
        "help",
        "status",
        "what is the capital of France?",
        "write a Python function to calculate factorial",
        "enable offline mode",
        "test gemini",
        "github search repositories"
    ]
    
    print("Testing Intent Handler with MiniLM classifier...")
    for query in test_queries:
        # Get the raw MiniLM classification
        minilm_intent = await handler.classify_with_minilm(query)
        
        # Get the mapped intent
        mapped_intent = await handler.classify(query)
        
        print(f"Query: '{query}'")
        print(f"  Raw MiniLM Intent: {minilm_intent}")
        print(f"  Mapped Intent: {mapped_intent}")
        print()

if __name__ == "__main__":
    asyncio.run(test())
