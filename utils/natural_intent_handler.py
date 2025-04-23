"""
Natural Intent Handler for General Pulse

This module provides an enhanced intent classification system that combines:
1. MiniLM for command detection (fast, efficient, works offline)
2. Mistral-Small for free-form analysis (when online)
3. Phi-2 for offline fallback (via Ollama)

This hybrid approach allows for both structured command handling and natural
conversation, with graceful degradation when offline.
"""

import os
import re
import json
import asyncio
import structlog
from typing import Dict, Any, Optional, List, Tuple
import time

# Import the base intent handler
from utils.intent_handler import IntentHandler

# Import the MiniLM classifier
from utils.minilm_classifier import MiniLMClassifier, classify_intent, classify_intent_detailed

# Import the optimized model interface
from skills.optimized_model_interface import OptimizedModelInterface

# Configure logger
logger = structlog.get_logger("natural_intent_handler")

class NaturalIntentHandler(IntentHandler):
    """
    Enhanced intent handler that combines MiniLM, Mistral-Small, and Phi-2 for better
    natural language understanding.
    """

    def __init__(self, keywords_path="models/keyword_classifier/keywords.json"):
        """
        Initialize the natural intent handler

        Args:
            keywords_path: Path to keywords file
        """
        # Initialize the base intent handler
        super().__init__(keywords_path)

        # Set confidence thresholds
        self.minilm_threshold = 0.65  # Default threshold for MiniLM
        self.phi_threshold = 0.60     # Default threshold for Phi-2 (slightly lower due to local model limitations)

        # Track system load to dynamically adjust thresholds
        self.last_memory_check = 0
        self.memory_check_interval = 60  # seconds
        self.system_load = 0.5  # Default medium load

        # Cache for Mistral-Small intent classifications to reduce API calls
        self.intent_cache = {}
        self.cache_ttl = 3600  # 1 hour cache lifetime

        logger.info("Natural intent handler initialized")

    async def _adjust_thresholds_based_on_load(self):
        """
        Dynamically adjust confidence thresholds based on system load
        Lower thresholds when system is under heavy load to reduce API calls
        """
        current_time = time.time()

        # Only check memory usage periodically to avoid overhead
        if current_time - self.last_memory_check > self.memory_check_interval:
            try:
                # Get system memory info
                import psutil
                memory = psutil.virtual_memory()
                memory_percent = memory.percent / 100.0

                # Calculate system load (0.0 to 1.0)
                self.system_load = memory_percent

                # Adjust thresholds based on load
                if self.system_load > 0.8:  # High load
                    self.minilm_threshold = 0.55  # Lower threshold to reduce API calls
                    self.phi_threshold = 0.50
                    logger.info(f"System under high load ({self.system_load:.2f}), lowered thresholds")
                elif self.system_load > 0.6:  # Medium load
                    self.minilm_threshold = 0.60
                    self.phi_threshold = 0.55
                    logger.info(f"System under medium load ({self.system_load:.2f}), using standard thresholds")
                else:  # Low load
                    self.minilm_threshold = 0.65  # Higher threshold for better accuracy
                    self.phi_threshold = 0.60
                    logger.info(f"System under low load ({self.system_load:.2f}), using higher thresholds")

                self.last_memory_check = current_time

            except ImportError:
                logger.warning("psutil not available, using default thresholds")
            except Exception as e:
                logger.error(f"Error adjusting thresholds: {str(e)}")

    async def _check_internet(self):
        """
        Check if internet connection is available

        Returns:
            bool: True if internet is available, False otherwise
        """
        try:
            # Use the model interface's internet check
            return await self.model_interface.check_internet()
        except Exception as e:
            logger.error(f"Error checking internet: {str(e)}")
            return False

    async def _classify_with_mistral(self, text: str) -> Optional[str]:
        """
        Classify intent using Mistral-Small API

        Args:
            text: Text to classify

        Returns:
            Intent string or None if classification failed
        """
        # Check if we have a cached result
        cache_key = text.lower().strip()
        if cache_key in self.intent_cache:
            cached_result = self.intent_cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_result["timestamp"] < self.cache_ttl:
                logger.info(f"Using cached Mistral classification for '{text[:30]}...'")
                return cached_result["intent"]

        # Check internet connection
        internet_available = await self._check_internet()
        if not internet_available:
            logger.warning("No internet connection for Mistral-Small classification")
            return None

        try:
            # Prepare the prompt for Mistral-Small (main brain)
            # This prompt uses the "Mistral-Small as a judge" pattern for better classification
            prompt = f"""INTENT CLASSIFICATION TASK:

User query: "{text}"

Classify this query into EXACTLY ONE of the following intents:
- time (time/date queries)
- task (todo/task management)
- github (GitHub related)
- notion (Notion related)
- ai_query (direct questions to AI models)
- system (system commands, help, status)
- personality (personality adjustments)
- memory (memory operations)
- ollama (offline mode, local models)
- code (coding assistance)
- debug (debugging help)
- troubleshoot (troubleshooting)
- docs (documentation)
- explain (explanations)
- trends (market/tech trends)
- content (content creation)
- technical (technical content)
- brainstorm (idea generation)
- ethics (ethical questions)
- automate (automation)
- visual (visual/design)
- reasoning (complex reasoning)
- math (mathematics)
- chemistry (chemistry)
- general (general conversation)

Respond with ONLY the intent name, nothing else.
"""

            # Call Mistral-Small API via OpenRouter
            response = await self.model_interface.call_openrouter(
                model_id="mistralai/mistral-small-3.1-24b-instruct:free",
                query=prompt,
                max_tokens=50  # Short response needed
            )

            if response and response.get("success", False):
                # Extract the intent from the response
                content = response.get("content", "").strip().lower()

                # Extract just the intent name (first word)
                intent = content.split()[0].strip()

                # Validate the intent
                valid_intents = [
                    "time", "task", "github", "notion", "ai_query", "system",
                    "personality", "memory", "ollama", "code", "debug",
                    "troubleshoot", "docs", "explain", "trends", "content",
                    "technical", "brainstorm", "ethics", "automate", "visual",
                    "reasoning", "math", "chemistry", "general"
                ]

                if intent in valid_intents:
                    # Cache the result
                    self.intent_cache[cache_key] = {
                        "intent": intent,
                        "timestamp": time.time()
                    }

                    logger.info(f"MiniLM classified '{text[:30]}...' as '{intent}'")
                    return intent
                else:
                    logger.warning(f"MiniLM returned invalid intent: '{content}'")
                    return "general"
            else:
                error = response.get("error", "Unknown error")
                logger.error(f"MiniLM classification failed: {error}")
                return None

        except Exception as e:
            logger.error(f"Error during MiniLM classification: {str(e)}")
            return None

    async def _classify_with_phi(self, text: str) -> Optional[str]:
        """
        Classify intent using Phi-2 via Ollama (offline fallback)

        Args:
            text: Text to classify

        Returns:
            Intent string or None if classification failed
        """
        try:
            # Check if Ollama is running
            status = await self.model_interface.check_status()
            ollama_running = status.get("ollama", {}).get("running", False)

            if not ollama_running:
                # Try to start Ollama
                start_result = await self.model_interface.manage_ollama(ensure_running=True)
                if not start_result:
                    logger.error("Failed to start Ollama for Phi classification")
                    return None

            # Prepare the prompt for Phi-2
            prompt = f"""TASK: Classify the following user query into exactly one intent category.

USER QUERY: "{text}"

AVAILABLE INTENTS:
- time (time/date queries)
- task (todo/task management)
- github (GitHub related)
- notion (Notion related)
- ai_query (direct questions to AI models)
- system (system commands, help, status)
- personality (personality adjustments)
- memory (memory operations)
- ollama (offline mode, local models)
- code (coding assistance)
- debug (debugging help)
- troubleshoot (troubleshooting)
- docs (documentation)
- explain (explanations)
- trends (market/tech trends)
- content (content creation)
- technical (technical content)
- brainstorm (idea generation)
- ethics (ethical questions)
- automate (automation)
- visual (visual/design)
- reasoning (complex reasoning)
- math (mathematics)
- chemistry (chemistry)
- general (general conversation)

RESPOND WITH ONLY THE INTENT NAME, NOTHING ELSE.
"""

            # Call Phi-2 via Ollama
            response = await self.model_interface.call_ollama(
                model_name="phi",
                query=prompt,
                max_tokens=50  # Short response needed
            )

            if response and response.get("success", False):
                # Extract the intent from the response
                content = response.get("content", "").strip().lower()

                # Extract just the intent name (first word)
                intent = content.split()[0].strip()

                # Validate the intent
                valid_intents = [
                    "time", "task", "github", "notion", "ai_query", "system",
                    "personality", "memory", "ollama", "code", "debug",
                    "troubleshoot", "docs", "explain", "trends", "content",
                    "technical", "brainstorm", "ethics", "automate", "visual",
                    "reasoning", "math", "chemistry", "general"
                ]

                if intent in valid_intents:
                    logger.info(f"Phi classified '{text[:30]}...' as '{intent}'")
                    return intent
                else:
                    logger.warning(f"Phi returned invalid intent: '{content}'")
                    return "general"
            else:
                error = response.get("error", "Unknown error")
                logger.error(f"Phi classification failed: {error}")
                return None

        except Exception as e:
            logger.error(f"Error during Phi classification: {str(e)}")
            return None

    async def classify(self, text):
        """
        Classify the intent of a text using the hybrid approach

        Args:
            text: Text to classify

        Returns:
            Intent string
        """
        try:
            # Adjust thresholds based on system load
            await self._adjust_thresholds_based_on_load()

            # First, check for explicit command patterns (highest priority)
            # These are the same patterns from the base IntentHandler

            # Check for model query pattern
            if re.search(r"^\s*(?:ask|query|use)\s+\w+\s+", text, re.IGNORECASE):
                self.logger.info(f"Detected model query pattern in '{text}', classifying as 'ai_query'")
                return "ai_query"

            # Check for CLI UI patterns
            if re.search(r"^\s*(?:launch|open|show|display|start)\s+(?:cli|ui|dashboard|interface)", text, re.IGNORECASE):
                self.logger.info(f"Detected CLI UI pattern in '{text}', classifying as 'system'")
                return "system"

            # Check for memory patterns
            if re.search(r"^\s*(?:search|save to|recall|show recent|show|get)\s+(?:memory|memories)", text, re.IGNORECASE):
                self.logger.info(f"Detected memory pattern in '{text}', classifying as 'memory'")
                return "memory"

            # Check for personality patterns
            if re.search(r"^\s*(?:show|adjust)\s+personality", text, re.IGNORECASE):
                self.logger.info(f"Detected personality pattern in '{text}', classifying as 'personality'")
                return "personality"

            # Check for system status patterns
            if re.search(r"^\s*(?:show|display|get)\s+(?:system|status)", text, re.IGNORECASE) or \
               re.search(r"^\s*system\s+(?:status|info|health)", text, re.IGNORECASE):
                self.logger.info(f"Detected system status pattern in '{text}', classifying as 'system'")
                return "system"

            # Check for Ollama commands
            if re.search(r"^\s*ollama\s+(on|off|status|pull)", text, re.IGNORECASE) or \
               re.search(r"^\s*(?:enable|disable|toggle)\s+offline\s+mode", text, re.IGNORECASE):
                self.logger.info(f"Detected Ollama command in '{text}', classifying as 'ollama'")
                return "ollama"

            # Get system status
            status = await self.model_interface.check_status()
            offline_mode = status.get("offline_mode", False)
            ollama_running = status.get("ollama", {}).get("running", False)

            # STEP 1: Try MiniLM first (fast, efficient, works offline)
            if self.use_minilm:
                # Use MiniLM for intent classification with adjusted threshold
                result = self.minilm_classifier.classify_detailed(text)
                intent = result["intent"]
                confidence = result["confidence"]

                # If confidence is high enough, use the MiniLM result
                if confidence >= self.minilm_threshold:
                    # Map MiniLM intents to our intents (same as in base class)
                    intent_mapping = {
                        # System commands
                        "status": "system",
                        "help": "system",
                        "version": "system",
                        "exit": "system",

                        # Model commands
                        "ask_model": "ai_query",
                        "test_model": "system",

                        # Ollama commands
                        "ollama_status": "ollama",
                        "ollama_start": "ollama",
                        "ollama_stop": "ollama",
                        "ollama_pull": "ollama",

                        # Mode commands
                        "enable_offline": "ollama",
                        "disable_offline": "ollama",
                        "toggle_debug": "system",

                        # Query types
                        "code": "code",
                        "debug": "debug",
                        "brainstorm": "brainstorm",
                        "document": "docs",
                        "automate": "automate",
                        "content": "content",
                        "trends": "trends",
                        "ethics": "ethics",

                        # Tool commands
                        "github": "github",
                        "notion": "notion",
                        "search": "ai_query",

                        # General conversation
                        "greeting": "general",
                        "general": "general"
                    }

                    # Map the intent
                    mapped_intent = intent_mapping.get(intent, "general")

                    self.logger.info(f"MiniLM classified '{text[:30]}...' as '{intent}' (mapped to '{mapped_intent}') with confidence {confidence:.4f}")
                    return mapped_intent

            # STEP 2: If online, try Mistral-Small (main brain) for natural language understanding
            if not offline_mode and await self._check_internet():
                mistral_intent = await self._classify_with_mistral(text)
                if mistral_intent:
                    return mistral_intent

            # STEP 3: If offline or Mistral-Small failed, try Phi-2 via Ollama
            if offline_mode or ollama_running:
                phi_intent = await self._classify_with_phi(text)
                if phi_intent:
                    return phi_intent

            # STEP 4: Fall back to the base implementation if all else fails
            return await super().classify(text)

        except Exception as e:
            self.logger.error(f"Error during hybrid classification: {str(e)}")
            # Fall back to the base implementation
            return await super().classify(text)
