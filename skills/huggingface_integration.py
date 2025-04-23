"""
Hugging Face Integration for General Pulse
Provides fallback AI capabilities using open models via Hugging Face's free API
"""

import os
import json
import time
from pathlib import Path
from huggingface_hub import InferenceClient, HfFolder
from utils.logger import GeneralPulseLogger

class HuggingFaceIntegration:
    """Integration with Hugging Face for accessing free AI models."""

    def __init__(self, config_path=None):
        """Initialize the Hugging Face integration."""
        self.logger = GeneralPulseLogger("HuggingFaceIntegration")
        self.logger.info("Initializing Hugging Face integration")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Get HF token from config or environment
        self.hf_token = self.config.get("hf_token") or os.environ.get("HUGGINGFACE_TOKEN")
        
        # Set default models if not in config
        if "models" not in self.config:
            self.config["models"] = {
                "llama3-8b": "meta-llama/Meta-Llama-3-8B-Instruct",
                "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
                "phi3": "microsoft/Phi-3-mini-4k-instruct"
            }
        
        # Initialize the client if token is available
        self.client = None
        if self.hf_token:
            try:
                self.client = InferenceClient(token=self.hf_token)
                self.logger.info("Hugging Face client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Hugging Face client: {str(e)}", exc_info=True)
        else:
            self.logger.warning("No Hugging Face token found, some features may be limited")

    def _load_config(self, config_path):
        """Load configuration from file."""
        if not config_path:
            config_path = "configs/huggingface_config.yaml"
        
        # Default configuration
        default_config = {
            "models": {
                "llama3-8b": "meta-llama/Meta-Llama-3-8B-Instruct",
                "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
                "phi3": "microsoft/Phi-3-mini-4k-instruct"
            },
            "max_new_tokens": 500,
            "temperature": 0.7,
            "cache_path": "memory/hf_cache"
        }
        
        try:
            # Try to load config file
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        import yaml
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)
                    
                    self.logger.info(f"Loaded Hugging Face config from {config_path}")
                    # Merge with default config
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    
                    return config
        except Exception as e:
            self.logger.error(f"Error loading Hugging Face config: {str(e)}", exc_info=True)
        
        # If loading failed, return default config
        self.logger.info("Using default Hugging Face configuration")
        return default_config
    
    def is_configured(self):
        """Check if the integration is properly configured."""
        return self.client is not None
    
    def get_available_models(self):
        """Get a list of available models."""
        return list(self.config["models"].keys())
    
    async def query_model(self, model_name, prompt, system_prompt=None, max_new_tokens=None, temperature=None):
        """
        Query a model with the given prompt.
        
        Args:
            model_name (str): Name of the model to use (e.g., "llama3-8b")
            prompt (str): The prompt to send to the model
            system_prompt (str, optional): System prompt for models that support it
            max_new_tokens (int, optional): Maximum number of tokens to generate
            temperature (float, optional): Temperature parameter for generation
            
        Returns:
            dict: A dictionary containing the response and metadata
        """
        if not self.is_configured():
            self.logger.error("Hugging Face integration not configured")
            return {"error": "Hugging Face integration not configured"}
        
        # Get actual model ID from config
        model_id = self.config["models"].get(model_name)
        if not model_id:
            self.logger.error(f"Unknown model: {model_name}")
            return {"error": f"Unknown model: {model_name}"}
        
        # Set defaults from config
        if max_new_tokens is None:
            max_new_tokens = self.config.get("max_new_tokens", 500)
        
        if temperature is None:
            temperature = self.config.get("temperature", 0.7)
        
        # Format the prompt based on whether a system prompt is provided
        formatted_prompt = prompt
        if system_prompt:
            # Use a simple format that works with most instruction models
            formatted_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>"
        
        self.logger.info(f"Querying Hugging Face model: {model_id}")
        start_time = time.time()
        
        try:
            # Call the model
            response = await self._call_model_async(model_id, formatted_prompt, max_new_tokens, temperature)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Hugging Face query completed in {elapsed_time:.2f}s")
            
            # Return the response
            return {
                "response": response,
                "model": model_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            self.logger.error(f"Error querying Hugging Face model: {str(e)}", exc_info=True)
            return {"error": f"Hugging Face API error: {str(e)}"}
    
    async def _call_model_async(self, model_id, prompt, max_new_tokens, temperature):
        """Call the model asynchronously using anyio."""
        import anyio
        
        def _call_sync():
            """Synchronous call to Hugging Face API."""
            try:
                return self.client.text_generation(
                    model=model_id,
                    prompt=prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True
                )
            except Exception as e:
                self.logger.error(f"Error in Hugging Face API call: {str(e)}", exc_info=True)
                raise
        
        # Run the sync call in a thread
        return await anyio.to_thread.run_sync(_call_sync)
    
    def save_response(self, model_name, prompt, response, cache_path=None):
        """Save a model response to the cache."""
        if not cache_path:
            cache_path = self.config.get("cache_path", "memory/hf_cache")
        
        # Ensure the cache directory exists
        Path(cache_path).mkdir(parents=True, exist_ok=True)
        
        # Create a unique file name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_name = f"{cache_path}/{model_name}_{timestamp}.json"
        
        # Save the response
        try:
            with open(file_name, 'w') as f:
                json.dump({
                    "model": model_name,
                    "prompt": prompt,
                    "response": response,
                    "timestamp": timestamp
                }, f, indent=2)
                
            self.logger.info(f"Saved response to {file_name}")
            return file_name
        except Exception as e:
            self.logger.error(f"Error saving response: {str(e)}", exc_info=True)
            return None

# Create a default instance
huggingface = HuggingFaceIntegration() 