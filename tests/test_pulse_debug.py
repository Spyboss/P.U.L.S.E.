import asyncio
import sys
import pulse

async def test():
    # Set debug flag
    sys.argv = ["pulse.py", "--debug"]
    
    # Run the main function
    await pulse.main()

if __name__ == "__main__":
    asyncio.run(test())
