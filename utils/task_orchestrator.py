"""
Task Orchestrator for General Pulse
Handles task routing, model selection, and execution flow
"""

import asyncio
import structlog
import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Union

logger = structlog.get_logger("task_orchestrator")

class TaskOrchestrator:
    """
    Orchestrates task execution by routing to appropriate models and handling fallbacks
    """

    def __init__(self, model_interface=None):
        """
        Initialize the task orchestrator

        Args:
            model_interface: Optional ModelInterface instance
        """
        self.logger = structlog.get_logger("task_orchestrator")

        # Import dependencies here to avoid circular imports
        if model_interface is None:
            from skills.optimized_model_interface import OptimizedModelInterface
            self.model_interface = OptimizedModelInterface()
        else:
            self.model_interface = model_interface

        # Define model roles and specialties
        self.model_roles = {
            "decision_making": ["gemini", "gpt-4", "claude-3-opus"],  # Strategic thinking
            "content_generation": ["claude-3-sonnet", "claude", "gpt-3.5-turbo"],  # Content creation
            "code_generation": ["deepseek", "claude-3-opus", "gpt-4"],  # Code writing
            "code_review": ["deepseek", "gpt-4", "claude-3-opus"],  # Code analysis
            "data_analysis": ["grok", "gpt-4", "gemini"],  # Data processing
            "creative": ["claude-3-opus", "claude", "gpt-4"],  # Creative tasks
            "research": ["claude-3-sonnet", "gpt-4", "gemini"],  # Research tasks
            "summarization": ["claude", "gpt-3.5-turbo", "gemini"]  # Summarization
        }

        # Task type detection keywords
        self.task_keywords = {
            "decision_making": ["decide", "choose", "plan", "strategy", "prioritize"],
            "content_generation": ["write", "create", "draft", "compose", "generate content"],
            "code_generation": ["code", "program", "script", "function", "class", "implement"],
            "code_review": ["review code", "debug", "fix", "optimize", "refactor"],
            "data_analysis": ["analyze", "data", "statistics", "trends", "metrics"],
            "creative": ["creative", "story", "design", "imagine", "invent"],
            "research": ["research", "find", "search", "investigate", "explore"],
            "summarization": ["summarize", "summary", "tldr", "brief", "overview"]
        }

        # Task history for context
        self.task_history = []
        self.max_history = 20

        self.logger.info("Task orchestrator initialized")

    async def execute_task(self, task_description: str, task_type: Optional[str] = None,
                          system_prompt: Optional[str] = None, temperature: float = 0.7,
                          max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Execute a task using the appropriate model based on task type

        Args:
            task_description: Description of the task to execute
            task_type: Optional explicit task type, otherwise detected from description
            system_prompt: Optional system prompt to guide the model
            temperature: Temperature for model generation
            max_tokens: Maximum tokens for model generation

        Returns:
            Dictionary with task results and metadata
        """
        start_time = time.time()

        # Detect task type if not provided
        if task_type is None:
            task_type = self._detect_task_type(task_description)
            self.logger.info(f"Detected task type: {task_type}")

        # Get appropriate models for this task type
        models = self.model_roles.get(task_type, ["gemini", "gpt-4", "claude"])

        # Create task context from history
        task_context = self._build_task_context(task_type)

        # Enhance system prompt with task context if provided
        enhanced_system_prompt = system_prompt or ""
        if task_context and enhanced_system_prompt:
            enhanced_system_prompt = f"{enhanced_system_prompt}\n\nTask Context: {task_context}"
        elif task_context:
            enhanced_system_prompt = f"Task Context: {task_context}"

        # Try models in sequence until one succeeds
        result = None
        used_model = None
        error = None

        for model in models:
            try:
                self.logger.info(f"Attempting task with model: {model}")

                # Call the model
                response = await self.model_interface.call_model_api_async(
                    model_name=model,
                    prompt=task_description,
                    system_prompt=enhanced_system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Check if successful
                if response and response.get("success", False):
                    result = response.get("content", "")
                    used_model = model
                    self.logger.info(f"Task completed successfully with model: {model}")
                    break
                else:
                    error = response.get("error", "Unknown error")
                    self.logger.warning(f"Model {model} failed: {error}")

            except Exception as e:
                error = str(e)
                self.logger.error(f"Error with model {model}: {error}")

        # Record task in history
        elapsed_time = time.time() - start_time
        task_record = {
            "timestamp": time.time(),
            "task_type": task_type,
            "description": task_description,
            "model_used": used_model,
            "success": result is not None,
            "elapsed_time": elapsed_time
        }
        self._add_to_history(task_record)

        # Return results
        return {
            "content": result,
            "success": result is not None,
            "model_used": used_model,
            "task_type": task_type,
            "elapsed_time": elapsed_time,
            "error": error if not result else None
        }

    async def execute_multi_stage_task(self, task_description: str,
                                      stages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a multi-stage task with different models for each stage

        Args:
            task_description: Overall task description
            stages: List of stage configurations with task types and prompts

        Returns:
            Dictionary with results from all stages
        """
        self.logger.info(f"Starting multi-stage task: {task_description}")

        results = []
        overall_success = True
        stage_outputs = {}

        for i, stage in enumerate(stages):
            stage_name = stage.get("name", f"Stage {i+1}")
            stage_type = stage.get("task_type", "decision_making")
            stage_prompt = stage.get("prompt", "")
            stage_system_prompt = stage.get("system_prompt", "")

            # Replace placeholders with previous stage outputs
            for prev_stage, output in stage_outputs.items():
                placeholder = f"{{{prev_stage}}}"
                if placeholder in stage_prompt:
                    stage_prompt = stage_prompt.replace(placeholder, output)
                if placeholder in stage_system_prompt:
                    stage_system_prompt = stage_system_prompt.replace(placeholder, output)

            self.logger.info(f"Executing {stage_name} ({stage_type})")

            # Execute this stage
            result = await self.execute_task(
                task_description=stage_prompt,
                task_type=stage_type,
                system_prompt=stage_system_prompt,
                temperature=stage.get("temperature", 0.7),
                max_tokens=stage.get("max_tokens", 1000)
            )

            # Store result
            results.append({
                "stage": stage_name,
                "result": result
            })

            # Update overall success
            if not result.get("success", False):
                overall_success = False
                self.logger.warning(f"Stage {stage_name} failed")
                if not stage.get("continue_on_failure", False):
                    self.logger.error(f"Stopping multi-stage task due to failure at {stage_name}")
                    break

            # Store output for next stages
            if result.get("content"):
                stage_outputs[stage_name] = result["content"]

        return {
            "success": overall_success,
            "stages": results,
            "task_description": task_description
        }

    def _detect_task_type(self, task_description: str) -> str:
        """
        Detect the type of task from its description

        Args:
            task_description: Description of the task

        Returns:
            Detected task type
        """
        task_description = task_description.lower()

        # Count keyword matches for each task type
        matches = {}
        for task_type, keywords in self.task_keywords.items():
            matches[task_type] = sum(1 for keyword in keywords if keyword.lower() in task_description)

        # Find task type with most matches
        if any(matches.values()):
            best_match = max(matches.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                return best_match[0]

        # Default to decision_making if no clear match
        return "decision_making"

    def _build_task_context(self, task_type: str) -> str:
        """
        Build context information for a task based on history

        Args:
            task_type: Type of task

        Returns:
            Context information as a string
        """
        # Filter history for relevant tasks
        relevant_tasks = [
            task for task in self.task_history
            if task["task_type"] == task_type and task["success"]
        ][-3:]  # Get last 3 successful tasks of this type

        if not relevant_tasks:
            return ""

        # Build context string
        context = "Previous similar tasks:\n"
        for i, task in enumerate(relevant_tasks):
            context += f"{i+1}. {task['description']} (using {task['model_used']})\n"

        return context

    def _add_to_history(self, task_record: Dict[str, Any]):
        """
        Add a task record to history

        Args:
            task_record: Task record to add
        """
        self.task_history.append(task_record)

        # Trim history if needed
        if len(self.task_history) > self.max_history:
            self.task_history = self.task_history[-self.max_history:]

    def get_recommended_workflow(self, task_description: str) -> Dict[str, Any]:
        """
        Get a recommended workflow for a complex task

        Args:
            task_description: Description of the complex task

        Returns:
            Dictionary with recommended workflow stages
        """
        # Detect primary task type
        primary_type = self._detect_task_type(task_description)

        # Define workflow based on primary task type
        if "code" in primary_type:
            # Code-related workflow
            return {
                "name": "Code Development Workflow",
                "stages": [
                    {
                        "name": "Planning",
                        "task_type": "decision_making",
                        "prompt": f"Create a detailed plan for: {task_description}",
                        "system_prompt": "You are a senior software architect. Create a detailed plan with steps, considerations, and potential challenges."
                    },
                    {
                        "name": "Implementation",
                        "task_type": "code_generation",
                        "prompt": f"Implement the following plan: {{Planning}}",
                        "system_prompt": "You are an expert programmer. Write clean, efficient, and well-documented code."
                    },
                    {
                        "name": "Review",
                        "task_type": "code_review",
                        "prompt": f"Review this code for bugs, edge cases, and improvements: {{Implementation}}",
                        "system_prompt": "You are a code reviewer. Identify bugs, edge cases, and suggest improvements."
                    }
                ]
            }
        elif primary_type == "content_generation":
            # Content creation workflow
            return {
                "name": "Content Creation Workflow",
                "stages": [
                    {
                        "name": "Outline",
                        "task_type": "decision_making",
                        "prompt": f"Create a detailed outline for: {task_description}",
                        "system_prompt": "You are a content strategist. Create a comprehensive outline with key points and structure."
                    },
                    {
                        "name": "Draft",
                        "task_type": "content_generation",
                        "prompt": f"Write a complete draft based on this outline: {{Outline}}",
                        "system_prompt": "You are a professional writer. Create engaging, well-structured content."
                    },
                    {
                        "name": "Edit",
                        "task_type": "content_generation",
                        "prompt": f"Edit and improve this draft: {{Draft}}",
                        "system_prompt": "You are an editor. Improve clarity, flow, and impact while maintaining the original message."
                    }
                ]
            }
        else:
            # Generic research workflow
            return {
                "name": "Research and Analysis Workflow",
                "stages": [
                    {
                        "name": "Research",
                        "task_type": "research",
                        "prompt": f"Research the following topic: {task_description}",
                        "system_prompt": "You are a research analyst. Gather comprehensive information on the topic."
                    },
                    {
                        "name": "Analysis",
                        "task_type": "data_analysis",
                        "prompt": f"Analyze the following research: {{Research}}",
                        "system_prompt": "You are a data analyst. Identify patterns, insights, and implications."
                    },
                    {
                        "name": "Summary",
                        "task_type": "summarization",
                        "prompt": f"Summarize the key findings from this analysis: {{Analysis}}",
                        "system_prompt": "You are an executive assistant. Create a concise, actionable summary of the key points."
                    }
                ]
            }

    def suggest_skill_acquisition(self, failed_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest skill acquisition based on a failed task

        Args:
            failed_task: Information about the failed task

        Returns:
            Dictionary with skill acquisition suggestions
        """
        task_type = failed_task.get("task_type", "unknown")
        error = failed_task.get("error", "Unknown error")
        description = failed_task.get("description", "")

        # Generate skill acquisition suggestions based on task type and error
        if "code" in task_type:
            if "API" in error or "authentication" in error:
                return {
                    "skill_type": "API Integration",
                    "description": "Improve API authentication and error handling",
                    "requirements": ["API key validation", "Error handling", "Retry mechanisms"],
                    "resources": ["https://docs.python-requests.org/", "https://www.oauth.com/"]
                }
            else:
                return {
                    "skill_type": "Code Generation",
                    "description": "Enhance code generation capabilities",
                    "requirements": ["Error handling", "Testing", "Documentation"],
                    "resources": ["https://github.com/features/copilot", "https://docs.python.org/"]
                }
        elif "web" in description.lower() and "scraper" in description.lower():
            return {
                "skill_type": "Web Scraping",
                "description": "Add web scraping capabilities",
                "requirements": ["BeautifulSoup", "Selenium", "HTML parsing"],
                "resources": ["https://www.crummy.com/software/BeautifulSoup/", "https://selenium-python.readthedocs.io/"]
            }
        else:
            return {
                "skill_type": "General Task Handling",
                "description": "Improve task handling and error recovery",
                "requirements": ["Task validation", "Error handling", "Fallback mechanisms"],
                "resources": ["https://docs.python.org/3/tutorial/errors.html"]
            }
