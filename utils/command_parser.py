"""
Command Parser for General Pulse
Provides natural language understanding for commands
"""

import re
from typing import Dict, Any, Optional, List, Tuple
import structlog

# Try to import spacy, but don't fail if it's not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Initialize logger
logger = structlog.get_logger("command_parser")

class CommandParser:
    """
    Parser for natural language commands
    """

    def __init__(self):
        """Initialize the command parser"""
        self.logger = structlog.get_logger("command_parser")

        # Try to load spaCy model if available
        self.spacy_available = False
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.spacy_available = True
                self.logger.info("Loaded spaCy model for NLP processing")
            except Exception as e:
                self.logger.warning(f"Could not load spaCy model: {str(e)}. Falling back to regex patterns.")
        else:
            self.logger.warning("spaCy not installed. Falling back to regex patterns.")

        # Initialize context
        self.context = {
            "previous_intent": None,
            "interaction_count": 0
        }

        # Import intent handler
        try:
            from utils.intent_handler import IntentHandler
            self.intent_handler = IntentHandler()
        except ImportError:
            self.logger.warning("IntentHandler not available. Some functionality may be limited.")
            self.intent_handler = None

        # Command patterns
        self.command_patterns = {
            "help": [
                r"help",
                r"commands",
                r"what can you do",
                r"show commands",
                r"available commands"
            ],
            "exit": [
                r"exit",
                r"quit",
                r"bye",
                r"goodbye"
            ],
            "time": [
                r"what(?:'s| is) the time(?: now)?",
                r"current time",
                r"time now"
            ],
            "date": [
                r"what(?:'s| is) (?:the|today's) date",
                r"what day is (?:it|today)",
                r"current date",
                r"today's date"
            ],
            "timezone": [
                r"what(?:'s| is) the time in ([a-zA-Z\s]+)",
                r"what(?:'s| is) the time (?:like )?in ([a-zA-Z\s]+)",
                r"time (?:in|at) ([a-zA-Z\s]+)",
                r"current time in ([a-zA-Z\s]+)",
                r"what time is it in ([a-zA-Z\s]+)"
            ],
            "github_info": [
                r"github\s+([^/\s]+/[^/\s]+)\s+info",
                r"(?:show|get|display)(?:\s+me)?\s+(?:info|information|details)(?:\s+about)?\s+(?:github\.com/)?([^/\s]+/[^/\s]+)",
                r"(?:info|information|details)(?:\s+about)?\s+(?:github\.com/)?([^/\s]+/[^/\s]+)"
            ],
            "github_issues": [
                r"github\s+([^/\s]+/[^/\s]+)\s+issues",
                r"(?:show|list|get|display)(?:\s+me)?\s+(?:issues|tickets|bugs)(?:\s+for)?\s+(?:github\.com/)?([^/\s]+/[^/\s]+)",
                r"(?:issues|tickets|bugs)(?:\s+for)?\s+(?:github\.com/)?([^/\s]+/[^/\s]+)"
            ],
            "github_commit": [
                r"github\s+([^/\s]+/[^/\s]+)\s+commit\s+([^\s]+)",
                r"(?:generate|create)(?:\s+a)?\s+commit(?:\s+message)?(?:\s+for)?\s+([^\s]+)(?:\s+in)?\s+(?:github\.com/)?([^/\s]+/[^/\s]+)",
                r"commit(?:\s+message)?(?:\s+for)?\s+([^\s]+)(?:\s+in)?\s+(?:github\.com/)?([^/\s]+/[^/\s]+)"
            ],
            "notion_document": [
                r"notion\s+create\s+(?:document|doc)\s+(.+)",
                r"create\s+(?:a)?\s+(?:notion)?\s+(?:document|doc)(?:\s+called)?\s+(.+)",
                r"(?:make|create)(?:\s+a)?\s+(?:new)?\s+(?:notion)?\s+(?:document|doc)(?:\s+called)?\s+(.+)"
            ],
            "notion_journal": [
                r"notion\s+(?:journal|diary)",
                r"create\s+(?:a)?\s+(?:notion)?\s+(?:journal|diary)(?:\s+entry)?",
                r"(?:make|add)(?:\s+a)?\s+(?:new)?\s+(?:notion)?\s+(?:journal|diary)(?:\s+entry)?"
            ],
            "ask_model": [
                r"ask\s+([a-zA-Z0-9_-]+)\s+(.+)",
                r"(?:query|use)\s+([a-zA-Z0-9_-]+)(?:\s+to)?\s+(.+)",
                r"([a-zA-Z0-9_-]+)(?:\s+model)?,\s+(.+)"
            ],
            "workflow": [
                r"workflow\s+(.+)",
                r"create(?:\s+a)?\s+workflow(?:\s+for)?\s+(.+)",
                r"(?:run|execute)(?:\s+a)?\s+workflow(?:\s+for)?\s+(.+)"
            ],
            "content_creation": [
                r"(?:write|create)(?:\s+a)?\s+(?:blog\s+post|article)(?:\s+about)?\s+(.+)",
                r"(?:generate|make)(?:\s+a)?\s+(?:blog\s+post|article)(?:\s+about)?\s+(.+)"
            ],
            "code_generation": [
                r"(?:write|create|generate)(?:\s+some)?\s+code(?:\s+for)?\s+(.+)",
                r"(?:code|program)(?:\s+for)?\s+(.+)"
            ],
            "system_status": [
                r"(?:system|status|health)(?:\s+status)?",
                r"(?:how|what)(?:'s| is) the system(?:\s+status)?",
                r"(?:check|show)(?:\s+the)?\s+(?:system|status)"
            ]
        }

        # Command handlers
        self.command_handlers = {
            "help": self._handle_help,
            "exit": self._handle_exit,
            "time": self._handle_time,
            "date": self._handle_date,
            "timezone": self._handle_timezone,
            "github_info": self._handle_github_info,
            "github_issues": self._handle_github_issues,
            "github_commit": self._handle_github_commit,
            "notion_document": self._handle_notion_document,
            "notion_journal": self._handle_notion_journal,
            "ask_model": self._handle_ask_model,
            "workflow": self._handle_workflow,
            "content_creation": self._handle_content_creation,
            "code_generation": self._handle_code_generation,
            "system_status": self._handle_system_status
        }

        self.logger.info("Command parser initialized")

    def parse_command(self, text: str) -> Dict[str, Any]:
        """
        Parse a command from text

        Args:
            text: The text to parse

        Returns:
            Dictionary with command type and parameters
        """
        # Normalize text
        text = text.strip().lower()

        # Try spaCy parsing first if available
        if self.spacy_available:
            spacy_result = self._parse_with_spacy(text)
            if spacy_result:
                return spacy_result

        # Fall back to regex patterns
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    # Get handler for this command type
                    handler = self.command_handlers.get(command_type)
                    if handler:
                        return handler(match)

        # No match found, try to use intent handler if available
        if self.intent_handler:
            intent = self.intent_handler.classify(text)

            # Update context
            self.context["previous_intent"] = intent
            self.context["interaction_count"] += 1

            # Generate suggestions based on intent
            suggestions = self._generate_suggestions(intent, text)

            # Return result with context and suggestions
            return {
                "command": "unknown",
                "original_text": text,
                "context": self.context,
                "suggestions": suggestions
            }
        else:
            # No intent handler available
            return {
                "command": "unknown",
                "original_text": text
            }

    def _parse_with_spacy(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a command using spaCy NLP

        Args:
            text: The text to parse

        Returns:
            Dictionary with command type and parameters, or None if no match
        """
        doc = self.nlp(text)

        # Extract key verbs and nouns
        verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN"]

        # Check for time-related queries
        if "time" in nouns:
            # Check for timezone
            for ent in doc.ents:
                if ent.label_ == "GPE":  # Geographical entity
                    return {
                        "command": "timezone",
                        "location": ent.text.capitalize()
                    }

            # Just current time
            return {
                "command": "time"
            }

        # Check for date-related queries
        if "date" in nouns or "day" in nouns:
            return {
                "command": "date"
            }

        # Check for GitHub-related queries
        if "github" in text or "repo" in nouns or "repository" in nouns:
            # Look for repository pattern (username/repo)
            repo_pattern = r"([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)"
            repo_match = re.search(repo_pattern, text)

            if repo_match:
                repo = repo_match.group(1)

                # Determine the type of GitHub command
                if "issue" in nouns or "issues" in nouns or "ticket" in nouns or "tickets" in nouns:
                    return {
                        "command": "github_issues",
                        "repo": repo
                    }
                elif "commit" in nouns or "message" in nouns:
                    # Look for file path
                    file_pattern = r"for\s+([^\s]+)\s+in"
                    file_match = re.search(file_pattern, text)
                    file_path = file_match.group(1) if file_match else None

                    return {
                        "command": "github_commit",
                        "repo": repo,
                        "file_path": file_path
                    }
                else:
                    return {
                        "command": "github_info",
                        "repo": repo
                    }

        # Check for Notion-related queries
        if "notion" in text or "document" in nouns or "doc" in nouns or "journal" in nouns or "diary" in nouns:
            if "journal" in nouns or "diary" in nouns:
                return {
                    "command": "notion_journal"
                }
            elif "document" in nouns or "doc" in nouns:
                # Extract document title
                title_pattern = r"(?:called|named|titled)\s+(.+)"
                title_match = re.search(title_pattern, text)
                title = title_match.group(1) if title_match else None

                if not title:
                    # Try to find the title after "document" or "doc"
                    title_pattern = r"(?:document|doc)\s+(.+)"
                    title_match = re.search(title_pattern, text)
                    title = title_match.group(1) if title_match else None

                # Capitalize the title
                if title:
                    title = title.title()

                return {
                    "command": "notion_document",
                    "title": title
                }

        # Check for model queries
        model_pattern = r"(?:ask|query|use)\s+([a-zA-Z0-9_-]+)\s+(.+)"
        model_match = re.search(model_pattern, text)
        if model_match:
            return {
                "command": "ask_model",
                "model": model_match.group(1),
                "query": model_match.group(2)
            }

        # Check for workflow
        if "workflow" in nouns:
            # Extract workflow description
            desc_pattern = r"workflow\s+(?:for)?\s*(.+)"
            desc_match = re.search(desc_pattern, text)
            description = desc_match.group(1) if desc_match else None

            return {
                "command": "workflow",
                "description": description
            }

        # No match found with spaCy
        return None

    def _handle_help(self, match) -> Dict[str, Any]:
        """Handle help command"""
        return {
            "command": "help"
        }

    def _handle_exit(self, match) -> Dict[str, Any]:
        """Handle exit command"""
        return {
            "command": "exit"
        }

    def _handle_time(self, match) -> Dict[str, Any]:
        """Handle time command"""
        return {
            "command": "time"
        }

    def _handle_date(self, match) -> Dict[str, Any]:
        """Handle date command"""
        return {
            "command": "date"
        }

    def _handle_timezone(self, match) -> Dict[str, Any]:
        """Handle timezone command"""
        location = match.group(1).strip() if match.groups() else None
        if location:
            location = location.capitalize()
        return {
            "command": "timezone",
            "location": location
        }

    def _handle_github_info(self, match) -> Dict[str, Any]:
        """Handle GitHub info command"""
        repo = match.group(1).strip() if match.groups() else None
        return {
            "command": "github_info",
            "repo": repo
        }

    def _handle_github_issues(self, match) -> Dict[str, Any]:
        """Handle GitHub issues command"""
        repo = match.group(1).strip() if match.groups() else None
        return {
            "command": "github_issues",
            "repo": repo
        }

    def _handle_github_commit(self, match) -> Dict[str, Any]:
        """Handle GitHub commit command"""
        if len(match.groups()) >= 2:
            repo = match.group(1).strip()
            file_path = match.group(2).strip()
        else:
            repo = match.group(1).strip()
            file_path = None

        return {
            "command": "github_commit",
            "repo": repo,
            "file_path": file_path
        }

    def _handle_notion_document(self, match) -> Dict[str, Any]:
        """Handle Notion document command"""
        title = match.group(1).strip() if match.groups() else None
        return {
            "command": "notion_document",
            "title": title
        }

    def _handle_notion_journal(self, match) -> Dict[str, Any]:
        """Handle Notion journal command"""
        return {
            "command": "notion_journal"
        }

    def _handle_ask_model(self, match) -> Dict[str, Any]:
        """Handle ask model command"""
        if len(match.groups()) >= 2:
            model = match.group(1).strip()
            query = match.group(2).strip()
            return {
                "command": "ask_model",
                "model": model,
                "query": query
            }
        return {
            "command": "unknown"
        }

    def _handle_workflow(self, match) -> Dict[str, Any]:
        """Handle workflow command"""
        description = match.group(1).strip() if match.groups() else None
        return {
            "command": "workflow",
            "description": description
        }

    def _handle_content_creation(self, match) -> Dict[str, Any]:
        """Handle content creation command"""
        topic = match.group(1).strip() if match.groups() else None
        return {
            "command": "content_creation",
            "topic": topic
        }

    def _handle_code_generation(self, match) -> Dict[str, Any]:
        """Handle code generation command"""
        description = match.group(1).strip() if match.groups() else None
        return {
            "command": "code_generation",
            "description": description
        }

    def _handle_system_status(self, match) -> Dict[str, Any]:
        """Handle system status command"""
        return {
            "command": "system_status"
        }

    def _generate_suggestions(self, intent, text):
        """Generate suggestions based on intent and text"""
        suggestions = []

        if intent == "task":
            suggestions.append("Add a new task")
            suggestions.append("Show all tasks")
            suggestions.append("Complete a task")
        elif intent == "github":
            suggestions.append("Show repository information")
            suggestions.append("List issues")
            suggestions.append("Generate commit message")
        elif intent == "notion":
            suggestions.append("Create a new document")
            suggestions.append("Add journal entry")
        elif intent == "time":
            suggestions.append("What time is it?")
            suggestions.append("What's today's date?")
            suggestions.append("What's the time in Tokyo?")
        elif intent == "ai_query":
            suggestions.append("Ask Claude about a topic")
            suggestions.append("Generate content with AI")
        elif intent == "system":
            suggestions.append("Show help")
            suggestions.append("Check system status")

        return suggestions
