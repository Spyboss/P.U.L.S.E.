"""
Test script for workflow executor
"""

import asyncio
from utils.workflow_executor import WorkflowExecutor
from utils.task_orchestrator import TaskOrchestrator
from skills.model_interface import ModelInterface

async def main():
    """Main test function"""
    print("Testing workflow executor...")
    
    # Initialize components
    model_interface = ModelInterface(simulate_responses=True)
    task_orchestrator = TaskOrchestrator(model_interface=model_interface)
    workflow_executor = WorkflowExecutor(task_orchestrator=task_orchestrator)
    
    # Test workflow execution
    task_description = "Create a personal portfolio website"
    print(f"Executing workflow for: {task_description}")
    
    result = await workflow_executor.execute_workflow(task_description)
    
    print("\nWorkflow Results:")
    print(f"Success: {result.get('success', False)}")
    print(f"Workflow: {result.get('workflow_name', 'Unknown')}")
    print("\nFormatted Results:")
    print(result.get('formatted_results', 'No results'))

if __name__ == "__main__":
    asyncio.run(main())
