"""
Comprehensive test for Ollama status check
"""

import asyncio
import structlog
import sys
from utils.ollama_manager import OllamaManager, OllamaClient

# Configure logger
logger = structlog.get_logger("test_ollama")

async def test_ollama_client():
    """Test OllamaClient"""
    print("\nTesting OllamaClient...")
    
    # Create OllamaClient instance
    client = OllamaClient()
    
    # Check health
    health = await client.check_health()
    print(f"Ollama health: {health}")
    
    # Check health with force=True
    health_force = await client.check_health(force=True)
    print(f"Ollama health (force=True): {health_force}")
    
    # Check health with offline_mode=False
    health_offline = await client.check_health(offline_mode=False)
    print(f"Ollama health (offline_mode=False): {health_offline}")
    
    return True

async def test_ollama_manager():
    """Test OllamaManager"""
    print("\nTesting OllamaManager...")
    
    # Create OllamaManager instance
    manager = OllamaManager()
    
    # Check status
    status = await manager.check_status()
    print(f"Ollama status: {status}")
    
    # Check status with force=True
    status_force = await manager.check_status(force=True)
    print(f"Ollama status (force=True): {status_force}")
    
    return True

async def main():
    """Main function"""
    print("=" * 60)
    print("Comprehensive Ollama Status Test")
    print("=" * 60)
    
    success = True
    
    try:
        # Test OllamaClient
        success = success and await test_ollama_client()
        
        # Test OllamaManager
        success = success and await test_ollama_manager()
        
        if success:
            print("\nSUCCESS: All Ollama tests passed!")
        else:
            print("\nERROR: Some Ollama tests failed!")
        
        return success
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
