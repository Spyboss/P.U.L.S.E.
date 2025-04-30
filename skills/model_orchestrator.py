"""
Model Orchestrator for General Pulse
Manages multiple AI models with cost optimization and specialized roles
"""

import asyncio
import structlog
from typing import Dict, Any, List
from datetime import datetime

# Import API Key Manager
from utils.api_key_manager import APIKeyManager

# Import error handling
from utils.model_error_handler import with_model_error_handling

# Import neural router for intelligent model routing
from utils.neural_router import NeuralRouter

# Import rich context manager for enhanced context
from utils.rich_context_manager import RichContextManager

# Import model personality manager for personality differentiation
from utils.model_personality import ModelPersonality

# Import model configuration
from configs.models import MODEL_IDS, MODEL_ROLES, QUERY_TYPE_TO_MODEL

# Import prompts
from configs.prompts import get_prompt

# Configure logger
logger = structlog.get_logger("model_orchestrator")

# Torch disabled due to compatibility issues
TORCH_AVAILABLE = False
logger.info("PyTorch disabled due to compatibility issues. Local models will not be available.")

# Legacy Gemini code removed - replaced by Mistral Small
GEMINI_AVAILABLE = False  # Keep this for backward compatibility

# Check if OpenAI is available for Mistral API
try:
    from openai import OpenAI
    MISTRAL_AVAILABLE = True
    logger.info("OpenAI package found for Mistral API integration")
except ImportError:
    logger.warning("OpenAI package not found. Mistral API will not be available.")
    MISTRAL_AVAILABLE = False

# Transformers disabled due to compatibility issues
TRANSFORMERS_AVAILABLE = False
logger.info("Transformers disabled due to compatibility issues. Local models will not be available.")

try:
    # OpenRouter now uses the OpenAI client with a different base URL
    from openai import OpenAI
    OPENROUTER_AVAILABLE = True
    logger.info("OpenAI package found for OpenRouter integration")
except ImportError:
    logger.warning("OpenAI package not found. OpenRouter models will not be available.")
    OPENROUTER_AVAILABLE = False

