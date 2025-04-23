"""
Integration Error Handler Module
Provides standardized error handling for external API integrations
"""

import re
import json
import structlog
import traceback
from typing import Dict, Any, Optional, Tuple, Callable
import requests
from requests.exceptions import RequestException

# Import error monitoring (with conditional import to avoid circular imports)
try:
    from utils.error_monitoring import from_integration_error, ErrorSeverity
    ERROR_MONITORING_AVAILABLE = True
except ImportError:
    ERROR_MONITORING_AVAILABLE = False

logger = structlog.get_logger("integration_error_handler")

class IntegrationError(Exception):
    """Base exception for integration errors"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response: Optional[Dict] = None, original_exception: Optional[Exception] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.original_exception = original_exception
        super().__init__(self.message)


class GitHubError(IntegrationError):
    """Exception for GitHub API errors"""
    pass


class NotionError(IntegrationError):
    """Exception for Notion API errors"""
    pass


def handle_github_error(e: Exception, operation: str) -> Dict[str, Any]:
    """
    Handle GitHub API errors and return a standardized error response

    Args:
        e: The exception that occurred
        operation: The operation being performed (e.g., "get_repo_info")

    Returns:
        A standardized error response dictionary
    """
    error_str = str(e).lower()
    error_dict = {
        "success": False,
        "error_type": "github_error",
        "operation": operation
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
    if isinstance(e, RequestException):
        error_dict["error_type"] = "network_error"
        error_dict["message"] = f"Network error connecting to GitHub: {str(e)}"
        error_dict["user_message"] = "Could not connect to GitHub. Please check your internet connection."

    elif status_code == 401:
        error_dict["message"] = "GitHub authentication failed"
        error_dict["user_message"] = "GitHub authentication failed. Please check your GitHub token."

    elif status_code == 403:
        error_dict["message"] = "GitHub permission denied"
        if "rate limit" in error_str:
            error_dict["user_message"] = "GitHub API rate limit exceeded. Please try again later."
        else:
            error_dict["user_message"] = "You don't have permission to access this GitHub resource."

    elif status_code == 404:
        error_dict["message"] = "GitHub resource not found"
        if "repository" in error_str:
            error_dict["user_message"] = "Repository not found. Please check the repository name."
        elif "file" in error_str:
            error_dict["user_message"] = "File not found in the repository. Please check the file path."
        else:
            error_dict["user_message"] = "The requested GitHub resource was not found."

    elif status_code == 422:
        error_dict["message"] = "GitHub validation failed"
        if "already exists" in error_str:
            error_dict["user_message"] = "A resource with this name already exists."
        else:
            error_dict["user_message"] = "The request was invalid. Please check your input."

    else:
        # Generic error handling
        error_dict["message"] = f"GitHub error: {str(e)}"
        error_dict["user_message"] = f"An error occurred while communicating with GitHub: {str(e)}"

    # Add detailed error info for debugging
    error_dict["detailed_error"] = str(e)

    # Log the error
    logger.error(f"GitHub error in {operation}",
                 error_type=error_dict["error_type"],
                 status_code=status_code,
                 message=error_dict["message"],
                 detailed_error=str(e))

    # Log to error monitoring system if available
    if ERROR_MONITORING_AVAILABLE:
        from_integration_error(
            error_dict=error_dict,
            source="github",
            operation=operation,
            context={"original_exception": str(e)}
        )

    return error_dict


def handle_notion_error(e: Exception, operation: str) -> Dict[str, Any]:
    """
    Handle Notion API errors and return a standardized error response

    Args:
        e: The exception that occurred
        operation: The operation being performed (e.g., "create_page")

    Returns:
        A standardized error response dictionary
    """
    error_str = str(e).lower()
    error_dict = {
        "success": False,
        "error_type": "notion_error",
        "operation": operation
    }

    # Extract status code if available
    status_code = None
    if hasattr(e, 'status_code'):
        status_code = e.status_code

    # Add status code to error dict if available
    if status_code:
        error_dict["status_code"] = status_code

    # Handle specific error types
    if isinstance(e, RequestException):
        error_dict["error_type"] = "network_error"
        error_dict["message"] = f"Network error connecting to Notion: {str(e)}"
        error_dict["user_message"] = "Could not connect to Notion. Please check your internet connection."

    elif "not configured" in error_str or "api key" in error_str:
        error_dict["message"] = "Notion API not configured"
        error_dict["user_message"] = "Notion API is not configured. Please set the NOTION_API_KEY environment variable in your .env file."

    elif status_code == 401:
        error_dict["message"] = "Notion authentication failed"
        error_dict["user_message"] = "Notion authentication failed. Please check your Notion API key."

    elif status_code == 403:
        error_dict["message"] = "Notion permission denied"
        error_dict["user_message"] = "You don't have permission to access this Notion resource."

    elif status_code == 404:
        error_dict["message"] = "Notion resource not found"
        if "database" in error_str:
            error_dict["user_message"] = "Notion database not found. Please check the database ID."
        elif "page" in error_str:
            error_dict["user_message"] = "Notion page not found. Please check the page ID."
        else:
            error_dict["user_message"] = "The requested Notion resource was not found."

    elif status_code == 400:
        error_dict["message"] = "Notion validation failed"
        error_dict["user_message"] = "The request to Notion was invalid. Please check your input."

    else:
        # Generic error handling
        error_dict["message"] = f"Notion error: {str(e)}"
        error_dict["user_message"] = f"An error occurred while communicating with Notion: {str(e)}"

    # Add detailed error info for debugging
    error_dict["detailed_error"] = str(e)

    # Log the error
    logger.error(f"Notion error in {operation}",
                 error_type=error_dict["error_type"],
                 status_code=status_code,
                 message=error_dict["message"],
                 detailed_error=str(e))

    # Log to error monitoring system if available
    if ERROR_MONITORING_AVAILABLE:
        from_integration_error(
            error_dict=error_dict,
            source="notion",
            operation=operation,
            context={"original_exception": str(e)}
        )

    return error_dict


def with_error_handling(integration_type: str, operation: str) -> Callable:
    """
    Decorator for handling integration errors

    Args:
        integration_type: The type of integration ("github" or "notion")
        operation: The operation being performed

    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if integration_type.lower() == "github":
                    return handle_github_error(e, operation)
                elif integration_type.lower() == "notion":
                    return handle_notion_error(e, operation)
                else:
                    # Generic error handling
                    logger.error(f"Error in {integration_type} integration during {operation}: {str(e)}")
                    return {
                        "success": False,
                        "error_type": "integration_error",
                        "message": f"Error in {operation}: {str(e)}",
                        "user_message": f"An error occurred: {str(e)}",
                        "detailed_error": str(e)
                    }

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if integration_type.lower() == "github":
                    return handle_github_error(e, operation)
                elif integration_type.lower() == "notion":
                    return handle_notion_error(e, operation)
                else:
                    # Generic error handling
                    logger.error(f"Error in {integration_type} integration during {operation}: {str(e)}")
                    return {
                        "success": False,
                        "error_type": "integration_error",
                        "message": f"Error in {operation}: {str(e)}",
                        "user_message": f"An error occurred: {str(e)}",
                        "detailed_error": str(e)
                    }

        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def extract_error_details(response: requests.Response) -> Tuple[str, Dict]:
    """
    Extract error details from a response

    Args:
        response: The response object

    Returns:
        Tuple of (error_message, error_details)
    """
    try:
        error_data = response.json()

        # GitHub error format
        if "message" in error_data:
            error_message = error_data["message"]
            return error_message, error_data

        # Notion error format
        if "object" in error_data and error_data["object"] == "error":
            error_message = error_data.get("message", "Unknown Notion error")
            return error_message, error_data

        # Generic error format
        return "Unknown API error", error_data

    except (json.JSONDecodeError, ValueError):
        # If response is not JSON
        return response.text, {"raw_text": response.text}


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

    return "An unknown error occurred. Please try again later."


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
