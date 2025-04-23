"""
Context Manager for General Pulse
Manages short-term conversation context and integrates with AugmentCode's context engine
"""

import os
import json
from collections import deque
from typing import Dict, List, Any, Optional, Deque
import structlog
from datetime import datetime

# Configure logger
logger = structlog.get_logger("context_manager")

# We're using our own dedicated context engine for the agent
# No need to import AugmentCode's context engine
AUGMENT_AVAILABLE = False

class PulseContext:
    """
    Manages conversation context for General Pulse
    Combines local deque storage with AugmentCode's context engine
    """

    def __init__(self, max_length: int = 10, user_id: str = "default_user"):
        """
        Initialize the context manager

        Args:
            max_length: Maximum number of conversation turns to store locally
            user_id: User identifier for context storage
        """
        self.history: Deque[Dict[str, str]] = deque(maxlen=max_length)
        self.user_id = user_id
        self.logger = logger

        # We're using our own dedicated context engine
        self.augment = None

        # Metadata for the current context
        self.metadata = {
            "session_start": datetime.now().isoformat(),
            "interaction_count": 0,
            "last_updated": datetime.now().isoformat()
        }

    def update(self, user_input: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the context with a new interaction

        Args:
            user_input: User's input text
            response: Assistant's response text
            metadata: Optional metadata about the interaction
        """
        # Update local history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        # Update metadata
        self.metadata["interaction_count"] += 1
        self.metadata["last_updated"] = datetime.now().isoformat()

        # Combine provided metadata with default metadata
        combined_metadata = {
            "timestamp": datetime.now().isoformat(),
            "interaction_id": self.metadata["interaction_count"]
        }
        if metadata:
            combined_metadata.update(metadata)

        # Infer mood if not provided
        if "mood" not in combined_metadata:
            combined_metadata["mood"] = self._infer_mood(user_input)

        # We're using our own dedicated context engine
        # No need to update AugmentCode

        # Log the interaction
        self.logger.info(
            "Context updated",
            user_input_preview=user_input[:50] + "..." if len(user_input) > 50 else user_input,
            response_preview=response[:50] + "..." if len(response) > 50 else response,
            metadata=combined_metadata
        )

    def get_context(self, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Get the current context

        Args:
            max_tokens: Maximum number of tokens to include in the context

        Returns:
            Dictionary containing conversation history and augmented context
        """
        context = {
            "history": list(self.history),
            "metadata": self.metadata
        }

        # We're using our own dedicated context engine
        # No need to retrieve from AugmentCode

        return context

    def clear(self) -> None:
        """
        Clear the context
        """
        self.history.clear()
        self.metadata["interaction_count"] = 0
        self.metadata["last_updated"] = datetime.now().isoformat()
        self.logger.info("Context cleared")

    def save_to_file(self, file_path: str) -> bool:
        """
        Save the context to a file

        Args:
            file_path: Path to save the context

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump({
                    "history": list(self.history),
                    "metadata": self.metadata
                }, f, indent=2)
            self.logger.info(f"Context saved to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save context to {file_path}: {str(e)}")
            return False

    def load_from_file(self, file_path: str) -> bool:
        """
        Load the context from a file

        Args:
            file_path: Path to load the context from

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Clear current history
            self.history.clear()

            # Load history (up to max_length)
            for item in data.get("history", [])[:self.history.maxlen]:
                self.history.append(item)

            # Load metadata
            if "metadata" in data:
                self.metadata = data["metadata"]
                # Update last_updated
                self.metadata["last_updated"] = datetime.now().isoformat()

            self.logger.info(f"Context loaded from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load context from {file_path}: {str(e)}")
            return False

    def _infer_mood(self, input_text: str) -> str:
        """
        Infer the user's mood from their input

        Args:
            input_text: User's input text

        Returns:
            Inferred mood
        """
        # Simple keyword-based mood detection
        lower_text = input_text.lower()

        # Check for coding/technical keywords
        if any(word in lower_text for word in ["code", "function", "bug", "error", "debug", "fix"]):
            return "hustling"

        # Check for positive keywords
        if any(word in lower_text for word in ["thanks", "great", "awesome", "good", "love", "like", "happy"]):
            return "positive"

        # Check for negative keywords
        if any(word in lower_text for word in ["bad", "hate", "dislike", "angry", "frustrated", "annoyed"]):
            return "negative"

        # Check for question keywords
        if any(word in lower_text for word in ["what", "how", "why", "when", "where", "who", "?"]):
            return "curious"

        # Default mood
        return "neutral"
