"""
Pulse Agent - Main agent class for General Pulse
Integrates all components and manages the overall system
"""

import asyncio
import json
import os  # Used in _launch_cli_ui method
import traceback
import psutil
from typing import Dict, Any, Optional
import structlog
from datetime import datetime

# Import spell correction utility
from utils.spell_correction import correct_typos

# Import components
from utils.context_manager import PulseContext
from utils.memory_manager import PulseMemory
from utils.personality_engine import PulsePersonality
from utils.optimization import memory_guard, get_system_status
from skills.model_orchestrator import ModelOrchestrator
from utils.natural_intent_handler import NaturalIntentHandler
from skills.optimized_model_interface import OptimizedModelInterface
from utils.proactive_monitor import ProactiveMonitor

# Configure logger
logger = structlog.get_logger("pulse_agent")

class PulseAgent:
    """
    Main agent class for General Pulse
    Integrates all components and manages the overall system
    """

    def __init__(self,
                 user_id: str = "uminda",
                 memory_path: str = "pulse_memory.db",
                 simulate_responses: bool = False):
        """
        Initialize the Pulse Agent

        Args:
            user_id: User identifier
            memory_path: Path to the memory database
            simulate_responses: Whether to simulate AI responses (for testing)
        """
        self.user_id = user_id
        self.logger = logger
        self.simulate_responses = simulate_responses
        self.version = "1.4.1"  # Current version of General Pulse

        # Initialize components
        self.logger.info("Initializing Pulse Agent components")

        # Initialize memory manager
        try:
            self.memory = PulseMemory(memory_path)
            self.logger.info("Memory manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize memory manager: {str(e)}")
            self.memory = None

        # Initialize context manager
        try:
            self.context = PulseContext(max_length=20, user_id=user_id)
            self.logger.info("Context manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize context manager: {str(e)}")
            self.context = None

        # Initialize personality engine
        try:
            self.personality = PulsePersonality(self.memory, self.context)
            self.logger.info("Personality engine initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize personality engine: {str(e)}")
            self.personality = None

        # Initialize model orchestrator
        try:
            self.model_orchestrator = ModelOrchestrator(simulate_responses=simulate_responses)
            self.logger.info("Model orchestrator initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize model orchestrator: {str(e)}")
            self.model_orchestrator = None

        # Connect components
        self._connect_components()

        # Initialize enhanced natural intent handler
        try:
            self.intent_handler = NaturalIntentHandler()
            self.logger.info("Natural intent handler initialized with hybrid approach")
        except Exception as e:
            self.logger.error(f"Failed to initialize natural intent handler: {str(e)}")
            self.intent_handler = None

        # Initialize optimized model interface
        try:
            self.model_interface = OptimizedModelInterface()
            self.logger.info("Optimized model interface initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize optimized model interface: {str(e)}")
            self.model_interface = None

        # Track conversation state
        self.conversation_state = {
            "last_response": None,
            "last_input": None,
            "session_start": datetime.now().isoformat(),
            "interaction_count": 0,
            "proactive_alerts": []
        }

        # Initialize proactive monitor
        try:
            self.proactive_monitor = ProactiveMonitor(callback=self._handle_proactive_alert)
            self.logger.info("Proactive monitor initialized")
            # Start the proactive monitor
            asyncio.create_task(self.proactive_monitor.start())
        except Exception as e:
            self.logger.error(f"Failed to initialize proactive monitor: {str(e)}")
            self.proactive_monitor = None

        self.logger.info("Pulse Agent initialization complete")

    @memory_guard
    async def process_input(self, user_input: str) -> str:
        """
        Process user input and generate a response

        Args:
            user_input: User's input text

        Returns:
            Agent's response
        """
        # Update conversation state
        self.conversation_state["last_input"] = user_input
        self.conversation_state["interaction_count"] += 1

        # Check for typos and correct if needed
        corrected_input, was_corrected = correct_typos(user_input)
        if was_corrected:
            self.logger.info(
                "Corrected typo in user input",
                original=user_input,
                corrected=corrected_input
            )
            # Use the corrected input for processing
            user_input = corrected_input

        # Log the input
        self.logger.info(
            "Processing user input",
            input_preview=user_input[:50] + "..." if len(user_input) > 50 else user_input,
            interaction_count=self.conversation_state["interaction_count"],
            was_corrected=was_corrected
        )

        try:
            # Check for system commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                return self._format_response("Goodbye! Have a great day!")

            if user_input.lower() in ["help", "commands", "?"]:
                return self._format_response(self._get_help_text())

            if user_input.lower() in ["status", "system", "info"]:
                return self._format_response(await self._get_system_status())

            # Check for simple greetings and handle them directly with Mistral-Small
            # This ensures consistent personality and better handling of greetings
            if user_input.lower().strip() in ["hi", "hello", "hey", "what's up", "how are you", "yo", "sup"]:
                self.logger.info("Detected simple greeting, routing directly to Mistral-Small")
                return await self._process_with_model(user_input)

            # Check for task-related queries and handle them with Mistral-Small
            # This ensures better handling of task-related queries
            if any(word in user_input.lower() for word in ["task", "todo", "to-do", "to do", "notion", "github"]):
                self.logger.info("Detected task-related query, routing directly to Mistral-Small")
                return await self._process_with_model(user_input)

            # Check for intent using intent handler
            if self.intent_handler:
                intent_result = await self.intent_handler.parse_command(user_input)
                if intent_result and intent_result.get("command_type"):
                    return await self._handle_intent(intent_result, user_input)

            # If no specific intent, process with model orchestrator
            return await self._process_with_model(user_input)

        except Exception as e:
            # Log the error
            self.logger.error(
                "Error processing input",
                error=str(e),
                traceback=traceback.format_exc()
            )

            # Return error message
            error_message = f"Sorry, I encountered an error: {str(e)}"
            return self._format_response(error_message, success=False)

    async def _handle_intent(self, intent_result: Dict[str, Any], user_input: str) -> str:
        """
        Handle a recognized intent

        Args:
            intent_result: Intent parsing result
            user_input: Original user input

        Returns:
            Agent's response
        """
        command_type = intent_result.get("command_type")
        self.logger.info(f"Handling intent: {command_type}")

        # Handle different command types
        if command_type == "time":
            # Handle time queries
            location = intent_result.get("location", "local")
            return self._format_response(self._get_time(location))

        elif command_type == "reminder":
            # Handle reminders
            reminder_text = intent_result.get("reminder_text")
            time_str = intent_result.get("time")
            return self._format_response(self._set_reminder(reminder_text, time_str))

        elif command_type == "goal":
            # Handle goals
            action = intent_result.get("action", "list")
            goal_text = intent_result.get("goal_text")
            priority = intent_result.get("priority", 1)
            return self._format_response(self._handle_goal(action, goal_text, priority))

        elif command_type == "model":
            # Handle model-specific queries
            model_name = intent_result.get("model_name", "gemini")
            query = intent_result.get("query", user_input)
            return await self._query_specific_model(model_name, query)

        elif command_type == "memory":
            # Handle memory queries
            action = intent_result.get("action", "search")
            query = intent_result.get("query", "")
            return self._format_response(self._handle_memory(action, query))

        elif command_type == "personality":
            # Handle personality adjustments
            trait = intent_result.get("trait")
            value = intent_result.get("value", 0.5)
            return self._format_response(self._adjust_personality(trait, value))

        elif command_type == "cli_ui":
            # Check if there's a specific action
            action = intent_result.get("action")
            if action == "test_all":
                # Launch the CLI UI with test_all command
                self.logger.info("Launching CLI UI for test all command")
                try:
                    # Import the CLI UI
                    from utils.cli_ui import PulseCLIUI

                    # Create a CLI UI instance with this agent
                    cli_ui = PulseCLIUI(agent=self)

                    # Run the test_all_models method
                    asyncio.create_task(cli_ui.test_all_models())

                    return self._format_response("Testing all models... Please wait for the results.", success=True)
                except Exception as e:
                    self.logger.error(f"Error launching CLI UI for test all: {str(e)}")
                    return self._format_response(f"Error launching CLI UI for test all: {str(e)}", success=False)
            elif action == "test_gemini":
                # Launch the CLI UI with test_gemini command
                self.logger.info("Launching CLI UI for test gemini command")
                try:
                    # Import the CLI UI
                    from utils.cli_ui import PulseCLIUI

                    # Create a CLI UI instance with this agent
                    cli_ui = PulseCLIUI(agent=self)

                    # Run the test_model method for gemini
                    asyncio.create_task(cli_ui.test_model("gemini"))

                    return self._format_response("Testing Gemini model... Please wait for the results.", success=True)
                except Exception as e:
                    self.logger.error(f"Error launching CLI UI for test gemini: {str(e)}")
                    return self._format_response(f"Error launching CLI UI for test gemini: {str(e)}", success=False)
            else:
                # Launch the CLI UI
                return self._format_response(self._launch_cli_ui())

        elif command_type == "ollama":
            # Handle Ollama commands
            action = intent_result.get("action", "status")
            model = intent_result.get("model")
            return await self._handle_ollama_command(action, model)

        elif command_type == "test_intent":
            # Handle test intent commands
            query = intent_result.get("query")
            intent = intent_result.get("intent")
            return await self._handle_test_intent_command(query, intent)

        # If no specific handler, process with model
        return await self._process_with_model(user_input)

    async def _process_with_model(self, user_input: str) -> str:
        """
        Process input with the model orchestrator

        Args:
            user_input: User's input text

        Returns:
            Model's response
        """
        # Update personality mood based on input
        if self.personality:
            self.personality.update_mood(user_input)

        # Get context for the model
        context_data = {}
        if self.context:
            context_data = self.context.get_context()

        # Add user data from memory
        if self.memory:
            context_data["user_data"] = {
                "projects": self.memory.get_user_data("projects"),
                "interests": self.memory.get_user_data("interests"),
                "goals": self.memory.get_active_goals()
            }

        # Get system prompt from personality (used in context_data)
        if self.personality:
            context_data["system_prompt"] = self.personality.get_system_prompt()

        # Call model orchestrator
        if self.model_orchestrator:
            response = await self.model_orchestrator.handle_query(
                input_text=user_input,
                context=context_data
            )

            # Check if response is successful
            if response and response.get("success", False):
                content = response.get("content", "")

                # Update context with the interaction
                if self.context:
                    self.context.update(
                        user_input=user_input,
                        response=content,
                        metadata={
                            "model": response.get("model", "unknown"),
                            "model_type": response.get("model_type", "unknown")
                        }
                    )

                # Remember the interaction
                if self.personality:
                    self.personality.remember_interaction(user_input, content)

                # Format the response with the model ID
                model_id = response.get("model_type", "gemini")
                return self._format_response(content, model_id=model_id)
            else:
                # Handle error response
                error_message = response.get("content", "Sorry, I couldn't process that request.")
                return self._format_response(error_message, success=False)

        # Fallback if model orchestrator is not available
        return self._format_response(
            "I'm having trouble connecting to my AI models. Please try again later.",
            success=False
        )

    async def _query_specific_model(self, model_name: str, query: str) -> str:
        """
        Query a specific model

        Args:
            model_name: Name of the model to query
            query: Query text

        Returns:
            Model's response
        """
        self.logger.info(f"Querying specific model: {model_name}")

        # Handle special case for 'all' or 'test all'
        if model_name.lower() == "all" or model_name.lower() == "test all":
            # Launch the CLI UI and run the test_all_models method
            try:
                # Import the CLI UI
                from utils.cli_ui import PulseCLIUI

                # Create a CLI UI instance with this agent
                cli_ui = PulseCLIUI(agent=self)

                # Run the test_all_models method
                self.logger.info("Running test_all_models from CLI UI")
                await cli_ui.test_all_models()

                return "Testing all models completed. See above for results."
            except Exception as e:
                self.logger.error(f"Error testing all models: {str(e)}")
                return f"Error testing all models: {str(e)}"

        # Map model names to types and OpenRouter categories
        model_type_map = {
            "gemini": "gemini",
            "claude": "openrouter",
            "deepseek": "openrouter",
            "grok": "openrouter",
            "llama": "openrouter",
            "mistral": "openrouter",
            "code": "openrouter",
            "debug": "openrouter",
            "algorithm": "openrouter",
            "docs": "openrouter",
            "explain": "openrouter",
            "summarize": "openrouter",
            "troubleshoot": "openrouter",
            "solve": "openrouter",
            "trends": "openrouter",
            "research": "openrouter",
            "content": "openrouter",
            "creative": "openrouter",
            "write": "openrouter",
            "technical": "openrouter",
            "math": "openrouter",
            "brainstorm": "openrouter",
            "ideas": "openrouter",
            "ethics": "openrouter"
        }

        # Get context for the model
        context_data = {}
        if self.context:
            context_data = self.context.get_context()

        # Add user data from memory
        if self.memory:
            context_data["user_data"] = {
                "projects": self.memory.get_user_data("projects"),
                "interests": self.memory.get_user_data("interests"),
                "goals": self.memory.get_active_goals()
            }

        # Call model orchestrator with specific model
        if self.model_orchestrator:
            try:
                # For OpenRouter specialized models, use the query_type parameter
                if model_name.lower() in model_type_map and model_type_map[model_name.lower()] == "openrouter":
                    self.logger.info(f"Using OpenRouter with query_type={model_name.lower()} for: {query[:50]}...")

                    # Use the specialized model query method
                    # For maverick and molmo, use their specific model IDs
                    if model_name.lower() == "maverick":
                        response = await self.model_orchestrator.query_specialized_model(
                            query_type="content",
                            input_text=query,
                            context=context_data
                        )
                    elif model_name.lower() == "molmo":
                        response = await self.model_orchestrator.query_specialized_model(
                            query_type="ethics",
                            input_text=query,
                            context=context_data
                        )
                    else:
                        response = await self.model_orchestrator.query_specialized_model(
                            query_type=model_name.lower(),
                            input_text=query,
                            context=context_data
                        )
                else:
                    # Use the general query method
                    self.logger.info(f"Using general query method for model {model_name}: {query[:50]}...")
                    response = await self.model_orchestrator.handle_query(
                        input_text=query,
                        context=context_data,
                        model_preference=model_name.lower()
                    )

                # Check if response is successful
                if response and response.get("success", False):
                    content = response.get("content", "")
                    model_used = response.get("model", "unknown")

                    # Update context with the interaction
                    if self.context:
                        self.context.update(
                            user_input=query,
                            response=content,
                            metadata={
                                "model": model_used,
                                "model_type": response.get("model_type", "unknown"),
                                "requested_model": model_name
                            }
                        )

                    # Format the response with model information
                    formatted_content = f"[{model_used}] {content}"
                    model_id = response.get("model_type", model_name.lower())
                    return self._format_response(formatted_content, model_id=model_id)
                else:
                    # Handle error response
                    error_message = response.get("content", f"Sorry, I couldn't query the {model_name} model.")
                    return self._format_response(error_message, success=False)
            except Exception as e:
                self.logger.error(f"Error querying model {model_name}: {str(e)}")
                return self._format_response(
                    f"I encountered an error while trying to use the {model_name} model: {str(e)}",
                    success=False
                )

        # Fallback if model orchestrator is not available
        return self._format_response(
            f"I'm having trouble connecting to the {model_name} model. Please try again later.",
            success=False
        )

    def _get_time(self, location: str = "local") -> str:
        """
        Get the current time for a location

        Args:
            location: Location name

        Returns:
            Formatted time string
        """
        try:
            from datetime import datetime
            import pytz

            # Map location names to timezone strings
            timezone_map = {
                "local": None,  # Local time
                "new york": "America/New_York",
                "london": "Europe/London",
                "tokyo": "Asia/Tokyo",
                "sydney": "Australia/Sydney",
                "paris": "Europe/Paris",
                "berlin": "Europe/Berlin",
                "beijing": "Asia/Shanghai",
                "dubai": "Asia/Dubai",
                "los angeles": "America/Los_Angeles",
                "chicago": "America/Chicago",
                "toronto": "America/Toronto",
                "sao paulo": "America/Sao_Paulo",
                "moscow": "Europe/Moscow",
                "johannesburg": "Africa/Johannesburg",
                "singapore": "Asia/Singapore",
                "sri lanka": "Asia/Colombo",
                "colombo": "Asia/Colombo"
            }

            # Get the timezone
            tz_str = timezone_map.get(location.lower())

            if tz_str:
                # Get time in specified timezone
                tz = pytz.timezone(tz_str)
                current_time = datetime.now(tz)
                time_str = current_time.strftime("%I:%M %p")
                date_str = current_time.strftime("%A, %B %d, %Y")
                return f"The current time in {location.title()} is {time_str} on {date_str}."
            else:
                # Get local time
                current_time = datetime.now()
                time_str = current_time.strftime("%I:%M %p")
                date_str = current_time.strftime("%A, %B %d, %Y")
                return f"The current local time is {time_str} on {date_str}."

        except Exception as e:
            self.logger.error(f"Error getting time: {str(e)}")
            return f"Sorry, I couldn't get the time for {location}. Error: {str(e)}"

    def _set_reminder(self, reminder_text: str, time_str: Optional[str] = None) -> str:
        """
        Set a reminder

        Args:
            reminder_text: Reminder text
            time_str: Time string

        Returns:
            Confirmation message
        """
        # TODO: Implement reminder functionality
        if not reminder_text:
            return "Please specify what you want to be reminded about."

        if time_str:
            return f"I've set a reminder for '{reminder_text}' at {time_str}."
        else:
            return f"I've noted down '{reminder_text}' for you."

    def _handle_goal(self, action: str, goal_text: Optional[str] = None, priority: int = 1) -> str:
        """
        Handle goal-related actions

        Args:
            action: Goal action (add, list, complete, delete)
            goal_text: Goal text
            priority: Goal priority

        Returns:
            Response message
        """
        if not self.memory:
            return "Sorry, I can't manage goals right now because the memory system is unavailable."

        if action == "add" or action == "create":
            if not goal_text:
                return "Please specify a goal to add."

            success = self.memory.save_goal(goal_text, priority, "active")
            if success:
                return f"Goal added: '{goal_text}' with priority {priority}."
            else:
                return f"Failed to add goal: '{goal_text}'."

        elif action == "list":
            goals = self.memory.get_active_goals()
            if not goals:
                return "You don't have any active goals."

            goal_list = "\n".join([f"{i+1}. {g['goal']} (Priority: {g['priority']})" for i, g in enumerate(goals)])
            return f"Your active goals:\n{goal_list}"

        elif action == "complete":
            if not goal_text:
                return "Please specify which goal you completed."

            # Find the goal
            goals = self.memory.get_all_goals()
            matching_goals = [g for g in goals if goal_text.lower() in g["goal"].lower()]

            if not matching_goals:
                return f"I couldn't find a goal matching '{goal_text}'."

            # Update the first matching goal
            goal_id = matching_goals[0]["id"]
            success = self.memory.update_goal_status(goal_id, "completed")

            if success:
                return f"Goal marked as completed: '{matching_goals[0]['goal']}'."
            else:
                return f"Failed to update goal: '{matching_goals[0]['goal']}'."

        elif action == "delete":
            if not goal_text:
                return "Please specify which goal you want to delete."

            # Find the goal
            goals = self.memory.get_all_goals()
            matching_goals = [g for g in goals if goal_text.lower() in g["goal"].lower()]

            if not matching_goals:
                return f"I couldn't find a goal matching '{goal_text}'."

            # Update the first matching goal
            goal_id = matching_goals[0]["id"]
            success = self.memory.update_goal_status(goal_id, "deleted")

            if success:
                return f"Goal deleted: '{matching_goals[0]['goal']}'."
            else:
                return f"Failed to delete goal: '{matching_goals[0]['goal']}'."

        else:
            return f"Unknown goal action: '{action}'. Available actions: add, list, complete, delete."

    def _handle_memory(self, action: str, query: str) -> str:
        """
        Handle memory-related actions

        Args:
            action: Memory action (search, save, recall)
            query: Query text

        Returns:
            Response message
        """
        if not self.memory:
            return "Sorry, I can't access memory right now because the memory system is unavailable."

        if action == "search":
            if not query:
                # If no query provided, show recent memories
                recent_memories = self.memory.get_memories_by_recency(10)
                if not recent_memories:
                    return "You don't have any memories stored yet."

                # Get recent interactions
                recent_interactions = self.memory.get_recent_interactions(5)

                # Format the output
                formatted_results = []

                if recent_memories:
                    memory_str = "\n".join([f"- {r['category']}: {r['data']}" for r in recent_memories])
                    formatted_results.append(f"Recent memories:\n{memory_str}")

                if recent_interactions:
                    interactions_str = "\n".join([f"- You: {r['user_input'][:50]}...\n  Me: {r['response'][:50]}..." for r in recent_interactions])
                    formatted_results.append(f"Recent conversations:\n{interactions_str}")

                return "\n\n".join(formatted_results)

            # Search with the provided query
            results = self.memory.search_memory(query)

            # Format results
            formatted_results = []

            if results.get("identity"):
                identity_str = "\n".join([f"- {r['key']}: {r['value']}" for r in results["identity"][:5]])
                formatted_results.append(f"Identity:\n{identity_str}")

            if results["user_data"]:
                user_data_str = "\n".join([f"- {r['category']}: {r['data']}" for r in results["user_data"][:5]])
                formatted_results.append(f"User data:\n{user_data_str}")

            if results["goals"]:
                goals_str = "\n".join([f"- {r['goal']} (Status: {r['status']})" for r in results["goals"][:5]])
                formatted_results.append(f"Goals:\n{goals_str}")

            if results["interactions"]:
                interactions_str = "\n".join([f"- You: {r['user_input'][:50]}...\n  Me: {r['response'][:50]}..." for r in results["interactions"][:3]])
                formatted_results.append(f"Conversations:\n{interactions_str}")

            if formatted_results:
                return f"Memory search results for '{query}':\n\n" + "\n\n".join(formatted_results)
            else:
                return f"No memory entries found for '{query}'."

        elif action == "save":
            if not query:
                return "Please specify what you want to save to memory."

            # Use the new direct memory saving method
            success = self.memory.save_direct_memory(query)

            if success:
                # Check if the memory contains a category
                if ":" in query:
                    parts = query.split(":", 1)
                    category = parts[0].strip()
                    data = parts[1].strip()
                    return f"Saved to memory: {category} - {data}"
                else:
                    return f"Saved to memory: {query}"
            else:
                return f"Failed to save to memory: {query}"

        elif action == "recall":
            if not query:
                return "Please specify what you want to recall from memory."

            # Check if it's an identity key
            identity_value = self.memory.recall(query)
            if identity_value:
                return f"{query}: {identity_value}"

            # Otherwise, treat as a category
            data_items = self.memory.get_user_data(query)

            if data_items:
                data_str = "\n".join([f"- {item}" for item in data_items])
                return f"{query}:\n{data_str}"
            else:
                return f"No memory entries found for '{query}'."

        else:
            return f"Unknown memory action: '{action}'. Available actions: search, save, recall."

    def _adjust_personality(self, trait: Optional[str] = None, value: float = 0.5) -> str:
        """
        Adjust personality traits

        Args:
            trait: Personality trait to adjust
            value: New trait value (0.0 to 1.0)

        Returns:
            Response message
        """
        if not self.personality:
            return "Sorry, I can't adjust my personality right now because the personality system is unavailable."

        if not trait:
            # Return current traits
            traits = self.personality.get_traits()
            mood_info = self.personality.get_current_mood()

            # Format traits with emojis
            trait_emojis = {
                "informative": "📚",
                "courageous": "🦁",
                "positive": "😊",
                "casual": "👋",
                "strict": "📏",
                "personal": "👤",
                "honest": "💯",
                "humor": "😂",
                "anime_references": "🎌"
            }

            traits_str = "\n".join([f"- {trait_emojis.get(t, '✨')} {t.title()}: {v:.1f}" for t, v in traits.items()])

            # Add mood information
            mood_str = f"Current Mood: {mood_info['mood'].title()} (Energy: {mood_info['energy_level']:.1f})"

            return f"# My Personality Profile\n\n{mood_str}\n\n## Traits\n{traits_str}\n\nYou can adjust any trait with 'adjust [trait] to [value]' (values from 0.0 to 1.0)"

        # Check if trait exists
        traits = self.personality.get_traits()
        if trait.lower() not in traits:
            valid_traits = ", ".join(traits.keys())
            return f"Unknown personality trait: '{trait}'. Valid traits: {valid_traits}"

        # Adjust trait
        self.personality.adjust_traits(trait.lower(), value)

        # Get the emoji for the trait
        trait_emojis = {
            "informative": "📚",
            "courageous": "🦁",
            "positive": "😊",
            "casual": "👋",
            "strict": "📏",
            "personal": "👤",
            "honest": "💯",
            "humor": "😂",
            "anime_references": "🎌"
        }
        emoji = trait_emojis.get(trait.lower(), "✨")

        return f"Adjusted personality trait: {emoji} {trait.title()} = {value:.1f}\n\nYou'll notice changes in how I respond based on this adjustment."

    def _get_help_text(self) -> str:
        """
        Get help text

        Returns:
            Help text
        """
        # Import the crew manifest to show AI crew information
        from configs.models import CREW_MANIFEST, MODEL_ROLES

        # Generate AI crew information
        ai_crew_info = ""

        # Add leader information
        leader_key = CREW_MANIFEST.get("leader", "gemini")
        if leader_key in MODEL_ROLES:
            leader_info = MODEL_ROLES[leader_key]
            ai_crew_info += f"        - 👑 **{leader_info['name']}** - {leader_info['role']} - {leader_info['description']}\n"

        # Add crew members information
        for member_key in CREW_MANIFEST.get("members", []):
            if member_key in MODEL_ROLES:
                member_info = MODEL_ROLES[member_key]
                # Skip if it's the leader (already added)
                if member_key == leader_key:
                    continue
                # Add emoji based on role
                emoji = "🧠"
                if "code" in member_key or "Code" in member_info['role']:
                    emoji = "💻"
                elif "troubleshoot" in member_key or "Troubleshooting" in member_info['role']:
                    emoji = "🔧"
                elif "doc" in member_key or "Documentation" in member_info['role']:
                    emoji = "📚"
                elif "trend" in member_key or "Trend" in member_info['role']:
                    emoji = "📈"
                elif "content" in member_key or "Content" in member_info['role']:
                    emoji = "✍️"
                elif "technical" in member_key or "Technical" in member_info['role']:
                    emoji = "🔬"
                elif "brainstorm" in member_key or "Brainstorming" in member_info['role']:
                    emoji = "💡"
                elif "ethics" in member_key or "Ethical" in member_info['role']:
                    emoji = "⚖️"
                elif "resource" in member_key or "Resource" in member_info['role']:
                    emoji = "🔋"
                elif "automation" in member_key or "Automation" in member_info['role']:
                    emoji = "⚙️"

                ai_crew_info += f"        - {emoji} **{member_info['name']}** - {member_info['role']} - {member_info['description']}\n"

        # Add paid fallbacks information
        for fallback_key in CREW_MANIFEST.get("paid_fallbacks", []):
            if fallback_key in MODEL_ROLES:
                fallback_info = MODEL_ROLES[fallback_key]
                ai_crew_info += f"        - 💰 **{fallback_info['name']}** - {fallback_info['role']} - {fallback_info['description']}\n"

        help_text = f"""
        # 🚀 P.U.L.S.E. Help

        ## 🔧 General Commands
        - `help` - Show this help message
        - `status` - Show system status
        - `exit` - Exit the application

        ## ⏰ Time Commands
        - `what time is it` - Get the current local time
        - `what time is it in [location]` - Get the time in a specific location

        ## 🎯 Goal Commands
        - `add goal [text]` - Add a new goal
        - `list goals` - List all active goals
        - `complete goal [text]` - Mark a goal as completed
        - `delete goal [text]` - Delete a goal

        ## 🧠 Memory Commands
        - `search memory [query]` - Search memory for a query
        - `search memory` - Show recent memories
        - `save to memory [text]` - Save a memory
        - `save to memory [category]: [data]` - Save categorized data to memory
        - `recall [category]` - Recall data from memory

        ## 🤖 AI Crew Commands
        - `ask [model] [query]` - Ask a specific AI crew member
        - `ask gemini [query]` - Ask Gemini (crew leader)
        - `ask deepseek [query]` - Ask DeepSeek (troubleshooting expert)
        - `ask deepcoder [query]` - Ask DeepCoder (code generation specialist)
        - `ask llama-doc [query]` - Ask Llama-Doc (documentation expert)
        - `ask mistral-small [query]` - Ask Mistral-Small (trends analyst)
        - `ask llama-content [query]` - Ask Llama-Content (content creation specialist)
        - `ask llama-technical [query]` - Ask Llama-Technical (technical translation expert)
        - `ask hermes [query]` - Ask Hermes (brainstorming specialist)
        - `ask olmo [query]` - Ask Olmo (ethical AI specialist)
        - `ask mistralai [query]` - Ask MistralAI (task automation specialist)
        - `ask kimi [query]` - Ask Kimi (visual reasoning specialist)
        - `ask nemotron [query]` - Ask Nemotron (advanced reasoning specialist)
        - `ask claude [query]` - Ask Claude (paid fallback)
        - `ask grok [query]` - Ask Grok (paid fallback)

        ## 🎭 Personality Commands
        - `show personality` - Show current personality traits
        - `adjust [trait] to [value]` - Adjust a personality trait (0.0 to 1.0)

        ## 🧩 Specialized Query Types
        - `ask code [query]` - Get coding help (routes to DeepCoder)
        - `ask debug [query]` - Debug code issues (routes to DeepCoder)
        - `ask algorithm [query]` - Get algorithm help (routes to DeepCoder)
        - `ask docs [query]` - Get documentation help (routes to Llama-Doc)
        - `ask explain [query]` - Get explanations (routes to Llama-Doc)
        - `ask summarize [query]` - Get summaries (routes to Llama-Doc)
        - `ask troubleshoot [query]` - Troubleshoot issues (routes to DeepSeek)
        - `ask solve [query]` - Solve problems (routes to DeepSeek)
        - `ask trends [query]` - Get trend information (routes to Mistral-Small)
        - `ask research [query]` - Get research information (routes to Mistral-Small)
        - `ask content [query]` - Generate content (routes to Llama-Content)
        - `ask creative [query]` - Generate creative content (routes to Llama-Content)
        - `ask write [query]` - Generate written content (routes to Llama-Content)
        - `ask technical [query]` - Get technical information (routes to Llama-Technical)
        - `ask math [query]` - Solve mathematical problems (routes to Llama-Technical)
        - `ask brainstorm [query]` - Brainstorm ideas (routes to Hermes)
        - `ask ideas [query]` - Generate ideas (routes to Hermes)
        - `ask ethics [query]` - Get ethical considerations (routes to Olmo)
        - `ask automate [query]` - Automate tasks (routes to MistralAI)
        - `ask workflow [query]` - Optimize workflows (routes to MistralAI)
        - `ask process [query]` - Improve processes (routes to MistralAI)
        - `ask visual [query]` - Analyze images or visual content (routes to Kimi)
        - `ask image [query]` - Work with images (routes to Kimi)
        - `ask design [query]` - Get UI/UX design help (routes to Kimi)
        - `ask reasoning [query]` - Solve complex reasoning problems (routes to Nemotron)
        - `ask complex [query]` - Handle complex analysis (routes to Nemotron)
        - `ask analyze [query]` - Get in-depth analysis (routes to Nemotron)

        ## 👥 AI Crew Members
{ai_crew_info}
        """

        return help_text

    async def get_system_status(self) -> str:
        """
        Get system status (public method)

        Returns:
            System status text
        """
        return await self._get_system_status()

    async def _get_system_status(self) -> str:
        """
        Get system status

        Returns:
            System status text
        """
        # Import the crew manifest to show AI crew information
        from configs.models import CREW_MANIFEST, MODEL_ROLES

        # Get system status
        system_status = get_system_status()

        # Get model usage stats
        model_stats = {}
        available_models_dict = {}
        if self.model_orchestrator:
            model_stats = self.model_orchestrator.get_usage_stats()
            available_models_dict = self.model_orchestrator.get_available_models()

        # Format timestamp to be more readable
        try:
            start_time = datetime.fromisoformat(self.conversation_state['session_start'])
            formatted_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = self.conversation_state['session_start']

        # Calculate uptime
        try:
            start_time = datetime.fromisoformat(self.conversation_state['session_start'])
            current_time = datetime.now()
            uptime_seconds = (current_time - start_time).total_seconds()

            # Format uptime
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        except:
            uptime_str = "Unknown"

        # Format memory and disk values to be more readable
        try:
            memory_used = float(system_status['memory']['used'].split('GB')[0])
            memory_total = float(system_status['memory']['total'].split('GB')[0]) if 'total' in system_status['memory'] else memory_used / (system_status['memory']['percent'] / 100)
            memory_str = f"{memory_used:.2f}GB / {memory_total:.2f}GB"

            disk_used = float(system_status['disk']['used'].split('GB')[0])
            disk_total = float(system_status['disk']['total'].split('GB')[0]) if 'total' in system_status['disk'] else disk_used / (system_status['disk']['percent'] / 100)
            disk_str = f"{disk_used:.2f}GB / {disk_total:.2f}GB"
        except:
            memory_str = system_status['memory']['used']
            disk_str = system_status['disk']['used']

        # Get color indicators based on usage percentages
        memory_color = "🟢 Green" if system_status['memory']['percent'] < 70 else "🟡 Yellow" if system_status['memory']['percent'] < 90 else "🔴 Red"
        disk_color = "🟢 Green" if system_status['disk']['percent'] < 70 else "🟡 Yellow" if system_status['disk']['percent'] < 90 else "🔴 Red"
        cpu_color = "🟢 Green" if system_status['cpu']['percent'] < 70 else "🟡 Yellow" if system_status['cpu']['percent'] < 90 else "🔴 Red"

        # Format AI crew status
        ai_crew_status = ""

        # Check if Gemini is available
        gemini_available = self.model_orchestrator and self.model_orchestrator.gemini is not None
        gemini_status = "✅ Available" if gemini_available else "❌ Unavailable"

        # Check if OpenRouter is available
        openrouter_available = self.model_orchestrator and self.model_orchestrator.openrouter is not None

        # Check if Ollama is available
        ollama_status = "❌ Unavailable"
        distilbert_status = "❌ Unavailable"
        if self.model_interface:
            try:
                status = await self.model_interface.check_status()
                ollama_info = status["ollama"]
                offline_mode = status["offline_mode"]
                distilbert_available = status["distilbert_available"]
                distilbert_initialized = status["distilbert_initialized"]
                # Internet status is checked but used elsewhere in the code

                if ollama_info["running"]:
                    models_str = ", ".join(ollama_info["models"]) if ollama_info["models"] else "None"
                    memory_usage = f"{ollama_info.get('memory_usage', 0):.2f}GB" if ollama_info.get('memory_usage', 0) > 0 else "Unknown"
                    status_text = "Running"
                    if offline_mode:
                        status_text += " (Offline Mode)"
                    ollama_status = f"✅ {status_text} (Models: {models_str}, Memory: {memory_usage})"
                else:
                    status_text = "Not Running"
                    if offline_mode:
                        status_text += " (Offline Mode)"
                    ollama_status = f"⚠️ {status_text}"

                    if ollama_info.get("error"):
                        ollama_status += f" - Error: {ollama_info['error']}"

                # DistilBERT status
                if distilbert_available:
                    distilbert_status = f"✅ Available{' (Initialized)' if distilbert_initialized else ''}"
                else:
                    distilbert_status = "❌ Unavailable"
            except Exception as e:
                self.logger.error(f"Error checking model interface status: {str(e)}")
                ollama_status = f"⚠️ Error: {str(e)}"

        # Add leader information
        leader_key = CREW_MANIFEST.get("leader", "gemini")
        if leader_key in MODEL_ROLES:
            leader_info = MODEL_ROLES[leader_key]
            leader_status = gemini_status if leader_key == "gemini" else "❌ Unavailable"
            ai_crew_status += f"        - 👑 **{leader_info['name']}** ({leader_info['role']}): {leader_status}\n"

        # Add crew members information
        for member_key in CREW_MANIFEST.get("members", []):
            if member_key in MODEL_ROLES:
                member_info = MODEL_ROLES[member_key]
                # Skip if it's the leader (already added)
                if member_key == leader_key:
                    continue

                # Determine if the model is available
                model_id = member_info.get('model_id', '')
                model_available = openrouter_available and model_id in available_models_dict.get('openrouter', [])
                model_status = "✅ Available" if model_available else "❌ Unavailable"

                # Add emoji based on role
                emoji = "🧠"
                if "code" in member_key or "Code" in member_info['role']:
                    emoji = "💻"
                elif "troubleshoot" in member_key or "Troubleshooting" in member_info['role']:
                    emoji = "🔧"
                elif "doc" in member_key or "Documentation" in member_info['role']:
                    emoji = "📚"
                elif "trend" in member_key or "Trend" in member_info['role']:
                    emoji = "📈"
                elif "content" in member_key or "Content" in member_info['role']:
                    emoji = "✍️"
                elif "technical" in member_key or "Technical" in member_info['role']:
                    emoji = "🔬"
                elif "brainstorm" in member_key or "Brainstorming" in member_info['role']:
                    emoji = "💡"
                elif "ethics" in member_key or "Ethical" in member_info['role']:
                    emoji = "⚖️"
                elif "resource" in member_key or "Resource" in member_info['role']:
                    emoji = "🔋"
                elif "automation" in member_key or "Automation" in member_info['role']:
                    emoji = "⚙️"

                ai_crew_status += f"        - {emoji} **{member_info['name']}** ({member_info['role']}): {model_status}\n"

        # Add paid fallbacks information
        for fallback_key in CREW_MANIFEST.get("paid_fallbacks", []):
            if fallback_key in MODEL_ROLES:
                fallback_info = MODEL_ROLES[fallback_key]
                model_id = fallback_info.get('model_id', '')
                model_available = openrouter_available and model_id in available_models_dict.get('openrouter', [])
                model_status = "✅ Available" if model_available else "❌ Unavailable"
                ai_crew_status += f"        - 💰 **{fallback_info['name']}** ({fallback_info['role']}): {model_status}\n"

        # Format specialized query types
        query_types = ""
        from configs.models import QUERY_TYPE_TO_MODEL

        # Group query types by the model they route to
        query_types_by_model = {}
        for query_type, model_key in QUERY_TYPE_TO_MODEL.items():
            if model_key not in query_types_by_model:
                query_types_by_model[model_key] = []
            query_types_by_model[model_key].append(query_type)

        # Format the query types
        for model_key, query_type_list in query_types_by_model.items():
            if model_key in MODEL_ROLES:
                model_info = MODEL_ROLES[model_key]
                query_types += f"        - **{model_info['name']}**: {', '.join(query_type_list)}\n"

        # Format status with emojis and better formatting
        status_text = f"""
        # 🚀 System Status

        ## 💻 Hardware
        - 🧠 Memory: {memory_str} ({system_status['memory']['percent']}%) [{memory_color}]
        - 💾 Disk: {disk_str} ({system_status['disk']['percent']}%) [{disk_color}]
        - ⚡ CPU: {system_status['cpu']['percent']}% used [{cpu_color}]
        - 🔌 Processor: {system_status['cpu'].get('processor', 'Unknown')}

        ## 🤖 AI Models Usage
        - 🧠 Gemini: {model_stats.get('gemini', {}).get('calls', 0)} calls
        - 🌐 OpenRouter: {model_stats.get('openrouter', {}).get('calls', 0)} calls
        - 💻 Local: {model_stats.get('local', {}).get('calls', 0)} calls
        - 🚀 Ollama: {ollama_status}
        - 🧠 DistilBERT: {distilbert_status}

        ## 👥 AI Crew Status
{ai_crew_status}
        ## 🧩 Specialized Query Types
{query_types}
        ## ⏱️ Session
        - 🕒 Started: {formatted_time}
        - ⏱️ Uptime: {uptime_str}
        - 💬 Interactions: {self.conversation_state['interaction_count']}
        """

        return status_text

    def _connect_components(self):
        """
        Connect all components to enable enhanced functionality
        """
        try:
            # Connect personality engine to model personality manager
            if hasattr(self, 'model_orchestrator') and self.model_orchestrator and \
               hasattr(self.model_orchestrator, 'model_personality') and \
               hasattr(self, 'personality') and self.personality:
                self.model_orchestrator.model_personality.personality_engine = self.personality
                self.logger.info("Connected personality engine to model personality manager")

            # Connect memory manager to rich context manager
            if hasattr(self, 'model_orchestrator') and self.model_orchestrator and \
               hasattr(self.model_orchestrator, 'rich_context_manager') and \
               hasattr(self, 'memory') and self.memory:
                self.model_orchestrator.rich_context_manager.memory_manager = self.memory
                self.logger.info("Connected memory manager to rich context manager")

            # Connect personality engine to rich context manager
            if hasattr(self, 'model_orchestrator') and self.model_orchestrator and \
               hasattr(self.model_orchestrator, 'rich_context_manager') and \
               hasattr(self, 'personality') and self.personality:
                self.model_orchestrator.rich_context_manager.personality_engine = self.personality
                self.logger.info("Connected personality engine to rich context manager")

            # Connect model interface to natural intent handler
            if hasattr(self, 'intent_handler') and self.intent_handler and \
               hasattr(self, 'model_orchestrator') and self.model_orchestrator:
                self.intent_handler.model_interface = self.model_orchestrator
                self.logger.info("Connected model interface to natural intent handler")

            # Connect model interface to proactive monitor
            if hasattr(self, 'proactive_monitor') and self.proactive_monitor and \
               hasattr(self, 'model_orchestrator') and self.model_orchestrator:
                self.proactive_monitor.model_interface = self.model_orchestrator
                self.logger.info("Connected model interface to proactive monitor")

        except Exception as e:
            self.logger.error(f"Error connecting components: {str(e)}")

    def _format_response(self, content: str, success: bool = True, model_id: str = "gemini") -> str:
        """
        Format a response using the personality engine

        Args:
            content: Response content
            success: Whether the operation was successful
            model_id: The model ID (default: gemini)

        Returns:
            Formatted response
        """
        # Update conversation state
        self.conversation_state["last_response"] = content

        # Check if this is a new session
        is_new_session = False
        if self.context:
            is_new_session = self.context.is_new_session()

        # Format with personality if available
        if self.personality:
            return self.personality.format_response(
                content,
                success=success,
                model_id=model_id,
                is_new_session=is_new_session
            )

        # Otherwise, return as is
        return content

    async def _handle_proactive_alert(self, alert_type: str, message: str, data: Dict[str, Any]) -> None:
        """
        Handle a proactive alert from the monitor

        Args:
            alert_type: Type of alert (system, calendar, project, error)
            message: Alert message
            data: Additional data about the alert
        """
        try:
            self.logger.info(f"Proactive alert: {alert_type} - {message}")

            # Add the alert to the conversation state
            alert_entry = {
                "type": alert_type,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            self.conversation_state["proactive_alerts"].append(alert_entry)

            # Limit the number of stored alerts
            if len(self.conversation_state["proactive_alerts"]) > 10:
                self.conversation_state["proactive_alerts"] = self.conversation_state["proactive_alerts"][-10:]

            # Format the alert message based on type
            formatted_message = self._format_alert_message(alert_type, message, data)

            # TODO: Implement a notification system to display the alert to the user
            # For now, just log it
            self.logger.info(f"PROACTIVE ALERT: {formatted_message}")

            # In a real implementation, this would send a notification to the user
            # For example, using a system notification, CLI UI alert, etc.

        except Exception as e:
            self.logger.error(f"Error handling proactive alert: {str(e)}")

    def _format_alert_message(self, alert_type: str, message: str, data: Dict[str, Any]) -> str:
        """
        Format an alert message for display

        Args:
            alert_type: Type of alert
            message: Alert message
            data: Additional data

        Returns:
            Formatted message
        """
        if alert_type == "system":
            # Format system alerts
            icon = "🔥" if data.get("type") == "temperature" else "⚠️"
            return f"{icon} SYSTEM ALERT: {message}"

        elif alert_type == "calendar":
            # Format calendar alerts
            return f"📅 CALENDAR ALERT: {message}"

        elif alert_type == "project":
            # Format project alerts
            if data.get("type") == "git":
                return f"📝 PROJECT ALERT: {message} ({data.get('change_count', 0)} changes)"
            elif data.get("type") == "todo":
                return f"📋 TODO ALERT: {message} ({data.get('file_count', 0)} files)"
            else:
                return f"📁 PROJECT ALERT: {message}"

        elif alert_type == "error":
            # Format error alerts
            return f"❌ ERROR ALERT: {message}"

        else:
            # Default format
            return f"ℹ️ ALERT: {message}"

    def _launch_cli_ui(self) -> str:
        """
        Launch the CLI UI

        Returns:
            Response message
        """
        try:
            # Create a new process to run the CLI UI
            import subprocess
            import sys
            import os

            # Create a script to launch the CLI UI
            script_content = """
# CLI UI Launcher
import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the CLI UI
from utils.cli_ui import PulseCLIUI
from skills.pulse_agent import PulseAgent

# Create a new agent instance
agent = PulseAgent()

# Create the CLI UI
cli_ui = PulseCLIUI(agent)

# Run the CLI UI
asyncio.run(cli_ui.run())
"""

            # Save the script to a temporary file
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cli_ui_launcher.py")
            with open(script_path, "w") as f:
                f.write(script_content)

            # Launch the script in a new process
            subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)

            return "Launching CLI UI in a new window. Please check your taskbar for the new console window."
        except Exception as e:
            self.logger.error(f"Error launching CLI UI: {str(e)}")
            return f"Failed to launch CLI UI: {str(e)}"

    async def _handle_ollama_command(self, action: str, model: Optional[str] = None) -> str:
        """
        Handle Ollama commands

        Args:
            action: Action to perform (on, off, status, pull)
            model: Model name for pull action

        Returns:
            Response message
        """
        if not self.model_interface:
            return self._format_response("Sorry, the model interface is not available.")

        try:
            if action == "on":
                # Start Ollama service and enable offline mode
                result = await self.model_interface.toggle_offline_mode(True)
                if result["success"]:
                    return self._format_response(f"🚀 {result['message']}")
                else:
                    return self._format_response(f"❌ {result['message']}")

            elif action == "off":
                # Disable offline mode and stop Ollama service
                result = await self.model_interface.toggle_offline_mode(False)
                if result["success"]:
                    return self._format_response(f"🛑 {result['message']}")
                else:
                    return self._format_response(f"❌ {result['message']}")

            elif action == "toggle":
                # Toggle offline mode
                current_mode = self.model_interface.offline_mode
                result = await self.model_interface.toggle_offline_mode(not current_mode)
                if result["success"]:
                    message = f"Offline mode {'enabled' if not current_mode else 'disabled'} successfully."
                    return self._format_response(f"🚀 {message}")
                else:
                    return self._format_response(f"❌ {result['message']}")

            elif action == "pull":
                # Pull a model
                if not model:
                    return self._format_response("Please specify a model to pull.")

                # Ensure Ollama is running
                await self.model_interface.manage_ollama(ensure_running=True)

                # This is a placeholder - actual implementation would use subprocess
                # to pull the model using the Ollama CLI
                return self._format_response(f"Pulling model {model}... (not implemented yet)")

            else:  # status
                # Get Ollama status
                ollama_running = await self.model_interface.ollama_client.check_health(force=True)
                memory = psutil.virtual_memory()
                available_gb = memory.available / (1024 ** 3)
                internet_available = await self.model_interface.check_internet()

                if ollama_running:
                    # Get available models
                    models = await self.model_interface.ollama_client.refresh_models()
                    models_str = ", ".join(models) if models else "None"

                    status_text = "Running"
                    if self.model_interface.offline_mode:
                        status_text += " (Offline Mode)"

                    message = f"🚀 Ollama Status: {status_text}\n"
                    message += f"Models Loaded: {models_str}\n"
                    message += f"System Memory: {available_gb:.2f}GB free ({memory.percent}% used)\n"
                    message += f"Internet: {'✅ Available' if internet_available else '❌ Not Available'}\n"
                    message += f"Offline Mode: {'✅ Enabled' if self.model_interface.offline_mode else '❌ Disabled'}"
                else:
                    status_text = "Not Running"
                    if self.model_interface.offline_mode:
                        status_text += " (Offline Mode)"

                    message = f"🛑 Ollama Status: {status_text}\n"
                    message += f"System Memory: {available_gb:.2f}GB free ({memory.percent}% used)\n"
                    message += f"Internet: {'✅ Available' if internet_available else '❌ Not Available'}\n"
                    message += f"Offline Mode: {'✅ Enabled' if self.model_interface.offline_mode else '❌ Disabled'}"

                return self._format_response(message)

        except Exception as e:
            self.logger.error(f"Error handling Ollama command: {str(e)}")
            return self._format_response(f"❌ Error handling Ollama command: {str(e)}")

    async def _handle_test_intent_command(self, query: Optional[str] = None, intent: Optional[str] = None) -> str:
        # Note: intent parameter is used in the function implementation below
        """
        Handle test intent commands

        Args:
            query: Query to test
            intent: Intent to test

        Returns:
            Response message
        """
        if not self.intent_handler:
            return self._format_response("Intent handler is not available.")

        try:
            if not query:
                return self._format_response("Please provide a query to test intent classification.")

            # Classify the intent (use provided intent if available, otherwise classify)
            classified_intent = intent if intent else await self.intent_handler.classify(query)

            # Parse the command
            command = await self.intent_handler.parse_command(query)

            # Special handling for time intent - process it locally instead of routing to a model
            if classified_intent == "time" and command and command.get("command_type") == "time":
                # Get the location from the command or use "local" as default
                location = command.get("location", "local")
                time_response = self._get_time(location)

                # Format the response with both intent classification and the actual time
                response = f"## Intent Test Results\n\n"
                response += f"**Query:** {query}\n\n"
                response += f"**Classified Intent:** {classified_intent}\n\n"
                response += f"**Parsed Command:**\n```\n{json.dumps(command, indent=2)}\n```\n\n"
                response += f"**Local Response:**\n{time_response}\n\n"
                response += f"**Note:** Time intents are handled locally and should not be routed to external models."

                return self._format_response(response)

            # Format the response for other intents
            response = f"## Intent Test Results\n\n"
            response += f"**Query:** {query}\n\n"
            response += f"**Classified Intent:** {classified_intent}\n\n"
            response += f"**Parsed Command:**\n```\n{json.dumps(command, indent=2)}\n```\n\n"

            return self._format_response(response)

        except Exception as e:
            self.logger.error(f"Error testing intent: {str(e)}")
            return self._format_response(f"Error testing intent: {str(e)}", success=False)

    def check_version(self) -> str:
        """
        Get the current version of General Pulse

        Returns:
            Version string
        """
        return f"General Pulse v{self.version}"

    def shutdown(self) -> None:
        """
        Shutdown the agent and clean up resources
        """
        try:
            self.logger.info("Shutting down Pulse Agent")

            # Stop the proactive monitor
            if hasattr(self, 'proactive_monitor') and self.proactive_monitor:
                try:
                    # Just set the running flag to False
                    # The monitor will stop on its own in the next iteration
                    if hasattr(self.proactive_monitor, 'running'):
                        self.proactive_monitor.running = False
                        self.logger.info("Proactive monitor stopping (async)")
                except Exception as e:
                    self.logger.error(f"Error stopping proactive monitor: {str(e)}")
                    self.logger.error(traceback.format_exc())

            # Close memory connection
            if self.memory:
                try:
                    self.memory.close()
                    self.logger.info("Memory connection closed")
                except Exception as e:
                    self.logger.error(f"Error closing memory connection: {str(e)}")
                    self.logger.error(traceback.format_exc())

            # Save context to file
            if self.context:
                try:
                    self.context.save_to_file("context_backup.json")
                    self.logger.info("Context saved to file")
                except Exception as e:
                    self.logger.error(f"Error saving context to file: {str(e)}")
                    self.logger.error(traceback.format_exc())

            # Save personality to file
            if self.personality:
                try:
                    self.personality.save_to_file("personality_backup.json")
                    self.logger.info("Personality saved to file")
                except Exception as e:
                    self.logger.error(f"Error saving personality to file: {str(e)}")
                    self.logger.error(traceback.format_exc())

            # Close model interface if available
            # We can't properly close it synchronously, but we can log that we're trying
            if hasattr(self, 'model_interface') and self.model_interface:
                self.logger.info("Model interface will be closed by Python's garbage collector")

            self.logger.info("Pulse Agent shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
