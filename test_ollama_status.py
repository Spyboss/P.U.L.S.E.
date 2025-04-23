"""
Test Ollama status check
"""

import asyncio
from utils.ollama_manager import OllamaManager

async def test_ollama_status():
    """Test Ollama status check"""
    print("Testing Ollama status check...")
    
    # Create OllamaManager instance
    manager = OllamaManager()
    
    # Check status
    status = await manager.check_status()
    print(f"Ollama status: {status}")
    
    # Test with force=True
    status_force = await manager.check_status(force=True)
    print(f"Ollama status (force=True): {status_force}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_ollama_status())
