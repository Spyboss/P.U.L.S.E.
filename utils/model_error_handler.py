"""
Model Error Handler Module
Provides standardized error handling for AI model integrations
"""

import json
import structlog
import traceback
from typing import Dict, Any, Optional, Tuple, Callable, List
import httpx
import aiohttp
from datetime import datetime

# Import error monitoring (with conditional import to avoid circular imports)
try:
    from utils.error_monitoring import from_integration_error, ErrorSeverity, log_error
    ERROR_MONITORING_AVAILABLE = True
except ImportError:
    ERROR_MONITORING_AVAILABLE = False

logger = structlog.get_logger("model_error_handler")

class ModelError(Exception):
    """Base exception for model errors"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response: Optional[Dict] = None, original_exception: Optional[Exception] = None,
                 model: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.original_exception = original_exception
        self.model = model
        super().__init__(self.message)


def handle_model_error(e: Exception, operation: str, model: str = "unknown") -> Dict[str, Any]:
    """
    Handle model API errors and return a standardized error response

    Args:
        e: The exception that occurred
        operation: The operation being performed (e.g., "generate_text")
        model: The model being used

    Returns:
        A standardized error response dictionary
    """
    error_str = str(e).lower()
    error_dict = {
        "success": False,
        "error_type": "model_error",
        "operation": operation,
        "model": model,
        "timestamp": datetime.now().isoformat()
    }

    # Extract status code if available
    status_code = None
    if hasattr(e, 'status_code'):
        status_code = e.status_code
    elif hasattr(e, 'status'):
        status_code = e.status

    # Add status code to error dict if available
    if status_code:
        error_dict["status_code"] = status_code

    # Handle specific error types
    if isinstance(e, (httpx.HTTPError, aiohttp.ClientError)):
        error_dict["error_type"] = "network_error"
        error_dict["message"] = f"Network error connecting to model API: {str(e)}"
        error_dict["user_message"] = "Could not connect to the AI model service. Please check your internet connection."

    elif "api key" in error_str or "authentication" in error_str or status_code == 401:
        error_dict["message"] = "Model API authentication failed"
        error_dict["user_message"] = "Authentication with the AI model service failed. Please check your API key."

    elif "rate limit" in error_str or status_code == 429:
        error_dict["message"] = "Model API rate limit exceeded"
        error_dict["user_message"] = "AI model rate limit exceeded. Please try again later."

    elif "context length" in error_str or "too long" in error_str:
        error_dict["message"] = "Input too long for model context window"
        error_dict["user_message"] = "Your input is too long for the AI model to process. Please try a shorter input."

    elif "content policy" in error_str or "moderation" in error_str:
        error_dict["message"] = "Content policy violation"
        error_dict["user_message"] = "Your request was flagged by the AI model's content policy. Please modify your input."

    elif status_code == 500:
        error_dict["message"] = "Model API server error"
        error_dict["user_message"] = "The AI model service encountered an internal error. Please try again later."

    else:
        # Generic error handling
        error_dict["message"] = f"Model error: {str(e)}"
        error_dict["user_message"] = f"An error occurred while communicating with the AI model: {str(e)}"

    # Add detailed error info for debugging
    error_dict["detailed_error"] = str(e)

    # Log the error
    logger.error(f"Model error in {operation}",
                 error_type=error_dict["error_type"],
                 status_code=status_code,
                 message=error_dict["message"],
                 model=model,
                 detailed_error=str(e))

    # Log to error monitoring system if available
    if ERROR_MONITORING_AVAILABLE:
        from_integration_error(
            error_dict=error_dict,
            source="model",
            operation=operation,
            context={
                "original_exception": str(e),
                "model": model
            }
        )

    return error_dict


def with_model_error_handling(operation: str) -> Callable:
    """
    Decorator for handling model errors

    Args:
        operation: The operation being performed

    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                # Extract model name from args or kwargs
                model = "unknown"
                if len(args) > 1 and isinstance(args[1], str):
                    model = args[1]  # Assuming model name is the second argument
                elif "model_name" in kwargs:
                    model = kwargs["model_name"]

                return await func(*args, **kwargs)
            except Exception as e:
                return handle_model_error(e, operation, model)

        def sync_wrapper(*args, **kwargs):
            try:
                # Extract model name from args or kwargs
                model = "unknown"
                if len(args) > 1 and isinstance(args[1], str):
                    model = args[1]  # Assuming model name is the second argument
                elif "model_name" in kwargs:
                    model = kwargs["model_name"]

                return func(*args, **kwargs)
            except Exception as e:
                return handle_model_error(e, operation, model)

        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def format_user_friendly_error(error_dict: Dict[str, Any]) -> str:
    """
    Format a user-friendly error message from an error dictionary

    Args:
        error_dict: The error dictionary

    Returns:
        A user-friendly error message
    """
    if "user_message" in error_dict:
        return error_dict["user_message"]

    if "message" in error_dict:
        return f"Error: {error_dict['message']}"

    return "An unknown error occurred with the AI model. Please try again later."


def is_retryable_error(error_dict: Dict[str, Any]) -> bool:
    """
    Determine if an error is retryable

    Args:
        error_dict: The error dictionary

    Returns:
        True if the error is retryable, False otherwise
    """
    # Network errors are generally retryable
    if error_dict.get("error_type") == "network_error":
        return True

    # Rate limit errors are retryable after a delay
    if "rate limit" in error_dict.get("message", "").lower():
        return True

    # Server errors (5xx) are generally retryable
    if error_dict.get("status_code", 0) >= 500:
        return True

    # Specific status codes that might be retryable
    retryable_status_codes = [429, 503, 504]
    if error_dict.get("status_code") in retryable_status_codes:
        return True

    return False


def extract_model_error_details(response: Dict[str, Any]) -> Tuple[str, Dict]:
    """
    Extract error details from a model API response

    Args:
        response: The response dictionary

    Returns:
        Tuple of (error_message, error_details)
    """
    # OpenAI error format
    if "error" in response:
        error_data = response["error"]
        if isinstance(error_data, dict):
            error_message = error_data.get("message", "Unknown model error")
            return error_message, error_data
        else:
            return str(error_data), {"raw_error": error_data}

    # OpenRouter error format
    if "error" in response:
        error_data = response["error"]
        error_message = error_data.get("message", "Unknown model error")
        return error_message, error_data

    # Generic error format
    return "Unknown model API error", {"raw_response": response}
