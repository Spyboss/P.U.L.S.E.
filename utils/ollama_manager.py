"""
Ollama Service Manager for General Pulse
Manages the Ollama service lifecycle and provides offline mode functionality
"""

import os
import sys
import subprocess
import asyncio
import platform
import structlog
import psutil
import time
import httpx
from typing import Dict, List, Any, Optional, Tuple

# OllamaClient class is now integrated into this file
# Previously imported from utils.ollama_client

class OllamaClient:
    """
    Enhanced Ollama client with health checks and reliable execution
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client

        Args:
            base_url: Base URL for Ollama server
        """
        self.base_url = base_url
        self.available_models = []
        self.is_healthy = False
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.default_model = "mistral"
        self.force_cpu = self._should_force_cpu()

    def _should_force_cpu(self) -> bool:
        """
        Determine if we should force CPU mode based on system specs

        Returns:
            True if CPU mode should be forced
        """
        # Check available RAM
        import psutil
        available_gb = psutil.virtual_memory().available / (1024 ** 3)

        # If less than 6GB available, force CPU mode
        if available_gb < 6:
            logger.warning(f"Low memory detected ({available_gb:.1f}GB available). Forcing CPU mode.")
            return True

        # Can also check for specific platforms or other conditions
        return False

    async def refresh_models(self) -> List[str]:
        """
        Refresh the list of available models

        Returns:
            List of available model names
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    self.available_models = [model["name"] for model in data.get("models", [])]
                    return self.available_models
        except Exception as e:
            logger.warning(f"Failed to refresh Ollama models: {str(e)}")
            self.available_models = []

        return self.available_models

    async def check_health(self, force: bool = False, offline_mode: bool = True) -> bool:
        """
        Check if Ollama service is healthy

        Args:
            force: Force a health check even if the cache is valid
            offline_mode: Whether offline mode is enabled

        Returns:
            True if Ollama is healthy
        """
        current_time = time.time()

        # Skip health check if offline mode is disabled (unless forced)
        if not offline_mode and not force:
            logger.debug("Skipping Ollama client health check because offline mode is disabled")
            self.last_health_check = current_time
            self.is_healthy = False
            return False

        # Return cached result if recent enough
        if not force and current_time - self.last_health_check < self.health_check_interval:
            return self.is_healthy

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/version")
                self.is_healthy = response.status_code == 200

                if self.is_healthy:
                    # Try to get available models
                    await self.refresh_models()
        except Exception as e:
            logger.debug(f"Ollama health check failed: {str(e)}")
            self.is_healthy = False

        self.last_health_check = current_time
        return self.is_healthy

    async def generate(self, prompt: str, model: str, system_prompt: Optional[str] = None,
                      temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate text using Ollama

        Args:
            prompt: The prompt to generate from
            model: The model to use
            system_prompt: Optional system prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary
        """
        try:
            # Prepare the request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt

            # Add CPU-only flag if needed
            if self.force_cpu:
                payload["options"] = {"num_gpu": 0}

            # Make the API call
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"Ollama API error: {response.status_code} {response.text}")
                    return {
                        "success": False,
                        "content": f"Ollama API error: {response.status_code}",
                        "model": model,
                        "error": response.text
                    }

                result = response.json()

                # Extract content
                content = result.get("response", "")

                # Get token usage if available
                usage = {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                }

                return {
                    "success": True,
                    "content": content,
                    "model": model,
                    "model_type": "ollama",
                    "usage": usage
                }

        except Exception as e:
            logger.error(f"Ollama API error for {model}: {str(e)}")
            return {
                "success": False,
                "content": f"Ollama API error: {str(e)}",
                "model": model,
                "error": str(e)
            }

# Configure logger
logger = structlog.get_logger("ollama_manager")

