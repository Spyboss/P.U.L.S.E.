"""
Query Preprocessor for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides improved intent recognition and fallback mechanisms
"""

import os
import re
import asyncio
import structlog
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import httpx

# Configure logger
logger = structlog.get_logger("intent_preprocessor")

class QueryPreprocessor:
    """
    Preprocesses user queries for improved intent recognition
    Features:
    - Pattern-based intent detection
    - Query normalization and cleaning
    - Fallback mechanisms for model failures
    - Intent classification with MiniLM
    """

    def __init__(self, minilm_classifier=None):
        """
        Initialize the query preprocessor

        Args:
            minilm_classifier: Optional MiniLM classifier for intent recognition
        """
        self.logger = logger
        self.minilm_classifier = minilm_classifier

        # Initialize patterns
        self.command_patterns = self._init_command_patterns()
        self.intent_patterns = self._init_intent_patterns()

        # Track recent failures for adaptive routing
        self.recent_failures = {}
        self.max_failures = 3
        self.failure_window = 300  # 5 minutes

        logger.info("Query preprocessor initialized")

    def _init_command_patterns(self) -> Dict[str, re.Pattern]:
        """
        Initialize command patterns for quick commands to be handled by MiniLM

        Returns:
            Dictionary of command patterns
        """
        patterns = {
            # One-word commands (highest priority for MiniLM)
            "help": re.compile(r"^help$|^help me$|^show help$", re.IGNORECASE),
            "status": re.compile(r"^status$|^system status$|^show status$", re.IGNORECASE),
            "exit": re.compile(r"^exit$|^quit$|^bye$", re.IGNORECASE),
            "memory": re.compile(r"^memory$|^show memory$|^list memory$", re.IGNORECASE),
            "dashboard": re.compile(r"^dashboard$", re.IGNORECASE),
            "version": re.compile(r"^version$", re.IGNORECASE),
            "test": re.compile(r"^test$", re.IGNORECASE),
            "clear": re.compile(r"^clear$|^cls$", re.IGNORECASE),
            "ollama": re.compile(r"^ollama$", re.IGNORECASE),

            # System commands (to be handled by MiniLM)
            "show_status": re.compile(r"^(?:show|display|get)\s+(?:system\s+)?status$", re.IGNORECASE),
            "show_dashboard": re.compile(r"^(?:show|display|open)\s+dashboard$", re.IGNORECASE),
            "show_help": re.compile(r"^(?:show|display|get)\s+help$", re.IGNORECASE),
            "show_memory": re.compile(r"^(?:show|display|get)\s+(?:my\s+)?memor(?:y|ies)$", re.IGNORECASE),
            "show_version": re.compile(r"^(?:show|display|get)\s+version$", re.IGNORECASE),
            "show_config": re.compile(r"^(?:show|display|get)\s+config(?:uration)?$", re.IGNORECASE),
            "show_skills": re.compile(r"^(?:show|display|get|list)\s+skills$", re.IGNORECASE),

            # Memory commands
            "search_memory": re.compile(r"^search memory (.+)$", re.IGNORECASE),
            "save_memory": re.compile(r"^save to memory (.+)$|^remember (.+)$", re.IGNORECASE),
            "clear_memory": re.compile(r"^clear memory$|^forget everything$", re.IGNORECASE),
            "chat_history": re.compile(r"^chat history$|^show chat history$|^history$|^show history$", re.IGNORECASE),
            "chat_history_limit": re.compile(r"^chat history (\d+)$|^show chat history (\d+)$|^history (\d+)$", re.IGNORECASE),

            # Goal commands
            "add_goal": re.compile(r"^add goal (.+)$|^new goal (.+)$", re.IGNORECASE),
            "list_goals": re.compile(r"^list goals$|^show goals$|^goals$", re.IGNORECASE),
            "complete_goal": re.compile(r"^complete goal (.+)$|^finish goal (.+)$", re.IGNORECASE),
            "delete_goal": re.compile(r"^delete goal (.+)$|^remove goal (.+)$", re.IGNORECASE),

            # Ollama commands
            "ollama_status": re.compile(r"^ollama status$", re.IGNORECASE),
            "ollama_on": re.compile(r"^ollama on$", re.IGNORECASE),
            "ollama_off": re.compile(r"^ollama off$", re.IGNORECASE),
            "enable_offline": re.compile(r"^enable offline mode$", re.IGNORECASE),
            "disable_offline": re.compile(r"^disable offline mode$", re.IGNORECASE),

            # Test commands
            "test_intent": re.compile(r"^test intent (.+)$", re.IGNORECASE),
            "test_model": re.compile(r"^test (.+?) (.+)$", re.IGNORECASE)
        }

        return patterns

    def _init_intent_patterns(self) -> Dict[str, re.Pattern]:
        """
        Initialize intent patterns

        Returns:
            Dictionary of intent patterns
        """
        patterns = {
            "code": re.compile(r"^ask code (.+)$|^code (.+)$", re.IGNORECASE),
            "debug": re.compile(r"^ask debug (.+)$|^debug (.+)$", re.IGNORECASE),
            "algorithm": re.compile(r"^ask algorithm (.+)$|^algorithm (.+)$", re.IGNORECASE),
            "docs": re.compile(r"^ask docs (.+)$|^docs (.+)$", re.IGNORECASE),
            "explain": re.compile(r"^ask explain (.+)$|^explain (.+)$", re.IGNORECASE),
            "summarize": re.compile(r"^ask summarize (.+)$|^summarize (.+)$", re.IGNORECASE),
            "troubleshoot": re.compile(r"^ask troubleshoot (.+)$|^troubleshoot (.+)$", re.IGNORECASE),
            "solve": re.compile(r"^ask solve (.+)$|^solve (.+)$", re.IGNORECASE),
            "trends": re.compile(r"^ask trends (.+)$|^trends (.+)$", re.IGNORECASE),
            "research": re.compile(r"^ask research (.+)$|^research (.+)$", re.IGNORECASE),
            "content": re.compile(r"^ask content (.+)$|^content (.+)$", re.IGNORECASE),
            "creative": re.compile(r"^ask creative (.+)$|^creative (.+)$", re.IGNORECASE),
            "write": re.compile(r"^ask write (.+)$|^write (.+)$", re.IGNORECASE),
            "technical": re.compile(r"^ask technical (.+)$|^technical (.+)$", re.IGNORECASE),
            "math": re.compile(r"^ask math (.+)$|^math (.+)$", re.IGNORECASE),
            "brainstorm": re.compile(r"^ask brainstorm (.+)$|^brainstorm (.+)$", re.IGNORECASE),
            "ideas": re.compile(r"^ask ideas (.+)$|^ideas (.+)$", re.IGNORECASE),
            "ethics": re.compile(r"^ask ethics (.+)$|^ethics (.+)$", re.IGNORECASE)
        }

        return patterns

    async def preprocess_query(self, query: str) -> Dict[str, Any]:
        """
        Preprocess a user query

        Args:
            query: User query

        Returns:
            Preprocessed query information
        """
        # Clean the query
        clean_query = self._clean_query(query)

        # Check for commands
        command_result = self._check_command_patterns(clean_query)
        if command_result:
            return {
                "type": "command",
                "command": command_result["command"],
                "args": command_result.get("args"),
                "original_query": query,
                "clean_query": clean_query
            }

        # Check for intent patterns
        intent_result = self._check_intent_patterns(clean_query)
        if intent_result:
            return {
                "type": "intent",
                "intent": intent_result["intent"],
                "query": intent_result.get("query", clean_query),
                "original_query": query,
                "clean_query": clean_query
            }

        # Use MiniLM for intent classification
        if self.minilm_classifier:
            try:
                intent_result = await self.minilm_classifier.classify_intent(clean_query)
                if intent_result["success"]:
                    return {
                        "type": "intent",
                        "intent": intent_result["intent"],
                        "confidence": intent_result.get("confidence", 0.0),
                        "query": clean_query,
                        "original_query": query,
                        "clean_query": clean_query
                    }
            except Exception as e:
                logger.error(f"Error classifying intent with MiniLM: {str(e)}")

        # Default to general intent
        return {
            "type": "intent",
            "intent": "general",
            "query": clean_query,
            "original_query": query,
            "clean_query": clean_query
        }

    def _clean_query(self, query: str) -> str:
        """
        Clean a user query

        Args:
            query: User query

        Returns:
            Cleaned query
        """
        # Remove extra whitespace
        clean = query.strip()
        clean = re.sub(r'\s+', ' ', clean)

        # Remove common filler words at the beginning
        filler_words = [
            "hey", "hi", "hello", "um", "uh", "er", "ah", "like", "so", "well",
            "actually", "basically", "literally", "please", "could you", "can you"
        ]

        for word in filler_words:
            pattern = f"^{word}\\s+"
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)

        return clean

    def _check_command_patterns(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if a query matches any command patterns

        Args:
            query: User query

        Returns:
            Command information or None if no match
        """
        for command, pattern in self.command_patterns.items():
            match = pattern.match(query)
            if match:
                # Extract arguments if any
                args = None
                if match.groups():
                    # Special case for chat_history_limit
                    if command == "chat_history_limit":
                        # Find the first non-None group (could be in different positions)
                        for group in match.groups():
                            if group is not None:
                                args = group
                                break
                        # Convert to chat_history command with args
                        command = "chat_history"
                    else:
                        args = match.group(1)

                return {
                    "command": command,
                    "args": args
                }

        return None

    def _check_intent_patterns(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if a query matches any intent patterns

        Args:
            query: User query

        Returns:
            Intent information or None if no match
        """
        # Debug: Print the query and all intent patterns
        self.logger.debug(f"Checking intent patterns for query: {query}")
        self.logger.debug(f"Intent patterns: {list(self.intent_patterns.keys())}")

        for intent, pattern in self.intent_patterns.items():
            match = pattern.match(query)
            if match:
                # Extract the actual query
                intent_query = None
                if match.groups():
                    intent_query = match.group(1)

                self.logger.info(f"Matched intent pattern '{intent}' with query: {intent_query}")

                # Important: For specialized model routing, keep the original "ask X" format
                # This ensures the neural router can detect the specialized model
                if intent in ["code", "debug", "algorithm", "docs", "explain", "summarize",
                             "troubleshoot", "solve", "trends", "research", "content",
                             "creative", "write", "technical", "math", "brainstorm",
                             "ideas", "ethics"]:
                    self.logger.info(f"Preserving 'ask {intent}' format for specialized routing")
                    return {
                        "intent": intent,
                        "query": query  # Keep the original query with "ask X" format
                    }
                else:
                    return {
                        "intent": intent,
                        "query": intent_query
                    }

        return None

    async def handle_model_failure(self, model: str, error: str) -> Dict[str, Any]:
        """
        Handle a model failure

        Args:
            model: Model name
            error: Error message

        Returns:
            Fallback information
        """
        # Record the failure
        current_time = datetime.utcnow().timestamp()

        if model not in self.recent_failures:
            self.recent_failures[model] = []

        # Add the failure
        self.recent_failures[model].append({
            "time": current_time,
            "error": error
        })

        # Remove old failures
        self.recent_failures[model] = [
            f for f in self.recent_failures[model]
            if current_time - f["time"] < self.failure_window
        ]

        # Check if we've exceeded the failure threshold
        failure_count = len(self.recent_failures[model])

        if failure_count >= self.max_failures:
            logger.warning(f"Model {model} has failed {failure_count} times in the last {self.failure_window} seconds")

            # Determine fallback model
            if model.lower() == "mistral" or model.lower() == "mistral-small":
                fallback_model = "minilm"
                fallback_provider = "local"
            else:
                fallback_model = "mistral-small"
                fallback_provider = "openrouter"

            return {
                "fallback_required": True,
                "failed_model": model,
                "fallback_model": fallback_model,
                "fallback_provider": fallback_provider,
                "failure_count": failure_count,
                "error": error
            }

        return {
            "fallback_required": False,
            "failed_model": model,
            "failure_count": failure_count,
            "error": error
        }

    async def check_internet_connection(self) -> bool:
        """
        Check if internet connection is available

        Returns:
            True if internet is available, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://www.google.com", timeout=2.0)
                return response.status_code == 200
        except:
            return False
