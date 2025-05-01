import asyncio
from utils.intent_handler import IntentHandler

async def test():
    # Initialize the intent handler
    handler = IntentHandler()
    
    # Test a specific query
    query = "help"
    intent = await handler.classify(query)
    
    print(f"Query: '{query}'")
    print(f"Mapped Intent: {intent}")

if __name__ == "__main__":
    asyncio.run(test())
