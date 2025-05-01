import asyncio
from utils.intent_handler import IntentHandler

async def test():
    handler = IntentHandler()
    intent = await handler.classify('help')
    print(f'Intent: {intent}')

if __name__ == "__main__":
    asyncio.run(test())
