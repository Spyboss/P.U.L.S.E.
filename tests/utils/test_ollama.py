import asyncio
from utils.ollama_manager import OllamaManager

async def test():
    manager = OllamaManager()
    status = await manager.check_status()
    print(f'Ollama status: {status}')

if __name__ == "__main__":
    asyncio.run(test())
