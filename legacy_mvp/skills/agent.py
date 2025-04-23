"""
General Pulse Agent - a conversational agent for productivity and development tasks
"""

import asyncio
import re
import traceback
import sys
import time
from typing import Optional, Dict, Any, List
from utils import get_logger
import structlog
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from utils.memory_guard import memory_guard
from utils.agent_personality import AgentPersonality
from utils.task_orchestrator import TaskOrchestrator
from utils.workflow_executor import WorkflowExecutor
from utils.command_parser import CommandParser
from utils.timezone_utils import TimezoneConverter

class Agent:
    """
    General Pulse Agent - a natural language interface for productivity and development.
    Processes natural language commands and integrates with GitHub, Notion, and AI models.
    """

    def __init__(self, model_interface=None, intent_handler=None, task_manager=None, simulate_responses=False):
        """
        Initialize the agent with required components

        Args:
            model_interface: Optional ModelInterface instance for AI model calls
            intent_handler: Optional IntentHandler instance for intent processing
            task_manager: Optional TaskMemoryManager for task management
            simulate_responses: Whether to simulate AI responses (for testing)
        """
        # Import dependencies
        from skills.model_interface import ModelInterface
        from utils.intent_handler import IntentHandler
        from skills.task_memory_manager import TaskMemoryManager

        # Initialize components
        self.logger = structlog.get_logger("agent")
        self.model_interface = model_interface or ModelInterface(simulate_responses=simulate_responses)
        self.intent_handler = intent_handler or IntentHandler()
        self.task_manager = task_manager or TaskMemoryManager()

        # Initialize personality, task orchestrator, and workflow executor
        self.personality = AgentPersonality(name="Pulse")
        self.task_orchestrator = TaskOrchestrator(model_interface=self.model_interface)
        self.workflow_executor = WorkflowExecutor(task_orchestrator=self.task_orchestrator)

        # Initialize command parser and timezone converter
        self.command_parser = CommandParser()
        self.timezone_converter = TimezoneConverter()

        # Set up regular expression patterns for direct commands
        self.github_pattern = re.compile(r'^github\s+([^\s]+)\s+(.+)')
        self.notion_pattern = re.compile(r'^notion\s+(.+)')
        self.ai_pattern = re.compile(r'^(?:ask|query)\s+(\w+)\s+(.*)')
        self.workflow_pattern = re.compile(r'^workflow\s+(.+)')

        # Ensure we're in simulation mode if requested
        if simulate_responses and not self.model_interface.simulate_responses:
            self.model_interface.simulate_responses = True
            self.logger.info("Forced simulation mode enabled")

        # Track conversation context
        self.last_command = None
        self.last_response = None
        self.conversation_context = "tech"  # Default context
        self.current_workflow_task = None  # Current workflow task

        self.logger.info("General Pulse Agent initialized")

        # Track if we are exiting
        self.is_exiting = False

        # Initialize the prompt session for better input handling
        self.prompt_session = PromptSession()

    async def run_async(self):
        """
        Run the agent, processing user input until an exit command is received.
        """
        try:
            self.logger.info("Starting General Pulse agent")
            print("General Pulse agent is running. Type 'exit' to quit.")

            while True:
                try:
                    # Use prompt_toolkit for better input handling
                    with patch_stdout():
                        user_input = await self.prompt_session.prompt_async("\nGP> ")

                    # Check if user wants to exit
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        self.logger.info("User requested exit")
                        print("Exiting General Pulse...")
                        break

                    # Check if input is empty
                    if not user_input.strip():
                        continue

                    # Handle simple help command directly
                    if user_input.lower() == 'help':
                        print(self._get_help_text())
                        continue

                    # Process time/date queries directly
                    if self._is_time_query(user_input):
                        print(self._handle_time_query(user_input))
                        continue

                    # Process the user input through the appropriate handler
                    await self._process_input(user_input)

                except EOFError:
                    self.logger.warning("EOFError encountered - handling gracefully")
                    print("\nDetected Ctrl+D. Type 'exit' to quit or continue typing.")
                    continue
                except KeyboardInterrupt:
                    self.logger.info("KeyboardInterrupt received")
                    print("\nOperation cancelled. Type 'exit' to quit or continue with another command.")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing input: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    print(f"Error processing your request: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in agent run_async method: {str(e)}")
            self.logger.error(traceback.format_exc())
            print(f"Agent encountered an error: {str(e)}")

    def _is_time_query(self, user_input):
        """Check if the input is a time or date query"""
        time_patterns = [
            r'\btime\b',
            r'\bdate\b',
            r'what day is',
            r'what time',
            r'current time',
            r'today\'s date'
        ]
        for pattern in time_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        return False

    def _handle_time_query(self, query):
        """Handle a time or date query directly"""
        query = query.lower()

        # Check for timezone queries with various patterns
        timezone_patterns = [
            r"time(?:\s+in|\s+at)\s+([a-zA-Z\s]+)",
            r"what(?:'s| is) the time in ([a-zA-Z\s]+)",
            r"what time is it in ([a-zA-Z\s]+)"
        ]

        for pattern in timezone_patterns:
            timezone_match = re.search(pattern, query)
            if timezone_match:
                location = timezone_match.group(1).strip()
                self.logger.debug(f"Extracted location from time query: {location}")
                time_str, timezone_name, error = self.timezone_converter.get_time_in_timezone(location)

                if error:
                    return f"I couldn't find the time in {location}. {error}"

                return f"The current time in {location.title()} is {time_str} ({timezone_name})."

        # Handle date queries
        if "date" in query:
            date_str = self.timezone_converter.get_current_date()
            return f"Today's date is {date_str}."

        # Handle time queries
        elif "time" in query or "what time" in query:
            time_str = self.timezone_converter.get_current_time()
            return f"The current time is {time_str}."

        # Handle general time/date queries
        else:
            date_str = self.timezone_converter.get_current_date()
            time_str = self.timezone_converter.get_current_time()
            return f"Today is {date_str} and the current time is {time_str}."

    async def _execute_workflow(self, task_description):
        """
        Execute a workflow for a task

        Args:
            task_description: Description of the task

        Returns:
            Workflow execution results
        """
        try:
            with memory_guard():
                self.logger.info(f"Executing workflow for task: {task_description}")

                # Execute the workflow
                result = await self.workflow_executor.execute_workflow(task_description)

                if result.get("success", False):
                    return f"Workflow executed successfully:\n\n{result.get('formatted_results', '')}\n\nWorkflow complete!"
                else:
                    return f"Workflow execution encountered some issues:\n\n{result.get('formatted_results', '')}\n\nSome stages may not have completed successfully."

        except Exception as e:
            self.logger.error(f"Error executing workflow: {str(e)}")
            self.logger.error(traceback.format_exc())
            return f"Error executing workflow: {str(e)}"

    def _get_help_text(self):
        """Get the help text for the agent"""
        help_text = """
General Pulse Commands:

General:
• "help" - Show this help message
• "exit" or "quit" - Exit the agent

Time & Date:
• "What time is it?" - Get the current time
• "What's today's date?" - Get today's date
• "What time is it in Tokyo?" - Get time in a specific timezone

GitHub:
• "github username/repo info" - Get repository information
• "github username/repo issues" - List repository issues
• "github username/repo commit file_path" - Generate commit message

Notion:
• "notion create document Project Ideas" - Create a document in Notion
• "notion journal" - Create a journal entry in Notion

AI Models:
• "ask claude What is machine learning?" - Query Claude
• "ask grok Why is the sky blue?" - Query Grok
• "ask deepseek Explain quantum computing" - Query DeepSeek

Workflows:
• "workflow Create a personal portfolio website" - Get a multi-stage workflow
• "workflow Write a blog post about AI" - Get a content creation workflow
• "workflow Research quantum computing" - Get a research workflow

Content Creation:
• "Write a blog post about machine learning" - Generate content
• "Create code for a simple web scraper" - Generate code examples
"""
        # Format with personality
        return self.personality.format_response(help_text, context="tech", success=True)

    def _is_github_command(self, input_text):
        """Check if input is a GitHub command"""
        return self.github_pattern.match(input_text) is not None

    def _is_notion_command(self, input_text):
        """Check if input is a Notion command"""
        return self.notion_pattern.match(input_text) is not None

    def _is_ai_command(self, input_text):
        """Check if input is an AI model query command"""
        return self.ai_pattern.match(input_text) is not None

    def _is_workflow_command(self, input_text):
        """Check if input is a workflow command"""
        return self.workflow_pattern.match(input_text) is not None

    async def _handle_workflow_command(self, command):
        """
        Handle a workflow command

        Format: workflow [task description]
        """
        try:
            with memory_guard():
                match = self.workflow_pattern.match(command)
                if not match:
                    return "Invalid workflow command format. Use: workflow [task description]"

                task_description = match.group(1)

                # Store the current workflow task
                self.current_workflow_task = task_description

                # Get recommended workflow
                workflow = self.task_orchestrator.get_recommended_workflow(task_description)

                # Show workflow plan
                response = f"Recommended workflow for: {task_description}\n\n"
                response += f"Workflow: {workflow['name']}\n\n"

                for i, stage in enumerate(workflow['stages']):
                    response += f"Stage {i+1}: {stage['name']} ({stage['task_type']})\n"
                    response += f"- {stage['prompt']}\n"

                response += "\nWould you like me to execute this workflow? (yes/no)"

                # Format with personality
                return self.personality.format_response(response, context="tech", success=True)

        except Exception as e:
            self.logger.error(f"Error handling workflow command: {str(e)}")
            self.logger.error(traceback.format_exc())
            return f"Error processing workflow command: {str(e)}"

    async def _handle_github_command(self, command):
        """
        Handle a direct GitHub command

        Format: github username/repo [action] [args]
        """
        try:
            with memory_guard():
                match = self.github_pattern.match(command)
                if not match:
                    return "Invalid GitHub command format. Use: github username/repo action [args]"

                repo_ref = match.group(1)  # username/repo or full URL
                action_args = match.group(2)  # The rest of the command

                # Convert to repo URL if needed
                if not repo_ref.startswith("http"):
                    repo_url = f"https://github.com/{repo_ref}"
                else:
                    repo_url = repo_ref

                # Parse the action
                parts = action_args.split(maxsplit=1)
                action = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Import GitHub skills
                try:
                    from skills.github_skills import GitHubSkills
                    github = GitHubSkills()
                except ImportError:
                    return "GitHub skills module is not available."

                # Handle different actions
                if action in ["info", "information"]:
                    return await github.get_repository_info_async(repo_url)

                elif action in ["issues", "list"]:
                    return await github.list_repository_issues_async(repo_url)

                elif action == "commit":
                    if not args:
                        return "Please specify a file path for the commit message."
                    return await github.generate_commit_message_async(repo_url, args)

                else:
                    return f"Unknown GitHub action: {action}. Valid actions: info, issues, commit"

        except Exception as e:
            self.logger.error(f"Error handling GitHub command: {str(e)}")
            self.logger.error(traceback.format_exc())

            # Check if the error is already a structured error response
            if isinstance(e, dict) and "success" in e and not e["success"]:
                return e

            error_str = str(e).lower()

            # Provide more helpful error messages based on the error type
            if "404" in error_str or "not found" in error_str:
                return {
                    "success": False,
                    "error_type": "github_error",
                    "message": f"Repository {repo_url} not found",
                    "user_message": f"Repository {repo_url} not found. Please check that the repository exists and is accessible.\n\nExample: github octocat/Hello-World info"
                }
            elif "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
                return {
                    "success": False,
                    "error_type": "github_error",
                    "message": "GitHub authentication failed",
                    "user_message": "GitHub authentication failed. Please check your GITHUB_TOKEN in the .env file."
                }
            elif "403" in error_str or "forbidden" in error_str:
                return {
                    "success": False,
                    "error_type": "github_error",
                    "message": "GitHub permission denied",
                    "user_message": "Access to this GitHub repository is forbidden. You may not have permission to access it."
                }
            elif "rate limit" in error_str:
                return {
                    "success": False,
                    "error_type": "github_error",
                    "message": "GitHub API rate limit exceeded",
                    "user_message": "GitHub API rate limit exceeded. Please try again later."
                }
            elif "network" in error_str or "connection" in error_str:
                return {
                    "success": False,
                    "error_type": "network_error",
                    "message": "Network error connecting to GitHub",
                    "user_message": "Network error while connecting to GitHub. Please check your internet connection."
                }
            else:
                return {
                    "success": False,
                    "error_type": "github_error",
                    "message": f"Error processing GitHub command: {str(e)}",
                    "user_message": f"Error processing GitHub command: {str(e)}"
                }

    async def _handle_notion_command(self, command):
        """
        Handle a direct Notion command

        Format: notion [action] [args]
        """
        try:
            with memory_guard():
                match = self.notion_pattern.match(command)
                if not match:
                    return "Invalid Notion command format. Use: notion action [args]"

                full_command = match.group(1)

                # Parse the action
                parts = full_command.split(maxsplit=1)
                action = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Import Notion skills
                try:
                    from skills.notion_skills import NotionSkills
                    notion = NotionSkills()
                except ImportError:
                    return "Notion skills module is not available."

                # Handle different actions
                if action in ["list", "search"]:
                    return await notion.search_notion_pages_async(args)

                elif action in ["create", "new"]:
                    if not args:
                        return "Please specify a title for the new document."
                    # Use the correct method name
                    return await notion.create_document_async(args)

                elif action == "journal":
                    return await notion.create_journal_entry_async()

                else:
                    return f"Unknown Notion action: {action}. Valid actions: list, create, journal"

        except Exception as e:
            self.logger.error(f"Error handling Notion command: {str(e)}")
            self.logger.error(traceback.format_exc())

            # Check if the error is already a structured error response
            if isinstance(e, dict) and "success" in e and not e["success"]:
                return e

            error_str = str(e).lower()

            # Provide more helpful error messages based on the error type
            if "not found" in error_str or "does not exist" in error_str:
                return {
                    "success": False,
                    "error_type": "notion_error",
                    "message": "Notion resource not found",
                    "user_message": "The requested Notion resource was not found. Please check that it exists and you have access to it."
                }
            elif "unauthorized" in error_str or "authentication" in error_str or "token" in error_str:
                return {
                    "success": False,
                    "error_type": "notion_error",
                    "message": "Notion authentication failed",
                    "user_message": "Notion authentication failed. Please check your NOTION_TOKEN in the .env file."
                }
            elif "permission" in error_str or "access" in error_str or "forbidden" in error_str:
                return {
                    "success": False,
                    "error_type": "notion_error",
                    "message": "Notion permission denied",
                    "user_message": "You don't have permission to access this Notion resource."
                }
            elif "rate limit" in error_str:
                return {
                    "success": False,
                    "error_type": "notion_error",
                    "message": "Notion API rate limit exceeded",
                    "user_message": "Notion API rate limit exceeded. Please try again later."
                }
            elif "network" in error_str or "connection" in error_str:
                return {
                    "success": False,
                    "error_type": "network_error",
                    "message": "Network error connecting to Notion",
                    "user_message": "Network error while connecting to Notion. Please check your internet connection."
                }
            else:
                return {
                    "success": False,
                    "error_type": "notion_error",
                    "message": f"Error processing Notion command: {str(e)}",
                    "user_message": f"Error processing Notion command: {str(e)}"
                }

    async def _handle_ai_command(self, command):
        """
        Handle a direct AI model query command

        Format: ask|query model_name question
        """
        try:
            with memory_guard():
                match = self.ai_pattern.match(command)
                if not match:
                    return "Invalid AI command format. Use: ask|query model your_question"

                # Since the pattern is now ^(?:ask|query)\s+(\w+)\s+(.*)
                # The groups are: 1=model_name, 2=query
                model_name = match.group(1).lower()
                query = match.group(2)

                if not query:
                    return f"What would you like to ask {model_name.capitalize()}?"

                # Call the model - direct method call instead of using asyncio.to_thread
                self.logger.info(f"Querying {model_name} with: {query}")

                if self.model_interface.simulate_responses:
                    # For simulation mode, we can directly call the method
                    model_response = self.model_interface.call_model_api(model_name, query)
                    return model_response.get("content", f"No response from {model_name}")

                # For real API calls, we'll use the appropriate async methods
                try:
                    # Create a task in the current event loop - this avoids the thread issues
                    model_response = await self.model_interface.call_model_api_async(
                        model_name=model_name,
                        prompt=query
                    )

                    # Log response details
                    self.logger.debug(f"Response received from {model_name}: {type(model_response)}")

                    # Check if the response indicates an error
                    if isinstance(model_response, dict) and not model_response.get("success", True):
                        error_msg = model_response.get("content") or model_response.get("error") or "Unknown error"
                        return f"Error from {model_name}: {error_msg}"

                    # Handle different response formats
                    if isinstance(model_response, str):
                        # It's already a string response
                        return model_response
                    elif isinstance(model_response, dict):
                        # It's a dictionary response
                        if "content" in model_response:
                            return model_response["content"]
                        elif "error" in model_response:
                            return f"Error from {model_name}: {model_response['error']}"
                        else:
                            # Try to print the full response for debugging
                            print(f"Full response: {model_response}")
                            return f"Received response from {model_name} but couldn't extract content"
                    else:
                        # Unknown response format
                        return f"Received response from {model_name} but it has an unexpected format: {type(model_response)}"

                except RuntimeError:
                    # Fallback if we're not in an async context
                    model_response = self.model_interface.call_model_api(model_name, query)
                    if isinstance(model_response, dict) and "content" in model_response:
                        return model_response["content"]
                    return str(model_response)

        except Exception as e:
            self.logger.error(f"Error handling AI command: {str(e)}")
            self.logger.error(traceback.format_exc())

            # Check if the error is already a structured error response
            if isinstance(e, dict) and "success" in e and not e["success"]:
                return e

            error_str = str(e).lower()

            # Provide more helpful error messages based on the error type
            if "api key" in error_str or "authentication" in error_str or "token" in error_str:
                return {
                    "success": False,
                    "error_type": "model_error",
                    "message": "AI model authentication failed",
                    "user_message": "AI model authentication failed. Please check your OPENROUTER_API_KEY in the .env file."
                }
            elif "rate limit" in error_str:
                return {
                    "success": False,
                    "error_type": "model_error",
                    "message": "AI model API rate limit exceeded",
                    "user_message": "AI model API rate limit exceeded. Please try again later."
                }
            elif "context length" in error_str or "too long" in error_str:
                return {
                    "success": False,
                    "error_type": "model_error",
                    "message": "Input too long for model context window",
                    "user_message": "Your input is too long for the AI model to process. Please try a shorter input."
                }
            elif "content policy" in error_str or "moderation" in error_str:
                return {
                    "success": False,
                    "error_type": "model_error",
                    "message": "Content policy violation",
                    "user_message": "Your request was flagged by the AI model's content policy. Please modify your input."
                }
            elif "network" in error_str or "connection" in error_str:
                return {
                    "success": False,
                    "error_type": "network_error",
                    "message": "Network error connecting to AI model API",
                    "user_message": "Network error while connecting to the AI model service. Please check your internet connection."
                }
            else:
                return {
                    "success": False,
                    "error_type": "model_error",
                    "message": f"Error querying AI model: {str(e)}",
                    "user_message": f"Error querying AI model: {str(e)}"
                }

    async def _process_input(self, user_input):
        """
        Process user input through the appropriate handler

        Args:
            user_input (str): The user's input
        """
        try:
            # Skip empty input
            if not user_input.strip():
                return

            # Apply memory guard to prevent memory leaks
            with memory_guard():
                self.logger.info(f"Processing input: {user_input}")

                # Store the input for context
                self.last_command = user_input

                # 1. Parse the command using the command parser
                parsed_command = self.command_parser.parse_command(user_input)
                command_type = parsed_command.get("command")

                # Log parsed command
                self.logger.debug(f"Parsed command: {parsed_command}")

                # Special handling for "What time is it in [location]?" format
                if command_type == "time" and "in" in user_input.lower():
                    # Try to extract the location
                    location_match = re.search(r"(?:time|what time is it)\s+in\s+([a-zA-Z\s]+)\??$", user_input, re.IGNORECASE)
                    if location_match:
                        location = location_match.group(1).strip()
                        self.logger.debug(f"Extracted location: {location}")

                        # Use the timezone converter
                        time_str, timezone_name, error = self.timezone_converter.get_time_in_timezone(location)

                        if error:
                            result = f"I couldn't find the time in {location}. {error}"
                        else:
                            result = f"The current time in {location.title()} is {time_str} ({timezone_name})."

                        # Time queries don't need personality formatting
                        print(result)
                        self.last_response = result
                        self.personality.remember_interaction(user_input, result)
                        return

                # Handle different command types
                if command_type == "github_info":
                    repo = parsed_command.get("repo")
                    result = await self._handle_github_command(f"github {repo} info")
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="tech", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="tech", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif command_type == "github_issues":
                    repo = parsed_command.get("repo")
                    result = await self._handle_github_command(f"github {repo} issues")
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="tech", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="tech", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif command_type == "github_commit":
                    repo = parsed_command.get("repo")
                    file_path = parsed_command.get("file_path")
                    result = await self._handle_github_command(f"github {repo} commit {file_path}")
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="tech", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="tech", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif command_type == "notion_document":
                    title = parsed_command.get("title")
                    result = await self._handle_notion_command(f"notion create document {title}")
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="creative", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="creative", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif command_type == "notion_journal":
                    result = await self._handle_notion_command("notion journal")
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="creative", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="creative", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif command_type == "ask_model":
                    model = parsed_command.get("model")
                    query = parsed_command.get("query")
                    result = await self._handle_ai_command(f"ask {model} {query}")
                    # AI responses already have their own style, so don't apply personality
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return
                elif command_type == "workflow":
                    description = parsed_command.get("description")
                    result = await self._handle_workflow_command(f"workflow {description}")
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return
                elif command_type == "time":
                    result = self._handle_time_query(user_input)
                    # Time queries don't need personality formatting
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return
                elif command_type == "date":
                    result = self._handle_time_query(user_input)
                    # Date queries don't need personality formatting
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return
                elif command_type == "timezone":
                    location = parsed_command.get("location")
                    if location:
                        # Use the location from the parsed command
                        time_str, timezone_name, error = self.timezone_converter.get_time_in_timezone(location)

                        if error:
                            result = f"I couldn't find the time in {location}. {error}"
                        else:
                            result = f"The current time in {location.title()} is {time_str} ({timezone_name})."
                    else:
                        # Fall back to the regex approach
                        result = self._handle_time_query(user_input)

                    # Time queries don't need personality formatting
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return
                elif command_type == "help":
                    result = self._get_help_text()
                    # Help text doesn't need personality formatting
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return
                elif command_type == "exit":
                    print("Goodbye!")
                    sys.exit(0)

                # Fall back to the original command processing
                if self._is_github_command(user_input):
                    result = await self._handle_github_command(user_input)
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="tech", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="tech", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif self._is_notion_command(user_input):
                    result = await self._handle_notion_command(user_input)
                    # Apply personality to the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("formatted_response", result.get("info", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        formatted_result = self.personality.format_response(message, context="creative", success=success)
                    else:
                        # Handle the old string response format
                        formatted_result = self.personality.format_response(result, context="creative", success="error" not in result.lower())
                    print(formatted_result)
                    self.last_response = formatted_result
                    self.personality.remember_interaction(user_input, formatted_result)
                    return
                elif self._is_ai_command(user_input):
                    result = await self._handle_ai_command(user_input)
                    # Handle the response
                    if isinstance(result, dict):
                        # Handle the new structured response format
                        success = result.get("success", False)
                        if success:
                            message = result.get("content", result.get("formatted_response", "Operation completed successfully"))
                        else:
                            message = result.get("user_message", result.get("message", "Operation failed"))
                        # AI responses already have their own style, so don't apply personality
                        print(message)
                        self.last_response = message
                    else:
                        # Handle the old string response format
                        print(result)
                        self.last_response = result
                    self.personality.remember_interaction(user_input, self.last_response)
                    return
                elif self._is_workflow_command(user_input):
                    result = await self._handle_workflow_command(user_input)
                    print(result)
                    self.last_response = result
                    self.personality.remember_interaction(user_input, result)
                    return

                # Check if this is a response to a workflow prompt
                if self.last_response and "Would you like me to execute this workflow?" in self.last_response:
                    if user_input.lower() in ["yes", "y", "yeah", "sure", "ok", "okay"]:
                        # User wants to execute the workflow
                        if self.current_workflow_task:
                            result = await self._execute_workflow(self.current_workflow_task)
                            formatted_result = self.personality.format_response(result, context="tech", success=True)
                            print(formatted_result)
                            self.last_response = formatted_result
                            self.personality.remember_interaction(user_input, formatted_result)
                            return

                # 2. Intent classification and processing
                try:
                    # Process input with the intent handler
                    result = await self.intent_handler.process_with_ai(user_input)

                    if result == "exit":
                        self.is_exiting = True
                        print("Exiting General Pulse...")
                        return

                    # Try to detect the context from the input
                    if any(word in user_input.lower() for word in ["code", "program", "function", "class", "bug"]):
                        self.conversation_context = "tech"
                    elif any(word in user_input.lower() for word in ["write", "draft", "blog", "article", "post"]):
                        self.conversation_context = "casual"

                    # Apply personality to the response
                    formatted_result = self.personality.format_response(
                        result,
                        context=self.conversation_context,
                        success="error" not in result.lower() and "fail" not in result.lower()
                    )

                    # Print the response
                    print(formatted_result)
                    self.last_response = formatted_result

                    # Store the task in memory if it's a meaningful interaction
                    if len(user_input) > 5 and len(result) > 5:
                        self.task_manager.add_task(user_input, result)

                    # Remember the interaction for future context
                    self.personality.remember_interaction(user_input, formatted_result)

                except Exception as e:
                    # If intent handler fails, fall back to direct AI query as last resort
                    self.logger.error(f"Intent handler error: {str(e)}")
                    self.logger.debug(traceback.format_exc())

                    # If the error is because API keys or configuration issues, show a helpful message
                    error_str = str(e).lower()
                    error_message = ""

                    if "api key" in error_str or "openrouter" in error_str or "token" in error_str:
                        error_message = "There seems to be an issue with API keys or service configuration. Please check your OPENROUTER_API_KEY in the .env file."
                    elif "model" in error_str and ("unavailable" in error_str or "error" in error_str):
                        error_message = "The requested model is unavailable or experiencing issues. Trying an alternative model..."

                        # Try with the task orchestrator for better fallback handling
                        try:
                            # Use task orchestrator with fallback models
                            task_result = await self.task_orchestrator.execute_task(
                                task_description=user_input,
                                task_type="content_generation"  # Default to content generation for general queries
                            )

                            if task_result and task_result.get("success", False):
                                result = task_result.get("content", "")
                                model_used = task_result.get("model_used", "fallback model")

                                # Format with personality
                                formatted_result = self.personality.format_response(
                                    f"Using {model_used} instead: {result}",
                                    context=self.conversation_context,
                                    success=True
                                )
                                print(formatted_result)
                                self.last_response = formatted_result
                                self.personality.remember_interaction(user_input, formatted_result)
                                return
                            else:
                                error_message = "All models failed to respond. Please check your configuration and try again."
                        except Exception as fallback_err:
                            self.logger.error(f"Fallback model error: {str(fallback_err)}")
                            error_message = f"Fallback models also failed: {str(fallback_err)}. Please check your API keys and network connection."
                    else:
                        # Check if this is a task that could benefit from skill acquisition
                        failed_task = {
                            "task_type": "unknown",
                            "error": str(e),
                            "description": user_input
                        }

                        # Get skill acquisition suggestion
                        skill_suggestion = self.task_orchestrator.suggest_skill_acquisition(failed_task)

                        error_message = f"Error processing your request: {str(e)}\n\n"
                        error_message += "I need to improve my skills to handle this task.\n"
                        error_message += f"Suggested skill acquisition: {skill_suggestion['skill_type']}\n"
                        error_message += f"Description: {skill_suggestion['description']}\n"
                        error_message += "Requirements: " + ", ".join(skill_suggestion['requirements'])

                    # Format the error message with personality
                    formatted_error = self.personality.format_response(error_message, context="tech", success=False)
                    print(formatted_error)
                    self.last_response = formatted_error
                    self.personality.remember_interaction(user_input, formatted_error)

        except Exception as e:
            self.logger.error(f"Unhandled error in _process_input: {str(e)}")
            self.logger.error(traceback.format_exc())
            print(f"An unexpected error occurred: {str(e)}")

    def run(self):
        """Run the agent synchronously (wrapper for the async version)"""
        try:
            import asyncio

            # Handle Windows-specific event loop policy
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            # Run the async version
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("\nExiting General Pulse...")
        except Exception as e:
            self.logger.error(f"Error running agent: {str(e)}")
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    # Create and run the agent when this file is executed directly
    agent = Agent()
    agent.run()