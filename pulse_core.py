"""
P.U.L.S.E. Core Integration Module
Integrates all enhanced components into a cohesive system
"""

import asyncio
import psutil
import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import unified logger
from utils.unified_logger import get_logger

# Import enhanced components
from utils.memory import MemoryManager
from routing.router import AdaptiveRouter
from context.history import ChatHistoryManager
from skills.marketplace import SkillMarketplace
from integrations.sync import GitHubNotionSync
from personality.charisma import CharismaEngine
from utils.intent_preprocessor import QueryPreprocessor

# Import existing components
from skills.pulse_agent import PulseAgent
from skills.model_orchestrator import ModelOrchestrator
from utils.optimization import optimize_for_hardware, get_system_status

# Get logger from unified logger module
logger = get_logger("pulse_core")

# Load environment variables
load_dotenv()

class PulseCore:
    """
    Core integration class for P.U.L.S.E.
    Integrates all enhanced components into a cohesive system
    """

    def __init__(self, user_id: str = "default", debug_mode: bool = False):
        """
        Initialize the P.U.L.S.E. core

        Args:
            user_id: User identifier
            debug_mode: Whether to enable debug mode
        """
        self.logger = logger
        self.user_id = user_id
        self.debug_mode = debug_mode

        # Initialize components
        self.memory_manager = None
        self.router = None
        self.history_manager = None
        self.skill_marketplace = None
        self.github_notion_sync = None
        self.self_awareness = None
        self.charisma_engine = None
        self.query_preprocessor = None
        self.pulse_agent = None
        self.model_orchestrator = None

        # Initialize system
        self._init_system()

        logger.info("P.U.L.S.E. core initialized")

    def _init_system(self) -> None:
        """Initialize the P.U.L.S.E. system"""
        try:
            # Optimize for hardware
            optimize_for_hardware()

            # Initialize memory manager
            self.memory_manager = MemoryManager(db_name="pulse", collection_prefix=self.user_id)
            logger.info("Memory manager initialized")

            # Initialize chat history manager
            self.history_manager = ChatHistoryManager(user_id=self.user_id)
            logger.info("Chat history manager initialized")

            # Initialize self-awareness engine
            from personality.self_awareness import SelfAwarenessEngine
            self.self_awareness = SelfAwarenessEngine()
            logger.info("Self-awareness engine initialized")

            # Initialize charisma engine with self-awareness
            self.charisma_engine = CharismaEngine(
                memory_manager=self.memory_manager,
                self_awareness=self.self_awareness
            )
            logger.info("Charisma engine initialized")

            # Initialize model orchestrator
            self.model_orchestrator = ModelOrchestrator(simulate_responses=self.debug_mode)
            logger.info("Model orchestrator initialized")

            # Initialize adaptive router
            self.router = AdaptiveRouter(neural_router=self.model_orchestrator.neural_router if hasattr(self.model_orchestrator, 'neural_router') else None)
            logger.info("Adaptive router initialized")

            # Initialize query preprocessor
            self.query_preprocessor = QueryPreprocessor(minilm_classifier=None)  # Will be set later
            logger.info("Query preprocessor initialized")

            # Initialize skill marketplace
            self.skill_marketplace = SkillMarketplace()
            logger.info("Skill marketplace initialized")

            # Initialize GitHub-Notion sync
            self.github_notion_sync = GitHubNotionSync()
            logger.info("GitHub-Notion sync initialized")

            # Initialize pulse agent
            self.pulse_agent = PulseAgent(
                user_id=self.user_id,
                memory_path="pulse_memory.db",
                simulate_responses=self.debug_mode
            )
            logger.info("Pulse agent initialized")

            # Start background tasks
            asyncio.create_task(self._run_background_tasks())

            logger.info("P.U.L.S.E. system initialization complete")
        except Exception as e:
            logger.error(f"Error initializing P.U.L.S.E. system: {str(e)}")
            raise

    async def _run_background_tasks(self) -> None:
        """Run background tasks"""
        try:
            # Start GitHub-Notion sync loop
            asyncio.create_task(self.github_notion_sync.start_sync_loop())

            # Start memory optimization loop
            asyncio.create_task(self._memory_optimization_loop())

            logger.info("Background tasks started")
        except Exception as e:
            logger.error(f"Error starting background tasks: {str(e)}")

    async def _memory_optimization_loop(self) -> None:
        """Run the memory optimization loop"""
        while True:
            try:
                # Check memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent

                if memory_percent > 80:
                    logger.warning(f"High memory usage detected: {memory_percent}%")

                    # Trigger garbage collection
                    import gc
                    collected = gc.collect()
                    logger.info(f"Garbage collection: collected {collected} objects")

                # Wait before checking again
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in memory optimization loop: {str(e)}")
                await asyncio.sleep(60)

    async def process_input(self, user_input: str) -> str:
        """
        Process user input

        Args:
            user_input: User input text

        Returns:
            Response text
        """
        try:
            # Log the input
            logger.info(f"Processing input: {user_input[:50]}...")

            # Preprocess the query
            preprocessed = await self.query_preprocessor.preprocess_query(user_input)

            # Update charisma engine mood
            self.charisma_engine.update_mood(user_input)

            # Handle commands
            if preprocessed["type"] == "command":
                return await self._handle_command(preprocessed)

            # Route the query to the appropriate model
            routing_result = await self.router.route(
                preprocessed["query"],
                intent=preprocessed.get("intent")
            )

            # Get the selected model
            model = routing_result["model"]
            model_name = routing_result["model_name"]
            provider = routing_result["provider"]

            # Log the routing decision
            logger.info(f"Routed to {model} ({provider})")

            # Get context for the model
            context_result = await self.history_manager.get_context_for_model()
            context = {}

            if context_result["success"]:
                context = context_result["context"]

            # Get historical context for the query
            historical_context = await self.history_manager.get_historical_context(query=preprocessed["query"])
            if historical_context:
                context["historical_context"] = historical_context

            # Get the system prompt and add it to the context
            context["system_prompt"] = await self.charisma_engine.get_system_prompt(model=model)

            # Call the model
            try:
                # Use the model orchestrator to call the model
                response = await self.model_orchestrator.handle_query(
                    input_text=preprocessed["query"],
                    context=context,
                    model_preference=model_name
                )

                # Check if the response was successful
                if not response.get("success", False):
                    # Handle model failure
                    failure_result = await self.query_preprocessor.handle_model_failure(
                        model=model,
                        error=response.get("error", "Unknown error")
                    )

                    # If fallback is required, try the fallback model
                    if failure_result["fallback_required"]:
                        logger.warning(f"Falling back to {failure_result['fallback_model']} due to {model} failure")

                        # Call the fallback model
                        fallback_response = await self.model_orchestrator.handle_query(
                            input_text=preprocessed["query"],
                            context=context,
                            model_preference=failure_result["fallback_model"]
                        )

                        if fallback_response.get("success", False):
                            response = fallback_response
                        else:
                            # If fallback also fails, use a generic error message
                            response = {
                                "success": False,
                                "content": "I'm having trouble connecting to my AI models right now. Please try again in a moment.",
                                "model": failure_result["fallback_model"],
                                "error": fallback_response.get("error", "Unknown error")
                            }
            except Exception as e:
                logger.error(f"Error calling model: {str(e)}")
                response = {
                    "success": False,
                    "content": f"I encountered an error: {str(e)}",
                    "model": model,
                    "error": str(e)
                }

            # Format the response
            content = response.get("content", "I'm not sure how to respond to that.")
            formatted_response = self.charisma_engine.format_response(
                content=content,
                context_type=preprocessed.get("intent", "general"),
                model=model,
                success=response.get("success", False)
            )

            # Save the interaction to history
            interaction_result = await self.history_manager.add_interaction(
                user_input=user_input,
                assistant_response=formatted_response,
                metadata={
                    "model": model,
                    "provider": provider,
                    "intent": preprocessed.get("intent", "general"),
                    "success": response.get("success", False)
                }
            )

            # Also store recent interactions in memory for easy access by other components
            if interaction_result.get("success", False):
                # Get recent interactions to store in memory
                recent_result = await self.history_manager.get_recent_interactions(count=5)
                if recent_result.get("success", False):
                    # Store in memory for easy access
                    if self.memory_manager:
                        await self.memory_manager.store(
                            "recent_interactions",
                            recent_result.get("interactions", []),
                            key="chat_history"
                        )
                        logger.debug("Stored recent interactions in memory")

            return formatted_response
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            return f"I encountered an error: {str(e)}"

    async def _handle_command(self, command_data: Dict[str, Any]) -> str:
        """
        Handle a command

        Args:
            command_data: Command data from preprocessor

        Returns:
            Response text
        """
        command = command_data["command"]
        args = command_data.get("args")

        try:
            # Handle built-in commands
            if command == "help":
                return self._get_help_text()
            elif command == "status":
                return await self._get_status_text()
            elif command == "exit":
                return "Goodbye! Have a great day!"
            elif command == "memory":
                return await self._handle_memory_command(args)
            elif command == "search_memory":
                return await self._handle_search_memory_command(args)
            elif command == "save_memory":
                return await self._handle_save_memory_command(args)
            elif command == "clear_memory":
                return await self._handle_clear_memory_command()
            elif command == "chat_history":
                return await self._handle_chat_history_command(args)
            elif command == "add_goal":
                return await self._handle_add_goal_command(args)
            elif command == "list_goals":
                return await self._handle_list_goals_command()
            elif command == "complete_goal":
                return await self._handle_complete_goal_command(args)
            elif command == "delete_goal":
                return await self._handle_delete_goal_command(args)
            else:
                # Unknown command, pass to pulse agent
                return await self.pulse_agent.process_input(command_data["original_query"])
        except Exception as e:
            logger.error(f"Error handling command {command}: {str(e)}")
            return f"Error handling command: {str(e)}"

    def _get_help_text(self) -> str:
        """
        Get help text

        Returns:
            Help text
        """
        return """
        # 🚀 P.U.L.S.E. Help

        ## 🔧 General Commands
        - `help` - Show this help message
        - `status` - Show system status
        - `exit` - Exit the application

        ## 🧠 Memory Commands
        - `memory` - Show recent memories
        - `search memory [query]` - Search memory for a query
        - `save to memory [text]` - Save a memory
        - `clear memory` - Clear all memories
        - `chat history` - Show recent chat history

        ## 🎯 Goal Commands
        - `add goal [text]` - Add a new goal
        - `list goals` - List all active goals
        - `complete goal [text]` - Mark a goal as completed
        - `delete goal [text]` - Delete a goal

        ## 🧩 Specialized Query Types
        - `ask code [query]` - Get coding help
        - `ask debug [query]` - Debug code issues
        - `ask algorithm [query]` - Get algorithm help
        - `ask docs [query]` - Get documentation help
        - `ask explain [query]` - Get explanations
        - `ask summarize [query]` - Get summaries
        - `ask troubleshoot [query]` - Troubleshoot issues
        - `ask solve [query]` - Solve problems
        - `ask trends [query]` - Get trend information
        - `ask research [query]` - Get research information
        - `ask content [query]` - Generate content
        - `ask creative [query]` - Generate creative content
        - `ask write [query]` - Generate written content
        - `ask technical [query]` - Get technical information
        - `ask math [query]` - Solve mathematical problems
        - `ask brainstorm [query]` - Brainstorm ideas
        - `ask ideas [query]` - Generate ideas
        - `ask ethics [query]` - Get ethical considerations
        """

    async def _get_status_text(self) -> str:
        """
        Get system status text

        Returns:
            Status text
        """
        try:
            # Get system status with robust error handling
            system_status = get_system_status()

            # Get router status
            router_status = await self.router.get_system_status()

            # Get model usage stats
            model_usage = await self.router.get_model_usage_stats()

            # Extract values from system_status with proper error handling
            try:
                cpu_percent = system_status['cpu']['percent']
            except (KeyError, TypeError):
                # Fallback if the structure is different
                cpu_percent = system_status.get('cpu_percent', 0)

            try:
                memory_percent = system_status['memory']['percent']
            except (KeyError, TypeError):
                # Fallback if the structure is different
                memory_percent = system_status.get('memory_percent', 0)

            try:
                # Calculate available memory in MB if not directly available
                if 'memory_available_mb' in system_status:
                    memory_available_mb = system_status['memory_available_mb']
                else:
                    # Try to extract from the nested structure
                    memory_total = system_status['memory']['total']
                    memory_used = system_status['memory']['used']

                    # Convert from string (e.g., "7.5GB") to float if needed
                    if isinstance(memory_total, str) and "GB" in memory_total:
                        memory_total = float(memory_total.replace("GB", "")) * 1024  # Convert GB to MB
                    if isinstance(memory_used, str) and "GB" in memory_used:
                        memory_used = float(memory_used.replace("GB", "")) * 1024  # Convert GB to MB

                    memory_available_mb = (memory_total - memory_used) * 1024  # Convert GB to MB if needed
            except (KeyError, TypeError, ValueError):
                # Fallback if calculation fails
                memory_available_mb = 1024  # Default to 1GB

            try:
                disk_percent = system_status['disk']['percent']
            except (KeyError, TypeError):
                # Fallback if the structure is different
                disk_percent = system_status.get('disk_percent', 0)

            # Format status text
            status_text = f"""
            # 📊 P.U.L.S.E. System Status

            ## 💻 System Resources
            - CPU: {cpu_percent:.1f}% used
            - Memory: {memory_percent:.1f}% used ({memory_available_mb:.1f} MB free)
            - Disk: {disk_percent:.1f}% used

            ## 🤖 Model Usage
            - Total queries: {model_usage['total']}
            """

            # Add model usage details
            for model, stats in model_usage.get("models", {}).items():
                status_text += f"- {model}: {stats['count']} queries ({stats['percentage']:.1f}%)\n"

            # Add router status
            status_text += f"""
            ## 🔄 Router Status
            - Memory constrained: {'Yes' if router_status['memory_constrained'] else 'No'}
            - CPU constrained: {'Yes' if router_status['cpu_constrained'] else 'No'}
            - Offline mode: {'Yes' if router_status['offline_mode'] else 'No'}
            """

            return status_text
        except Exception as e:
            self.logger.error(f"Error generating status text: {str(e)}")
            return f"""
            # 📊 P.U.L.S.E. System Status

            ## ⚠️ Error
            There was an error retrieving the system status: {str(e)}

            Please try again later or check the logs for more information.
            """

    async def _handle_memory_command(self, args: Optional[str] = None) -> str:
        """
        Handle memory command

        Args:
            args: Command arguments (optional, not used in current implementation)

        Returns:
            Response text
        """
        # Get recent memories from history manager (args is ignored in current implementation)
        result = await self.history_manager.get_recent_interactions(count=5)

        if not result["success"]:
            return f"Error retrieving memories: {result.get('error', 'Unknown error')}"

        interactions = result["interactions"]

        if not interactions:
            return "No recent interactions found."

        # Format memories
        memory_text = "# 🧠 Recent Interactions\n\n"

        for i, interaction in enumerate(interactions):
            timestamp = datetime.fromisoformat(interaction["timestamp"].replace('Z', '+00:00'))
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            memory_text += f"## Interaction {i+1} ({formatted_time})\n"
            memory_text += f"**You:** {interaction['user_input'][:100]}{'...' if len(interaction['user_input']) > 100 else ''}\n"
            memory_text += f"**P.U.L.S.E.:** {interaction['assistant_response'][:100]}{'...' if len(interaction['assistant_response']) > 100 else ''}\n\n"

        return memory_text

    async def _handle_search_memory_command(self, query: Optional[str]) -> str:
        """
        Handle search memory command

        Args:
            query: Search query

        Returns:
            Response text
        """
        if not query:
            return "Please provide a search query."

        # Get memories from history manager
        result = await self.history_manager.get_relevant_memories(query=query)

        if not result["success"]:
            return f"Error searching memories: {result.get('error', 'Unknown error')}"

        memories = result["memories"]

        if not memories:
            return f"No memories found for query: {query}"

        # Format memories
        memory_text = f"# 🔍 Memory Search Results for '{query}'\n\n"

        for i, memory in enumerate(memories):
            memory_text += f"## Memory {i+1}\n"
            memory_text += f"**Category:** {memory.get('category', 'Unknown')}\n"
            memory_text += f"**Content:** {memory.get('content', memory.get('summary', 'No content'))}\n\n"

        return memory_text

    async def _handle_save_memory_command(self, memory_text: Optional[str]) -> str:
        """
        Handle save memory command

        Args:
            memory_text: Memory text

        Returns:
            Response text
        """
        if not memory_text:
            return "Please provide text to save to memory."

        # Check if the memory contains a category
        category = "memory"
        content = memory_text

        if ":" in memory_text:
            parts = memory_text.split(":", 1)
            category = parts[0].strip().lower()
            content = parts[1].strip()

        # Save to memory
        result = await self.history_manager.add_memory(
            category=category,
            content=content
        )

        if result["success"]:
            return f"Memory saved to category '{category}'."
        else:
            return f"Error saving memory: {result.get('error', 'Unknown error')}"

    async def _handle_clear_memory_command(self) -> str:
        """
        Handle clear memory command

        Returns:
            Response text
        """
        return "Memory clearing is not supported for safety reasons. Your memories are important!"

    async def _handle_chat_history_command(self, args: Optional[str] = None) -> str:
        """
        Handle chat history command

        Args:
            args: Optional limit (number of interactions to show)

        Returns:
            Response text with formatted chat history
        """
        try:
            # Parse limit if provided
            limit = 10  # Default limit
            if args and args.isdigit():
                limit = int(args)
                limit = min(max(limit, 1), 50)  # Limit between 1 and 50

            # Get recent interactions from history manager
            result = await self.history_manager.get_recent_interactions(count=limit)

            if not result["success"]:
                # Fall back to memory manager if history manager fails
                memory_result = await self.memory_manager.retrieve("recent_interactions", limit=limit)

                if not memory_result["success"]:
                    return f"Error retrieving chat history: {result.get('error', 'Unknown error')}"

                interactions = memory_result.get("data", [])

                if not interactions:
                    return "No chat history found."

                # Format chat history from memory manager
                history_text = "# 📝 Recent Chat History\n\n"

                for i, interaction in enumerate(reversed(interactions[-limit:])):
                    query = interaction.get("query", "")
                    response = interaction.get("response", "")
                    timestamp = interaction.get("timestamp", "")

                    if timestamp:
                        try:
                            # Convert timestamp to string if it's a datetime object
                            if isinstance(timestamp, datetime.datetime):
                                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            history_text += f"## Interaction {i+1} ({timestamp})\n\n"
                        except:
                            history_text += f"## Interaction {i+1}\n\n"
                    else:
                        history_text += f"## Interaction {i+1}\n\n"

                    history_text += f"**You:** {query}\n\n"
                    history_text += f"**P.U.L.S.E.:** {response}\n\n"
                    history_text += "---\n\n"

                return history_text

            # Process interactions from history manager
            interactions = result["interactions"]

            if not interactions:
                return "No chat history found."

            # Format chat history
            history_text = "# 📝 Recent Chat History\n\n"

            for i, interaction in enumerate(interactions):
                user_input = interaction.get("user_input", "")
                assistant_response = interaction.get("assistant_response", "")
                timestamp = interaction.get("timestamp", "")
                model = interaction.get("metadata", {}).get("model", "unknown")

                if timestamp:
                    try:
                        # Format timestamp
                        if isinstance(timestamp, str):
                            timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        history_text += f"## Interaction {i+1} ({formatted_time})\n\n"
                    except:
                        history_text += f"## Interaction {i+1}\n\n"
                else:
                    history_text += f"## Interaction {i+1}\n\n"

                history_text += f"**You:** {user_input}\n\n"
                history_text += f"**P.U.L.S.E. ({model}):** {assistant_response}\n\n"
                history_text += "---\n\n"

            return history_text

        except Exception as e:
            logger.error(f"Error handling chat history command: {str(e)}")
            return f"Error retrieving chat history: {str(e)}"

    async def _handle_add_goal_command(self, goal_text: Optional[str]) -> str:
        """
        Handle add goal command

        Args:
            goal_text: Goal text

        Returns:
            Response text
        """
        if not goal_text:
            return "Please provide a goal to add."

        # Save to memory
        result = await self.history_manager.add_memory(
            category="goal",
            content=goal_text,
            metadata={"status": "active", "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        )

        if result["success"]:
            return f"Goal added: {goal_text}"
        else:
            return f"Error adding goal: {result.get('error', 'Unknown error')}"

    async def _handle_list_goals_command(self) -> str:
        """
        Handle list goals command

        Returns:
            Response text
        """
        # Get goals from history manager
        result = await self.history_manager.get_relevant_memories(query="goal")

        if not result["success"]:
            return f"Error retrieving goals: {result.get('error', 'Unknown error')}"

        goals = [m for m in result["memories"] if m.get("category") == "goal"]

        if not goals:
            return "No goals found."

        # Format goals
        goal_text = "# 🎯 Goals\n\n"

        for i, goal in enumerate(goals):
            status = goal.get("metadata", {}).get("status", "active")
            created_at = goal.get("metadata", {}).get("created_at", "Unknown")

            if created_at != "Unknown":
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime("%Y-%m-%d")
                except:
                    pass

            goal_text += f"{i+1}. **{goal.get('content')}** - *{status}* (created: {created_at})\n"

        return goal_text

    async def _handle_complete_goal_command(self, goal_text: Optional[str]) -> str:
        """
        Handle complete goal command

        Args:
            goal_text: Goal text

        Returns:
            Response text
        """
        if not goal_text:
            return "Please provide a goal to complete."

        # Get goals from history manager
        result = await self.history_manager.get_relevant_memories(query="goal")

        if not result["success"]:
            return f"Error retrieving goals: {result.get('error', 'Unknown error')}"

        goals = [m for m in result["memories"] if m.get("category") == "goal"]

        # Find the goal
        matching_goal = None

        for goal in goals:
            if goal_text.lower() in goal.get("content", "").lower():
                matching_goal = goal
                break

        if not matching_goal:
            return f"Goal not found: {goal_text}"

        # Update the goal
        # Note: In a real implementation, we would update the goal in the database
        # For now, we'll just add a new memory with the completed status
        result = await self.history_manager.add_memory(
            category="goal",
            content=matching_goal.get("content"),
            metadata={
                "status": "completed",
                "created_at": matching_goal.get("metadata", {}).get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        )

        if result["success"]:
            return f"Goal completed: {matching_goal.get('content')}"
        else:
            return f"Error completing goal: {result.get('error', 'Unknown error')}"

    async def _handle_delete_goal_command(self, goal_text: Optional[str]) -> str:
        """
        Handle delete goal command

        Args:
            goal_text: Goal text

        Returns:
            Response text
        """
        if not goal_text:
            return "Please provide a goal to delete."

        # Get goals from history manager
        result = await self.history_manager.get_relevant_memories(query="goal")

        if not result["success"]:
            return f"Error retrieving goals: {result.get('error', 'Unknown error')}"

        goals = [m for m in result["memories"] if m.get("category") == "goal"]

        # Find the goal
        matching_goal = None

        for goal in goals:
            if goal_text.lower() in goal.get("content", "").lower():
                matching_goal = goal
                break

        if not matching_goal:
            return f"Goal not found: {goal_text}"

        # Update the goal
        # Note: In a real implementation, we would delete the goal from the database
        # For now, we'll just add a new memory with the deleted status
        result = await self.history_manager.add_memory(
            category="goal",
            content=matching_goal.get("content"),
            metadata={
                "status": "deleted",
                "created_at": matching_goal.get("metadata", {}).get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                "deleted_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        )

        if result["success"]:
            return f"Goal deleted: {matching_goal.get('content')}"
        else:
            return f"Error deleting goal: {result.get('error', 'Unknown error')}"

    async def shutdown(self) -> None:
        """Shutdown the P.U.L.S.E. system"""
        try:
            logger.info("Shutting down P.U.L.S.E. system")

            # Close connections
            if self.memory_manager:
                await self.memory_manager.close()

            if self.history_manager:
                await self.history_manager.close()

            if self.github_notion_sync:
                await self.github_notion_sync.close()

            # Shutdown model orchestrator
            if self.model_orchestrator:
                try:
                    await self.model_orchestrator.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down model orchestrator: {str(e)}")

            # Shutdown pulse agent
            if self.pulse_agent:
                self.pulse_agent.shutdown()

            logger.info("P.U.L.S.E. system shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down P.U.L.S.E. system: {str(e)}")
            raise