class OllamaManager:
    """
    Manages the Ollama service lifecycle and provides offline mode functionality
    """

    def __init__(self):
        """
        Initialize the Ollama manager
        """
        self.client = OllamaClient()
        self.is_running = False
        self.is_offline_mode = False
        self.process = None
        self.ollama_path = self._find_ollama_executable()
        self.last_status_check = 0
        self.status_check_interval = 10  # seconds
        self.loaded_models = []

    def _find_ollama_executable(self) -> str:
        """
        Find the Ollama executable path

        Returns:
            Path to the Ollama executable
        """
        # Check if Ollama is in PATH
        if platform.system() == "Windows":
            # On Windows, check common installation locations
            possible_paths = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Ollama", "ollama.exe"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Ollama", "ollama.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Ollama", "ollama.exe"),
                "ollama.exe"  # If in PATH
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return path

            # Try to find using where command
            try:
                result = subprocess.run(["where", "ollama"], capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split("\n")[0]
            except Exception:
                pass

        else:
            # On Linux/Mac, check common installation locations
            possible_paths = [
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
                "/opt/ollama/bin/ollama",
                os.path.expanduser("~/.local/bin/ollama"),
                "ollama"  # If in PATH
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return path

            # Try to find using which command
            try:
                result = subprocess.run(["which", "ollama"], capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                pass

        # Default to just the command name and hope it's in PATH
        return "ollama"

    async def check_status(self, force: bool = False) -> Dict[str, Any]:
        """
        Check the status of the Ollama service

        Args:
            force: Force a status check even if the cache is valid

        Returns:
            Status information
        """
        current_time = time.time()

        # Return cached result if recent enough
        if not force and current_time - self.last_status_check < self.status_check_interval:
            return self._get_cached_status()

        # Check if we have enough memory to run Ollama
        memory_info = self._get_system_memory()
        free_memory_gb = memory_info["free_gb"]
        memory_percent = memory_info["percent_used"]

        # Skip health check if offline mode is disabled (unless forced)
        if not self.is_offline_mode and not force:
            logger.debug("Skipping Ollama health check because offline mode is disabled")
            self.last_status_check = current_time
            self.is_running = False  # Assume not running when offline mode is disabled
            return {
                "running": False,
                "offline_mode": False,
                "models": [],
                "memory_usage": 0.0,
                "executable_found": bool(self.ollama_path),
                "system_memory": {
                    "free_gb": free_memory_gb,
                    "percent_used": memory_percent
                },
                "error": None,
                "skipped": True
            }

        # Check if Ollama is running
        try:
            is_healthy = await self.client.check_health(force=True, offline_mode=self.is_offline_mode)
            self.is_running = is_healthy

            # Get available models if running
            if is_healthy:
                self.loaded_models = await self.client.refresh_models()

            # Get memory usage
            memory_usage = self._get_ollama_memory_usage()

            # Update last check time
            self.last_status_check = current_time

            status = {
                "running": self.is_running,
                "offline_mode": self.is_offline_mode,
                "models": self.loaded_models,
                "memory_usage": memory_usage,
                "executable_found": bool(self.ollama_path),
                "system_memory": {
                    "free_gb": free_memory_gb,
                    "percent_used": memory_percent
                },
                "error": None
            }

            return status
        except Exception as e:
            logger.error(f"Error checking Ollama status: {str(e)}")

            # Try to determine the specific error
            error_message = str(e)
            specific_error = "Unknown error"

            if "connection refused" in error_message.lower():
                specific_error = "Connection refused: Ollama service is not running"
            elif "timeout" in error_message.lower():
                specific_error = "Connection timeout: Ollama service is not responding"
            elif "address already in use" in error_message.lower():
                specific_error = "Port 11434 is already in use by another application"
            elif "permission denied" in error_message.lower():
                specific_error = "Permission denied: Cannot access Ollama service"

            # Update last check time
            self.last_status_check = current_time
            self.is_running = False

            return {
                "running": False,
                "offline_mode": self.is_offline_mode,
                "models": [],
                "memory_usage": 0.0,
                "executable_found": bool(self.ollama_path),
                "system_memory": {
                    "free_gb": free_memory_gb,
                    "percent_used": memory_percent
                },
                "error": specific_error
            }

    def _get_cached_status(self) -> Dict[str, Any]:
        """
        Get cached status information

        Returns:
            Cached status information
        """
        memory_usage = self._get_ollama_memory_usage()

        return {
            "running": self.is_running,
            "offline_mode": self.is_offline_mode,
            "models": self.loaded_models,
            "memory_usage": memory_usage,
            "executable_found": bool(self.ollama_path),
            "cached": True
        }

    def _get_system_memory(self) -> Dict[str, float]:
        """
        Get system memory information

        Returns:
            Dictionary with memory information
        """
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)
            free_gb = memory.available / (1024 ** 3)
            used_gb = total_gb - free_gb
            percent_used = memory.percent

            return {
                "total_gb": round(total_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_gb": round(used_gb, 2),
                "percent_used": round(percent_used, 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get system memory info: {str(e)}")
            return {
                "total_gb": 0.0,
                "free_gb": 0.0,
                "used_gb": 0.0,
                "percent_used": 0.0
            }

    def _get_ollama_memory_usage(self) -> float:
        """
        Get Ollama's memory usage in GB

        Returns:
            Memory usage in GB
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                if 'ollama' in proc.info['name'].lower():
                    return proc.info['memory_info'].rss / (1024 ** 3)  # Convert to GB
        except Exception as e:
            logger.warning(f"Failed to get Ollama memory usage: {str(e)}")

        return 0.0

    async def start_service(self) -> Dict[str, Any]:
        """
        Start the Ollama service

        Returns:
            Dictionary with status information
        """
        # Check if already running
        status = await self.check_status(force=True)
        if status["running"]:
            logger.info("Ollama service is already running")
            return {
                "success": True,
                "message": "Ollama service is already running",
                "status": status
            }

        # Check if executable exists
        if not self.ollama_path or not os.path.exists(self.ollama_path):
            error_msg = f"Ollama executable not found at {self.ollama_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status": status
            }

        # Check if we have enough memory
        memory_info = self._get_system_memory()
        free_memory_gb = memory_info["free_gb"]
        memory_percent = memory_info["percent_used"]

        if free_memory_gb < 1.5:
            error_msg = f"Not enough memory to start Ollama. Free memory: {free_memory_gb:.2f}GB, Used: {memory_percent}%"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status": status
            }

        try:
            # Start the Ollama service
            if platform.system() == "Windows":
                # On Windows, use CREATE_NO_WINDOW flag to hide console window
                self.process = subprocess.Popen(
                    [self.ollama_path, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # On Linux/Mac
                self.process = subprocess.Popen(
                    [self.ollama_path, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            # Wait for service to start
            for attempt in range(10):  # Try for 10 seconds
                await asyncio.sleep(1)
                try:
                    if await self.client.check_health(offline_mode=self.is_offline_mode):
                        self.is_running = True
                        logger.info("Ollama service started successfully")

                        # Get updated status
                        new_status = await self.check_status(force=True)

                        return {
                            "success": True,
                            "message": "Ollama service started successfully",
                            "status": new_status
                        }
                except Exception as e:
                    logger.warning(f"Health check attempt {attempt+1}/10 failed: {str(e)}")

            error_msg = "Ollama service started but health check failed after 10 attempts"
            logger.warning(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status": await self.check_status(force=True)
            }

        except Exception as e:
            error_msg = f"Failed to start Ollama service: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status": await self.check_status(force=True)
            }

    async def stop_service(self) -> Dict[str, Any]:
        """
        Stop the Ollama service

        Returns:
            Dictionary with status information
        """
        # Check if running
        status = await self.check_status(force=True)
        if not status["running"]:
            logger.info("Ollama service is not running")
            return {
                "success": True,
                "message": "Ollama service is not running",
                "status": status
            }

        try:
            # If we started the process, terminate it
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()

                self.process = None
                self.is_running = False
                logger.info("Ollama service stopped successfully")

                # Get updated status
                new_status = await self.check_status(force=True)

                return {
                    "success": True,
                    "message": "Ollama service stopped successfully",
                    "status": new_status
                }

            # Otherwise, try to find and kill the process
            ollama_processes_found = False
            for proc in psutil.process_iter(['pid', 'name']):
                if 'ollama' in proc.info['name'].lower():
                    ollama_processes_found = True
                    try:
                        psutil.Process(proc.info['pid']).terminate()
                        logger.info(f"Terminated Ollama process with PID {proc.info['pid']}")
                    except Exception as e:
                        logger.warning(f"Failed to terminate Ollama process with PID {proc.info['pid']}: {str(e)}")

            if not ollama_processes_found:
                logger.warning("No Ollama processes found to terminate")

            # Verify it's stopped
            await asyncio.sleep(2)
            try:
                is_healthy = await self.client.check_health(force=True, offline_mode=self.is_offline_mode)
                if not is_healthy:
                    self.is_running = False
                    logger.info("Ollama service stopped successfully")

                    # Get updated status
                    new_status = await self.check_status(force=True)

                    return {
                        "success": True,
                        "message": "Ollama service stopped successfully",
                        "status": new_status
                    }
                else:
                    error_msg = "Failed to stop Ollama service - service is still running"
                    logger.warning(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "status": await self.check_status(force=True)
                    }
            except Exception as e:
                # If check_health fails, it likely means the service is stopped
                self.is_running = False
                logger.info(f"Ollama service appears to be stopped (health check failed with: {str(e)})")

                # Get updated status
                new_status = await self.check_status(force=True)

                return {
                    "success": True,
                    "message": "Ollama service appears to be stopped",
                    "status": new_status
                }

        except Exception as e:
            error_msg = f"Failed to stop Ollama service: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status": await self.check_status(force=True)
            }

    async def toggle_offline_mode(self, enable: bool) -> Dict[str, Any]:
        """
        Toggle offline mode

        Args:
            enable: True to enable offline mode, False to disable

        Returns:
            Status information
        """
        if enable == self.is_offline_mode:
            # No change needed
            status = await self.check_status()
            return {
                "success": True,
                "message": f"Offline mode already {'enabled' if enable else 'disabled'}",
                "status": status
            }

        if enable:
            # Enable offline mode
            # Start Ollama if not running
            if not self.is_running:
                result = await self.start_service()
                if not result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to start Ollama service: {result['message']}",
                        "offline_mode": False,
                        "status": result["status"]
                    }

            # Set offline mode flag
            self.is_offline_mode = True
            logger.info("Offline mode enabled")

            # Get updated status
            status = await self.check_status(force=True)

            return {
                "success": True,
                "message": "Offline mode enabled successfully",
                "offline_mode": True,
                "status": status
            }

        else:
            # Disable offline mode
            # Set offline mode flag
            self.is_offline_mode = False
            logger.info("Offline mode disabled")

            # Get updated status
            status = await self.check_status(force=True)

            return {
                "success": True,
                "message": "Offline mode disabled successfully",
                "offline_mode": False,
                "status": status
            }

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        Pull a model from Ollama

        Args:
            model_name: Name of the model to pull

        Returns:
            Status information
        """
        # Check if Ollama is running
        status = await self.check_status()
        if not status["running"]:
            result = await self.start_service()
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to start Ollama service: {result['message']}",
                    "model": model_name,
                    "status": result["status"]
                }

        # Check if we have enough memory
        memory_info = self._get_system_memory()
        free_memory_gb = memory_info["free_gb"]
        memory_percent = memory_info["percent_used"]

        # Different models have different memory requirements
        min_memory_required = 1.5  # Default minimum
        if "llama" in model_name.lower():
            min_memory_required = 4.0  # Llama models need more memory
        elif "mistral" in model_name.lower():
            min_memory_required = 3.0  # Mistral models need more memory
        elif "phi" in model_name.lower():
            min_memory_required = 2.0  # Phi models need moderate memory

        if free_memory_gb < min_memory_required:
            error_msg = f"Not enough memory to pull model {model_name}. Required: {min_memory_required:.1f}GB, Available: {free_memory_gb:.1f}GB, Used: {memory_percent}%"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "model": model_name,
                "status": status
            }

        try:
            # Pull the model
            logger.info(f"Pulling model {model_name}")

            # Use subprocess to pull the model
            process = subprocess.Popen(
                [self.ollama_path, "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # Don't use text=True to avoid encoding issues
                text=False
            )

            # Wait for process to complete with increased timeout
            stdout_bytes, stderr_bytes = process.communicate(timeout=1200)  # 20 minute timeout

            # Safely decode output
            stdout_text = stdout_bytes.decode('utf-8', errors='replace')
            stderr_text = stderr_bytes.decode('utf-8', errors='replace')

            if process.returncode != 0:
                error_msg = f"Failed to pull model {model_name}: {stderr_text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg,
                    "model": model_name,
                    "status": await self.check_status(force=True)
                }

            # Refresh models
            models = await self.client.refresh_models()

            # Get updated status
            new_status = await self.check_status(force=True)

            success_msg = f"Model {model_name} pulled successfully"
            logger.info(success_msg)
            return {
                "success": True,
                "message": success_msg,
                "model": model_name,
                "models": models,
                "status": new_status
            }

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while pulling model {model_name} (exceeded 10 minutes)"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "model": model_name,
                "status": await self.check_status(force=True)
            }
        except Exception as e:
            error_msg = f"Failed to pull model {model_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "model": model_name,
                "status": await self.check_status(force=True)
            }

    async def list_models(self) -> Dict[str, Any]:
        """
        List available models

        Returns:
            Dictionary with model information
        """
        # Check if Ollama is running
        status = await self.check_status()
        if not status["running"]:
            return {
                "success": False,
                "message": "Ollama service is not running",
                "models": [],
                "status": status
            }

        # Refresh models
        models = await self.client.refresh_models()

        # Get model details
        model_details = []
        try:
            # Use subprocess to get model details
            process = subprocess.Popen(
                [self.ollama_path, "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for process to complete
            stdout, stderr = process.communicate(timeout=10)  # 10 second timeout

            if process.returncode == 0:
                # Parse the output
                lines = stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    for line in lines[1:]:  # Skip header row
                        parts = line.split()
                        if len(parts) >= 3:
                            model_details.append({
                                "name": parts[0],
                                "id": parts[1],
                                "size": parts[2],
                                "modified": " ".join(parts[3:]) if len(parts) > 3 else ""
                            })
        except Exception as e:
            logger.warning(f"Failed to get detailed model information: {str(e)}")

        return {
            "success": True,
            "message": f"Found {len(models)} models",
            "models": models,
            "model_details": model_details,
            "status": status
        }

    async def check_internet_connection(self) -> bool:
        """
        Check if internet connection is available

        Returns:
            True if internet connection is available
        """
        try:
            # Try to connect to Google's DNS server
            process = subprocess.Popen(
                ["ping", "-n", "1", "8.8.8.8"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Wait for process to complete
            process.communicate(timeout=5)

            # Check return code
            return process.returncode == 0
        except Exception as e:
            logger.warning(f"Failed to check internet connection: {str(e)}")
            return False

    async def auto_start_if_offline(self) -> Dict[str, Any]:
        """
        Auto-start Ollama if internet connection is not available

        Returns:
            Status information
        """
        # Check internet connection
        internet_available = await self.check_internet_connection()

        if not internet_available:
            logger.info("Internet connection not available, auto-starting Ollama for offline mode")

            # Start Ollama if not running
            status = await self.check_status()
            if not status["running"]:
                result = await self.start_service()
                if result["success"]:
                    # Enable offline mode
                    self.is_offline_mode = True
                    logger.info("Offline mode enabled automatically")

                    return {
                        "success": True,
                        "message": "Ollama started automatically for offline mode",
                        "offline_mode": True,
                        "status": result["status"]
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to auto-start Ollama: {result['message']}",
                        "offline_mode": False,
                        "status": result["status"]
                    }
            else:
                # Enable offline mode
                self.is_offline_mode = True
                logger.info("Offline mode enabled automatically")

                return {
                    "success": True,
                    "message": "Ollama was already running, enabled offline mode",
                    "offline_mode": True,
                    "status": status
                }
        else:
            logger.info("Internet connection available, no need for auto-start")
            return {
                "success": True,
                "message": "Internet connection available, no need for auto-start",
                "offline_mode": self.is_offline_mode,
                "status": await self.check_status()
            }

    async def generate(self, prompt: str, model: str = "phi", system_prompt: Optional[str] = None,
                      temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate text using Ollama

        Args:
            prompt: The prompt to generate from
            model: The model to use (default: phi)
            system_prompt: Optional system prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary
        """
        # Ensure model is a valid model name, not the user's query
        # If model looks like a greeting or common query, default to phi
        if model.lower().strip() in ["hi", "hello", "hey", "what's up", "how are you"]:
            logger.warning(f"Invalid model name detected: '{model}', defaulting to 'phi'")
            model = "phi"

        # Check if Ollama is running
        status = await self.check_status()
        if not status["running"]:
            # Try to start Ollama
            result = await self.start_service()
            if not result["success"]:
                return {
                    "success": False,
                    "content": f"Failed to start Ollama: {result['message']}",
                    "model": model,
                    "error": "Ollama service unavailable"
                }

        # Check if model is available
        if model not in status["models"]:
            logger.warning(f"Model {model} not available, attempting to pull")
            pull_result = await self.pull_model(model)
            if not pull_result["success"]:
                return {
                    "success": False,
                    "content": f"Model {model} not available and failed to pull: {pull_result['message']}",
                    "model": model,
                    "error": "Model unavailable"
                }

        # Use the client to generate text
        return await self.client.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
