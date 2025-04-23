"""
Local Model Manager for General Pulse
Handles local model integration with Ollama
"""

import asyncio
import structlog
import time
import os
import platform

# Try to import ollama for local models
try:
    import ollama
    from ollama import AsyncClient
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class OllamaError(Exception):
    """Exception raised for Ollama-related errors"""
    pass

class OllamaManager:
    """Manager for local Ollama models with health checks and auto-retry"""
    
    def __init__(self, host="http://localhost:11434"):
        """
        Initialize Ollama manager
        
        Args:
            host: Ollama server host URL
        """
        self.logger = structlog.get_logger("ollama_manager")
        self.available = OLLAMA_AVAILABLE
        
        if self.available:
            try:
                self.client = AsyncClient(host=host)
                self.logger.info(f"OllamaManager initialized with host: {host}")
            except Exception as e:
                self.logger.error(f"Error initializing Ollama client: {str(e)}")
                self.available = False
        else:
            self.logger.warning("Ollama not available (package not installed)")
            
        # Default models to use for fallback
        self.available_models = []
        self.default_models = ["llama3:8b", "deepseek-coder:6.7b", "mistral:latest"]
    
    async def health_check(self):
        """
        Check if Ollama is running and responsive
        
        Returns:
            bool: True if Ollama is healthy, False otherwise
        """
        if not self.available:
            return False
            
        try:
            # Simple ping to check if Ollama is responsive
            await self.client.embeddings(model="llama3:8b", prompt="ping", options={"num_ctx": 32})
            self.logger.debug("Ollama health check passed")
            return True
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def get_available_models(self):
        """
        Get list of available models from Ollama
        
        Returns:
            list: Available model names
        """
        if not self.available:
            return []
            
        try:
            models = await asyncio.to_thread(self.client.list)
            model_names = [model.get("name") for model in models.get("models", [])]
            self.available_models = model_names
            self.logger.debug(f"Available Ollama models: {model_names}")
            return model_names
        except Exception as e:
            self.logger.error(f"Error getting Ollama models: {str(e)}")
            return []
    
    async def ensure_model_available(self, model_name):
        """
        Ensure the specified model is available, downloading if needed
        
        Args:
            model_name: Name of the model to ensure
            
        Returns:
            bool: True if model is available, False otherwise
        """
        if not self.available:
            return False
            
        try:
            models = await self.get_available_models()
            if not models:
                return False
                
            if model_name in models:
                return True
                
            # Try to pull the model
            self.logger.info(f"Model {model_name} not found, pulling from Ollama")
            await asyncio.to_thread(ollama.pull, model_name)
            
            # Verify it's available now
            models = await self.get_available_models()
            return model_name in models
        except Exception as e:
            self.logger.error(f"Error ensuring model availability: {str(e)}")
            return False
    
    async def generate(self, prompt, model=None, temperature=0.7, max_tokens=1000, retries=3):
        """
        Generate text using local Ollama model with retries
        
        Args:
            prompt: The prompt to send to the model
            model: The model to use (default: first available model)
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            retries: Number of retry attempts
            
        Returns:
            dict: Response containing generated text
            
        Raises:
            OllamaError: If all attempts fail
        """
        if not self.available:
            raise OllamaError("Ollama is not available")
            
        # If no model specified, try default models in order
        if model is None:
            # Try to find an available model
            available = await self.get_available_models()
            if available:
                model = available[0]  # Use first available
            else:
                # Try default models
                for default_model in self.default_models:
                    if await self.ensure_model_available(default_model):
                        model = default_model
                        break
                        
            if model is None:
                raise OllamaError("No models available and unable to pull defaults")
        
        # Options for low-memory environments
        options = {
            "temperature": temperature,
            "num_predict": max_tokens
        }
        
        # Auto-detect low memory environment
        if platform.system() == "Windows" and psutil_available:
            try:
                import psutil
                mem = psutil.virtual_memory()
                if mem.available < 8 * 1024 * 1024 * 1024:  # Less than 8GB
                    self.logger.info("Low memory environment detected, using CPU-only mode")
                    options["num_gpu"] = 0  # Force CPU-only
            except:
                pass
        
        self.logger.info(f"Generating with Ollama model: {model}")
        
        for attempt in range(retries):
            try:
                # Try to ensure model is available
                if not await self.ensure_model_available(model):
                    # Try a fallback model
                    for fallback in self.default_models:
                        if await self.ensure_model_available(fallback):
                            model = fallback
                            self.logger.info(f"Using fallback model: {model}")
                            break
                
                response = await asyncio.to_thread(
                    self.client.generate,
                    model=model,
                    prompt=prompt,
                    options=options
                )
                
                if response and "response" in response:
                    return {
                        "content": response["response"],
                        "model": f"ollama/{model}",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                else:
                    raise OllamaError("Empty response from Ollama")
                    
            except Exception as e:
                self.logger.error(f"Ollama generation attempt {attempt+1}/{retries} failed: {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise OllamaError(f"All {retries} attempts failed: {str(e)}")
                    
# Try to import psutil for memory detection
try:
    import psutil
    psutil_available = True
except ImportError:
    psutil_available = False 