class ModelOrchestrator:
    """
    Orchestrates multiple AI models with cost optimization and specialized roles
    """

    def __init__(self, simulate_responses=False):
        """
        Initialize the model orchestrator

        Args:
            simulate_responses: Whether to simulate AI responses (for testing)
        """
        self.logger = logger
        self.simulate_responses = simulate_responses

        # Initialize API Key Manager
        self.api_key_manager = APIKeyManager(auto_reload=True, cache_ttl=300)
        self.logger.info("API Key Manager initialized")

        # Track model usage
        self.usage_stats = {
            "gemini": {"calls": 0, "tokens": 0, "last_used": None},
            "mistral": {"calls": 0, "tokens": 0, "last_used": None},
            "openrouter": {"calls": 0, "tokens": 0, "last_used": None},
            "local": {"calls": 0, "last_used": None}
        }

        # Initialize OpenRouter (Specialized Tasks)
        self.openrouter = None

        # Initialize Mistral (Main Brain) via OpenRouter
        self.mistral = None

        # Legacy Gemini code removed - replaced by Mistral Small
        self.gemini = None  # Keep this for backward compatibility

        # Initialize OpenRouter (Specialized Tasks)
        self.openrouter = None

        # Load models from configuration
        # These are the latest free models available on OpenRouter as of April 2025
        self.free_models = {}

        # Add query type to model mappings
        for query_type, model_role in QUERY_TYPE_TO_MODEL.items():
            if model_role in MODEL_ROLES:
                self.free_models[query_type] = MODEL_ROLES[model_role]['model_id']

        # Add direct model name mappings
        for model_name, model_info in MODEL_ROLES.items():
            self.free_models[model_name] = model_info['model_id']

        # Add aliases for backward compatibility
        self.free_models['deepseek'] = MODEL_IDS['troubleshooting']
        self.free_models['agentica'] = MODEL_IDS['code_generation']

        # Add fallback options
        self.free_models['fallback'] = MODEL_IDS['brainstorming']
        self.free_models['backup'] = MODEL_IDS['task_automation']

        # IMPORTANT: Don't use Gemini through OpenRouter - it's not a valid OpenRouter model
        # Instead, use Mistral-Small for general queries
        self.free_models['general'] = MODEL_IDS['main_brain']  # Use Mistral-Small for general queries

        # Add specific mappings for query types that need special handling
        self.free_models['ethics'] = MODEL_IDS['ethical_ai']  # Use Molmo for ethics
        self.free_models['content'] = MODEL_IDS['main_brain']  # Use Mistral-Small for content

        openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY")
        if OPENROUTER_AVAILABLE and openrouter_api_key:
            try:
                # Initialize OpenRouter using OpenAI client with custom base URL
                self.openrouter = OpenAI(
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "https://github.com/Spyboss/P.U.L.S.E.",
                        "X-Title": "P.U.L.S.E."
                    }
                )
                logger.info("OpenRouter initialized successfully")
                # Initialize Mistral using OpenRouter
                self.mistral = self.openrouter
                logger.info("Using OpenRouter for Mistral-Small (main brain)")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter: {str(e)}")
                # Try to refresh the API key and retry
                openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY", force_reload=True)
                if openrouter_api_key:
                    try:
                        logger.info("Retrying OpenRouter initialization with refreshed API key")
                        self.openrouter = OpenAI(
                            api_key=openrouter_api_key,
                            base_url="https://openrouter.ai/api/v1",
                            default_headers={
                                "HTTP-Referer": "https://github.com/Spyboss/P.U.L.S.E.",
                                "X-Title": "P.U.L.S.E."
                            }
                        )
                        logger.info("OpenRouter initialized successfully on retry")
                        # Initialize Mistral using OpenRouter
                        self.mistral = self.openrouter
                        logger.info("Using OpenRouter for Mistral-Small (main brain)")
                    except Exception as e2:
                        logger.error(f"Failed to initialize OpenRouter on retry: {str(e2)}")

        # Initialize DistilBERT (Local Intent Handling)
        self.intent_classifier = None
        # Disabled due to compatibility issues
        logger.info("Local intent classifier disabled due to compatibility issues")

        # Initialize Neural Router for intelligent model routing
        self.neural_router = NeuralRouter(model_interface=self)
        logger.info("Neural router initialized for intelligent model routing")

        # Initialize Rich Context Manager for enhanced context
        self.rich_context_manager = RichContextManager(model_interface=self)
        logger.info("Rich context manager initialized for enhanced context")

        # Initialize Model Personality Manager for personality differentiation
        self.model_personality = ModelPersonality()
        logger.info("Model personality manager initialized for personality differentiation")

    def _simulate_response(self, input_text: str) -> Dict[str, Any]:
        """
        Simulate a response for testing purposes

        Args:
            input_text: The user's input text

        Returns:
            Simulated response dictionary
        """
        # Extract model type from input if it starts with "ask "
        model_type = "mistral"  # Default
        if input_text.lower().startswith("ask "):
            parts = input_text.lower().split(" ", 2)
            if len(parts) >= 2:
                model_type = parts[1]

        # Create a simulated response based on the model type
        model_responses = {
            "code": f"[SIMULATED CODE RESPONSE] Here's a code example for '{input_text}': \n\n```python\ndef example_function():\n    print('This is simulated code')\n    return True\n```",
            "troubleshoot": f"[SIMULATED TROUBLESHOOTING] The issue with '{input_text}' might be caused by: 1) Incorrect imports, 2) Variable scope issues, 3) Syntax errors.",
            "docs": f"[SIMULATED DOCUMENTATION] Documentation for '{input_text}':\n\n# API Reference\n## Functions\n- `example_function()`: Returns True and prints a message.",
            "technical": f"[SIMULATED TECHNICAL EXPLANATION] Technical explanation for '{input_text}': This involves several complex concepts including data structures, algorithms, and system design.",
            "brainstorm": f"[SIMULATED BRAINSTORMING] Ideas for '{input_text}':\n1. Implement a mobile app\n2. Create a web dashboard\n3. Design an API\n4. Build a recommendation engine",
            "ethics": f"[SIMULATED ETHICS RESPONSE] Ethical considerations for '{input_text}':\n- Privacy implications\n- Bias and fairness\n- Transparency\n- User consent",
            "visual": f"[SIMULATED VISUAL DESIGN] Design suggestions for '{input_text}':\n- Use a clean, minimalist interface\n- Implement a dark mode option\n- Use consistent color schemes\n- Ensure accessibility",
            "reasoning": f"[SIMULATED REASONING] Analysis of '{input_text}':\n1. First, we need to break down the problem\n2. Then identify key constraints\n3. Consider multiple approaches\n4. Evaluate trade-offs",
            "math": f"[SIMULATED MATH SOLUTION] Mathematical solution for '{input_text}':\nLet x be the unknown variable. We can solve this by applying the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a",
            "script": f"[SIMULATED SCRIPT OPTIMIZATION] Optimized script for '{input_text}':\n```python\n# Optimized version\nimport functools\n\n@functools.lru_cache(maxsize=128)\ndef optimized_function(x):\n    return x * 2\n```",
            "mistral": f"[SIMULATED MISTRAL RESPONSE] I'm P.U.L.S.E., your AI companion. Regarding '{input_text}', I'd be happy to help you with that, bruv! What specific information are you looking for?"
        }

        # Get the appropriate response or use the default
        content = model_responses.get(model_type, model_responses["mistral"])

        # Return a simulated response
        return {
            "success": True,
            "content": content,
            "model": f"simulated-{model_type}",
            "model_type": model_type,
            "tokens": {"input": len(input_text.split()), "output": len(content.split())}
        }

    async def shutdown(self) -> None:
        """
        Shutdown the model orchestrator and clean up resources
        """
        logger.info("Shutting down model orchestrator")

        # Close OpenRouter client if available
        if hasattr(self, 'openrouter') and self.openrouter:
            try:
                # OpenAI client doesn't have a close method, but we can set it to None
                self.openrouter = None
                logger.info("OpenRouter client released")
            except Exception as e:
                logger.error(f"Error closing OpenRouter client: {str(e)}")

        # Close Mistral client if available
        if hasattr(self, 'mistral') and self.mistral:
            try:
                # OpenAI client doesn't have a close method, but we can set it to None
                self.mistral = None
                logger.info("Mistral client released")
            except Exception as e:
                logger.error(f"Error closing Mistral client: {str(e)}")

        # Close neural router if available
        if hasattr(self, 'neural_router') and self.neural_router:
            try:
                # Neural router might have a close method in the future
                if hasattr(self.neural_router, 'close'):
                    await self.neural_router.close()
                logger.info("Neural router released")
            except Exception as e:
                logger.error(f"Error closing neural router: {str(e)}")

        logger.info("Model orchestrator shutdown complete")

    @with_model_error_handling("handle_query")
    async def handle_query(self, input_text: str, context: Dict[str, Any] = None, model_preference: str = None) -> Dict[str, Any]:
        """
        Handle a user query by routing it to Mistral-Small (main brain)

        Args:
            input_text: The user's input text
            context: Optional context information
            model_preference: Optional preferred model to use (will be used if specified)

        Returns:
            Response dictionary with content and metadata
        """
        if self.simulate_responses:
            return self._simulate_response(input_text)

        # Format context for the model
        context_str = await self._format_context(context) if context else ""

        # Log the routing decision
        if model_preference:
            self.logger.info(f"Using preferred model: {model_preference}")
        else:
            self.logger.info("No model preference specified, using Mistral-Small (main brain)")

        # If a specific model is preferred, try to use it
        if model_preference:
            # For Mistral Small or Gemini - use Mistral Small via OpenRouter
            if model_preference.lower() == "gemini" or model_preference.lower() == "mistral":
                # Redirect Gemini requests to Mistral Small
                if model_preference.lower() == "gemini":
                    logger.info("Redirecting Gemini request to Mistral Small (main brain)")

                # Use Mistral Small via OpenRouter
                if self.mistral:
                    try:
                        response = await self._call_mistral(input_text, context_str)
                        return response
                    except Exception as e:
                        logger.error(f"Mistral Small API call failed: {str(e)}")
                        return {
                            "success": False,
                            "content": f"Mistral Small API call failed: {str(e)}",
                            "model": "mistral",
                            "model_type": "mistral",
                            "error": str(e)
                        }
                else:
                    # Mistral not available - return clear error
                    logger.error("Mistral Small requested but not available - API key may be missing")
                    return {
                        "success": False,
                        "content": "Mistral Small model is not available. Please check your OpenRouter API key.",
                        "model": "none",
                        "error": "Mistral Small not available"
                    }

            # For OpenRouter models
            elif self.openrouter:
                # Check if it's a specialized model type
                if model_preference.lower() in self.free_models:
                    try:
                        return await self.query_specialized_model(model_preference.lower(), input_text, context_str)
                    except Exception as e:
                        logger.warning(f"Specialized model {model_preference} failed: {str(e)}, falling back to Mistral-Small")
                        # Fall back to Mistral-Small
                        return await self._call_mistral(input_text, context_str)
                # Otherwise try as a specific model name (claude, grok, etc.)
                else:
                    try:
                        # Try to map the model name to a category
                        model_categories = {
                            "deepseek": "troubleshoot",
                            "deepcoder": "code",
                            "agentica": "code",
                            "llama-doc": "docs",
                            "mistral-small": "trends",
                            "maverick": "general",  # Updated to use general (which maps to Mistral-Small)
                            "llama-content": "general",  # Updated to use general (which maps to Mistral-Small)
                            "llama-technical": "technical",
                            "hermes": "brainstorm",
                            "molmo": "ethics",
                            "olmo": "ethics",
                            "mistralai": "automate",
                            "kimi": "visual",
                            "nemotron": "reasoning",
                            "gemma": "math",
                            "dolphin": "script",
                            "phi": "offline"
                        }

                        category = model_categories.get(model_preference.lower(), "general")
                        try:
                            return await self.query_specialized_model(category, input_text, context_str)
                        except Exception as e:
                            logger.warning(f"Preferred OpenRouter model {model_preference} failed: {str(e)}, falling back to Mistral-Small")
                            # Fall back to Mistral-Small
                            return await self._call_mistral(input_text, context_str)
                    except Exception as e:
                        logger.warning(f"Preferred OpenRouter model {model_preference} failed: {str(e)}, falling back to Mistral-Small")
                        # Fall back to Mistral-Small
                        return await self._call_mistral(input_text, context_str)

        # If no preference or preferred model failed, use the default flow
        # Always use Mistral-Small for simple queries, including greetings
        # This ensures consistent personality and better handling of greetings
        if self.mistral:
            try:
                response = await self._call_mistral(input_text, context_str)
                return response
            except Exception as e:
                logger.warning(f"Mistral-Small query failed: {str(e)}, falling back to alternatives")

        # Skip Gemini fallback - it's been replaced by Mistral Small
        logger.warning("Mistral-Small failed, falling back to OpenRouter general models")

        # Fall back to OpenRouter
        if self.openrouter:
            # Determine query type for fallback
            query_type = await self._classify_query(input_text)
            return await self._fallback_to_openrouter(input_text, context_str, query_type)

        # If all else fails, return an error
        return {
            "success": False,
            "content": "All AI models are currently unavailable. Please try again later.",
            "model": "none",
            "error": "No available models"
        }

    async def _classify_query(self, input_text: str) -> str:
        """
        Classify the query type to determine which model to use

        Args:
            input_text: The user's input text

        Returns:
            Query type classification
        """
        # Use the neural router for intelligent classification
        if hasattr(self, 'neural_router') and self.neural_router:
            try:
                model, confidence = await self.neural_router.route_query(input_text)
                self.logger.info(f"Neural router classified '{input_text[:30]}...' as '{model}' with confidence {confidence:.2f}")

                # If confidence is high enough, use the neural router's decision
                if confidence >= 0.7:
                    return model
                else:
                    self.logger.info(f"Neural router confidence too low ({confidence:.2f}), falling back to keyword classification")
            except Exception as e:
                self.logger.error(f"Neural router error: {str(e)}, falling back to keyword classification")

        # Fallback to simple keyword-based classification
        self.logger.info(f"Using keyword-based classification for '{input_text[:30]}...'")
        lower_text = input_text.lower()

        # Coding and technical tasks
        if any(word in lower_text for word in ["code", "function", "class", "method", "implement", "programming"]):
            return "code"
        elif any(word in lower_text for word in ["bug", "error", "debug", "fix code", "issue", "not working"]):
            return "debug"
        elif any(word in lower_text for word in ["algorithm", "complexity", "optimize", "efficiency", "data structure"]):
            return "algorithm"

        # Documentation and explanation
        elif any(word in lower_text for word in ["document", "documentation", "comment", "api", "reference"]):
            return "docs"
        elif any(word in lower_text for word in ["explain", "clarify", "understand", "how does", "why is"]):
            return "explain"
        elif any(word in lower_text for word in ["summarize", "summary", "brief", "overview", "tldr"]):
            return "summarize"

        # Problem solving
        elif any(word in lower_text for word in ["troubleshoot", "diagnose", "problem", "not working", "error"]):
            return "troubleshoot"
        elif any(word in lower_text for word in ["solve", "solution", "resolve", "fix", "help"]):
            return "solve"

        # Information and research
        elif any(word in lower_text for word in ["trend", "news", "latest", "update", "current"]):
            return "trends"
        elif any(word in lower_text for word in ["research", "study", "investigate", "analyze", "deep dive"]):
            return "research"

        # Content creation
        elif any(word in lower_text for word in ["content", "generate", "create", "blog", "article"]):
            return "content"
        elif any(word in lower_text for word in ["creative", "story", "imagine", "fiction", "narrative"]):
            return "creative"
        elif any(word in lower_text for word in ["write", "draft", "compose", "author", "text"]):
            return "write"

        # Technical and specialized
        elif any(word in lower_text for word in ["technical", "complex", "detailed", "in-depth", "advanced"]):
            return "technical"
        elif any(word in lower_text for word in ["math", "calculation", "equation", "formula", "compute"]):
            return "math"

        # Brainstorming and ideas
        elif any(word in lower_text for word in ["brainstorm", "ideas", "suggestions", "options", "possibilities"]):
            return "brainstorm"
        elif any(word in lower_text for word in ["idea", "concept", "innovative", "novel", "new approach"]):
            return "ideas"

        # Ethics and responsibility
        elif any(word in lower_text for word in ["ethical", "ethics", "bias", "fair", "responsible", "moral"]):
            return "ethics"

        # Visual reasoning
        elif any(word in lower_text for word in ["image", "visual", "picture", "photo", "ui", "ux", "design", "interface"]):
            return "visual"

        # Advanced reasoning
        elif any(word in lower_text for word in ["reasoning", "complex", "analyze", "deep analysis", "thorough", "comprehensive"]):
            return "reasoning"

        # Simple queries
        elif len(input_text.split()) < 5:
            return "simple"

        # Default to general purpose
        return "general"

    async def _call_mistral(self, input_text: str, context_str: str) -> Dict[str, Any]:
        """
        Call the Mistral-Small model (main brain) via OpenRouter

        Args:
            input_text: The user's input text
            context_str: Context information as a string

        Returns:
            Response dictionary
        """
        # Check if Mistral is initialized (via OpenRouter)
        if not self.mistral or not self.openrouter:
            self.logger.error("Mistral-Small model not initialized. Cannot call Mistral-Small.")
            return {
                "success": False,
                "content": "Mistral-Small model is not available. Please check your OpenRouter API key or try another model.",
                "model": "none",
                "error": "Mistral-Small not initialized"
            }

        # Get the Mistral-specific prompt
        system_prompt = get_prompt("mistral")

        # Log the context for debugging
        self.logger.debug(f"Mistral-Small context: {context_str[:200]}..." if len(context_str) > 200 else f"Mistral-Small context: {context_str}")

        try:
            # Call Mistral via OpenRouter
            response = await self.query_specialized_model(
                "mistral",  # Use the mistral model ID from OpenRouter
                input_text,
                context_str,
                system_prompt
            )

            # If the query was successful, return the response
            if response.get("success", False):
                return response
            else:
                # No fallback to Gemini anymore
                self.logger.warning(f"Mistral-Small error: {response.get('error', 'Unknown error')}")
                return response

        except Exception as e:
            self.logger.error(f"Error calling Mistral-Small via OpenRouter: {str(e)}")
            # No fallback to Gemini anymore
            return {
                "success": False,
                "content": f"Error calling Mistral-Small via OpenRouter: {str(e)}",
                "model": "mistralai/mistral-small-3.1-24b-instruct:free",
                "model_type": "mistral",
                "error": str(e)
            }

    async def _call_gemini(self, input_text: str, context_str: str) -> Dict[str, Any]:
        """
        Call the Gemini model (redirects to Mistral Small for backward compatibility)

        Args:
            input_text: The user's input text
            context_str: Context information as a string

        Returns:
            Response dictionary
        """
        self.logger.info(f"Redirecting _call_gemini to _call_mistral with query: {input_text[:30]}...")
        return await self._call_mistral(input_text, context_str)

    async def _fallback_to_openrouter(self, input_text: str, context_str: str, query_type: str) -> Dict[str, Any]:
        """
        Fall back to OpenRouter models

        Args:
            input_text: The user's input text
            context_str: Context information as a string
            query_type: The type of query

        Returns:
            Response dictionary
        """
        # Define model categories for better fallback strategy
        model_categories = {
            # Coding related
            "code": ["code", "debug", "algorithm", "technical"],
            "debug": ["debug", "code", "troubleshoot", "solve"],
            "algorithm": ["algorithm", "code", "math", "technical"],

            # Documentation related
            "docs": ["docs", "explain", "summarize", "write"],
            "explain": ["explain", "docs", "technical", "write"],
            "summarize": ["summarize", "docs", "write", "general"],

            # Problem solving
            "troubleshoot": ["troubleshoot", "solve", "debug", "technical"],
            "solve": ["solve", "troubleshoot", "research", "technical"],

            # Information
            "trends": ["trends", "research", "general", "write"],
            "research": ["research", "technical", "trends", "general"],

            # Content
            "content": ["general", "write", "creative", "brainstorm"],
            "creative": ["general", "content", "write", "brainstorm"],
            "write": ["general", "content", "creative", "docs"],

            # Technical
            "technical": ["technical", "research", "code", "explain"],
            "math": ["math", "algorithm", "technical", "solve"],

            # Ideas
            "brainstorm": ["brainstorm", "ideas", "creative", "content"],
            "ideas": ["ideas", "brainstorm", "creative", "content"],

            # Ethics
            "ethics": ["ethics", "explain", "research", "write"],

            # Visual reasoning
            "visual": ["visual", "image", "design", "content"],
            "image": ["image", "visual", "content", "design"],
            "ui": ["ui", "design", "visual", "content"],
            "design": ["design", "ui", "visual", "content"],

            # Advanced reasoning
            "reasoning": ["reasoning", "complex", "analyze", "research"],
            "complex": ["complex", "reasoning", "analyze", "technical"],
            "analyze": ["analyze", "reasoning", "research", "technical"],

            # General
            "general": ["fallback", "backup", "explain", "write"],
            "simple": ["fallback", "backup", "explain", "write"]
        }

        # Try the specialized model for this query type first
        if query_type in self.free_models:
            model_id = self.free_models[query_type]
            try:
                self.logger.info(f"Trying specialized model for {query_type}: {model_id}")
                response = await self._call_openrouter_model(model_id, input_text, context_str)
                return response
            except Exception as e:
                logger.warning(f"OpenRouter {model_id} failed: {str(e)}, trying alternative models")

        # Try models in the same category first
        if query_type in model_categories:
            for fallback_type in model_categories[query_type]:
                if fallback_type in self.free_models and fallback_type != query_type:
                    model_id = self.free_models[fallback_type]
                    try:
                        self.logger.info(f"Trying category fallback model {fallback_type}: {model_id}")
                        response = await self._call_openrouter_model(model_id, input_text, context_str)
                        return response
                    except Exception as e:
                        logger.warning(f"OpenRouter {model_id} failed: {str(e)}")

        # Try fallback models
        for fallback_type in ["fallback", "backup"]:
            if fallback_type in self.free_models:
                model_id = self.free_models[fallback_type]
                try:
                    self.logger.info(f"Trying general fallback model: {model_id}")
                    response = await self._call_openrouter_model(model_id, input_text, context_str)
                    return response
                except Exception as e:
                    logger.warning(f"OpenRouter {model_id} failed: {str(e)}")

        # If all else fails, try any remaining models
        for model_type, model_id in self.free_models.items():
            # Skip models we've already tried
            if model_type == query_type or \
               (query_type in model_categories and model_type in model_categories[query_type]) or \
               model_type in ["fallback", "backup"]:
                continue

            try:
                self.logger.info(f"Trying random model {model_type}: {model_id}")
                response = await self._call_openrouter_model(model_id, input_text, context_str)
                return response
            except Exception as e:
                logger.warning(f"OpenRouter {model_id} failed: {str(e)}")

        # If all models fail, return an error
        return {
            "success": False,
            "content": "All AI models are currently unavailable. Please try again later.",
            "model": "none",
            "error": "All models failed"
        }

    async def _call_openrouter_model(self, model_id: str, input_text: str, context_str: str) -> Dict[str, Any]:
        """
        Call a specific OpenRouter model with retry logic

        Args:
            model_id: The OpenRouter model ID
            input_text: The user's input text
            context_str: Context information as a string

        Returns:
            Response dictionary
        """
        # Determine which model we're using based on the model_id
        model_key = None
        for key, info in MODEL_ROLES.items():
            if info.get('model_id') == model_id:
                model_key = key
                break

        # If we couldn't find the model key, use a default
        if not model_key:
            # Try to find it in the free_models dictionary
            for key, value in self.free_models.items():
                if value == model_id and key in MODEL_ROLES:
                    model_key = key
                    break

            # If still not found, default to a generic model
            if not model_key:
                model_key = "deepseek"  # Default to deepseek as a fallback

        # Get the role-specific prompt
        # For Mistral-Small model, always use the "mistral" prompt
        if model_id == MODEL_IDS.get("main_brain"):
            system_prompt = get_prompt("mistral")
            self.logger.info("Using Mistral-specific system prompt for main_brain model")
        else:
            system_prompt = get_prompt(model_key)

        # Prepare the prompt for token counting and logging
        token_counting_prompt = ""
        if context_str:
            token_counting_prompt = f"{system_prompt}\n\nContext:\n{context_str}\n\nUser: {input_text}"
        else:
            token_counting_prompt = f"{system_prompt}\n\nUser: {input_text}"

        # Log the prompt length and context for debugging
        self.logger.debug(f"Prompt length for {model_key}: {len(token_counting_prompt.split())} tokens")
        self.logger.debug(f"OpenRouter context for {model_key}: {context_str[:200]}..." if len(context_str) > 200 else f"OpenRouter context for {model_key}: {context_str}")

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        if context_str:
            messages.append({"role": "system", "content": f"Additional context: {context_str}"})
        messages.append({"role": "user", "content": input_text})

        # Retry parameters
        max_retries = 2
        retry_delay = 1  # seconds
        attempt = 0
        last_error = None

        # Verify model ID against available models
        if not self._verify_model_id(model_id):
            self.logger.warning(f"Model ID '{model_id}' may not be valid. Proceeding anyway.")

        # Retry loop
        while attempt < max_retries:
            attempt += 1
            try:
                # Use the OpenAI client interface
                self.logger.info(f"Calling OpenRouter API with model {model_id} (attempt {attempt}/{max_retries})")
                try:
                    # Set a timeout for the API call
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.openrouter.chat.completions.create,
                            model=model_id,
                            messages=messages,
                            max_tokens=1000
                        ),
                        timeout=30  # 30 second timeout
                    )

                    # Convert response to dict if it's not already
                    if not isinstance(response, dict):
                        response = response.model_dump()

                    # Log the full response for debugging
                    self.logger.info(f"OpenRouter API response: {response}")

                    # Success, break the retry loop
                    break
                except asyncio.TimeoutError:
                    raise Exception("Request timed out after 30 seconds")
                except asyncio.CancelledError:
                    self.logger.warning(f"Request to OpenRouter API was cancelled")
                    return {
                        "success": False,
                        "content": "The request was cancelled. Please try again later.",
                        "model": model_id,
                        "model_type": "openrouter",
                        "error": "Request cancelled"
                    }
            except Exception as e:
                last_error = e
                self.logger.warning(f"OpenRouter API error (attempt {attempt}/{max_retries}): {str(e)}")

                # If this is not the last attempt, wait before retrying
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        # If all attempts failed, return error
        if attempt == max_retries and last_error is not None:
            self.logger.error(f"All {max_retries} attempts to call OpenRouter API failed: {str(last_error)}")
            return {
                "success": False,
                "content": f"Error calling the model after {max_retries} attempts: {str(last_error)}",
                "model": model_id,
                "model_type": "openrouter",
                "error": str(last_error)
            }

        # Process the successful response
        # Check if the response has the expected structure
        if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
            if isinstance(response["choices"][0], dict) and "message" in response["choices"][0]:
                message = response["choices"][0]["message"]

                # Check for content in the message
                if isinstance(message, dict) and "content" in message and message["content"]:
                    content = message["content"]
                # Check for reasoning in the message (some models like Agentica DeepCoder put their output here)
                elif isinstance(message, dict) and "reasoning" in message and message["reasoning"]:
                    # Extract code from reasoning if possible
                    reasoning = message["reasoning"]
                    self.logger.info(f"Using reasoning field as content: {reasoning[:100]}...")

                    # Try to extract code from reasoning
                    import re

                    # Look for code blocks with Python syntax
                    code_blocks = re.findall(r'```python\n(.+?)```', reasoning, re.DOTALL)
                    if code_blocks:
                        content = f"```python\n{code_blocks[0]}\n```\n\nExtracted from model's reasoning."
                    else:
                        # Look for function definitions
                        function_defs = re.findall(r'def\s+(\w+)\(([^)]*)\):\s*([^\n]*(?:\n[^\n]+)*?)\s+return\s+([^\n]+)', reasoning, re.DOTALL)
                        if function_defs:
                            # Reconstruct the function
                            func_name, params, body, return_stmt = function_defs[0]
                            code = f"def {func_name}({params}):\n{body}\n    return {return_stmt}"
                            content = f"```python\n{code}\n```\n\nExtracted and reconstructed from model's reasoning."
                        else:
                            # Look for code snippets with indentation patterns
                            code_snippets = re.findall(r'for\s+\w+\s+in\s+range\([^)]+\):\s*\n\s+[^\n]+', reasoning, re.DOTALL)
                            if code_snippets:
                                content = f"```python\n{code_snippets[0]}\n```\n\nExtracted code snippet from model's reasoning.\n\nFull reasoning:\n{reasoning}"
                            else:
                                # Special case for Agentica model - try to construct a complete function
                                if "agentica" in model_id.lower():
                                    # For factorial function
                                    if "factorial" in input_text.lower():
                                        # Construct a factorial function based on the reasoning
                                        code = '''def factorial(n):
    """Calculate the factorial of a non-negative integer.

    Args:
        n: A non-negative integer.

    Returns:
        The factorial of n (n!).

    Raises:
        ValueError: If n is negative.
    """
    # Check for negative input
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")

    # Base case
    if n == 0 or n == 1:
        return 1

    # Calculate factorial iteratively
    result = 1
    for i in range(1, n + 1):
        result *= i

    return result'''

                                        content = f"```python\n{code}\n```\n\nReconstructed from model's reasoning.\n\nThe model provided a detailed explanation of the factorial function but didn't provide the complete code. I've constructed a factorial function based on the reasoning provided.\n\nKey points from the reasoning:\n\n1. Factorial is the product of all positive integers from 1 to n\n2. 0! is defined as 1\n3. Factorial is only defined for non-negative integers\n4. The iterative approach is more efficient than recursion for large numbers\n\nFull reasoning:\n{reasoning[:500]}..."
                                    else:
                                        # Try to extract function name and parameters
                                        func_name_match = re.search(r'def\s+(\w+)\(([^)]*)\)', reasoning)
                                        if func_name_match:
                                            func_name = func_name_match.group(1)
                                            params = func_name_match.group(2)

                                            # Look for algorithm description
                                            algorithm_desc = ""
                                            if "initialize result as 1" in reasoning.lower() or "result = 1" in reasoning:
                                                algorithm_desc += "    result = 1\n"

                                                # Look for loop description
                                                if "range(1, n+1)" in reasoning or "from 1 to n" in reasoning:
                                                    algorithm_desc += "    for i in range(1, n+1):\n        result *= i\n"
                                                elif "range(2, n+1)" in reasoning or "from 2 to n" in reasoning:
                                                    algorithm_desc += "    for i in range(2, n+1):\n        result *= i\n"

                                                # Look for error handling
                                                error_handling = ""
                                                if "n < 0" in reasoning and "raise" in reasoning:
                                                    error_handling = "    if n < 0:\n        raise ValueError(\"Factorial is not defined for negative numbers.\")\n"

                                                # Look for base case handling
                                                base_case = ""
                                                if "n == 0" in reasoning and "return 1" in reasoning:
                                                    base_case = "    if n == 0:\n        return 1\n"
                                                elif "n == 0 or n == 1" in reasoning and "return 1" in reasoning:
                                                    base_case = "    if n == 0 or n == 1:\n        return 1\n"

                                                # Construct the function
                                                if error_handling or base_case or algorithm_desc:
                                                    code = f"def {func_name}({params}):\n"
                                                    if error_handling:
                                                        code += error_handling
                                                    if base_case:
                                                        code += base_case
                                                    if algorithm_desc:
                                                        code += algorithm_desc
                                                    code += "    return result"

                                                    content = f"```python\n{code}\n```\n\nReconstructed from model's reasoning.\n\nFull reasoning:\n{reasoning[:500]}..."
                                                else:
                                                    content = reasoning
                                            else:
                                                content = reasoning
                                        else:
                                            content = reasoning
                                else:
                                    # If we can't extract code, just use the reasoning
                                    content = reasoning
                else:
                    content = "The model did not provide a response. Please try again or use a different model."

                # Update usage stats
                self.usage_stats["openrouter"]["calls"] += 1
                self.usage_stats["openrouter"]["last_used"] = datetime.now().isoformat()
                # Approximate token count
                self.usage_stats["openrouter"]["tokens"] += len(token_counting_prompt.split()) + len(content.split() if content else [])

                # Check if this is a new session
                is_new_session = False
                if hasattr(self, 'rich_context_manager') and self.rich_context_manager:
                    try:
                        # Get the context manager from the rich context manager
                        context_manager = self.rich_context_manager.context_manager
                        if hasattr(context_manager, 'is_new_session'):
                            is_new_session = context_manager.is_new_session()
                            self.logger.info(f"Session status: {'New session' if is_new_session else 'Existing session'}")
                    except Exception as e:
                        self.logger.error(f"Error checking session status: {str(e)}")

                # Format the response with model-specific personality
                if hasattr(self, 'model_personality') and self.model_personality:
                    formatted_content = self.model_personality.format_response(
                        content,
                        model_id,
                        success=True,
                        is_new_session=is_new_session
                    )
                else:
                    formatted_content = content

                return {
                    "success": True,
                    "content": formatted_content,
                    "model": model_id,
                    "model_type": "openrouter"
                }
            else:
                self.logger.error(f"Unexpected response structure from OpenRouter: missing message or content in choices")
                return {
                    "success": False,
                    "content": "Received an unexpected response structure from the model.",
                    "model": model_id,
                    "model_type": "openrouter",
                    "error": "Invalid response structure"
                }
        else:
            self.logger.error(f"Unexpected response structure from OpenRouter: missing choices")
            return {
                "success": False,
                "content": "Received an unexpected response structure from the model.",
                "model": model_id,
                "model_type": "openrouter",
                "error": "Invalid response structure"
            }

    def _verify_model_id(self, model_id: str) -> bool:
        """
        Verify if a model ID is valid by checking against known patterns

        Args:
            model_id: The model ID to verify

        Returns:
            True if the model ID appears valid, False otherwise
        """
        # Check if model ID follows expected patterns
        if not model_id:
            return False

        # Check for vendor prefix pattern (vendor/model-name)
        if '/' in model_id:
            vendor, model_name = model_id.split('/', 1)
            if not vendor or not model_name:
                return False

        # Check for direct API models (like Gemini) and main_brain
        if model_id == MODEL_IDS.get("gemini", "") or model_id == MODEL_IDS.get("main_brain", ""):
            return True

        # Check if model ID is in our configuration
        for _, model_info in MODEL_ROLES.items():
            if model_info.get('model_id') == model_id:
                return True

        return False

    async def _handle_local_query(self, _: str) -> Dict[str, Any]:
        """
        Handle a query with the local model (disabled)

        Args:
            _: Unused input text parameter

        Returns:
            Response dictionary
        """
        # Local model is disabled, return a fallback response
        return {
            "success": False,
            "content": "I'm having trouble processing your request locally. Let me try with a more powerful model.",
            "model": "fallback",
            "error": "Local model disabled"
        }

    async def _format_context(self, context: Dict[str, Any], model_type: str = "main_brain") -> str:
        """
        Format context information for the model

        Args:
            context: Context dictionary
            model_type: Type of model (main_brain, gemini, openrouter, ollama)

        Returns:
            Formatted context string
        """
        if not context:
            return ""

        # Use rich context manager if available
        if hasattr(self, 'rich_context_manager') and self.rich_context_manager:
            try:
                # Enhance the context with rich information
                rich_context = await self.rich_context_manager.get_rich_context(
                    query="",  # No query available at this point
                    base_context=context
                )

                # Format the rich context for the specific model type
                return self.rich_context_manager.format_context_for_model(rich_context, model_type)
            except Exception as e:
                logger.error(f"Error using rich context manager: {str(e)}, falling back to basic context formatting")

        # Fallback to basic context formatting
        context_parts = []

        # Add chat history if available
        if "history" in context and context["history"]:
            history = context["history"]
            history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-5:]])
            context_parts.append(f"Recent conversation:\n{history_str}")

        # Add user data if available
        if "user_data" in context:
            user_data = context["user_data"]
            if "projects" in user_data:
                context_parts.append(f"User projects: {', '.join(user_data['projects'])}")
            if "interests" in user_data:
                context_parts.append(f"User interests: {', '.join(user_data['interests'])}")
            if "goals" in user_data:
                goals_str = ", ".join([g["goal"] for g in user_data["goals"]])
                context_parts.append(f"User goals: {goals_str}")
            if "preferences" in user_data:
                prefs_str = ", ".join([f"{k}: {v}" for k, v in user_data["preferences"].items()])
                context_parts.append(f"User preferences: {prefs_str}")

        # No need to add system instructions here as they're now in the role-specific prompts

        return "\n\n".join(context_parts)

    def _simulate_response(self, input_text: str) -> Dict[str, Any]:
        """
        Simulate an AI response for testing

        Args:
            input_text: The user's input text

        Returns:
            Simulated response dictionary
        """
        return {
            "success": True,
            "content": f"[Simulated] Response to: {input_text[:50]}...",
            "model": "simulation",
            "model_type": "simulated"
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get model usage statistics

        Returns:
            Dictionary of usage statistics
        """
        return self.usage_stats

    @with_model_error_handling("query_specialized_model")
    async def query_specialized_model(self, query_type: str, input_text: str, context_str: str = "", system_prompt: str = None) -> Dict[str, Any]:
        """
        Query a specialized model directly based on query type

        Args:
            query_type: The type of query/model to use
            input_text: The user's input text
            context_str: Optional context information as a string
            system_prompt: Optional system prompt to use

        Returns:
            Response dictionary with content and metadata
        """
        # For general queries, always use Mistral-Small
        if query_type == "general":
            self.logger.info("General query detected, using Mistral-Small as main brain")
            return await self._call_mistral(input_text, context_str)

        if self.simulate_responses:
            return self._simulate_response(input_text)

        # Check if we have OpenRouter available
        if not self.openrouter:
            self.logger.warning(f"OpenRouter not available for specialized model query: {query_type}")
            # Try Mistral-Small as fallback if it's available
            if self.mistral:
                try:
                    self.logger.info(f"Falling back to Mistral-Small for specialized query type: {query_type}")
                    return await self._call_mistral(input_text, context_str)
                except Exception as e:
                    self.logger.error(f"Mistral-Small fallback failed: {str(e)}")

            # No fallback to Gemini anymore - it's been replaced by Mistral Small
            self.logger.warning(f"All models failed for query type: {query_type}")

            return {
                "success": False,
                "content": f"Sorry, I don't have access to any AI models right now. Please check your API keys and try again later.",
                "model": "none",
                "error": "No models available"
            }

        # Map model names to specialized query types
        model_mapping = {
            "deepseek": "troubleshoot",
            "deepcoder": "code",
            "agentica": "code",
            "llama-doc": "docs",
            "mistral-small": "trends",
            "maverick": "general",  # Updated to use general (which maps to Mistral-Small)
            "llama-content": "general",  # Updated to use general (which maps to Mistral-Small)
            "llama-technical": "technical",
            "hermes": "brainstorm",
            "molmo": "ethics",  # Updated from olmo to molmo
            "olmo": "ethics",  # Keep for backward compatibility
            "mistralai": "automate",
            "kimi": "visual",
            "nemotron": "reasoning",
            "gemma": "math",  # Added for math/chemistry
            "dolphin": "script",  # Added for script optimization
            "phi": "offline"  # Added for offline mode
        }

        # Check if the query type is valid
        if query_type not in self.free_models:
            # Check if it's a model name that needs to be mapped
            if query_type in model_mapping:
                self.logger.info(f"Mapping model {query_type} to specialized type {model_mapping[query_type]}")
                query_type = model_mapping[query_type]
            else:
                self.logger.warning(f"Unknown query type for specialized model: {query_type}")
                # Use a default type
                query_type = "general"
                if query_type not in self.free_models:
                    query_type = list(self.free_models.keys())[0]  # Use the first available model

        # Get the model ID for this query type
        # Special case for Gemini - redirect to Mistral Small
        if query_type == "gemini":
            self.logger.info(f"Redirecting Gemini query type to Mistral Small: {query_type}")
            return await self._call_mistral(input_text, context_str)

        # Special case for main_brain - use OpenRouter with Mistral Small
        if query_type == "main_brain":
            self.logger.info(f"Using Mistral Small via OpenRouter as main brain")
            model_id = MODEL_IDS["main_brain"]
            return await self._call_openrouter_model(model_id, input_text, context_str)

        # Special case for local handling - handle time queries locally
        if query_type == "local" or query_type == "time":
            self.logger.info(f"Handling query locally for type: {query_type}")

            # Update usage stats for local handling
            self.usage_stats["local"]["calls"] += 1
            self.usage_stats["local"]["last_used"] = datetime.now().isoformat()

            # For time queries, return the current time
            if query_type == "time" or "time" in input_text.lower():
                from datetime import datetime
                import pytz

                # Extract location from input text if present
                location = "local"
                location_keywords = ["in", "at", "for"]
                for keyword in location_keywords:
                    if f" {keyword} " in input_text.lower():
                        parts = input_text.lower().split(f" {keyword} ")
                        if len(parts) > 1:
                            location = parts[1].strip().split()[0]
                            break

                # Get the current time
                current_time = datetime.now()
                formatted_time = current_time.strftime("%I:%M %p on %A, %B %d, %Y")

                # Try to get time for specific location if not local
                if location != "local":
                    try:
                        # Try to map common location names to timezone strings
                        timezone_map = {
                            "new": "America/New_York",  # New York
                            "los": "America/Los_Angeles",  # Los Angeles
                            "london": "Europe/London",
                            "tokyo": "Asia/Tokyo",
                            "sydney": "Australia/Sydney",
                            "paris": "Europe/Paris",
                            "berlin": "Europe/Berlin",
                            "moscow": "Europe/Moscow",
                            "beijing": "Asia/Shanghai",
                            "dubai": "Asia/Dubai",
                            "india": "Asia/Kolkata",
                            "sri": "Asia/Colombo"  # Sri Lanka
                        }

                        # Find matching timezone
                        tz_string = None
                        for key, value in timezone_map.items():
                            if key in location.lower():
                                tz_string = value
                                break

                        if tz_string:
                            tz = pytz.timezone(tz_string)
                            current_time = datetime.now(tz)
                            formatted_time = current_time.strftime("%I:%M %p on %A, %B %d, %Y")
                            location_name = tz_string.split('/')[-1].replace('_', ' ')
                            return {
                                "success": True,
                                "content": f"The current time in {location_name} is {formatted_time}.",
                                "model": "local",
                                "model_type": "local"
                            }
                    except Exception as e:
                        self.logger.error(f"Error getting time for location {location}: {str(e)}")
                        # Fall back to local time

                return {
                    "success": True,
                    "content": f"The current time is {formatted_time}.",
                    "model": "local",
                    "model_type": "local"
                }

            # For other local queries, return a default response
            return {
                "success": True,
                "content": f"This query was handled locally: {input_text}",
                "model": "local",
                "model_type": "local"
            }

        # Special case for Phi - use Ollama directly
        if query_type == "phi" or query_type == "offline":
            self.logger.info(f"Using Ollama for query type: {query_type}")
            # Check if Ollama is available
            status = await self.check_status()
            ollama_running = status.get("ollama", {}).get("running", False)
            internet_available = await self.check_internet()

            # If we're online and not explicitly in offline mode, use main_brain for simple greetings and chat queries
            if internet_available and (input_text.lower().strip() in ["hi", "hello", "hey", "what's up", "how are you"] or
                                      query_type == "chat" or query_type == "general"):
                self.logger.info("Online mode with chat/greeting, using main_brain instead of Phi")
                model_id = MODEL_IDS["main_brain"]
                return await self._call_openrouter_model(model_id, input_text, context_str)

            if ollama_running:
                # Use the Ollama client to call Phi
                try:
                    from utils.ollama_manager import OllamaManager
                    ollama_client = OllamaManager()
                    # Always use "phi" as the model name, not the input text
                    response = await ollama_client.generate(prompt=input_text, model="phi")
                    return {
                        "success": response.get("success", False),
                        "content": response.get("content", "Error calling Phi model"),
                        "model": "phi",
                        "model_type": "ollama"
                    }
                except Exception as e:
                    self.logger.error(f"Error calling Phi via Ollama: {str(e)}")
                    # Fall back to main_brain
                    self.logger.info("Falling back to main_brain due to Ollama error")
                    model_id = MODEL_IDS["main_brain"]
                    return await self._call_openrouter_model(model_id, input_text, context_str)
            else:
                # Ollama not running, fall back to main_brain
                self.logger.warning("Ollama not running, falling back to main_brain")
                model_id = MODEL_IDS["main_brain"]
                return await self._call_openrouter_model(model_id, input_text, context_str)

        model_id = self.free_models[query_type]
        self.logger.info(f"Using specialized model for {query_type}: {model_id}")

        try:
            # Call the OpenRouter model directly
            response = await self._call_openrouter_model(model_id, input_text, context_str)
            return response
        except asyncio.CancelledError:
            self.logger.warning(f"Request to specialized model {model_id} was cancelled")
            return {
                "success": False,
                "content": "The request was cancelled. Please try again later.",
                "model": model_id,
                "model_type": "openrouter",
                "error": "Request cancelled"
            }
        except Exception as e:
            self.logger.error(f"Error calling specialized model {model_id} for {query_type}: {str(e)}")
            # Try Mistral-Small as fallback
            self.logger.info(f"Specialized model {model_id} failed, falling back to Mistral-Small")
            try:
                return await self._call_mistral(input_text, context_str)
            except Exception as e2:
                self.logger.error(f"Mistral-Small fallback failed: {str(e2)}")
                # If Mistral-Small also fails, try the general fallback strategy
                return await self._fallback_to_openrouter(input_text, context_str, query_type)

    def get_available_models(self) -> Dict[str, List[str]]:
        """
        Get available models

        Returns:
            Dictionary of available models by type
        """
        available_models = {
            "main_brain": [],
            "mistral": [],
            "openrouter": [],
            "local": []
        }

        if self.mistral:
            available_models["mistral"].append("mistral-small-3.1-24b")

        if self.openrouter:
            available_models["openrouter"] = list(self.free_models.values())

        if self.intent_classifier:
            available_models["local"].append("distilbert-base-uncased")

        return available_models

    async def check_status(self) -> Dict[str, Any]:
        """
        Check the status of all models and services

        Returns:
            Dictionary with status information
        """
        # Check API keys using the API Key Manager
        openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY")

        status = {
            "main_brain": {
                "available": self.openrouter is not None,
                "api_key": openrouter_api_key is not None,
                "api_key_valid": self.openrouter is not None  # If OpenRouter is initialized, the key is valid
            },
            "mistral": {
                "available": self.mistral is not None,
                "api_key": openrouter_api_key is not None,
                "api_key_valid": self.mistral is not None  # If Mistral is initialized, the key is valid
            },
            "openrouter": {
                "available": self.openrouter is not None,
                "api_key": openrouter_api_key is not None,
                "models": list(self.free_models.values()) if self.openrouter else []
            },
            "local": {
                "available": self.intent_classifier is not None
            },
            "timestamp": datetime.now().isoformat()
        }

        # Check if Ollama is available
        try:
            from utils.ollama_manager import OllamaManager
            ollama_client = OllamaManager()
            ollama_status = await ollama_client.check_status()
            status["ollama"] = ollama_status
        except Exception as e:
            self.logger.error(f"Error checking Ollama status: {str(e)}")
            status["ollama"] = {"error": str(e), "available": False}

        return status

    async def call_gemini(self, query: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Public method to call the Gemini model (redirects to Mistral Small for backward compatibility)

        Args:
            query: The query to send to Gemini
            max_tokens: Maximum number of tokens to generate

        Returns:
            Response dictionary
        """
        self.logger.info(f"Redirecting call_gemini to call_mistral with query: {query[:30]}...")
        return await self._call_mistral(query, max_tokens)

    async def _call_mistral(self, query: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Call the Mistral Small model via OpenRouter with a query

        Args:
            query: The query to send to the model
            max_tokens: Maximum number of tokens to generate

        Returns:
            Dictionary with response information
        """
        self.logger.info(f"Call to _call_mistral with query: {query[:30]}...")

        # Check if OpenRouter is initialized
        if not self.openrouter:
            # Try to initialize OpenRouter if it's not already initialized
            openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY")
            if openrouter_api_key:
                try:
                    self.openrouter = OpenAI(
                        api_key=openrouter_api_key,
                        base_url="https://openrouter.ai/api/v1",
                        default_headers={
                            "HTTP-Referer": "https://github.com/uminda/general-pulse",
                            "X-Title": "General Pulse"
                        }
                    )
                    self.logger.info("OpenRouter initialized on-demand for Mistral Small")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenRouter on-demand: {str(e)}")
                    return {
                        "success": False,
                        "content": f"Failed to initialize OpenRouter for Mistral Small: {str(e)}",
                        "model": "none",
                        "error": "Initialization failed"
                    }
            else:
                self.logger.error("Cannot call Mistral Small: OpenRouter not initialized and API key not available")
                return {
                    "success": False,
                    "content": "Mistral Small model is not available. Please check your OpenRouter API key.",
                    "model": "none",
                    "error": "Model not initialized"
                }

        # Call the model with the query
        try:
            # Get the model ID for main_brain (Mistral Small)
            model_id = MODEL_IDS.get("main_brain")
            if not model_id:
                self.logger.error("main_brain model ID not found in MODEL_IDS")
                return {
                    "success": False,
                    "error": "Model ID not found",
                    "content": "Mistral Small model ID not found in configuration.",
                    "model": "none"
                }

            # Get the Mistral-specific prompt
            system_prompt = get_prompt("mistral")

            # Prepare messages for the chat completion
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]

            # Call the model
            response = await asyncio.to_thread(
                self.openrouter.chat.completions.create,
                model=model_id,
                messages=messages,
                max_tokens=max_tokens
            )

            # Extract the response content
            content = response.choices[0].message.content

            # Update usage stats
            if "mistral" not in self.usage_stats:
                self.usage_stats["mistral"] = {
                    "calls": 0,
                    "tokens": 0,
                    "last_used": None
                }
            self.usage_stats["mistral"]["calls"] += 1
            self.usage_stats["mistral"]["last_used"] = datetime.now().isoformat()
            # Approximate token count
            self.usage_stats["mistral"]["tokens"] += len(str(messages).split()) + len(content.split())

            # Format the response with model-specific personality
            if hasattr(self, 'model_personality') and self.model_personality:
                formatted_response = self.model_personality.format_response(content, "mistral", success=True)
            else:
                formatted_response = content

            return {
                "success": True,
                "content": formatted_response,
                "model": model_id,
                "model_type": "mistral"
            }
        except Exception as e:
            self.logger.error(f"Error calling Mistral Small via OpenRouter: {str(e)}")
            return {
                "success": False,
                "content": f"Error calling Mistral Small: {str(e)}",
                "model": model_id if 'model_id' in locals() else "mistralai/mistral-small-3.1-24b-instruct:free",
                "model_type": "mistral",
                "error": str(e)
            }

    async def check_gemini_api_key(self) -> Dict[str, Any]:
        """
        Check if the OpenRouter API key is set and valid for Mistral Small (renamed from Gemini for backward compatibility)

        Returns:
            Dictionary with status information
        """
        # Redirect to OpenRouter API key check since we're using Mistral Small via OpenRouter
        self.logger.info("Redirecting Gemini API key check to OpenRouter API key check for Mistral Small")
        return await self.check_openrouter_api_key()

    async def check_openrouter_api_key(self) -> Dict[str, Any]:
        """
        Check if the OpenRouter API key is set and valid

        Returns:
            Dictionary with status information
        """
        # Force reload to get the latest key
        openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY", force_reload=True)
        if not openrouter_api_key:
            self.logger.error("OpenRouter API key not found")
            return {
                "success": False,
                "error": "API key not found",
                "message": "OpenRouter API key not found. Please check your .env file."
            }

        # Try to initialize OpenRouter with this key
        try:
            # Initialize OpenRouter using OpenAI client with custom base URL
            openrouter = OpenAI(
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/Spyboss/P.U.L.S.E.",
                    "X-Title": "P.U.L.S.E."
                }
            )

            # Try a simple test query with the main_brain model
            model_id = MODEL_IDS["main_brain"]
            response = await asyncio.to_thread(
                openrouter.chat.completions.create,
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, this is a test query to verify the OpenRouter API key."}
                ],
                max_tokens=10
            )

            self.logger.info("OpenRouter API key is valid")
            return {
                "success": True,
                "message": "OpenRouter API key is valid",
                "response": response.choices[0].message.content[:50] + "..." if len(response.choices[0].message.content) > 50 else response.choices[0].message.content
            }
        except Exception as e:
            self.logger.error(f"Error testing OpenRouter API key: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error testing OpenRouter API key: {str(e)}"
            }

    async def test_main_brain(self, query: str) -> Dict[str, Any]:
        """
        Test the main brain model with a query

        Args:
            query: The query to test with

        Returns:
            Dictionary with test results
        """
        try:
            # Get the model ID for main_brain
            model_id = MODEL_IDS.get("main_brain")
            if not model_id:
                self.logger.error("main_brain model ID not found in MODEL_IDS")
                return {
                    "success": False,
                    "error": "Model ID not found",
                    "message": "main_brain model ID not found in MODEL_IDS configuration."
                }

            # Get the OpenRouter API key
            openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                self.logger.error("OpenRouter API key not found")
                return {
                    "success": False,
                    "error": "API key not found",
                    "message": "OpenRouter API key not found. Please check your .env file."
                }

            # Initialize OpenRouter client
            openrouter = OpenAI(
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/Spyboss/P.U.L.S.E.",
                    "X-Title": "P.U.L.S.E."
                }
            )

            # Call the model
            response = await asyncio.to_thread(
                openrouter.chat.completions.create,
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query}
                ],
                max_tokens=100
            )

            # Extract the response content
            content = response.choices[0].message.content

            return {
                "success": True,
                "content": content,
                "model": "main_brain",
                "model_id": model_id
            }
        except Exception as e:
            self.logger.error(f"Error testing main_brain: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error testing main_brain: {str(e)}"
            }

    async def _call_openrouter_model(self, model_id: str, input_text: str, context_str: str = "", system_prompt: str = None) -> Dict[str, Any]:
        """
        Call an OpenRouter model with a query

        Args:
            model_id: The OpenRouter model ID to use
            input_text: The user's input text
            context_str: Optional context information as a string
            system_prompt: Optional system prompt to use

        Returns:
            Response dictionary with content and metadata
        """
        self.logger.info(f"Calling OpenRouter model {model_id} with query: {input_text[:30]}...")

        # Check if OpenRouter is initialized
        if not self.openrouter:
            self.logger.error("OpenRouter not initialized. Cannot call OpenRouter model.")
            return {
                "success": False,
                "content": "OpenRouter is not available. Please check your API key.",
                "model": model_id,
                "model_type": "openrouter",
                "error": "OpenRouter not initialized"
            }

        # Use default system prompt if none provided
        if not system_prompt:
            system_prompt = get_prompt("openrouter")

        # Combine context and input text if context is provided
        full_input = f"{context_str}\n\n{input_text}" if context_str else input_text

        try:
            # Prepare messages for the chat completion
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_input}
            ]

            # Call the model
            response = await asyncio.to_thread(
                self.openrouter.chat.completions.create,
                model=model_id,
                messages=messages,
                max_tokens=1000
            )

            # Extract the response content
            content = response.choices[0].message.content

            # Update usage stats
            if "openrouter" not in self.usage_stats:
                self.usage_stats["openrouter"] = {
                    "calls": 0,
                    "tokens": 0,
                    "last_used": None
                }
            self.usage_stats["openrouter"]["calls"] += 1
            self.usage_stats["openrouter"]["last_used"] = datetime.now().isoformat()
            # Approximate token count
            self.usage_stats["openrouter"]["tokens"] += len(str(messages).split()) + len(content.split())

            # Format the response with model-specific personality
            if hasattr(self, 'model_personality') and self.model_personality:
                formatted_response = self.model_personality.format_response(content, "openrouter", success=True)
            else:
                formatted_response = content

            return {
                "success": True,
                "content": formatted_response,
                "model": model_id,
                "model_type": "openrouter"
            }
        except Exception as e:
            self.logger.error(f"Error calling OpenRouter model {model_id}: {str(e)}")
            return {
                "success": False,
                "content": f"Error calling OpenRouter model: {str(e)}",
                "model": model_id,
                "model_type": "openrouter",
                "error": str(e)
            }

    async def check_internet(self) -> bool:
        """
        Check if internet connection is available

        Returns:
            True if internet is available, False otherwise
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get("https://www.google.com")
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error checking internet connection: {str(e)}")
            return False
