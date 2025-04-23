import os
import json
import re
import asyncio
import structlog
from difflib import SequenceMatcher
from typing import Dict, Any, Optional

# Import the MiniLM classifier (replacing DistilBERT for better performance on low-spec hardware)
from utils.minilm_classifier import MiniLMClassifier

# DistilBERT classifier is disabled to save memory

# Import the optimized model interface
from skills.optimized_model_interface import OptimizedModelInterface

# Configure logger
logger = structlog.get_logger("intent_handler")

class IntentHandler:
    def __init__(self, keywords_path="models/keyword_classifier/keywords.json"):
        self.logger = logger
        self.keywords_path = keywords_path

        # Initialize optimized model interface
        self.model_interface = OptimizedModelInterface()

        # Initialize MiniLM classifier (primary)
        try:
            self.minilm_classifier = MiniLMClassifier()
            self.use_minilm = True
            self.logger.info("MiniLM classifier initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize MiniLM classifier: {str(e)}")
            self.use_minilm = False

        # Disable DistilBERT classifier to save memory
        self.use_distilbert = False
        self.distilbert_classifier = None
        self.logger.info("DistilBERT classifier disabled to save memory")

        # Check if keywords file exists
        if not os.path.exists(keywords_path):
            self.logger.warning(f"Keywords file not found at {keywords_path}, using default keywords")
            self._init_default_keywords()
        else:
            self.logger.info(f"Loading keywords from {keywords_path}")
            self._init_from_file()

        # Add common stopwords to ignore
        self.stopwords = set([
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "i", "you", "he", "she", "it", "we", "they", "my", "your",
            "his", "her", "its", "our", "their", "me", "him", "us", "them"
        ])

    def _init_from_file(self):
        try:
            # Load keywords
            with open(self.keywords_path, "r", encoding="utf-8") as f:
                self.keywords = json.load(f)

            self.logger.info(f"Loaded {len(self.keywords)} intents from keywords file")
        except Exception as e:
            self.logger.error(f"Error loading keywords: {e}")
            self._init_default_keywords()

    async def classify_with_minilm(self, text):
        """
        Classify the intent of a text using MiniLM

        Args:
            text: Text to classify

        Returns:
            Intent string
        """
        try:
            # Use the MiniLM classifier
            result = self.minilm_classifier.classify_detailed(text)
            intent = result["intent"]
            confidence = result["confidence"]

            # Map MiniLM intents to our intents
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
                "code": "ai_query",
                "debug": "ai_query",
                "brainstorm": "ai_query",
                "document": "ai_query",
                "automate": "ai_query",
                "content": "ai_query",
                "trends": "ai_query",
                "ethics": "ai_query",

                # Tool commands
                "github": "github",
                "notion": "notion",
                "search": "ai_query",

                # General conversation
                "greeting": "chat",
                "general": "chat"
            }

            # Map the intent
            mapped_intent = intent_mapping.get(intent, "other")

            self.logger.info(f"MiniLM classified '{text}' as '{intent}' (mapped to '{mapped_intent}') with confidence {confidence:.4f}")
            return mapped_intent

        except Exception as e:
            self.logger.error(f"Error during MiniLM classification: {str(e)}")
            return None

    async def classify_with_distilbert(self, text):
        """
        Classify the intent of a text using DistilBERT (fallback classifier)

        Args:
            text: Text to classify

        Returns:
            Intent string
        """
        try:
            # Use the DistilBERT classifier
            result = await self.distilbert_classifier.classify_intent(text)

            if result["success"]:
                intent = result["intent"]
                confidence = result.get("confidence", 0.0)

                # Map DistilBERT intents to our intents
                intent_mapping = {
                    "code": "ai_query",
                    "debug": "ai_query",
                    "algorithm": "ai_query",
                    "docs": "ai_query",
                    "explain": "ai_query",
                    "summarize": "ai_query",
                    "troubleshoot": "ai_query",
                    "solve": "ai_query",
                    "trends": "ai_query",
                    "research": "ai_query",
                    "content": "ai_query",
                    "creative": "ai_query",
                    "write": "ai_query",
                    "technical": "ai_query",
                    "math": "ai_query",
                    "brainstorm": "ai_query",
                    "ideas": "ai_query",
                    "ethics": "ai_query",
                    "visual": "ai_query",
                    "reasoning": "ai_query",
                    "general": "ai_query",
                    "time": "time",
                    "reminder": "task",
                    "goal": "task",
                    "model": "ai_query",
                    "memory": "memory",
                    "personality": "personality",
                    "cli_ui": "system",
                    "ollama": "ollama"
                }

                # Map the intent
                mapped_intent = intent_mapping.get(intent, "other")

                self.logger.info(f"DistilBERT classified '{text}' as '{intent}' (mapped to '{mapped_intent}') with confidence {confidence}")
                return mapped_intent
            else:
                self.logger.warning(f"DistilBERT classification failed: {result.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            self.logger.error(f"Error during DistilBERT classification: {str(e)}")
            return None

    def _init_default_keywords(self):
        # Default keywords for each intent
        self.keywords = {
            "task": ["task", "todo", "to-do", "to do", "list", "add", "create", "show", "display", "update", "edit", "complete", "finish", "goal", "goals"],
            "time": ["time", "date", "day", "hour", "minute", "today", "tomorrow", "yesterday", "timezone", "clock"],
            "github": ["github", "repo", "repository", "commit", "issue", "pull request", "pr", "branch", "merge", "code"],
            "notion": ["notion", "document", "page", "journal", "entry", "note", "notes"],
            "ai_query": ["ask", "query", "claude", "grok", "deepseek", "gemini", "ai", "model", "question", "llama", "mistral", "openai", "gpt", "anthropic", "openrouter", "main_brain"],
            "system": ["help", "exit", "quit", "stop", "restart", "system", "status", "cli", "ui", "dashboard", "interface", "launch", "open", "start", "vitals", "health", "check"],
            "personality": ["personality", "trait", "traits", "adjust", "character", "mood", "style", "tone", "show personality"],
            "memory": ["memory", "remember", "recall", "forget", "search", "save", "store"],
            "ollama": ["ollama", "offline", "local", "toggle", "status", "on", "off", "enable", "disable"]
        }
        self.logger.info("Using default keywords")

    def _similarity(self, a, b):
        """Calculate string similarity using SequenceMatcher"""
        return SequenceMatcher(None, a, b).ratio()

    def _get_fuzzy_matches(self, word, keywords, threshold=0.8):
        """Find fuzzy matches for a word in keywords"""
        matches = []
        for keyword in keywords:
            similarity = self._similarity(word, keyword)
            if similarity >= threshold:
                matches.append((keyword, similarity))
        return matches

    async def classify(self, text):
        try:
            # Check for model query pattern first (highest priority)
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

            # Check if we should use MiniLM or DistilBERT
            # Get Ollama status from model interface
            status = await self.model_interface.check_status()

            # First try MiniLM if available (preferred for low-spec hardware)
            if self.use_minilm:
                # Use MiniLM for intent classification
                minilm_intent = await self.classify_with_minilm(text)
                if minilm_intent:
                    return minilm_intent

            # Fall back to DistilBERT if MiniLM failed or isn't available
            # Use DistilBERT if it's available and either offline mode is enabled or Ollama is running
            if self.use_distilbert and (status.get("offline_mode", False) or status.get("ollama", {}).get("running", False)):
                # Use DistilBERT for intent classification
                distilbert_intent = await self.classify_with_distilbert(text)
                if distilbert_intent:
                    return distilbert_intent

            # Fallback to keyword-based classification
            # Preprocess text
            text = text.lower().strip()

            # Tokenize text
            words = set(re.findall(r'\b\w+\b', text))

            # Remove stopwords
            words = words - self.stopwords

            # Calculate score for each intent
            scores = {}
            for intent, intent_keywords in self.keywords.items():
                # Count exact matching keywords
                exact_matches = words.intersection(intent_keywords)

                # Find fuzzy matches for words that didn't have exact matches
                fuzzy_matches = []
                for word in words - exact_matches:
                    # Only consider words with length >= 3 for fuzzy matching to avoid false positives
                    if len(word) >= 3:
                        matches = self._get_fuzzy_matches(word, intent_keywords)
                        fuzzy_matches.extend(matches)

                # Calculate score: exact matches count as 1, fuzzy matches count based on similarity
                score = len(exact_matches) + sum(similarity for _, similarity in fuzzy_matches)

                # Prioritize ai_query intent for model-related queries
                if intent == "ai_query" and any(model in text for model in ["main_brain", "gemini", "claude", "deepseek", "grok", "llama", "mistral"]):
                    score += 3.0  # Highest boost for model queries
                # Prioritize memory intent for memory-related queries
                elif intent == "memory" and any(word in text for word in ["memory", "remember", "recall", "search", "save"]):
                    score += 3.0  # Highest boost for memory queries
                # Prioritize personality intent for personality-related queries
                elif intent == "personality" and any(word in text for word in ["personality", "trait", "adjust", "show"]):
                    score += 3.0  # Highest boost for personality queries
                # Prioritize task intent for ambiguous cases
                elif intent == "task" and score > 0:
                    score += 2.0  # Boost for task intent
                # Prioritize time intent for date-related queries
                elif intent == "time" and "date" in text:
                    score += 2.0  # Boost for time intent
                # Prioritize notion intent for document-related queries
                elif intent == "notion" and ("document" in text or "doc" in text):
                    score += 2.0  # Boost for notion intent
                # Prioritize ollama intent for offline-related queries
                elif intent == "ollama" and any(word in text for word in ["ollama", "offline", "local"]):
                    score += 3.0  # Highest boost for ollama queries

                scores[intent] = score

            # Get the intent with the highest score
            if any(scores.values()):
                max_intent = max(scores.items(), key=lambda x: x[1])[0]
                self.logger.info(f"Classified '{text}' as '{max_intent}' with scores {scores}")
                return max_intent
            else:
                self.logger.info(f"No keywords matched for '{text}', defaulting to 'other'")
                return "other"
        except Exception as e:
            self.logger.error(f"Error during classification: {e}")
            return "other"

    async def get_model_for_intent(self, intent, command=None):
        """
        Get the appropriate model for an intent

        Args:
            intent: The intent to route
            command: Optional command parameters

        Returns:
            Model name to use
        """
        # Get system status to check if we're in offline mode
        status = await self.model_interface.check_status()
        offline_mode = status.get("offline_mode", False)
        ollama_running = status.get("ollama", {}).get("running", False)
        internet_available = status.get("internet_available", True)

        # Default model is main_brain for online mode, Phi for offline mode
        # Only use Phi if explicitly in offline mode or if internet is not available
        # For simple greetings, always try to use main_brain if internet is available
        is_greeting = intent == "greeting" or (command and command.get("query", "").lower().strip() in ["hi", "hello", "hey", "what's up", "how are you"])

        if is_greeting and internet_available:
            default_model = "main_brain"  # Always use main_brain for greetings if internet is available
        else:
            default_model = "phi" if offline_mode or (not internet_available and ollama_running) else "main_brain"

        # Intent to model mapping
        intent_model_map = {
            # General queries
            "time": "local",  # Time queries should always be handled locally
            "general": "main_brain" if internet_available else default_model, # Always use main_brain for general queries if online
            "chat": "main_brain" if internet_available else default_model,   # Always use main_brain for chat if online
            "other": default_model,   # Default model for unclassified queries

            # Debugging and troubleshooting
            "debug": "deepseek",  # DeepSeek for debugging
            "troubleshoot": "deepseek",  # DeepSeek for troubleshooting

            # Code and script related
            "code": "deepcoder",  # DeepCoder for code generation
            "script": "dolphin",  # Dolphin for script optimization
            "optimize": "dolphin",  # Dolphin for optimization

            # Documentation and explanation
            "docs": "llama-doc",  # Llama-Doc for documentation
            "explain": "llama-doc",  # Llama-Doc for explanations

            # Math and chemistry
            "math": "gemma",  # Gemma for math problems
            "chemistry": "gemma",  # Gemma for chemistry problems

            # Trends and research
            "trends": "mistral-small",  # Mistral-Small for trends
            "research": "mistral-small",  # Mistral-Small for research

            # Content creation
            "content": "maverick",  # Maverick for content creation
            "creative": "maverick",  # Maverick for creative writing

            # Technical content
            "technical": "llama-technical",  # Llama-Technical for technical content

            # Brainstorming and ideas
            "brainstorm": "hermes", # Hermes for brainstorming
            "ideas": "hermes",  # Hermes for idea generation

            # Ethics and values
            "ethics": "molmo",  # Molmo for ethical questions

            # Automation and workflows
            "automate": "mistralai",  # MistralAI for automation
            "workflow": "mistralai",  # MistralAI for workflows

            # Visual and design
            "visual": "kimi",  # Kimi for visual reasoning
            "design": "kimi",  # Kimi for design

            # Complex reasoning
            "reasoning": "nemotron",  # Nemotron for advanced reasoning
            "complex": "nemotron",  # Nemotron for complex problems

            # Offline mode
            "offline": "phi"  # Phi for offline mode
        }

        # If we're in offline mode, use local models only
        if offline_mode or ollama_running:
            # In offline mode, route everything through local models
            # Phi is our default local model
            return "phi"

        # Get the model for this intent
        model = intent_model_map.get(intent, default_model)

        # If a specific model was requested in the command, use that instead
        if command and "model_name" in command:
            requested_model = command["model_name"].lower()
            # Validate the requested model
            valid_models = [
                "main_brain",   # Main brain model
                "gemini",       # Legacy Direct API model
                "deepseek",     # Troubleshooting
                "deepcoder",    # Code generation
                "llama-doc",    # Documentation
                "mistral-small", # Trends
                "maverick",     # Content creation (renamed from llama-content)
                "llama-content", # Backward compatibility
                "llama-technical", # Technical content
                "hermes",       # Brainstorming
                "molmo",        # Ethical AI (renamed from olmo)
                "olmo",         # Backward compatibility
                "mistralai",    # Task automation
                "kimi",         # Visual reasoning
                "nemotron",     # Advanced reasoning
                "gemma",        # Math and chemistry
                "dolphin",      # Script optimization
                "phi"           # Local model
            ]
            if requested_model in valid_models:
                model = requested_model

        self.logger.info(f"Routing intent '{intent}' to model '{model}'")
        return model

    async def parse_command(self, text):
        """
        Parse a command from text and extract parameters

        Args:
            text: The text to parse

        Returns:
            Dictionary with command type and parameters, or None if no command recognized
        """
        try:
            # Check for specific command patterns first

            # Check for "launch cli ui" or similar commands
            if re.search(r"^\s*(?:launch|open|show|display|start)\s+(?:cli|ui|dashboard|interface)\s*$", text, re.IGNORECASE):
                self.logger.info("Detected CLI UI command")
                return {
                    "command_type": "cli_ui"
                }

            # Check for "show personality" command
            if re.search(r"^\s*show\s+personality\s*$", text, re.IGNORECASE):
                self.logger.info("Detected 'show personality' command")
                return {
                    "command_type": "personality",
                    "trait": None  # No specific trait, show all
                }

            # Check for "adjust [trait] to [value]" pattern
            adjust_match = re.search(r"adjust\s+(\w+)\s+to\s+([0-9.]+)", text, re.IGNORECASE)
            if adjust_match:
                trait = adjust_match.group(1).lower()
                try:
                    value = float(adjust_match.group(2))
                    # Clamp value between 0 and 1
                    value = max(0.0, min(1.0, value))
                except ValueError:
                    value = 0.5  # Default value

                self.logger.info(f"Detected personality adjustment: trait={trait}, value={value}")
                return {
                    "command_type": "personality",
                    "trait": trait,
                    "value": value
                }

            # Check for Ollama commands
            ollama_match = re.search(r"^\s*ollama\s+(on|off|status|pull)\s*(.*)$", text, re.IGNORECASE)
            if ollama_match:
                action = ollama_match.group(1).lower()
                model_name = ollama_match.group(2).strip() if action == "pull" else None
                self.logger.info(f"Detected Ollama command: action={action}, model={model_name}")
                return {
                    "command_type": "ollama",
                    "action": action,
                    "model": model_name
                }

            # Check for offline mode commands
            offline_match = re.search(r"^\s*(?:enable|disable|toggle)\s+offline\s+mode\s*$", text, re.IGNORECASE)
            if offline_match:
                if "enable" in text.lower():
                    action = "on"
                elif "disable" in text.lower():
                    action = "off"
                else:  # toggle
                    action = "toggle"

                self.logger.info(f"Detected offline mode command: action={action}")
                return {
                    "command_type": "ollama",
                    "action": action
                }

            # Check for test all command
            test_all_match = re.search(r"^\s*test\s+all\s*$", text, re.IGNORECASE)
            if test_all_match:
                self.logger.info("Detected test all command")
                return {
                    "command_type": "cli_ui",
                    "action": "test_all"
                }

            # Check for test main_brain command
            test_main_brain_match = re.search(r"^\s*test\s+main_brain\s*$", text, re.IGNORECASE)
            if test_main_brain_match:
                self.logger.info("Detected test main_brain command")
                return {
                    "command_type": "cli_ui",
                    "action": "test_main_brain"
                }

            # Check for legacy test gemini command (for backward compatibility)
            test_gemini_match = re.search(r"^\s*test\s+gemini\s*$", text, re.IGNORECASE)
            if test_gemini_match:
                self.logger.info("Detected test gemini command (redirecting to main_brain)")
                return {
                    "command_type": "cli_ui",
                    "action": "test_main_brain"
                }

            # Check for test intent command
            test_intent_match = re.search(r"^\s*test\s+intent\s+(.+)$", text, re.IGNORECASE)
            if test_intent_match:
                query = test_intent_match.group(1).strip()
                self.logger.info(f"Detected test intent command: query={query}")
                intent = await self.classify(query)
                return {
                    "command_type": "test_intent",
                    "query": query,
                    "intent": intent
                }

            # First, classify the intent
            intent = await self.classify(text)

            # Parse command based on intent
            command = None
            if intent == "time":
                command = self._parse_time_command(text)
            elif intent == "task":
                command = self._parse_task_command(text)
            elif intent == "github":
                command = self._parse_github_command(text)
            elif intent == "notion":
                command = self._parse_notion_command(text)
            elif intent == "ai_query":
                command = self._parse_ai_query_command(text)
            elif intent == "system":
                command = self._parse_system_command(text)
            elif intent == "personality":
                # Generic personality command if not caught by specific patterns above
                command = {
                    "command_type": "personality",
                    "trait": None  # No specific trait, show all
                }
            elif intent == "memory":
                command = self._parse_memory_command(text)
            elif intent == "ollama":
                command = self._parse_ollama_command(text)
            else:
                # For other intents, create a model query command
                model = await self.get_model_for_intent(intent)
                command = {
                    "command_type": "model",
                    "model_name": model,
                    "query": text,
                    "intent": intent
                }

            # If we have a command, add the intent and model information
            if command:
                # Add the intent to the command
                command["intent"] = intent

                # If the command doesn't specify a model, add the appropriate model
                if "model_name" not in command and command["command_type"] not in ["system", "personality", "ollama"]:
                    command["model_name"] = await self.get_model_for_intent(intent, command)

            return command
        except Exception as e:
            self.logger.error(f"Error parsing command: {e}")
            return None

    def _parse_time_command(self, text):
        """
        Parse time-related commands
        """
        # Extract location if present
        location_match = re.search(r"in\s+([\w\s]+)(?:\?|$)", text)
        location = location_match.group(1).strip() if location_match else "local"

        # Determine timezone based on location
        timezone = self._get_timezone_for_location(location)

        # Check if it's a date query
        is_date_query = any(word in text.lower() for word in ["date", "day", "today", "tomorrow", "yesterday"])

        return {
            "command_type": "time",
            "location": location,
            "timezone": timezone,
            "date_query": is_date_query
        }

    def _get_timezone_for_location(self, location):
        """
        Get timezone for a location

        Args:
            location: Location name

        Returns:
            Timezone string
        """
        # Common locations and their timezones
        timezone_map = {
            "local": "local",
            "new york": "EST",
            "los angeles": "PST",
            "london": "GMT",
            "paris": "CET",
            "tokyo": "JST",
            "sydney": "AEST",
            "beijing": "CST",
            "moscow": "MSK",
            "dubai": "GST",
            "singapore": "SGT",
            "hong kong": "HKT",
            "berlin": "CET",
            "rome": "CET",
            "madrid": "CET",
            "toronto": "EST",
            "vancouver": "PST",
            "chicago": "CST",
            "mexico city": "CST",
            "sao paulo": "BRT",
            "johannesburg": "SAST",
            "cairo": "EET",
            "istanbul": "TRT",
            "mumbai": "IST",
            "delhi": "IST",
            "bangkok": "ICT",
            "jakarta": "WIB",
            "seoul": "KST",
            "auckland": "NZST"
        }

        # Normalize location name
        location_lower = location.lower()

        # Check for exact match
        if location_lower in timezone_map:
            return timezone_map[location_lower]

        # Check for partial match
        for loc, tz in timezone_map.items():
            if loc in location_lower or location_lower in loc:
                return tz

        # Default to UTC if no match
        return "UTC"

    def _parse_task_command(self, text):
        """
        Parse task-related commands
        """
        # Default to list action
        action = "list"
        task_text = None
        priority = 1

        # Check for add/create action
        if any(word in text.lower() for word in ["add", "create", "new"]):
            action = "add"
            # Extract task text
            task_match = re.search(r"(?:add|create|new)\s+(?:task|goal|todo)?\s+(.+)(?:\?|$)", text, re.IGNORECASE)
            if task_match:
                task_text = task_match.group(1).strip()

        # Check for complete/finish action
        elif any(word in text.lower() for word in ["complete", "finish", "done"]):
            action = "complete"
            # Extract task text
            task_match = re.search(r"(?:complete|finish|done)\s+(?:task|goal|todo)?\s+(.+)(?:\?|$)", text, re.IGNORECASE)
            if task_match:
                task_text = task_match.group(1).strip()

        # Check for delete/remove action
        elif any(word in text.lower() for word in ["delete", "remove"]):
            action = "delete"
            # Extract task text
            task_match = re.search(r"(?:delete|remove)\s+(?:task|goal|todo)?\s+(.+)(?:\?|$)", text, re.IGNORECASE)
            if task_match:
                task_text = task_match.group(1).strip()

        # Check for priority
        priority_match = re.search(r"priority\s+([1-5])", text, re.IGNORECASE)
        if priority_match:
            priority = int(priority_match.group(1))

        return {
            "command_type": "goal",
            "action": action,
            "goal_text": task_text,
            "priority": priority
        }

    def _parse_github_command(self, text):
        """
        Parse GitHub-related commands
        """
        # This is a placeholder - implement GitHub command parsing
        return {
            "command_type": "github",
            "action": "view"
        }

    def _parse_notion_command(self, text):
        """
        Parse Notion-related commands
        """
        # This is a placeholder - implement Notion command parsing
        return {
            "command_type": "notion",
            "action": "view"
        }

    def _parse_ai_query_command(self, text):
        """
        Parse AI query commands
        """
        # Extract model name if present - improved regex to better match model queries
        model_match = re.search(r"(?:ask|query|use)\s+(\w+)\s+(.+)", text, re.IGNORECASE)

        if model_match:
            model_name = model_match.group(1).lower()
            query = model_match.group(2).strip()

            # Log the successful model query parsing
            self.logger.info(f"Parsed model query: model={model_name}, query={query[:50]}...")

            return {
                "command_type": "model",
                "model_name": model_name,
                "query": query
            }
        else:
            # If no specific model mentioned but contains 'ask' keyword, use default model
            if re.search(r"^\s*ask\s+", text, re.IGNORECASE):
                query = re.sub(r"^\s*ask\s+", "", text, flags=re.IGNORECASE).strip()
                self.logger.info(f"Using default model for query: {query[:50]}...")

                return {
                    "command_type": "model",
                    "model_name": "main_brain",  # Default model
                    "query": query
                }

            # Not a model query
            return None

    def _parse_system_command(self, text):
        """
        Parse system commands
        """
        if "help" in text.lower():
            return {"command_type": "help"}
        elif any(word in text.lower() for word in ["exit", "quit", "stop"]):
            return {"command_type": "exit"}
        elif "restart" in text.lower():
            return {"command_type": "restart"}
        elif "status" in text.lower() or "system" in text.lower():
            return {"command_type": "status"}
        elif "cli" in text.lower() or "ui" in text.lower() or "dashboard" in text.lower():
            return {"command_type": "cli_ui"}
        elif "vitals" in text.lower() or "health" in text.lower() or "check" in text.lower():
            return {"command_type": "status"}

        return {"command_type": "system"}

    def _parse_memory_command(self, text):
        """
        Parse memory-related commands
        """
        # Default to search action
        action = "search"
        query = ""

        # Check for save action
        if "save" in text.lower():
            action = "save"
            # Extract query text
            query_match = re.search(r"save\s+(?:to\s+memory\s+)?(.+)(?:\?|$)", text, re.IGNORECASE)
            if query_match:
                query = query_match.group(1).strip()
            else:
                # Try another pattern
                query_match = re.search(r"save\s+(.+)\s+to\s+memory(?:\?|$)", text, re.IGNORECASE)
                if query_match:
                    query = query_match.group(1).strip()

        # Check for recall action
        elif "recall" in text.lower():
            action = "recall"
            # Extract query text
            query_match = re.search(r"recall\s+(?:from\s+memory\s+)?(.+)(?:\?|$)", text, re.IGNORECASE)
            if query_match:
                query = query_match.group(1).strip()

        # Check for search action or show recent memories
        elif "search" in text.lower() or "show" in text.lower() or "get" in text.lower():
            action = "search"
            # Extract query text
            query_match = re.search(r"search\s+(?:memory\s+)?(.+)(?:\?|$)", text, re.IGNORECASE)
            if query_match:
                query = query_match.group(1).strip()
            else:
                # If just "search memory" or "show recent memories" with no query, return empty query to show all memories
                if re.search(r"^\s*(?:search\s+memory|show\s+(?:recent\s+)?memories|get\s+memories)\s*$", text, re.IGNORECASE):
                    query = ""

        self.logger.info(f"Parsed memory command: action={action}, query={query[:30] if query else ''}")

        return {
            "command_type": "memory",
            "action": action,
            "query": query
        }

    def _parse_ollama_command(self, text):
        """
        Parse Ollama-related commands
        """
        # Default to status action
        action = "status"
        model = None

        # Check for specific actions
        if re.search(r"\b(?:enable|on|start|activate)\b", text, re.IGNORECASE):
            action = "on"
        elif re.search(r"\b(?:disable|off|stop|deactivate)\b", text, re.IGNORECASE):
            action = "off"
        elif re.search(r"\btoggle\b", text, re.IGNORECASE):
            action = "toggle"
        elif re.search(r"\bstatus\b", text, re.IGNORECASE):
            action = "status"
        elif re.search(r"\bpull\b", text, re.IGNORECASE):
            action = "pull"
            # Extract model name
            model_match = re.search(r"pull\s+(\w+(?:-\w+)*)", text, re.IGNORECASE)
            if model_match:
                model = model_match.group(1).strip()
            else:
                model = "phi-2"  # Default model to pull

        self.logger.info(f"Parsed Ollama command: action={action}, model={model}")

        return {
            "command_type": "ollama",
            "action": action,
            "model": model
        }
