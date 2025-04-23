"""
Neural Router for General Pulse

This module provides an intelligent routing system that uses the main brain model to decide
when to route queries to specialized models based on the query content.
"""

import os
import json
import asyncio
import structlog
import re
from typing import Dict, Any, Optional, List, Tuple
import time

# Import model configurations
from configs.models import MODEL_IDS

# Configure logger
logger = structlog.get_logger("neural_router")

class NeuralRouter:
    """
    Intelligent router that uses the main brain model to decide when to route queries to
    specialized models based on the query content.
    """

    def __init__(self, model_interface):
        """
        Initialize the neural router

        Args:
            model_interface: Model interface for calling models
        """
        self.model_interface = model_interface

        # Cache for routing decisions to reduce API calls
        self.routing_cache = {}
        self.cache_ttl = 3600  # 1 hour cache lifetime

        # Load model specializations
        self._load_model_specializations()

        logger.info("Neural router initialized")

    def _load_model_specializations(self):
        """
        Load model specializations from configuration
        """
        # Default model specializations
        self.model_specializations = {
            "main_brain": {
                "name": "Main Brain",
                "description": "General-purpose model, best for conversation and personal queries",
                "strengths": ["conversation", "general knowledge", "personal", "creative writing", "summarization"],
                "examples": ["How are you today?", "Tell me about yourself", "What's the weather like?"]
            },
            "deepseek": {
                "name": "DeepSeek",
                "description": "Specialized for troubleshooting and debugging",
                "strengths": ["debugging", "error analysis", "troubleshooting", "system issues", "performance optimization"],
                "examples": ["Why is my code crashing?", "How do I fix this error?", "My system is running slow"]
            },
            "deepcoder": {
                "name": "DeepCoder",
                "description": "Specialized for code generation and programming",
                "strengths": ["code generation", "programming", "algorithms", "software development", "code review"],
                "examples": ["Write a Python function to sort a list", "How do I implement a binary search?", "Create a React component"]
            },
            "llama-doc": {
                "name": "Llama-Doc",
                "description": "Specialized for documentation and explanation",
                "strengths": ["documentation", "explanation", "tutorials", "how-to guides", "concept clarification"],
                "examples": ["Explain how databases work", "Document this function", "How does blockchain work?"]
            },
            "mistral-small": {
                "name": "Mistral-Small",
                "description": "Specialized for trends and research",
                "strengths": ["trends", "research", "market analysis", "technology forecasting", "data interpretation"],
                "examples": ["What are the latest AI trends?", "Research on renewable energy", "Market analysis for cryptocurrencies"]
            },
            "maverick": {
                "name": "Maverick",
                "description": "Specialized for content creation",
                "strengths": ["content creation", "blog posts", "marketing copy", "creative writing", "storytelling"],
                "examples": ["Write a blog post about AI", "Create marketing copy for a product", "Write a short story"]
            },
            "llama-technical": {
                "name": "Llama-Technical",
                "description": "Specialized for technical content",
                "strengths": ["technical writing", "technical documentation", "scientific content", "academic writing", "technical explanation"],
                "examples": ["Explain quantum computing", "Write a technical specification", "Document this API"]
            },
            "hermes": {
                "name": "Hermes",
                "description": "Specialized for brainstorming and idea generation",
                "strengths": ["brainstorming", "idea generation", "creativity", "innovation", "problem-solving"],
                "examples": ["Generate ideas for a startup", "Brainstorm solutions to climate change", "Creative ways to market a product"]
            },
            "molmo": {
                "name": "Molmo",
                "description": "Specialized for ethical AI and bias detection",
                "strengths": ["ethics", "bias detection", "fairness", "responsible AI", "social impact"],
                "examples": ["Is this AI system biased?", "Ethical considerations for facial recognition", "How to ensure AI fairness"]
            },
            "mistralai": {
                "name": "MistralAI",
                "description": "Specialized for task automation and workflows",
                "strengths": ["automation", "workflows", "productivity", "process optimization", "task management"],
                "examples": ["How to automate file processing", "Create a workflow for content approval", "Optimize my daily routine"]
            },
            "kimi": {
                "name": "Kimi",
                "description": "Specialized for visual reasoning and design",
                "strengths": ["visual design", "UI/UX", "graphic design", "visual reasoning", "design principles"],
                "examples": ["Design principles for a mobile app", "How to improve this UI", "Color theory for web design"]
            },
            "nemotron": {
                "name": "Nemotron",
                "description": "Specialized for complex reasoning and problem-solving",
                "strengths": ["complex reasoning", "problem-solving", "logical analysis", "critical thinking", "decision making"],
                "examples": ["Solve this logic puzzle", "Analyze this complex situation", "Help me make a difficult decision"]
            },
            "gemma": {
                "name": "Gemma",
                "description": "Specialized for mathematics and chemistry",
                "strengths": ["mathematics", "chemistry", "equations", "formulas", "scientific calculations"],
                "examples": ["Solve this equation", "Explain this chemical reaction", "Calculate the derivative"]
            },
            "dolphin": {
                "name": "Dolphin",
                "description": "Specialized for script optimization and automation",
                "strengths": ["script optimization", "automation scripts", "shell scripting", "batch processing", "performance tuning"],
                "examples": ["Optimize this bash script", "Create a PowerShell script to automate backups", "Improve the performance of this script"]
            },
            "phi": {
                "name": "Phi",
                "description": "Local model for offline use",
                "strengths": ["offline operation", "privacy", "local processing", "basic tasks", "fallback operations"],
                "examples": ["Basic questions when offline", "Private data processing", "Simple tasks without internet"]
            }
        }

        # Try to load from configuration file if available
        try:
            config_path = "configs/model_specializations.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded_specializations = json.load(f)
                    self.model_specializations.update(loaded_specializations)
                    logger.info(f"Loaded model specializations from {config_path}")
        except Exception as e:
            logger.error(f"Error loading model specializations: {str(e)}")

    async def route_query(self, query: str, context: Optional[Dict[str, Any]] = None, intent: str = None) -> Tuple[str, float]:
        """
        Route a query to the most appropriate model

        Args:
            query: User query
            context: Optional context information
            intent: Optional intent classification

        Returns:
            Tuple of (model_name, confidence)
        """
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in self.routing_cache:
            cached_result = self.routing_cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_result["timestamp"] < self.cache_ttl:
                logger.info(f"Using cached routing decision for '{query[:30]}...'")
                return cached_result["model"], cached_result["confidence"]

        # Check if we're in offline mode
        status = await self.model_interface.check_status()
        offline_mode = status.get("offline_mode", False)
        ollama_running = status.get("ollama", {}).get("running", False)

        # If we're in offline mode, route to Phi
        if offline_mode or (not await self.model_interface.check_internet() and ollama_running):
            # Even in offline mode, for simple greetings and chat queries, try to use Mistral if internet is available
            if await self.model_interface.check_internet() and (
                query.lower().strip() in ["hi", "hello", "hey", "what's up", "how are you"] or
                intent == "chat" or intent == "general" or intent == "greeting"
            ):
                logger.info(f"Online mode with chat/greeting, routing to mistral despite offline mode")
                return "mistral", 1.0
            else:
                logger.info(f"Offline mode active, routing to phi")
                return "phi", 1.0
        else:
            # If we're online and not in offline mode, never route to phi for these common queries
            if query.lower().strip() in ["hi", "hello", "hey", "what's up", "how are you"] or \
               intent == "chat" or intent == "general" or intent == "greeting":
                logger.info(f"Online mode with chat/greeting, routing to mistral")
                return "mistral", 1.0

        # Use Mistral-Small (via OpenRouter) to decide which model to route to
        try:
            # Prepare the routing prompt
            prompt = self._create_routing_prompt(query)

            # Call Mistral-Small via OpenRouter for routing decisions
            if hasattr(self.model_interface, 'call_openrouter'):
                model_id = MODEL_IDS["mistral"]
                response = await self.model_interface.call_openrouter(
                    model_id=model_id,
                    query=prompt,
                    max_tokens=100  # Short response needed
                )
            # No fallback to Gemini anymore, as we've replaced it with Mistral Small
            # Just log the error and return a default routing decision
            else:
                logger.error("No routing API method available")
                return "mistral", 0.5

            if response and response.get("success", False):
                # Parse the response to get the model and confidence
                model, confidence = self._parse_routing_response(response.get("content", ""))

                # Cache the result
                self.routing_cache[cache_key] = {
                    "model": model,
                    "confidence": confidence,
                    "timestamp": time.time()
                }

                logger.info(f"Routed '{query[:30]}...' to '{model}' with confidence {confidence:.2f}")
                return model, confidence
            else:
                # Fallback to mistral if routing fails
                logger.warning(f"Routing failed, falling back to mistral")
                return "mistral", 0.5

        except Exception as e:
            logger.error(f"Error during neural routing: {str(e)}")
            # Fallback to mistral
            return "mistral", 0.5

    def _create_routing_prompt(self, query: str) -> str:
        """
        Create a prompt for the main brain to decide which model to route to

        Args:
            query: User query

        Returns:
            Prompt for routing decision
        """
        # Create a list of model options with their specializations
        model_options = []
        for model_id, spec in self.model_specializations.items():
            strengths = ", ".join(spec["strengths"])
            model_options.append(f"- {spec['name']} ({model_id}): {spec['description']}. Strengths: {strengths}")

        model_options_str = "\n".join(model_options)

        # Create the prompt
        prompt = f"""ROUTING TASK:

Analyze the following user query and determine which specialized AI model would be best suited to handle it.

USER QUERY: "{query}"

AVAILABLE MODELS:
{model_options_str}

INSTRUCTIONS:
1. Analyze the query to understand its intent, domain, and complexity
2. Match the query characteristics with the strengths of the available models
3. Select the SINGLE most appropriate model for this query
4. Assign a confidence score (0.0 to 1.0) to your selection

RESPOND IN THIS EXACT FORMAT:
model: [model_id]
confidence: [score between 0.0 and 1.0]
reasoning: [brief explanation of your choice]

DO NOT include any other text in your response.
"""

        return prompt

    def _parse_routing_response(self, response: str) -> Tuple[str, float]:
        """
        Parse the routing response from the main brain

        Args:
            response: Response from the routing model

        Returns:
            Tuple of (model_name, confidence)
        """
        try:
            # Default values
            model = "mistral"
            confidence = 0.5

            # Extract model
            model_match = re.search(r"model:\s*(\w+)", response, re.IGNORECASE)
            if model_match:
                model_candidate = model_match.group(1).lower()
                # Validate the model
                if model_candidate in self.model_specializations:
                    model = model_candidate

            # Extract confidence
            confidence_match = re.search(r"confidence:\s*(0\.\d+|1\.0|1)", response, re.IGNORECASE)
            if confidence_match:
                try:
                    confidence = float(confidence_match.group(1))
                    # Ensure confidence is between 0 and 1
                    confidence = max(0.0, min(1.0, confidence))
                except ValueError:
                    pass

            return model, confidence

        except Exception as e:
            logger.error(f"Error parsing routing response: {str(e)}")
            return "mistral", 0.5

    async def get_routing_explanation(self, query: str, routed_model: str) -> str:
        """
        Get an explanation for why a query was routed to a specific model

        Args:
            query: User query
            routed_model: Model the query was routed to

        Returns:
            Explanation string
        """
        try:
            # Get model specialization
            spec = self.model_specializations.get(routed_model, {
                "name": routed_model.capitalize(),
                "description": "Unknown specialization",
                "strengths": []
            })

            # Create prompt for explanation
            prompt = f"""EXPLAIN ROUTING DECISION:

User query: "{query}"

This query was routed to the {spec['name']} model, which specializes in {spec['description']}.

Explain in 1-2 sentences why this model is appropriate for this query, based on the query's content and the model's strengths: {', '.join(spec.get('strengths', []))}

Keep your explanation concise and focused on the match between the query and the model's capabilities.
"""

            # Call Mistral-Small via OpenRouter for explanations
            if hasattr(self.model_interface, 'call_openrouter'):
                model_id = MODEL_IDS["mistral"]
                response = await self.model_interface.call_openrouter(
                    model_id=model_id,
                    query=prompt,
                    max_tokens=100  # Short explanation
                )
            # No fallback to Gemini anymore, as we've replaced it with Mistral Small
            # Just log the error and return a default explanation
            else:
                logger.error("No routing API method available for explanation")
                # Return a simple explanation
                strengths = ", ".join(spec.get("strengths", []))
                return f"This query was routed to {spec['name']} because it appears to involve {strengths}."

            if response and response.get("success", False):
                explanation = response.get("content", "").strip()
                return explanation
            else:
                # Fallback explanation
                strengths = ", ".join(spec.get("strengths", []))
                return f"This query was routed to {spec['name']} because it appears to involve {strengths}."

        except Exception as e:
            logger.error(f"Error generating routing explanation: {str(e)}")
            return f"This query was routed to {routed_model} based on its content."
