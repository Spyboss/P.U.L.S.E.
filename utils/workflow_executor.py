"""
Workflow Executor for General Pulse
Handles execution of multi-stage workflows
"""

import asyncio
import structlog
import time
from typing import Dict, List, Any, Optional

logger = structlog.get_logger("workflow_executor")

class WorkflowExecutor:
    """
    Executes multi-stage workflows
    """
    
    def __init__(self, task_orchestrator=None):
        """
        Initialize the workflow executor
        
        Args:
            task_orchestrator: Optional TaskOrchestrator instance
        """
        self.logger = structlog.get_logger("workflow_executor")
        
        # Import dependencies here to avoid circular imports
        if task_orchestrator is None:
            from utils.task_orchestrator import TaskOrchestrator
            self.task_orchestrator = TaskOrchestrator()
        else:
            self.task_orchestrator = task_orchestrator
        
        # Store the current workflow
        self.current_workflow = None
        self.current_task = None
        
        self.logger.info("Workflow executor initialized")
    
    async def execute_workflow(self, task_description: str) -> Dict[str, Any]:
        """
        Execute a workflow for a task
        
        Args:
            task_description: Description of the task
            
        Returns:
            Dictionary with workflow results
        """
        # Get recommended workflow
        workflow = self.task_orchestrator.get_recommended_workflow(task_description)
        self.current_workflow = workflow
        self.current_task = task_description
        
        self.logger.info(f"Executing workflow: {workflow['name']} for task: {task_description}")
        
        # Execute the workflow
        results = await self.task_orchestrator.execute_multi_stage_task(
            task_description=task_description,
            stages=workflow['stages']
        )
        
        # Format the results
        formatted_results = self._format_workflow_results(results)
        
        return {
            "success": results.get("success", False),
            "workflow_name": workflow['name'],
            "task_description": task_description,
            "formatted_results": formatted_results,
            "raw_results": results
        }
    
    def _format_workflow_results(self, results: Dict[str, Any]) -> str:
        """
        Format workflow results for display
        
        Args:
            results: Workflow results
            
        Returns:
            Formatted results string
        """
        if not results.get("success", False):
            return f"Workflow execution failed. Some stages did not complete successfully."
        
        formatted = f"Workflow Results for: {results.get('task_description', 'Unknown Task')}\n\n"
        
        for i, stage_result in enumerate(results.get("stages", [])):
            stage = stage_result.get("stage", f"Stage {i+1}")
            result = stage_result.get("result", {})
            
            formatted += f"--- {stage} ---\n"
            
            if result.get("success", False) and result.get("content"):
                # Truncate long content for display
                content = result.get("content", "")
                if len(content) > 500:
                    content = content[:500] + "...\n[Content truncated for display]"
                
                formatted += f"{content}\n\n"
            else:
                formatted += f"Failed to complete this stage: {result.get('error', 'Unknown error')}\n\n"
        
        return formatted
