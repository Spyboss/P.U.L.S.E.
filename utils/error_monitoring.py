"""
Centralized Error Logging and Monitoring System

This module provides a centralized system for logging, monitoring, and analyzing errors
across the application. It includes:
- Structured error logging with context
- Error aggregation and categorization
- Error notification capabilities
- Error analysis utilities
"""

import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
import structlog
from collections import defaultdict

# Configure structlog for consistent logging
logger = structlog.get_logger("error_monitoring")

# Error storage for in-memory aggregation
_error_store = {
    "errors": [],
    "error_counts": defaultdict(int),
    "last_errors": {},
    "error_trends": defaultdict(list)
}

# Maximum number of errors to store in memory
MAX_ERROR_HISTORY = 1000

# Error severity levels
class ErrorSeverity:
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def log_error(
    error: Exception,
    context: Dict[str, Any],
    source: str,
    operation: str,
    severity: str = ErrorSeverity.ERROR,
    user_id: Optional[str] = None,
    notify: bool = False
) -> Dict[str, Any]:
    """
    Log an error with context information
    
    Args:
        error: The exception that occurred
        context: Dictionary with contextual information about the error
        source: The source of the error (e.g., "github", "notion", "model")
        operation: The operation being performed when the error occurred
        severity: The severity level of the error
        user_id: Optional user ID associated with the error
        notify: Whether to send a notification for this error
        
    Returns:
        Dictionary with error details
    """
    # Extract error details
    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()
    
    # Create error record
    timestamp = datetime.now().isoformat()
    error_id = f"{source}_{int(time.time())}_{hash(error_message) % 10000}"
    
    error_record = {
        "error_id": error_id,
        "timestamp": timestamp,
        "source": source,
        "operation": operation,
        "error_type": error_type,
        "error_message": error_message,
        "traceback": error_traceback,
        "context": context,
        "severity": severity,
        "user_id": user_id
    }
    
    # Log the error
    log_context = {
        "error_id": error_id,
        "source": source,
        "operation": operation,
        "error_type": error_type,
        "severity": severity
    }
    
    if user_id:
        log_context["user_id"] = user_id
        
    # Add context to log
    for key, value in context.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            log_context[key] = value
    
    # Log with appropriate severity
    if severity == ErrorSeverity.CRITICAL:
        logger.error(f"CRITICAL ERROR: {error_message}", **log_context)
    elif severity == ErrorSeverity.ERROR:
        logger.error(error_message, **log_context)
    elif severity == ErrorSeverity.WARNING:
        logger.warning(error_message, **log_context)
    elif severity == ErrorSeverity.INFO:
        logger.info(error_message, **log_context)
    else:
        logger.debug(error_message, **log_context)
    
    # Store error for aggregation
    _store_error(error_record)
    
    # Send notification if requested
    if notify:
        _send_error_notification(error_record)
    
    return error_record


def _store_error(error_record: Dict[str, Any]) -> None:
    """
    Store an error record for aggregation and analysis
    
    Args:
        error_record: The error record to store
    """
    # Add to error history, maintaining max size
    _error_store["errors"].append(error_record)
    if len(_error_store["errors"]) > MAX_ERROR_HISTORY:
        _error_store["errors"].pop(0)
    
    # Update error counts
    error_key = f"{error_record['source']}:{error_record['error_type']}"
    _error_store["error_counts"][error_key] += 1
    
    # Update last error of this type
    _error_store["last_errors"][error_key] = error_record
    
    # Update error trends (store count by hour)
    hour = datetime.fromisoformat(error_record["timestamp"]).strftime("%Y-%m-%d %H:00:00")
    _error_store["error_trends"][error_key].append(hour)
    
    # Trim trend data to last 24 data points
    if len(_error_store["error_trends"][error_key]) > 24:
        _error_store["error_trends"][error_key] = _error_store["error_trends"][error_key][-24:]


def _send_error_notification(error_record: Dict[str, Any]) -> None:
    """
    Send a notification for a critical error
    
    Args:
        error_record: The error record to send a notification for
    """
    # This is a placeholder for actual notification logic
    # In a real implementation, this would send an email, Slack message, etc.
    logger.info(f"Would send notification for error: {error_record['error_id']}")
    
    # Example implementation for different notification channels:
    # if os.getenv("SLACK_WEBHOOK_URL"):
    #     _send_slack_notification(error_record)
    # if os.getenv("EMAIL_NOTIFICATIONS_ENABLED") == "true":
    #     _send_email_notification(error_record)


def get_error_stats() -> Dict[str, Any]:
    """
    Get statistics about errors
    
    Returns:
        Dictionary with error statistics
    """
    # Count errors by source
    errors_by_source = defaultdict(int)
    for error in _error_store["errors"]:
        errors_by_source[error["source"]] += 1
    
    # Count errors by type
    errors_by_type = defaultdict(int)
    for error in _error_store["errors"]:
        errors_by_type[error["error_type"]] += 1
    
    # Count errors by severity
    errors_by_severity = defaultdict(int)
    for error in _error_store["errors"]:
        errors_by_severity[error["severity"]] += 1
    
    # Get most frequent errors
    sorted_error_counts = sorted(
        _error_store["error_counts"].items(),
        key=lambda x: x[1],
        reverse=True
    )
    most_frequent = [{"key": k, "count": v} for k, v in sorted_error_counts[:10]]
    
    return {
        "total_errors": len(_error_store["errors"]),
        "errors_by_source": dict(errors_by_source),
        "errors_by_type": dict(errors_by_type),
        "errors_by_severity": dict(errors_by_severity),
        "most_frequent_errors": most_frequent
    }


