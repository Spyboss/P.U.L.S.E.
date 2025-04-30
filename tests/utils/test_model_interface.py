"""
Test OptimizedModelInterface
"""

import asyncio
import structlog
import sys
from skills.optimized_model_interface import OptimizedModelInterface

# Configure logger
logger = structlog.get_logger("test_model_interface")

async def test_model_interface():
    """Test OptimizedModelInterface"""
    print("\nTesting OptimizedModelInterface...")
    
    # Create OptimizedModelInterface instance
    model_interface = OptimizedModelInterface()
    
    # Check status
    status = await model_interface.check_status()
    print(f"Model interface status: {status}")
    
    # Get context data
    context_data = await model_interface.get_context_data()
    print(f"Context data: {context_data}")
    
    return True

async def main():
    """Main function"""
    print("=" * 60)
    print("OptimizedModelInterface Test")
    print("=" * 60)
    
    success = True
    
    try:
        # Test OptimizedModelInterface
        success = success and await test_model_interface()
        
        if success:
            print("\nSUCCESS: OptimizedModelInterface test passed!")
        else:
            print("\nERROR: OptimizedModelInterface test failed!")
        
        return success
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
