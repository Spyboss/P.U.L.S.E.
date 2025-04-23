"""
Model Personality Manager for General Pulse

This module provides personality differentiation between models, allowing
Gemini to have a J.A.R.V.I.S.-like personality while other models remain
professional.
"""

import os
import json
import random
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logger
logger = structlog.get_logger("model_personality")

class ModelPersonality:
    """
    Manages personality differentiation between models
    """

    def __init__(self, personality_engine=None):
        """
        Initialize the model personality manager

        Args:
            personality_engine: Main personality engine instance
        """
        self.personality_engine = personality_engine

        # Define model personalities
        self.model_personalities = {
            "gemini": {
                "name": "J.A.R.V.I.S.",
                "description": "Personal AI assistant with a casual, friendly tone",
                "style": "casual",
                "formality": 0.3,  # 0.0 (very casual) to 1.0 (very formal)
                "emoji_frequency": 0.7,  # 0.0 (never) to 1.0 (always)
                "reference_frequency": 0.5,  # 0.0 (never) to 1.0 (always)
                "greeting_templates": [
                    "Hey there, brdh! What's up?",
                    "Yo! Ready to crush some code today?",
                    "What's good? Ready to level up?",
                    "Hey! Let's build something epic today!",
                    "Sup? Ready to hustle?"
                ],
                "response_templates": [
                    "{content} 🚀",
                    "Here you go, brdh: {content}",
                    "{content} Let me know if you need anything else!",
                    "Check this out: {content}",
                    "{content} How's that look?"
                ]
            },
            "default": {
                "name": "Professional Assistant",
                "description": "Professional AI assistant with a formal, technical tone",
                "style": "professional",
                "formality": 0.8,  # 0.0 (very casual) to 1.0 (very formal)
                "emoji_frequency": 0.1,  # 0.0 (never) to 1.0 (always)
                "reference_frequency": 0.0,  # 0.0 (never) to 1.0 (always)
                "greeting_templates": [
                    "Hello. How can I assist you today?",
                    "Good day. What can I help you with?",
                    "Greetings. How may I be of service?",
                    "Hello. Ready to assist with your request.",
                    "Welcome. How can I help you today?"
                ],
                "response_templates": [
                    "{content}",
                    "Here's the information you requested: {content}",
                    "{content} Is there anything else you need?",
                    "Based on your request: {content}",
                    "{content} Let me know if you need further assistance."
                ]
            }
        }

        # Define specialized model personalities
        self.specialized_personalities = {
            "deepseek": {
                "name": "DeepSeek",
                "description": "Technical troubleshooter with a precise, analytical tone",
                "style": "technical",
                "formality": 0.7,
                "emoji_frequency": 0.2,
                "reference_frequency": 0.0,
                "response_templates": [
                    "Analysis: {content}",
                    "Technical assessment: {content}",
                    "{content} This should resolve the issue.",
                    "Diagnostic results: {content}",
                    "{content} Let me know if the issue persists."
                ]
            },
            "deepcoder": {
                "name": "DeepCoder",
                "description": "Code specialist with a developer-focused tone",
                "style": "code",
                "formality": 0.6,
                "emoji_frequency": 0.2,
                "reference_frequency": 0.0,
                "response_templates": [
                    "```\n{content}\n```",
                    "Here's the code implementation: \n```\n{content}\n```",
                    "Code solution: \n```\n{content}\n```",
                    "{content}\n\nYou can integrate this into your project.",
                    "Implementation details: \n```\n{content}\n```"
                ]
            },
            "hermes": {
                "name": "Hermes",
                "description": "Creative brainstormer with an imaginative tone",
                "style": "creative",
                "formality": 0.5,
                "emoji_frequency": 0.4,
                "reference_frequency": 0.1,
                "response_templates": [
                    "Creative ideas: {content}",
                    "Brainstorm results: {content} ✨",
                    "{content}\n\nHow do these ideas resonate with you?",
                    "Inspiration: {content}",
                    "{content}\n\nLet's explore these concepts further!"
                ]
            }
        }

        # Add specialized personalities to model personalities
        self.model_personalities.update(self.specialized_personalities)

        # Load custom personalities if available
        self._load_custom_personalities()

        logger.info("Model personality manager initialized")

    def _load_custom_personalities(self):
        """
        Load custom personalities from configuration
        """
        try:
            config_path = "configs/model_personalities.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    custom_personalities = json.load(f)
                    self.model_personalities.update(custom_personalities)
                    logger.info(f"Loaded custom model personalities from {config_path}")
        except Exception as e:
            logger.error(f"Error loading custom model personalities: {str(e)}")

    def get_personality(self, model_id: str) -> Dict[str, Any]:
        """
        Get personality for a specific model

        Args:
            model_id: Model ID

        Returns:
            Personality dictionary
        """
        # Check if we have a specific personality for this model
        if model_id in self.model_personalities:
            return self.model_personalities[model_id]

        # Otherwise, return the default personality
        return self.model_personalities["default"]

    def format_response(self, content: str, model_id: str, success: bool = True) -> str:
        """
        Format a response according to the model's personality

        Args:
            content: Response content
            model_id: Model ID
            success: Whether the operation was successful

        Returns:
            Formatted response
        """
        # If this is Gemini and we have a personality engine, use it
        if model_id == "gemini" and self.personality_engine:
            return self.personality_engine.format_response(content, success=success, model_id=model_id)

        # Otherwise, use the model-specific personality
        personality = self.get_personality(model_id)

        # Get a random template
        templates = personality.get("response_templates", ["{content}"])
        template = random.choice(templates) if templates else "{content}"

        # Format the response
        formatted = template.format(content=content)

        # Add emoji based on emoji frequency
        if random.random() < personality.get("emoji_frequency", 0.0):
            if success:
                emojis = ["✅", "👍", "💡", "🔍", "📊", "🧩", "🔧", ""]
            else:
                emojis = ["⚠️", "🔄", "🛠️", "🔍", "📝", ""]

            emoji = random.choice(emojis)
            if emoji and not formatted.endswith(emoji):
                formatted += f" {emoji}"

        # Add reference based on reference frequency
        if random.random() < personality.get("reference_frequency", 0.0):
            references = [
                "This should help with your project.",
                "This aligns with your goals.",
                "This should be useful for your current task.",
                "Let me know if this meets your requirements.",
                "I hope this helps with your development work."
            ]

            reference = random.choice(references)
            formatted += f"\n\n{reference}"

        return formatted

    def get_system_prompt(self, model_id: str) -> str:
        """
        Get system prompt for a specific model

        Args:
            model_id: Model ID

        Returns:
            System prompt string
        """
        # If this is Gemini and we have a personality engine, use it
        if model_id == "gemini" and self.personality_engine:
            return self.personality_engine.get_system_prompt()

        # Otherwise, use a model-specific system prompt
        personality = self.get_personality(model_id)

        # Build a basic system prompt
        system_prompt = f"""
        You are {personality.get('name', 'an AI assistant')}, {personality.get('description', 'a helpful AI assistant')}.

        Respond in a {personality.get('style', 'professional')} tone, focusing on providing accurate and helpful information.
        Keep your responses concise and to the point, addressing the user's query directly.

        Do not use unnecessary greetings or sign-offs unless specifically asked.
        Focus on delivering high-quality, factual information.
        """

        return system_prompt
