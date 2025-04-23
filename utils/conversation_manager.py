"""
Conversation Manager for General Pulse
Manages and maintains conversation history for context
"""

import json
import os
from datetime import datetime
from .logger import default_logger as logger

class ConversationManager:
    """Manages the conversation history for the agent."""
    
    def __init__(self, max_history=10, storage_dir="memory/conversations"):
        """Initialize the conversation manager."""
        self.max_history = max_history
        self.storage_dir = storage_dir
        self.conversation_id = None
        self.messages = []
        self.logger = logger
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        self.logger.debug(f"ConversationManager initialized with storage in {self.storage_dir}")
        
    def start_conversation(self):
        """Start a new conversation."""
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.logger.info(f"Starting new conversation: {self.conversation_id}")
        return self.conversation_id
        
    def add_message(self, role, content, metadata=None):
        """Add a message to the conversation history."""
        if not self.conversation_id:
            self.start_conversation()
            
        timestamp = datetime.now().isoformat()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        
        if metadata:
            message["metadata"] = metadata
            
        self.messages.append(message)
        
        # Trim history if it exceeds max_history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
            
        self.logger.debug(f"Added {role} message to conversation {self.conversation_id}")
        return message
        
    def get_history(self, formatted=False):
        """Get the conversation history."""
        if formatted:
            return self._format_for_model()
        return self.messages
        
    def _format_for_model(self):
        """Format the conversation history for model input."""
        formatted = []
        for msg in self.messages:
            formatted.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })
        return formatted
        
    def save_conversation(self):
        """Save the conversation to disk."""
        if not self.conversation_id or not self.messages:
            self.logger.warning("No conversation to save")
            return None
            
        filename = f"{self.storage_dir}/{self.conversation_id}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "conversation_id": self.conversation_id,
                    "start_time": self.messages[0]["timestamp"] if self.messages else datetime.now().isoformat(),
                    "messages": self.messages
                }, f, indent=2)
                
            self.logger.info(f"Saved conversation {self.conversation_id} to {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error saving conversation: {str(e)}", exc_info=True)
            return None
            
    def load_conversation(self, conversation_id):
        """Load a conversation from disk."""
        filename = f"{self.storage_dir}/{conversation_id}.json"
        
        if not os.path.exists(filename):
            self.logger.warning(f"Conversation file not found: {filename}")
            return False
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.conversation_id = data.get("conversation_id")
            self.messages = data.get("messages", [])
            
            self.logger.info(f"Loaded conversation {self.conversation_id} with {len(self.messages)} messages")
            return True
        except Exception as e:
            self.logger.error(f"Error loading conversation: {str(e)}", exc_info=True)
            return False
            
    def get_latest_conversations(self, limit=5):
        """Get a list of the latest conversations."""
        try:
            # Get all conversation files
            files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            
            # Sort by filename (which contains timestamp)
            files.sort(reverse=True)
            
            # Limit the number of results
            files = files[:limit]
            
            conversations = []
            for file in files:
                conversation_id = file.replace('.json', '')
                
                # Load basic info
                try:
                    with open(f"{self.storage_dir}/{file}", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    conversations.append({
                        "conversation_id": conversation_id,
                        "start_time": data.get("start_time"),
                        "message_count": len(data.get("messages", [])),
                        "first_message": data.get("messages", [{}])[0].get("content", "")[:50] + "..." if data.get("messages") else ""
                    })
                except Exception as e:
                    self.logger.error(f"Error loading conversation info: {str(e)}", exc_info=True)
            
            return conversations
        except Exception as e:
            self.logger.error(f"Error getting conversation list: {str(e)}", exc_info=True)
            return [] 