def get_recent_errors(
    limit: int = 10,
    source: Optional[str] = None,
    severity: Optional[str] = None,
    error_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get recent errors, optionally filtered
    
    Args:
        limit: Maximum number of errors to return
        source: Optional filter by source
        severity: Optional filter by severity
        error_type: Optional filter by error type
        
    Returns:
        List of error records
    """
    # Start with all errors
    errors = _error_store["errors"]
    
    # Apply filters
    if source:
        errors = [e for e in errors if e["source"] == source]
    if severity:
        errors = [e for e in errors if e["severity"] == severity]
    if error_type:
        errors = [e for e in errors if e["error_type"] == error_type]
    
    # Sort by timestamp (newest first) and limit
    return sorted(errors, key=lambda x: x["timestamp"], reverse=True)[:limit]


def analyze_error_trends() -> Dict[str, Any]:
    """
    Analyze error trends over time
    
    Returns:
        Dictionary with error trend analysis
    """
    # Count errors by hour
    errors_by_hour = defaultdict(int)
    for error in _error_store["errors"]:
        hour = datetime.fromisoformat(error["timestamp"]).strftime("%Y-%m-%d %H:00:00")
        errors_by_hour[hour] += 1
    
    # Sort by hour
    sorted_hours = sorted(errors_by_hour.items())
    
    # Calculate trend (increasing or decreasing)
    trend = "stable"
    if len(sorted_hours) >= 2:
        first_half = sorted_hours[:len(sorted_hours)//2]
        second_half = sorted_hours[len(sorted_hours)//2:]
        
        first_half_avg = sum(count for _, count in first_half) / len(first_half) if first_half else 0
        second_half_avg = sum(count for _, count in second_half) / len(second_half) if second_half else 0
        
        if second_half_avg > first_half_avg * 1.2:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.8:
            trend = "decreasing"
    
    return {
        "errors_by_hour": dict(sorted_hours),
        "trend": trend,
        "error_type_trends": {
            key: {"count": len(hours), "trend": "increasing" if len(hours) > 3 else "stable"}
            for key, hours in _error_store["error_trends"].items()
        }
    }


def clear_error_store() -> None:
    """
    Clear the error store (mainly for testing)
    """
    _error_store["errors"] = []
    _error_store["error_counts"] = defaultdict(int)
    _error_store["last_errors"] = {}
    _error_store["error_trends"] = defaultdict(list)


def export_errors(filepath: str) -> bool:
    """
    Export errors to a JSON file
    
    Args:
        filepath: Path to export the errors to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w') as f:
            # Convert defaultdicts to regular dicts for JSON serialization
            export_data = {
                "errors": _error_store["errors"],
                "error_counts": dict(_error_store["error_counts"]),
                "last_errors": _error_store["last_errors"],
                "error_trends": {k: list(v) for k, v in _error_store["error_trends"].items()}
            }
            json.dump(export_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error exporting errors: {str(e)}")
        return False


def import_errors(filepath: str) -> bool:
    """
    Import errors from a JSON file
    
    Args:
        filepath: Path to import the errors from
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
            # Convert back to defaultdicts
            _error_store["errors"] = data["errors"]
            _error_store["error_counts"] = defaultdict(int)
            for k, v in data["error_counts"].items():
                _error_store["error_counts"][k] = v
                
            _error_store["last_errors"] = data["last_errors"]
            
            _error_store["error_trends"] = defaultdict(list)
            for k, v in data["error_trends"].items():
                _error_store["error_trends"][k] = v
                
        return True
    except Exception as e:
        logger.error(f"Error importing errors: {str(e)}")
        return False


# Integration with other error handling systems
def from_integration_error(
    error_dict: Dict[str, Any],
    source: str,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an error record from an integration error dictionary
    
    Args:
        error_dict: The error dictionary from an integration
        source: The source of the error
        operation: The operation being performed
        context: Additional context information
        
    Returns:
        Error record
    """
    if context is None:
        context = {}
    
    # Determine severity based on error type and status code
    severity = ErrorSeverity.ERROR
    if error_dict.get("error_type") == "network_error":
        severity = ErrorSeverity.WARNING
    elif error_dict.get("status_code", 0) >= 500:
        severity = ErrorSeverity.CRITICAL
    
    # Create a synthetic exception for logging
    error_message = error_dict.get("message", "Unknown error")
    error = Exception(error_message)
    
    # Add error dict to context
    context["integration_error"] = error_dict
    
    # Log the error
    return log_error(
        error=error,
        context=context,
        source=source,
        operation=operation,
        severity=severity
    )
