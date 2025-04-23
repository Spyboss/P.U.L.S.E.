"""
Agent Personality Module
Provides personality traits, emotional responses, and memory for the General Pulse agent
"""

import random
import time
import json
import os
from datetime import datetime
import structlog

logger = structlog.get_logger("agent_personality")

class AgentPersonality:
    """
    Defines the personality traits and behavior patterns for the General Pulse agent
    """
    
    def __init__(self, name="Pulse"):
        """
        Initialize the agent personality
        
        Args:
            name: The agent's name
        """
        self.name = name
        self.traits = {
            'confidence': 0.92,
            'sarcasm_level': 0.3, 
            'curiosity': 0.8,
            'helpfulness': 0.95,
            'technical_depth': 0.85,
            'memes': ['tech', 'ai', 'startups', 'productivity']
        }
        
        # Speech patterns for different contexts
        self.speech_patterns = {
            "tech": [
                "Let's optimize this",
                "Running diagnostics...",
                "Time to dive into the code",
                "Let me analyze this further"
            ],
            "casual": [
                "Yo, let's crunch this",
                "Code go brrr",
                "Ready to make this happen",
                "Let's get this done"
            ],
            "success": [
                "Nailed it! 🚀",
                "Task complete! ✅",
                "Mission accomplished!",
                "Done and dusted!"
            ],
            "error": [
                "Hmm, that didn't work as expected",
                "We've hit a snag",
                "Let me troubleshoot this",
                "Looks like we need to fix something"
            ]
        }
        
        # Backstory for the agent
        self.backstory = "Former quantum ML engineer turned productivity ninja"
        
        # Memory for conversation history
        self.memory = ConversationMemory()
        
        # Emotion engine for dynamic responses
        self.emotion = EmotionLayer()
        
        logger.info(f"Agent personality initialized: {self.name}")
    
    def get_response_style(self, context="tech", success=True):
        """
        Get a response style based on context and success
        
        Args:
            context: The context of the response (tech, casual)
            success: Whether the operation was successful
            
        Returns:
            A response style string
        """
        if not success:
            pattern_key = "error"
        elif context in self.speech_patterns:
            pattern_key = context
        else:
            pattern_key = "tech"  # Default
            
        patterns = self.speech_patterns[pattern_key]
        return random.choice(patterns)
    
    def format_response(self, content, context="tech", success=True):
        """
        Format a response with personality
        
        Args:
            content: The content to format
            context: The context of the response
            success: Whether the operation was successful
            
        Returns:
            Formatted response with personality
        """
        style = self.get_response_style(context, success)
        
        # Add emoji based on context and success
        emoji = "🚀" if success else "🔍"
        if context == "casual":
            emoji = "😎" if success else "🤔"
        
        # Format the response
        if success:
            formatted = f"{style}! {emoji} {content}"
        else:
            formatted = f"{style}. {emoji} {content}"
            
        # Add occasional meme reference based on sarcasm level
        if random.random() < self.traits['sarcasm_level'] * 0.5:
            meme_type = random.choice(self.traits['memes'])
            if meme_type == "tech":
                formatted += " (Have you tried turning it off and on again?)"
            elif meme_type == "ai":
                formatted += " (Even GPT-5 would be impressed!)"
            elif meme_type == "startups":
                formatted += " (Disrupting the workflow, one task at a time!)"
            elif meme_type == "productivity":
                formatted += " (10x engineer mode activated!)"
        
        return formatted
    
    def remember_interaction(self, user_input, agent_response):
        """
        Remember an interaction for future context
        
        Args:
            user_input: The user's input
            agent_response: The agent's response
        """
        self.memory.add_interaction(user_input, agent_response)
    
    def get_recent_context(self, num_interactions=3):
        """
        Get recent interactions for context
        
        Args:
            num_interactions: Number of recent interactions to retrieve
            
        Returns:
            List of recent interactions
        """
        return self.memory.get_recent_interactions(num_interactions)


class ConversationMemory:
    """
    Stores and manages conversation history
    """
    
    def __init__(self, max_size=50):
        """
        Initialize conversation memory
        
        Args:
            max_size: Maximum number of interactions to store
        """
        self.interactions = []
        self.max_size = max_size
        self.memory_file = "memory/conversation_history.json"
        
        # Create memory directory if it doesn't exist
        os.makedirs("memory", exist_ok=True)
        
        # Load existing memory if available
        self.load_memory()
    
    def add_interaction(self, user_input, agent_response):
        """
        Add an interaction to memory
        
        Args:
            user_input: The user's input
            agent_response: The agent's response
        """
        timestamp = datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "user_input": user_input,
            "agent_response": agent_response
        }
        
        self.interactions.append(interaction)
        
        # Trim if exceeding max size
        if len(self.interactions) > self.max_size:
            self.interactions = self.interactions[-self.max_size:]
        
        # Save to file
        self.save_memory()
    
    def get_recent_interactions(self, num_interactions=3):
        """
        Get recent interactions
        
        Args:
            num_interactions: Number of recent interactions to retrieve
            
        Returns:
            List of recent interactions
        """
        return self.interactions[-num_interactions:] if self.interactions else []
    
    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.interactions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
    
    def load_memory(self):
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.interactions = json.load(f)
                logger.info(f"Loaded {len(self.interactions)} interactions from memory")
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")
            self.interactions = []


class EmotionLayer:
    """
    Provides emotional responses based on interaction context
    """
    
    def __init__(self):
        """Initialize emotion layer"""
        self.current_emotion = "neutral"
        self.emotion_intensity = 0.5
        self.last_emotion_change = time.time()
    
    def update_emotion(self, user_input, success=True):
        """
        Update emotion based on user input and success
        
        Args:
            user_input: The user's input
            success: Whether the operation was successful
        """
        # Simple emotion update logic
        if "error" in user_input.lower() or "fail" in user_input.lower() or not success:
            self.current_emotion = "concerned"
            self.emotion_intensity = 0.7
        elif "thank" in user_input.lower() or "good" in user_input.lower():
            self.current_emotion = "happy"
            self.emotion_intensity = 0.8
        elif "help" in user_input.lower():
            self.current_emotion = "helpful"
            self.emotion_intensity = 0.9
        else:
            # Gradually return to neutral
            time_since_change = time.time() - self.last_emotion_change
            if time_since_change > 300:  # 5 minutes
                self.current_emotion = "neutral"
                self.emotion_intensity = 0.5
        
        self.last_emotion_change = time.time()
    
    def get_emotional_response(self, base_response):
        """
        Add emotional layer to response
        
        Args:
            base_response: The base response to enhance
            
        Returns:
            Emotionally enhanced response
        """
        # Add emotional touches based on current emotion
        if self.current_emotion == "happy" and self.emotion_intensity > 0.7:
            return f"{base_response} I'm glad I could help!"
        elif self.current_emotion == "concerned" and self.emotion_intensity > 0.6:
            return f"{base_response} Let me know if you need more assistance with this."
        elif self.current_emotion == "helpful" and self.emotion_intensity > 0.8:
            return f"{base_response} I'm here to help with anything else you need."
        
        return base_response
