"""
Adaptive Router for P.U.L.S.E. (Prime Uminda's Learning System Engine)
Provides hardware-aware model selection based on system resources
"""

import os
import asyncio
import psutil
import structlog
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Configure logger
logger = structlog.get_logger("adaptive_router")

# Constants
CPU_HIGH_THRESHOLD = 0.80  # 80% CPU usage threshold
MEMORY_LOW_THRESHOLD = 0.20  # 20% free memory threshold
CACHE_TTL = 300  # 5 minutes cache TTL for routing decisions
ROUTING_CHECK_INTERVAL = 60  # 1 minute between routing checks

# Import model IDs from configs
from configs.models import MODEL_IDS

# Model configurations
MODEL_CONFIGS = {
    "mistral-small": {
        "name": "mistralai/mistral-small-3.1-24b-instruct:free",
        "provider": "openrouter",
        "memory_requirement": "high",
        "cpu_requirement": "medium",
        "offline": False,
        "priority": 1
    },
    "minilm": {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "provider": "local",
        "memory_requirement": "low",
        "cpu_requirement": "low",
        "offline": True,
        "priority": 2
    },
    "phi": {
        "name": "phi",
        "provider": "ollama",
        "memory_requirement": "medium",
        "cpu_requirement": "high",
        "offline": True,
        "priority": 3
    },
    # Specialized models from OpenRouter
    "deepcoder": {
        "name": MODEL_IDS["code_generation"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 4
    },
    "deepseek": {
        "name": MODEL_IDS["troubleshooting"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 5
    },
    "llama-doc": {
        "name": MODEL_IDS["documentation"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 6
    },
    "llama-technical": {
        "name": MODEL_IDS["technical_translation"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 7
    },
    "hermes": {
        "name": MODEL_IDS["brainstorming"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 8
    },
    "molmo": {
        "name": MODEL_IDS["ethical_ai"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 9
    },
    "mistralai": {
        "name": MODEL_IDS["task_automation"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 10
    },
    "kimi": {
        "name": MODEL_IDS["visual_reasoning"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 11
    },
    "nemotron": {
        "name": MODEL_IDS["advanced_reasoning"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 12
    },
    "gemma": {
        "name": MODEL_IDS["math_chemistry"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 13
    },
    "dolphin": {
        "name": MODEL_IDS["script_optimization"],
        "provider": "openrouter",
        "memory_requirement": "low",  # Cloud API
        "cpu_requirement": "low",     # Cloud API
        "offline": False,
        "priority": 14
    }
}

class AdaptiveRouter:
    """
    Hardware-adaptive router for P.U.L.S.E.
    Features:
    - Selects models based on available system resources
    - Adapts to memory and CPU constraints
    - Provides fallback options for offline operation
    - Caches routing decisions to reduce overhead
    """

    def __init__(self, neural_router=None):
        """
        Initialize the adaptive router

        Args:
            neural_router: Optional neural router for intent-based routing
        """
        self.logger = logger
        self.neural_router = neural_router

        # Cache for routing decisions
        self.routing_cache = {}
        self.last_system_check = time.time()
        self.system_status = self._get_system_status()

        # Track model usage
        self.model_usage = {model: 0 for model in MODEL_CONFIGS}

        logger.info("Adaptive router initialized")
        logger.info(f"System status: {self.system_status}")

    def _get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status

        Returns:
            Dictionary with system status
        """
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Get memory info
            memory = psutil.virtual_memory()
            memory_free_percent = memory.available / memory.total
            memory_free_mb = memory.available / (1024 * 1024)

            # Check if we're in offline mode
            offline_mode = not self._check_internet_connection()

            # Check if Ollama is available
            ollama_available = self._check_ollama_available()

            status = {
                "cpu_percent": cpu_percent,
                "memory_free_percent": memory_free_percent,
                "memory_free_mb": memory_free_mb,
                "offline_mode": offline_mode,
                "ollama_available": ollama_available,
                "timestamp": time.time()
            }

            # Determine resource constraints
            status["cpu_constrained"] = cpu_percent > CPU_HIGH_THRESHOLD * 100
            status["memory_constrained"] = memory_free_percent < MEMORY_LOW_THRESHOLD

            return status
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "cpu_percent": 0,
                "memory_free_percent": 0.5,
                "memory_free_mb": 4000,
                "offline_mode": False,
                "ollama_available": False,
                "cpu_constrained": False,
                "memory_constrained": False,
                "timestamp": time.time(),
                "error": str(e)
            }

    def _check_internet_connection(self) -> bool:
        """
        Check if internet connection is available

        Returns:
            True if internet is available, False otherwise
        """
        try:
            # Simple check - try to resolve google.com
            import socket
            socket.create_connection(("www.google.com", 80), timeout=1)
            return True
        except:
            return False

    def _check_ollama_available(self) -> bool:
        """
        Check if Ollama is available

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            # Check if Ollama process is running
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                    return True

            # Try to connect to Ollama API
            import httpx
            response = httpx.get("http://localhost:11434/api/tags", timeout=1)
            return response.status_code == 200
        except:
            return False

    async def _update_system_status(self) -> None:
        """Update system status if needed"""
        current_time = time.time()
        if current_time - self.last_system_check > ROUTING_CHECK_INTERVAL:
            self.system_status = self._get_system_status()
            self.last_system_check = current_time
            logger.debug(f"Updated system status: {self.system_status}")

    def _select_model_for_constraints(self, query_type: str = "general") -> str:
        """
        Select the best model based on current system constraints and query type

        Args:
            query_type: Type of query (command, intent, general)

        Returns:
            Model name
        """
        status = self.system_status

        # For command queries, always use MiniLM regardless of constraints
        if query_type == "command":
            logger.info("Command query detected, selecting minilm for fast response")
            return "minilm"

        # If we're offline, use a local model
        if status["offline_mode"]:
            if status["ollama_available"]:
                logger.info("Offline mode with Ollama available, selecting phi")
                return "phi"
            else:
                logger.info("Offline mode without Ollama, selecting minilm")
                return "minilm"

        # For non-command queries in online mode, prefer Mistral-Small even with memory constraints
        # since it's a cloud API and doesn't use local memory
        if not status["offline_mode"]:
            logger.info("Online mode, selecting mistral-small (cloud API)")
            return "mistral-small"

        # If CPU is extremely constrained, use a low-CPU model
        if status["cpu_constrained"] and status["cpu_percent"] > 90:
            logger.info(f"Extreme CPU constraint ({status['cpu_percent']:.2f}% usage), selecting minilm")
            return "minilm"

        # Default to the highest priority model
        logger.info("No constraints detected, selecting mistral-small")
        return "mistral-small"

    async def route(self, query: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Route a query to the appropriate model

        Args:
            query: User query
            intent: Optional intent for specialized routing

        Returns:
            Routing result with model selection
        """
        # Update system status if needed
        await self._update_system_status()

        # Check cache for this query
        cache_key = f"{query}:{intent}"
        if cache_key in self.routing_cache:
            cached_result = self.routing_cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_result["timestamp"] < CACHE_TTL:
                logger.debug(f"Using cached routing for query: {query[:30]}...")
                return cached_result

        # Try neural routing if available and we have an intent
        neural_model = None
        neural_confidence = 0.0

        if self.neural_router and not self.system_status["memory_constrained"]:
            try:
                neural_model, neural_confidence = await self.neural_router.route_query(query, intent=intent)
                logger.debug(f"Neural router suggested {neural_model} with confidence {neural_confidence}")

                # If confidence is high enough, use the neural router's suggestion
                if neural_confidence >= 0.7:
                    # Map the neural router's model name to our model configs
                    if neural_model == "mistral" or neural_model == "mistral-small":
                        neural_model = "mistral-small"
                    elif neural_model in ["minilm", "phi"]:
                        # These are already in our config
                        pass
                    elif neural_model in ["deepcoder", "deepseek", "llama-doc", "llama-technical",
                                         "hermes", "molmo", "mistralai", "kimi", "nemotron",
                                         "gemma", "dolphin"]:
                        # These are specialized models from OpenRouter
                        logger.info(f"Using specialized model {neural_model} from OpenRouter")
                        # Keep the model name as is - it will be handled by the model orchestrator
                    else:
                        # Unknown model, ignore
                        logger.warning(f"Unknown model {neural_model} suggested by neural router, ignoring")
                        neural_model = "mistral-small"  # Default to mistral-small for unknown models
            except Exception as e:
                logger.error(f"Error in neural routing: {str(e)}")
                neural_model = None

        # Determine query type from the intent
        query_type = "general"
        if intent:
            if intent in ["help", "status", "exit", "memory", "dashboard", "version", "test", "clear", "ollama"]:
                query_type = "command"

        # Always use neural router's suggestion if available, regardless of confidence
        if neural_model:
            # For command queries, always use MiniLM regardless of neural router suggestion
            if query_type == "command":
                selected_model = "minilm"
                logger.info(f"Command query detected, overriding neural router suggestion with minilm")
            else:
                selected_model = neural_model
                logger.info(f"Using neural router's suggestion: {selected_model}")

                # Skip the system constraints check for specialized models
                # This ensures that specialized models are always used when suggested by the neural router
                if selected_model in ["deepcoder", "deepseek", "llama-doc", "llama-technical",
                                     "hermes", "molmo", "mistralai", "kimi", "nemotron",
                                     "gemma", "dolphin"]:
                    logger.info(f"Using specialized model {selected_model} regardless of system constraints")
                    # Skip the rest of the routing logic
                    model_config = MODEL_CONFIGS.get(selected_model, MODEL_CONFIGS["mistral-small"])

                    # Update model usage
                    self.model_usage[selected_model] = self.model_usage.get(selected_model, 0) + 1

                    # Create routing result
                    result = {
                        "model": selected_model,
                        "model_name": model_config["name"],
                        "provider": model_config["provider"],
                        "offline_compatible": model_config["offline"],
                        "neural_confidence": neural_confidence,
                        "system_status": {
                            "memory_constrained": self.system_status["memory_constrained"],
                            "cpu_constrained": self.system_status["cpu_constrained"],
                            "offline_mode": self.system_status["offline_mode"]
                        },
                        "timestamp": time.time()
                    }

                    # Cache the result
                    self.routing_cache[cache_key] = result

                    logger.info(f"Routed query to {selected_model} ({model_config['provider']})")
                    return result
        else:
            # Fall back to system constraints if neural routing didn't work
            selected_model = self._select_model_for_constraints(query_type)

        # Get model config
        model_config = MODEL_CONFIGS.get(selected_model, MODEL_CONFIGS["mistral-small"])

        # Update model usage
        self.model_usage[selected_model] = self.model_usage.get(selected_model, 0) + 1

        # Create routing result
        result = {
            "model": selected_model,
            "model_name": model_config["name"],
            "provider": model_config["provider"],
            "offline_compatible": model_config["offline"],
            "neural_confidence": neural_confidence if neural_model else 0.0,
            "system_status": {
                "memory_constrained": self.system_status["memory_constrained"],
                "cpu_constrained": self.system_status["cpu_constrained"],
                "offline_mode": self.system_status["offline_mode"]
            },
            "timestamp": time.time()
        }

        # Cache the result
        self.routing_cache[cache_key] = result

        logger.info(f"Routed query to {selected_model} ({model_config['provider']})")
        return result

    async def get_model_usage_stats(self) -> Dict[str, Any]:
        """
        Get model usage statistics

        Returns:
            Dictionary with model usage statistics
        """
        total_usage = sum(self.model_usage.values())
        if total_usage == 0:
            return {"total": 0, "models": {}}

        stats = {
            "total": total_usage,
            "models": {}
        }

        for model, count in self.model_usage.items():
            stats["models"][model] = {
                "count": count,
                "percentage": count / total_usage * 100
            }

        return stats

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status

        Returns:
            Dictionary with system status
        """
        # Update system status if needed
        await self._update_system_status()
        return self.system_status
