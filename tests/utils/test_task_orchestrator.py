"""
Test script for task orchestrator
"""

import asyncio
from utils.task_orchestrator import TaskOrchestrator
from skills.model_interface import ModelInterface

def main():
    """Main test function"""
    print("Testing task orchestrator...")
    
    # Initialize components
    model_interface = ModelInterface(simulate_responses=True)
    task_orchestrator = TaskOrchestrator(model_interface=model_interface)
    
    # Test workflow recommendation
    task_description = "Create a personal portfolio website"
    print(f"Getting recommended workflow for: {task_description}")
    
    workflow = task_orchestrator.get_recommended_workflow(task_description)
    
    print("\nRecommended Workflow:")
    print(f"Name: {workflow.get('name', 'Unknown')}")
    print("\nStages:")
    for i, stage in enumerate(workflow.get('stages', [])):
        print(f"Stage {i+1}: {stage.get('name', 'Unknown')} ({stage.get('task_type', 'Unknown')})")
        print(f"- {stage.get('prompt', 'No prompt')}")
        print()

if __name__ == "__main__":
    main()
