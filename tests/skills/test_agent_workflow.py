"""
Test script for agent workflow execution
"""

import asyncio
from skills.agent import Agent
from utils.logger import setup_logger
import logging

async def main():
    """Main test function"""
    print("Testing agent workflow execution...")
    
    # Set up logging
    setup_logger(logging.INFO)
    
    # Initialize agent with simulation mode
    agent = Agent(simulate_responses=True)
    
    # Test workflow command
    task_description = "Create a personal portfolio website"
    print(f"Executing workflow command: workflow {task_description}")
    
    # Handle workflow command
    workflow_result = await agent._handle_workflow_command(f"workflow {task_description}")
    print("\nWorkflow Command Result:")
    print(workflow_result)
    
    # Store the current workflow task
    agent.current_workflow_task = task_description
    
    # Execute the workflow
    print("\nExecuting workflow...")
    execution_result = await agent._execute_workflow(task_description)
    print("\nWorkflow Execution Result:")
    print(execution_result)

if __name__ == "__main__":
    asyncio.run(main())
