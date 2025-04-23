"""
Model Registry for General Pulse
Centralizes model configuration and fallback chains
"""

import os
import asyncio
import structlog
from typing import Dict, List, Any, Optional, Union, Tuple

from utils.openrouter_client import OpenRouterClient
from utils.execution_flow import ExecutionFlow

logger = structlog.get_logger("model_registry")

class ModelRegistry:
    """
    Centralized registry for model configuration and execution
    Manages model IDs, fallback chains, and execution strategies
    """
    
    def __init__(self):
        """Initialize the model registry"""
        self.models = {}
        self.openrouter_client = OpenRouterClient()
        self.execution_flow = ExecutionFlow(cache_ttl=300)  # 5 minute cache
        self._fallback_chains = {}
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize the model registry with default models"""
        # Default OpenRouter model mappings
        self.models = {
            # Large models
            "claude-3-opus": "anthropic/claude-3-opus:beta",
            "claude-3-sonnet": "anthropic/claude-3-sonnet",
            "gpt-4-turbo": "openai/gpt-4-turbo",
            "gpt-4o": "openai/gpt-4o",
            "gemini-pro": "google/gemini-pro",
            "deepseek-coder": "deepseek-ai/deepseek-coder",
            "mistral-large": "mistralai/mistral-large-latest",
            
            # Medium models
            "claude-3-haiku": "anthropic/claude-3-haiku",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
            "mistral-medium": "mistralai/mistral-medium",
            "llama3-70b": "meta-llama/llama-3-70b-instruct",
            
            # Small models
            "llama3-8b": "meta-llama/llama-3-8b-instruct",
            "mistral-small": "mistralai/mistral-7b-instruct",
            "gemma-7b": "google/gemma-7b-it"
        }
        
        # Initialize fallback chains - order matters (first = primary, rest = fallbacks)
        self._fallback_chains = {
            "premium": [
                "claude-3-opus", 
                "gpt-4o", 
                "claude-3-sonnet", 
                "gpt-4-turbo", 
                "mistral-large"
            ],
            "standard": [
                "claude-3-sonnet", 
                "gpt-4-turbo", 
                "mistral-large", 
                "gpt-4o"
            ],
            "efficient": [
                "claude-3-haiku", 
                "gpt-3.5-turbo", 
                "llama3-8b", 
                "mistral-small"
            ],
            "code": [
                "deepseek-coder", 
                "claude-3-sonnet", 
                "gpt-4o", 
                "mistral-large"
            ]
        }
    
    async def refresh_models(self):
        """Refresh model list from OpenRouter"""
        if not self.openrouter_client.available:
            logger.warning("OpenRouter client unavailable - using default models")
            return
            
        try:
            # Get models from OpenRouter
            models = await self.openrouter_client.get_available_models()
            
            # Create a mapping from display names to model IDs
            new_models = {}
            for model in models:
                if 'id' in model:
                    # Strip provider prefix for display name if applicable
                    display_name = model['id'].split('/')[-1] if '/' in model['id'] else model['id']
                    new_models[display_name] = model['id']
            
            # Update our models dictionary, preserving our aliases
            # This ensures our fallback chains continue to work
            for alias, model_id in self.models.items():
                provider_model = model_id.split('/')[-1] if '/' in model_id else model_id
                # Find if we have a refreshed version
                for display_name, new_id in new_models.items():
                    if provider_model == display_name:
                        self.models[alias] = new_id
                        break
            
            logger.info(f"Refreshed model registry with {len(new_models)} models")
            
        except Exception as e:
            logger.error(f"Failed to refresh models: {str(e)}")
    
    def get_model_id(self, model_name: str) -> str:
        """
        Get the actual model ID for a given model name
        
        Args:
            model_name: Name/alias of the model
            
        Returns:
            str: The actual model ID used by OpenRouter
        """
        if model_name in self.models:
            return self.models[model_name]
        # If not in our mapping, assume it's already a proper model ID
        return model_name
    
    def get_fallback_chain(self, chain_name: str) -> List[str]:
        """
        Get the fallback chain for a given name
        
        Args:
            chain_name: Name of the fallback chain
            
        Returns:
            list: List of model names in fallback order
        """
        return self._fallback_chains.get(chain_name, [])
    
    async def execute_with_fallback_chain(self, 
                                        chain_name: str,
                                        prompt: str,
                                        system_prompt: Optional[str] = None,
                                        temperature: float = 0.7,
                                        max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Execute a request with a fallback chain
        
        Args:
            chain_name: Name of the fallback chain to use
            prompt: The prompt to send to the models
            system_prompt: Optional system prompt
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            dict: Response from the first successful model in the chain
        """
        fallback_chain = self.get_fallback_chain(chain_name)
        
        if not fallback_chain:
            logger.error(f"Fallback chain not found: {chain_name}")
            return {"error": f"Fallback chain '{chain_name}' not found", "success": False}
            
        # Define the execution functions for each model in the chain
        async def call_model(model_name: str) -> Dict[str, Any]:
            model_id = self.get_model_id(model_name)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            try:
                return await self.openrouter_client.chat(
                    model_id=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {str(e)}")
                raise e
        
        # Create execution functions for each model
        primary_model = fallback_chain[0]
        fallback_models = fallback_chain[1:] if len(fallback_chain) > 1 else []
        
        primary_fn = lambda: call_model(primary_model)
        fallback_fns = [lambda m=model: call_model(m) for model in fallback_models]
        
        # Generate a cache key
        cache_key = f"{prompt[:50]}_{system_prompt[:20] if system_prompt else 'no_sys'}_{temperature}_{max_tokens}"
        
        # Execute with fallbacks
        result = await self.execution_flow.execute_with_fallbacks(
            primary_fn, 
            fallback_fns,
            cache_key=cache_key
        )
        
        return result
    
    def list_available_chains(self) -> List[str]:
        """List all available fallback chains"""
        return list(self._fallback_chains.keys())
    
    def register_custom_chain(self, chain_name: str, models: List[str]):
        """
        Register a custom fallback chain
        
        Args:
            chain_name: Name for the custom chain
            models: List of model names in fallback order
        """
        # Validate models exist
        invalid_models = [m for m in models if m not in self.models]
        if invalid_models:
            logger.warning(f"Some models in custom chain are not registered: {invalid_models}")
            
        self._fallback_chains[chain_name] = models
        logger.info(f"Registered custom chain '{chain_name}' with {len(models)} models")
    
    async def query_multiple_models(self,
                                  prompt: str,
                                  models: List[str],
                                  system_prompt: Optional[str] = None,
                                  temperature: float = 0.7,
                                  max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Query multiple models concurrently
        
        Args:
            prompt: The prompt to send
            models: List of model names to query
            system_prompt: Optional system prompt
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            dict: Mapping of model names to responses
        """
        # Create model mapping
        model_mapping = {model: self.get_model_id(model) for model in models}
        
        # Query all models concurrently
        result = await self.openrouter_client.multi_model_query(
            prompts=prompt,
            model_mapping=model_mapping,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return result

# Global registry instance
_registry = ModelRegistry()

async def refresh_models():
    """Refresh the global model registry"""
    await _registry.refresh_models()
    
def get_model_id(model_name):
    """Get model ID from the global registry"""
    return _registry.get_model_id(model_name)
    
def get_fallback_chain(chain_name):
    """Get fallback chain from the global registry"""
    return _registry.get_fallback_chain(chain_name)
    
async def execute_with_fallback_chain(chain_name, prompt, system_prompt=None, temperature=0.7, max_tokens=1000):
    """Execute a request with a fallback chain from the global registry"""
    return await _registry.execute_with_fallback_chain(chain_name, prompt, system_prompt, temperature, max_tokens)
    
def list_available_chains():
    """List all available fallback chains from the global registry"""
    return _registry.list_available_chains()
    
def register_custom_chain(chain_name, models):
    """Register a custom fallback chain in the global registry"""
    _registry.register_custom_chain(chain_name, models)
    
async def query_multiple_models(prompt, models, system_prompt=None, temperature=0.7, max_tokens=1000):
    """Query multiple models concurrently from the global registry"""
    return await _registry.query_multiple_models(prompt, models, system_prompt, temperature, max_tokens)

def get_model_display_name(model_name):
    """Get a user-friendly display name for a model"""
    # If it's a model ID with a provider prefix (e.g. "openai/gpt-4"), show only the model part
    if "/" in model_name:
        parts = model_name.split("/")
        if len(parts) == 2:
            provider, model = parts
            return f"{model} ({provider.title()})"
    
    # Return the original name if we don't have special handling
    return model_name 