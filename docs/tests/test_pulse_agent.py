import asyncio
from skills.pulse_agent import PulseAgent

async def test():
    # Initialize the Pulse Agent
    agent = PulseAgent(user_id="test_user", memory_path="test_memory.db", simulate_responses=True)
    
    # Test a specific query
    query = "help"
    response = await agent.process_input(query)
    
    print(f"Query: '{query}'")
    print(f"Response: {response}")
    
    # Test another query
    query = "status"
    response = await agent.process_input(query)
    
    print(f"\nQuery: '{query}'")
    print(f"Response: {response}")
    
    # Test a general query
    query = "What is the capital of France?"
    response = await agent.process_input(query)
    
    print(f"\nQuery: '{query}'")
    print(f"Response: {response}")
    
    # Shutdown the agent
    agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test())
