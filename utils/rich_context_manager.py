"""
Rich Context Manager for General Pulse

This module provides enhanced context management capabilities that ensure
all models receive rich, relevant context for more informed responses.
"""

import os
import json
import asyncio
import structlog
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

# Configure logger
logger = structlog.get_logger("rich_context_manager")

class RichContextManager:
    """
    Enhanced context manager that provides rich, relevant context to all models
    for more informed responses.
    """

    def __init__(self, memory_manager=None, personality_engine=None, model_interface=None):
        """
        Initialize the rich context manager

        Args:
            memory_manager: Memory manager instance
            personality_engine: Personality engine instance
            model_interface: Model interface instance
        """
        self.memory_manager = memory_manager
        self.personality_engine = personality_engine
        self.model_interface = model_interface

        # Cache for system status to avoid frequent checks
        self.system_status_cache = {}
        self.system_status_ttl = 60  # 60 seconds cache lifetime

        logger.info("Rich context manager initialized")

    async def get_rich_context(self, query: str, base_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get rich context for a query

        Args:
            query: User query
            base_context: Optional base context

        Returns:
            Rich context dictionary
        """
        # Start with base context or empty dict
        if base_context is None:
            context = {}
        elif isinstance(base_context, dict):
            context = base_context.copy()
        elif isinstance(base_context, str):
            # Handle case where base_context is a string
            context = {"text": base_context}
        else:
            # Handle other types
            logger.warning(f"Unexpected base_context type: {type(base_context)}")
            context = {"raw_context": str(base_context)}

        # Add system status
        system_status = await self._get_system_status()
        context["system_status"] = system_status

        # Add user data from memory
        if self.memory_manager:
            user_data = await self._get_user_data()
            context["user_data"] = user_data

        # Add personality information
        if self.personality_engine:
            personality_data = self._get_personality_data()
            context["personality"] = personality_data

        # Add query analysis
        query_analysis = self._analyze_query(query)
        context["query_analysis"] = query_analysis

        # Add model availability
        if self.model_interface:
            model_status = await self._get_model_status()
            context["model_status"] = model_status

        return context

    async def _get_system_status(self) -> Dict[str, Any]:
        """
        Get system status information

        Returns:
            System status dictionary
        """
        # Check cache first
        current_time = time.time()
        if "timestamp" in self.system_status_cache and current_time - self.system_status_cache["timestamp"] < self.system_status_ttl:
            return self.system_status_cache["data"]

        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)

            # Get memory usage
            memory = psutil.virtual_memory()

            # Get disk usage
            disk = psutil.disk_usage('/')

            # Get network info
            net_io = psutil.net_io_counters()

            # Check internet connection
            internet_available = True
            if self.model_interface:
                internet_available = await self.model_interface.check_internet()

            # Check offline mode
            offline_mode = False
            if self.model_interface:
                status = await self.model_interface.check_status()
                offline_mode = status.get("offline_mode", False)

            # Format system status
            system_status = {
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(logical=True)
                },
                "memory": {
                    "total": f"{memory.total / (1024 ** 3):.2f}GB",
                    "available": f"{memory.available / (1024 ** 3):.2f}GB",
                    "used": f"{memory.used / (1024 ** 3):.2f}GB",
                    "percent": memory.percent
                },
                "disk": {
                    "total": f"{disk.total / (1024 ** 3):.2f}GB",
                    "used": f"{disk.used / (1024 ** 3):.2f}GB",
                    "free": f"{disk.free / (1024 ** 3):.2f}GB",
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                },
                "internet_available": internet_available,
                "offline_mode": offline_mode,
                "timestamp": datetime.now().isoformat()
            }

            # Cache the result
            self.system_status_cache = {
                "data": system_status,
                "timestamp": current_time
            }

            return system_status

        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "error": f"Failed to get system status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _get_user_data(self) -> Dict[str, Any]:
        """
        Get user data from memory manager

        Returns:
            User data dictionary
        """
        if not self.memory_manager:
            return {}

        try:
            # Get user identity
            identity_data = self.memory_manager.get_identity()

            # Extract the actual identity dictionary if it's nested
            # The get_identity method returns a nested structure with 'identity' as a key
            if isinstance(identity_data, dict) and 'identity' in identity_data:
                identity = identity_data['identity']
            else:
                # If it's not nested or not a dictionary, use it as is
                identity = identity_data if isinstance(identity_data, dict) else {}

            # Get user projects
            projects = self.memory_manager.get_user_data("projects")

            # Get user interests
            interests = self.memory_manager.get_user_data("interests")

            # Get active goals
            goals = self.memory_manager.get_active_goals()

            # Get recent interactions
            recent_interactions = self.memory_manager.get_recent_interactions(3)

            # Format user data
            user_data = {
                "identity": identity,
                "projects": projects,
                "interests": interests,
                "goals": goals,
                "recent_interactions": recent_interactions
            }

            return user_data

        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return {}

    def _get_personality_data(self) -> Dict[str, Any]:
        """
        Get personality data

        Returns:
            Personality data dictionary
        """
        if not self.personality_engine:
            return {}

        try:
            # Get personality traits
            traits = self.personality_engine.get_traits()

            # Get current mood
            mood = self.personality_engine.get_current_mood()

            # Format personality data
            personality_data = {
                "traits": traits,
                "mood": mood
            }

            return personality_data

        except Exception as e:
            logger.error(f"Error getting personality data: {str(e)}")
            return {}

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query for context

        Args:
            query: User query

        Returns:
            Query analysis dictionary
        """
        try:
            # Simple query analysis
            word_count = len(query.split())
            character_count = len(query)

            # Check for code
            contains_code = "```" in query or any(keyword in query.lower() for keyword in ["function", "class", "def ", "var ", "const ", "let ", "import ", "from "])

            # Check for question
            is_question = query.endswith("?") or any(keyword in query.lower() for keyword in ["what", "how", "why", "when", "where", "who", "which", "can you", "could you"])

            # Check for command
            is_command = any(keyword in query.lower() for keyword in ["show", "list", "create", "update", "delete", "add", "remove", "start", "stop", "enable", "disable"])

            # Format query analysis
            query_analysis = {
                "word_count": word_count,
                "character_count": character_count,
                "contains_code": contains_code,
                "is_question": is_question,
                "is_command": is_command,
                "timestamp": datetime.now().isoformat()
            }

            return query_analysis

        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                "error": f"Failed to analyze query: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _get_model_status(self) -> Dict[str, Any]:
        """
        Get model status information

        Returns:
            Model status dictionary
        """
        if not self.model_interface:
            return {}

        try:
            # Get model status
            status = await self.model_interface.check_status()

            # Get usage stats
            usage_stats = self.model_interface.get_usage_stats()

            # Format model status
            model_status = {
                "offline_mode": status.get("offline_mode", False),
                "ollama": status.get("ollama", {}),
                "usage_stats": usage_stats,
                "timestamp": datetime.now().isoformat()
            }

            return model_status

        except Exception as e:
            logger.error(f"Error getting model status: {str(e)}")
            return {
                "error": f"Failed to get model status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def format_context_for_model(self, context: Dict[str, Any], model_type: str) -> str:
        """
        Format context for a specific model type

        Args:
            context: Context dictionary
            model_type: Model type (gemini, openrouter, ollama)

        Returns:
            Formatted context string
        """
        try:
            # Start with empty context
            context_parts = []

            # Add user information
            if "user_data" in context and context["user_data"]:
                user_data = context["user_data"]

                # Add identity
                if "identity" in user_data and user_data["identity"]:
                    identity_str = ", ".join([f"{k}: {v}" for k, v in user_data["identity"].items() if k != "password"])
                    context_parts.append(f"User: {identity_str}")

                # Add projects
                if "projects" in user_data and user_data["projects"]:
                    projects_str = ", ".join(user_data["projects"])
                    context_parts.append(f"Projects: {projects_str}")

                # Add interests
                if "interests" in user_data and user_data["interests"]:
                    interests_str = ", ".join(user_data["interests"])
                    context_parts.append(f"Interests: {interests_str}")

                # Add goals
                if "goals" in user_data and user_data["goals"]:
                    goals_str = ", ".join([g["goal"] for g in user_data["goals"]])
                    context_parts.append(f"Goals: {goals_str}")

            # Add conversation history
            if "history" in context and context["history"]:
                history = context["history"]
                history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-5:]])
                context_parts.append(f"Recent conversation:\n{history_str}")

            # Add system status (simplified for most models)
            if "system_status" in context and context["system_status"]:
                system_status = context["system_status"]

                # Only include basic system status for most models
                if model_type != "gemini":
                    # Simplified system status
                    offline_mode = system_status.get("offline_mode", False)
                    internet_available = system_status.get("internet_available", True)
                    context_parts.append(f"System: {'Offline mode' if offline_mode else 'Online mode'}, Internet: {'Available' if internet_available else 'Not available'}")
                else:
                    # Detailed system status for Gemini
                    memory_percent = system_status.get("memory", {}).get("percent", 0)
                    cpu_percent = system_status.get("cpu", {}).get("percent", 0)
                    offline_mode = system_status.get("offline_mode", False)
                    internet_available = system_status.get("internet_available", True)

                    system_str = f"System Status: Memory: {memory_percent}% used, CPU: {cpu_percent}% used, {'Offline mode' if offline_mode else 'Online mode'}, Internet: {'Available' if internet_available else 'Not available'}"
                    context_parts.append(system_str)

            # Add personality information (only for Gemini)
            if model_type == "gemini" and "personality" in context and context["personality"]:
                personality = context["personality"]

                # Add mood
                if "mood" in personality and personality["mood"]:
                    mood = personality["mood"]
                    mood_str = f"Current mood: {mood.get('mood', 'neutral')}, Energy: {mood.get('energy_level', 0.5)}"
                    context_parts.append(mood_str)

            # Join all context parts
            formatted_context = "\n\n".join(context_parts)

            return formatted_context

        except Exception as e:
            logger.error(f"Error formatting context for model {model_type}: {str(e)}")
            return "Error formatting context"
