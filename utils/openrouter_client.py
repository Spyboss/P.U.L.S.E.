"""
OpenRouter client for General Pulse
Provides interface to OpenRouter API with fallback and retry mechanisms
"""

import os
import json
import time
import asyncio
import httpx
import structlog
from typing import Dict, List, Any, Optional, Union, Tuple

from utils.execution_flow import retry_async

logger = structlog.get_logger("openrouter_client")

class OpenRouterError(Exception):
    """OpenRouter API error"""
    pass

class OpenRouterClient:
    """Client for OpenRouter API with fault tolerance"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key (or from env var OPENROUTER_API_KEY)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.available = bool(self.api_key)
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        if not self.available:
            logger.warning("OpenRouter API key not provided, client will be unavailable")
    
    @retry_async(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    async def chat(self, 
                  model_id: str, 
                  messages: List[Dict[str, str]], 
                  temperature: float = 0.7, 
                  max_tokens: int = 1000,
                  stream: bool = False) -> Dict[str, Any]:
        """
        Call OpenRouter chat API
        
        Args:
            model_id: OpenRouter model ID
            messages: List of message objects with role and content
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            dict: Response containing content, model and timestamp
        """
        if not self.available:
            raise OpenRouterError("OpenRouter API key not provided")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://general-pulse.github.io", # Replace with your site
            "X-Title": "General Pulse"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            # Log request details for debugging
            logger.debug(
                "Calling OpenRouter API", 
                model=model_id, 
                temp=temperature, 
                max_tokens=max_tokens
            )
            
            # Make API request
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Handle streaming response
            if stream:
                return response  # Return the response object for streaming
                
            # Handle non-streaming response
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"]
                except:
                    pass
                
                raise OpenRouterError(
                    f"OpenRouter API returned error {response.status_code}: {error_detail}"
                )
                
            # Parse response
            response_data = response.json()
            
            # Format the response in a consistent way
            formatted_response = {
                "content": response_data["choices"][0]["message"]["content"],
                "model": response_data.get("model", model_id),
                "id": response_data.get("id"),
                "usage": response_data.get("usage", {}),
                "timestamp": time.time()
            }
            
            return formatted_response
            
        except httpx.TimeoutException:
            raise OpenRouterError(f"Request to OpenRouter timed out after {self.timeout}s")
        except httpx.RequestError as e:
            raise OpenRouterError(f"Request to OpenRouter failed: {str(e)}")
        except json.JSONDecodeError:
            raise OpenRouterError("Failed to parse OpenRouter API response")
        except Exception as e:
            if isinstance(e, OpenRouterError):
                raise
            raise OpenRouterError(f"Error calling OpenRouter API: {str(e)}")
    
    async def chat_with_retry(self, *args, **kwargs) -> Dict[str, Any]:
        """Wrapper with built-in retry for chat method"""
        return await self.chat(*args, **kwargs)
    
    async def process_stream(self, response) -> str:
        """
        Process a streaming response from OpenRouter
        
        Args:
            response: Streaming response from OpenRouter
            
        Returns:
            str: Aggregated content from stream
        """
        content = ""
        
        try:
            async for line in response.aiter_lines():
                if not line or line.strip() == "":
                    continue
                    
                if line.startswith("data: "):
                    line = line[6:]  # Remove "data: " prefix
                    
                if line == "[DONE]":
                    break
                    
                try:
                    chunk = json.loads(line)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            content_chunk = delta["content"]
                            content += content_chunk
                            # You can yield here if implementing a live stream
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.error(f"Error processing stream: {str(e)}")
            
        return content
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter
        
        Returns:
            list: List of model objects with id, name, context_length, etc.
        """
        if not self.available:
            return []
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch models: {response.status_code} {response.text}")
                return []
                
            models_data = response.json()
            return models_data.get("data", [])
            
        except Exception as e:
            logger.error(f"Error fetching OpenRouter models: {str(e)}")
            return []
    
    async def multi_model_query(self, 
                              prompts: Union[str, List[str]], 
                              model_mapping: Dict[str, str],
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Query multiple models concurrently using OpenRouter
        
        Args:
            prompts: String prompt or list of prompts (one per model)
            model_mapping: Mapping of model names to OpenRouter model IDs
            system_prompt: Optional system prompt to prepend to all messages
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            dict: Mapping of model names to responses
        """
        if not self.available:
            return {name: {"error": "OpenRouter API key not provided", "model": name} 
                   for name in model_mapping}
        
        # Handle single prompt case
        if isinstance(prompts, str):
            prompts = {name: prompts for name in model_mapping}
        elif isinstance(prompts, list):
            if len(prompts) != len(model_mapping):
                raise ValueError("Number of prompts must match number of models")
            prompts = dict(zip(model_mapping.keys(), prompts))
        
        # Create tasks
        tasks = {}
        for model_name, model_id in model_mapping.items():
            prompt = prompts[model_name]
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Create task
            tasks[model_name] = asyncio.create_task(
                self.chat_with_retry(
                    model_id=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            )
        
        # Gather results
        results = {}
        for model_name, task in tasks.items():
            try:
                results[model_name] = await task
            except Exception as e:
                logger.error(f"Error querying {model_name}: {str(e)}")
                results[model_name] = {
                    "error": str(e),
                    "model": model_name
                }
        
        return results 