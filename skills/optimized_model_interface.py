"""
Optimized Model Interface for General Pulse
Provides efficient API for interacting with AI models with memory optimization
"""

import os
import asyncio
import structlog
import gc
import psutil
import json
import time
import subprocess
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
import httpx

from utils.ollama_manager import OllamaManager
from configs.models import MODEL_IDS, MODEL_ROLES, QUERY_TYPE_TO_MODEL
from utils.prompts import get_prompt
from utils.api_key_manager import APIKeyManager

logger = structlog.get_logger(__name__)

class OptimizedModelInterface:
    """
    Memory-efficient model interface with proper Ollama management
    """

    def __init__(self):
        """
        Initialize the optimized model interface
        """
        # Initialize API Key Manager
        self.api_key_manager = APIKeyManager(auto_reload=True, cache_ttl=300)

        self.ollama_client = OllamaManager()
        self.offline_mode = False

        # Get API keys from the API Key Manager
        self.openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY")
        # We'll use OpenRouter for Mistral-Small, so we don't need a separate Mistral API key

        # Initialize HTTP clients with proper timeouts
        self.openrouter_client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            timeout=httpx.Timeout(30.0),
            headers={
                "HTTP-Referer": "https://github.com/uminda/general-pulse",
                "X-Title": "General Pulse"
            }
        )

        # Track memory usage
        self.memory_threshold = 6.0  # GB
        self.last_gc_time = time.time()
        self.gc_interval = 60  # seconds

        # Initialize model mappings from configs
        self.models = MODEL_IDS
        self.model_roles = MODEL_ROLES
        self.query_type_mapping = QUERY_TYPE_TO_MODEL

        # Initialize usage stats
        self.usage_stats = {
            "gemini": {"calls": 0, "tokens": 0, "last_used": None},
            "mistral": {"calls": 0, "tokens": 0, "last_used": None},
            "openrouter": {"calls": 0, "tokens": 0, "last_used": None},
            "ollama": {"calls": 0, "tokens": 0, "last_used": None}
        }

        logger.info("Optimized model interface initialized")

    async def check_memory(self) -> float:
        """
        Check available memory and run garbage collection if needed

        Returns:
            Available memory in GB
        """
        # Get available memory
        available_gb = psutil.virtual_memory().available / (1024 ** 3)

        # Run garbage collection if memory is low or it's been a while
        current_time = time.time()
        if available_gb < self.memory_threshold or (current_time - self.last_gc_time) > self.gc_interval:
            logger.info(f"Running garbage collection. Available memory: {available_gb:.2f} GB")
            gc.collect()
            self.last_gc_time = current_time

            # Update available memory after GC
            available_gb = psutil.virtual_memory().available / (1024 ** 3)

        return available_gb

    async def check_internet(self) -> bool:
        """
        Check if internet connection is available

        Returns:
            True if internet is available
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get("https://www.google.com")
                return response.status_code == 200
        except Exception:
            return False

    async def manage_ollama(self, ensure_running: bool = False) -> bool:
        """
        Manage Ollama service - start if needed or stop if not needed

        Args:
            ensure_running: If True, ensure Ollama is running

        Returns:
            True if Ollama is running after the operation
        """
        # Skip if offline mode is disabled and we're not trying to ensure it's running
        if not self.offline_mode and not ensure_running:
            logger.debug("Skipping Ollama management because offline mode is disabled")
            return False

        # Check current status
        status = await self.ollama_client.check_status()
        is_running = status.get("running", False)

        if ensure_running and not is_running:
            # Need to start Ollama
            logger.info("Starting Ollama service")
            await self.start_ollama()
            return await self.ollama_client.check_health(force=True)

        elif not ensure_running and is_running and not self.offline_mode:
            # Need to stop Ollama to save resources
            logger.info("Stopping Ollama service to save resources")
            await self.stop_ollama()
            return not await self.ollama_client.check_health(force=True)

        return is_running

    async def start_ollama(self) -> Dict[str, Any]:
        """
        Start the Ollama service

        Returns:
            Status dictionary
        """
        try:
            # Check if already running
            status = await self.ollama_client.check_status(force=True)
            if status.get("running", False):
                logger.info("Ollama service is already running")
                return {
                    "success": True,
                    "message": "Ollama service is already running"
                }

            # Start Ollama service using the start_service method
            if hasattr(self.ollama_client, 'start_service'):
                result = await self.ollama_client.start_service()
            else:
                # Fallback to using subprocess directly
                try:
                    subprocess.Popen(["ollama", "serve"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    creationflags=subprocess.CREATE_NO_WINDOW)

                    # Wait for service to start
                    for _ in range(5):
                        await asyncio.sleep(1)
                        status = await self.ollama_client.check_status(force=True)
                        if status.get("running", False):
                            logger.info("Ollama service started successfully")
                            result = True
                            break
                    else:
                        logger.warning("Ollama service failed to start")
                        result = False
                except Exception as e:
                    logger.error(f"Error starting Ollama service: {str(e)}")
                    result = False

            if result:
                logger.info("Ollama service started successfully")
                return {
                    "success": True,
                    "message": "Ollama service started successfully"
                }
            else:
                logger.error("Failed to start Ollama service")
                return {
                    "success": False,
                    "message": "Failed to start Ollama service"
                }

        except Exception as e:
            logger.error(f"Error starting Ollama service: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting Ollama service: {str(e)}"
            }

    async def stop_ollama(self) -> Dict[str, Any]:
        """
        Stop the Ollama service

        Returns:
            Status dictionary
        """
        try:
            # Check if running
            status = await self.ollama_client.check_status(force=True)
            if not status.get("running", False):
                logger.info("Ollama service is not running")
                return {
                    "success": True,
                    "message": "Ollama service is not running"
                }

            # Stop Ollama service
            if hasattr(self.ollama_client, 'stop_service'):
                result = await self.ollama_client.stop_service()
            else:
                # Fallback to using subprocess directly
                try:
                    subprocess.run(["taskkill", "/f", "/im", "ollama.exe"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

                    # Wait for service to stop
                    for _ in range(5):
                        await asyncio.sleep(1)
                        if not await self.ollama_client.check_health(force=True):
                            logger.info("Ollama service stopped successfully")
                            result = True
                            break
                    else:
                        logger.warning("Ollama service failed to stop")
                        result = False
                except Exception as e:
                    logger.error(f"Error stopping Ollama service: {str(e)}")
                    result = False

            if result:
                logger.info("Ollama service stopped successfully")
                return {
                    "success": True,
                    "message": "Ollama service stopped successfully"
                }
            else:
                logger.error("Failed to stop Ollama service")
                return {
                    "success": False,
                    "message": "Failed to stop Ollama service"
                }

        except Exception as e:
            logger.error(f"Error stopping Ollama service: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping Ollama service: {str(e)}"
            }

    async def toggle_offline_mode(self, enable: bool = True) -> Dict[str, Any]:
        """
        Toggle offline mode

        Args:
            enable: True to enable offline mode, False to disable

        Returns:
            Status information
        """
        self.offline_mode = enable

        if enable:
            # Ensure Ollama is running for offline mode
            ollama_running = await self.manage_ollama(ensure_running=True)
            if not ollama_running:
                return {
                    "success": False,
                    "message": "Failed to start Ollama for offline mode"
                }

            logger.info("Offline mode enabled")
            return {
                "success": True,
                "message": "Offline mode enabled successfully",
                "ollama_status": "running"
            }
        else:
            # We can stop Ollama if we're going back online
            await self.manage_ollama(ensure_running=False)
            logger.info("Offline mode disabled")
            return {
                "success": True,
                "message": "Offline mode disabled successfully",
                "ollama_status": "stopped" if not (await self.ollama_client.check_status(force=True)).get("running", False) else "running"
            }

    async def check_status(self, force: bool = False) -> Dict[str, Any]:
        """
        Check the status of the model interface and its components

        Args:
            force: Force a health check even if offline mode is disabled

        Returns:
            Status information dictionary
        """
        # Check Ollama status - respect offline mode unless forced
        ollama_status = await self.ollama_client.check_status(force=force)
        ollama_running = ollama_status.get("running", False)
        ollama_models = ollama_status.get("models", [])

        # Check internet connection
        internet_available = await self.check_internet()

        # Get system information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Create status dictionary
        status = {
            "ollama": {
                "running": ollama_running,
                "models": ollama_models,
                "executable_found": True,  # Placeholder, would need to check if ollama is installed
                "system_memory": {
                    "total_gb": memory.total / (1024 ** 3),
                    "used_gb": memory.used / (1024 ** 3),
                    "free_gb": memory.available / (1024 ** 3),
                    "percent_used": memory.percent
                }
            },
            "offline_mode": self.offline_mode,
            "internet_available": internet_available,
            "distilbert_available": False,  # Placeholder, would need to check if DistilBERT is available
            "distilbert_initialized": False,  # Placeholder, would need to check if DistilBERT is initialized
            "system": {
                "memory": {
                    "total_gb": memory.total / (1024 ** 3),
                    "used_gb": memory.used / (1024 ** 3),
                    "free_gb": memory.available / (1024 ** 3),
                    "percent_used": memory.percent
                },
                "cpu": {
                    "percent_used": psutil.cpu_percent()
                },
                "disk": {
                    "total_gb": disk.total / (1024 ** 3),
                    "used_gb": disk.used / (1024 ** 3),
                    "free_gb": disk.free / (1024 ** 3),
                    "percent_used": disk.percent
                }
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        return status

    async def get_context_data(self) -> Dict[str, Any]:
        """
        Get context data for AI models

        Returns:
            Context data dictionary
        """
        # Get system information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Create context data
        context_data = {
            "system_status": {
                "memory_percent": memory.percent,
                "memory_used": f"{memory.used / (1024 ** 3):.2f}GB",
                "memory_total": f"{memory.total / (1024 ** 3):.2f}GB",
                "memory_available": f"{memory.available / (1024 ** 3):.2f}GB",
                "cpu_percent": psutil.cpu_percent(),
                "disk_percent": disk.percent,
                "disk_used": f"{disk.used / (1024 ** 3):.2f}GB",
                "disk_total": f"{disk.total / (1024 ** 3):.2f}GB"
            },
            "ollama_status": (await self.ollama_client.check_status(force=False)).get("running", False),
            "offline_mode": self.offline_mode,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        return context_data

    async def call_mistral(self,
                         query: str,
                         context_data: Optional[Dict[str, Any]] = None,
                         system_prompt: Optional[str] = None,
                         max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Call the Mistral-Small model with optimized parameters via OpenRouter

        Args:
            query: User query
            context_data: Optional context data
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary
        """
        # Use OpenRouter for Mistral-Small
        return await self.call_openrouter(
            model_id="mistralai/mistral-small-3.1-24b-instruct:free",
            query=query,
            context_data=context_data,
            system_prompt=system_prompt,
            max_tokens=max_tokens
        )

    async def call_gemini(self,
                         query: str,
                         context_data: Optional[Dict[str, Any]] = None,
                         system_prompt: Optional[str] = None,
                         max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Call the Gemini model (redirects to Mistral-Small for backward compatibility)

        Args:
            query: User query
            context_data: Optional context data
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary
        """
        logger.info(f"Redirecting call_gemini to call_mistral with query: {query[:30]}...")
        return await self.call_mistral(query, context_data, system_prompt, max_tokens)

    async def call_openrouter(self,
                             model_id: str,
                             query: str,
                             context_data: Optional[Dict[str, Any]] = None,
                             system_prompt: Optional[str] = None,
                             max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Call an OpenRouter model with optimized parameters

        Args:
            model_id: OpenRouter model ID
            query: User query
            context_data: Optional context data
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary
        """
        # Check internet connection
        if not await self.check_internet():
            logger.warning(f"No internet connection for OpenRouter API ({model_id})")
            return {
                "success": False,
                "content": "No internet connection available for OpenRouter API",
                "model": model_id,
                "error": "No internet connection"
            }

        # Get the latest API key from the API Key Manager
        self.openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            logger.error("OpenRouter API key not found")
            # Try to force reload the API key
            self.openrouter_api_key = self.api_key_manager.get_key("OPENROUTER_API_KEY", force_reload=True)
            if not self.openrouter_api_key:
                logger.error("OpenRouter API key still not found after forced reload")
                return {
                    "success": False,
                    "content": "OpenRouter API key not found. Please check your .env file.",
                    "model": model_id,
                    "error": "API key missing"
                }

        # Get system prompt if not provided
        if not system_prompt:
            # Try to find a role-specific prompt
            for role, info in self.model_roles.items():
                if info.get('model_id') == model_id:
                    system_prompt = get_prompt(role)
                    break

            # If no role-specific prompt found, use a generic one
            if not system_prompt:
                system_prompt = get_prompt("general")

        # Format context data
        context_str = ""
        if context_data:
            context_str = json.dumps(context_data, indent=2)

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if context_str:
            messages.append({"role": "system", "content": f"Additional context: {context_str}"})

        messages.append({"role": "user", "content": query})

        # Prepare request payload
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.95
        }

        # Make the API call
        try:
            headers = {"Authorization": f"Bearer {self.openrouter_api_key}"}

            response = await self.openrouter_client.post(
                "/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} {response.text}")
                return {
                    "success": False,
                    "content": f"OpenRouter API error: {response.status_code}",
                    "model": model_id,
                    "error": response.text
                }

            result = response.json()

            # Check for error in the response
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                logger.error(f"OpenRouter API error: {error_msg}")
                return {
                    "success": False,
                    "content": f"OpenRouter API error: {error_msg}",
                    "model": model_id,
                    "error": error_msg
                }

            # Extract content
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Update usage stats
            self.usage_stats["openrouter"]["calls"] += 1
            self.usage_stats["openrouter"]["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Get token usage if available
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            self.usage_stats["openrouter"]["tokens"] += total_tokens

            # Run garbage collection
            await self.check_memory()

            return {
                "success": True,
                "content": content,
                "model": model_id,
                "model_type": "openrouter",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            }

        except Exception as e:
            logger.error(f"OpenRouter API error for {model_id}: {str(e)}")
            return {
                "success": False,
                "content": f"OpenRouter API error: {str(e)}",
                "model": model_id,
                "error": str(e)
            }

    async def call_ollama(self,
                         model_name: str,
                         query: str,
                         context_data: Optional[Dict[str, Any]] = None,
                         system_prompt: Optional[str] = None,
                         max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Call an Ollama model with optimized parameters

        Args:
            model_name: Ollama model name
            query: User query
            context_data: Optional context data
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary
        """
        # Ensure Ollama is running
        ollama_running = await self.manage_ollama(ensure_running=True)
        if not ollama_running:
            logger.error("Failed to start Ollama")
            return {
                "success": False,
                "content": "Failed to start Ollama service",
                "model": model_name,
                "error": "Ollama service unavailable"
            }

        # Get system prompt if not provided
        if not system_prompt:
            system_prompt = get_prompt("local")

        # Format context data
        context_str = ""
        if context_data:
            context_str = json.dumps(context_data, indent=2)

        # Call Ollama
        result = await self.ollama_client.generate(
            prompt=query,
            model=model_name,
            system_prompt=f"{system_prompt}\n\nContext: {context_str}" if context_str else system_prompt,
            temperature=0.7,
            max_tokens=max_tokens
        )

        # Update usage stats
        if result.get("success", False):
            self.usage_stats["ollama"]["calls"] += 1
            self.usage_stats["ollama"]["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Get token usage if available
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            self.usage_stats["ollama"]["tokens"] += total_tokens

        # Run garbage collection
        await self.check_memory()

        return result

    async def route_query(self,
                         query: str,
                         intent: Optional[str] = None,
                         model_name: Optional[str] = None,
                         context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a query to the appropriate model based on intent or model name

        Args:
            query: User query
            intent: Optional intent for routing
            model_name: Optional specific model to use
            context_data: Optional context data

        Returns:
            Response from the selected model
        """
        # Get context data if not provided
        if not context_data:
            context_data = await self.get_context_data()

        # Check if we're in offline mode or have no internet
        if self.offline_mode or not await self.check_internet():
            logger.info("Using offline mode with Ollama")
            self.offline_mode = True  # Set offline mode if internet is unavailable

            # Ensure Ollama is running
            await self.manage_ollama(ensure_running=True)

            # Use phi model as fallback
            return await self.call_ollama("phi", query, context_data)

        # If a specific model is requested
        if model_name:
            # Check if it's a local model or Phi
            if model_name.startswith("local-") or model_name.lower() == "phi":
                logger.info(f"Using Ollama for model: {model_name}")
                # Ensure Ollama is running
                await self.manage_ollama(ensure_running=True)
                return await self.call_ollama(
                    model_name.replace("local-", ""),
                    query,
                    context_data
                )

            # Get the model ID
            model_id = self.models.get(model_name)
            if not model_id:
                logger.warning(f"Unknown model: {model_name}, using Mistral Small as fallback")
                return await self.call_mistral(query, context_data)

            # Call the model via OpenRouter
            return await self.call_openrouter(model_id, query, context_data)

        # If an intent is provided, route to the appropriate model
        if intent:
            # Map intent to model
            model_role = self.query_type_mapping.get(intent)
            if not model_role:
                logger.warning(f"Unknown intent: {intent}, using main_brain")
                model_id = MODEL_IDS["main_brain"]
                return await self.call_openrouter(model_id, query, context_data)

            # Get model ID for the role
            model_id = MODEL_ROLES.get(model_role, {}).get('model_id')
            if not model_id:
                logger.warning(f"No model ID for role: {model_role}, using main_brain")
                model_id = MODEL_IDS["main_brain"]
                return await self.call_openrouter(model_id, query, context_data)

            # Create a concise handoff message
            handoff_message = f"Routing to {model_role.capitalize()}..."

            # Call the specialized model
            response = await self.call_openrouter(model_id, query, context_data)

            # If the specialized model fails, fall back to main_brain
            if not response.get("success", False):
                logger.warning(f"Specialized model {model_role} failed, falling back to main_brain")
                model_id = MODEL_IDS["main_brain"]
                main_brain_response = await self.call_openrouter(model_id, query, context_data)
                return {
                    **main_brain_response,
                    "handoff_attempted": True,
                    "handoff_target": model_role,
                    "handoff_error": response.get("error")
                }

            # Add the handoff message to the response
            response["handoff_message"] = handoff_message
            response["handoff_target"] = model_role
            return response

        # Default to main_brain for general queries
        model_id = MODEL_IDS["main_brain"]
        return await self.call_openrouter(model_id, query, context_data)

    async def close(self):
        """
        Clean up resources
        """
        # Close HTTP clients
        await self.openrouter_client.aclose()

        # Stop Ollama if not in offline mode
        if not self.offline_mode:
            await self.manage_ollama(ensure_running=False)

        # Final garbage collection
        gc.collect()

        logger.info("Model interface resources cleaned up")
