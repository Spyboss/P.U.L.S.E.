# Error Handling System

This document describes the error handling system implemented in P.U.L.S.E. (Prime Uminda's Learning System Engine).

## Overview

The error handling system provides a standardized way to handle errors across different parts of the application. It includes:

1. **Standardized Error Responses**: Consistent error response format across all components
2. **Error Monitoring**: Centralized error logging, aggregation, and analysis
3. **User-Friendly Error Messages**: Clear, actionable error messages for users
4. **Retry Logic**: Automatic retry for transient errors
5. **Error Categorization**: Classification of errors by type, source, and severity

## Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error_type": "error_category",
  "message": "Technical error message for logging",
  "user_message": "User-friendly error message",
  "status_code": 404, // Optional HTTP status code
  "detailed_error": "Detailed technical information",
  "operation": "operation_being_performed",
  "timestamp": "2023-04-15T12:34:56"
}
```

## Error Handlers

### Integration Error Handler

Located in `utils/integration_error_handler.py`, this module handles errors from external API integrations:

- GitHub API errors
- Notion API errors
- Other third-party service errors

It provides:

- Error classification
- Standardized error responses
- Retry logic for transient errors
- User-friendly error messages

### Model Error Handler

Located in `utils/model_error_handler.py`, this module handles errors from AI model interactions:

- Authentication errors
- Rate limit errors
- Context length errors
- Content policy violations
- Network errors

It provides:

- Error classification by model type
- Standardized error responses
- Retry logic for transient errors
- User-friendly error messages
- Decorator for easy application to model interface methods

## Error Monitoring System

Located in `utils/error_monitoring.py`, this system provides:

- Centralized error logging
- Error aggregation and categorization
- Error trend analysis
- Notification capabilities for critical errors
- Export/import functionality for error logs

## Usage Examples

### Using the Integration Error Handler

```python
from utils.integration_error_handler import handle_github_error

try:
    # GitHub API call
    response = github_client.get_repository(repo_name)
    return process_response(response)
except Exception as e:
    error_dict = handle_github_error(e, "get_repository_info")
    return error_dict
```

### Using the Model Error Handler

```python
from utils.model_error_handler import with_model_error_handling

@with_model_error_handling("generate_text")
async def call_model_api(self, model_name, prompt, temperature=0.7):
    # Model API call
    response = await model_client.generate(prompt, temperature)
    return process_response(response)
```

### Using the Error Monitoring System

```python
from utils.error_monitoring import log_error, ErrorSeverity

try:
    # Some operation
    result = perform_operation()
    return result
except Exception as e:
    error_record = log_error(
        error=e,
        context={"operation_params": params},
        source="module_name",
        operation="operation_name",
        severity=ErrorSeverity.ERROR
    )
    return {"success": False, "error": str(e), "error_id": error_record["error_id"]}
```

## Error Severity Levels

The system uses the following severity levels:

- **DEBUG**: Minor issues that don't affect functionality
- **INFO**: Informational messages about potential issues
- **WARNING**: Issues that might affect functionality but don't cause failure
- **ERROR**: Issues that cause a specific operation to fail
- **CRITICAL**: Severe issues that might affect system stability

## Retryable Errors

The system automatically identifies and retries the following types of errors:

- Network connectivity issues
- Rate limiting errors
- Temporary service unavailability (HTTP 503)
- Gateway timeouts (HTTP 504)
- Other transient errors

## Error Notification

Critical errors can trigger notifications through:

- Console logging
- Log files
- (Future) Email notifications
- (Future) Slack/Discord webhooks

## Testing

Unit tests for the error handling system are located in:

- `tests/utils/test_integration_error_handler.py`
- `tests/utils/test_model_error_handler.py`
- `tests/utils/test_error_monitoring.py`
