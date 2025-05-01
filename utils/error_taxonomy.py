"""
Error Taxonomy for P.U.L.S.E.
Provides a comprehensive classification system for errors
"""

from enum import Enum, auto
from typing import Dict, Any, Optional, List, Set, Union
import structlog

logger = structlog.get_logger("error_taxonomy")

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"

class ErrorCategory(str, Enum):
    """High-level error categories"""
    SYSTEM = "system"           # System-level errors (OS, hardware, etc.)
    NETWORK = "network"         # Network-related errors
    AUTHENTICATION = "auth"     # Authentication and authorization errors
    VALIDATION = "validation"   # Input validation errors
    INTEGRATION = "integration" # External integration errors
    MODEL = "model"             # AI model errors
    DATABASE = "database"       # Database errors
    MEMORY = "memory"           # Memory-related errors
    TIMEOUT = "timeout"         # Timeout errors
    RESOURCE = "resource"       # Resource exhaustion errors
    CONFIGURATION = "config"    # Configuration errors
    LOGIC = "logic"             # Business logic errors
    UNKNOWN = "unknown"         # Unknown or unclassified errors

class ErrorSource(str, Enum):
    """Error sources"""
    GITHUB = "github"           # GitHub API
    NOTION = "notion"           # Notion API
    MONGODB = "mongodb"         # MongoDB
    SQLITE = "sqlite"           # SQLite
    LANCEDB = "lancedb"         # LanceDB
    MISTRAL = "mistral"         # Mistral AI
    OPENROUTER = "openrouter"   # OpenRouter
    OPENAI = "openai"           # OpenAI
    GEMINI = "gemini"           # Google Gemini
    ANTHROPIC = "anthropic"     # Anthropic
    FILESYSTEM = "filesystem"   # File system
    NETWORK = "network"         # Network
    SYSTEM = "system"           # Operating system
    APPLICATION = "application" # Application code
    USER = "user"               # User input
    UNKNOWN = "unknown"         # Unknown source

class ErrorType(str, Enum):
    """Specific error types"""
    # Network errors
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    DNS_ERROR = "dns_error"
    SSL_ERROR = "ssl_error"
    
    # Authentication errors
    INVALID_API_KEY = "invalid_api_key"
    EXPIRED_TOKEN = "expired_token"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Validation errors
    INVALID_INPUT = "invalid_input"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    VALUE_OUT_OF_RANGE = "value_out_of_range"
    
    # Integration errors
    API_ERROR = "api_error"
    SCHEMA_MISMATCH = "schema_mismatch"
    VERSION_MISMATCH = "version_mismatch"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_CONFLICT = "resource_conflict"
    
    # Model errors
    CONTENT_FILTER = "content_filter"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"
    INVALID_MODEL = "invalid_model"
    MODEL_OVERLOADED = "model_overloaded"
    
    # Database errors
    CONNECTION_FAILED = "connection_failed"
    QUERY_ERROR = "query_error"
    TRANSACTION_ERROR = "transaction_error"
    CONSTRAINT_VIOLATION = "constraint_violation"
    DEADLOCK = "deadlock"
    
    # Memory errors
    OUT_OF_MEMORY = "out_of_memory"
    MEMORY_LEAK = "memory_leak"
    
    # Resource errors
    CPU_LIMIT_EXCEEDED = "cpu_limit_exceeded"
    DISK_SPACE_EXHAUSTED = "disk_space_exhausted"
    
    # Configuration errors
    MISSING_CONFIG = "missing_config"
    INVALID_CONFIG = "invalid_config"
    ENV_VAR_MISSING = "env_var_missing"
    
    # Logic errors
    INVALID_STATE = "invalid_state"
    ASSERTION_FAILED = "assertion_failed"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    
    # Unknown errors
    UNKNOWN_ERROR = "unknown_error"

class RetryStrategy(str, Enum):
    """Retry strategies for different error types"""
    NO_RETRY = "no_retry"               # Do not retry
    IMMEDIATE_RETRY = "immediate_retry" # Retry immediately
    LINEAR_BACKOFF = "linear_backoff"   # Retry with linear backoff
    EXPONENTIAL_BACKOFF = "exponential_backoff" # Retry with exponential backoff
    JITTERED_BACKOFF = "jittered_backoff" # Retry with jittered exponential backoff

# Mapping of error types to retry strategies
DEFAULT_RETRY_STRATEGIES: Dict[ErrorType, RetryStrategy] = {
    # Network errors - generally retryable
    ErrorType.CONNECTION_ERROR: RetryStrategy.JITTERED_BACKOFF,
    ErrorType.TIMEOUT_ERROR: RetryStrategy.JITTERED_BACKOFF,
    ErrorType.DNS_ERROR: RetryStrategy.LINEAR_BACKOFF,
    ErrorType.SSL_ERROR: RetryStrategy.LINEAR_BACKOFF,
    
    # Authentication errors - some retryable
    ErrorType.INVALID_API_KEY: RetryStrategy.NO_RETRY,
    ErrorType.EXPIRED_TOKEN: RetryStrategy.IMMEDIATE_RETRY,
    ErrorType.INSUFFICIENT_PERMISSIONS: RetryStrategy.NO_RETRY,
    ErrorType.RATE_LIMIT_EXCEEDED: RetryStrategy.EXPONENTIAL_BACKOFF,
    
    # Validation errors - not retryable
    ErrorType.INVALID_INPUT: RetryStrategy.NO_RETRY,
    ErrorType.MISSING_REQUIRED_FIELD: RetryStrategy.NO_RETRY,
    ErrorType.INVALID_FORMAT: RetryStrategy.NO_RETRY,
    ErrorType.VALUE_OUT_OF_RANGE: RetryStrategy.NO_RETRY,
    
    # Integration errors - some retryable
    ErrorType.API_ERROR: RetryStrategy.JITTERED_BACKOFF,
    ErrorType.SCHEMA_MISMATCH: RetryStrategy.NO_RETRY,
    ErrorType.VERSION_MISMATCH: RetryStrategy.NO_RETRY,
    ErrorType.RESOURCE_NOT_FOUND: RetryStrategy.NO_RETRY,
    ErrorType.RESOURCE_CONFLICT: RetryStrategy.LINEAR_BACKOFF,
    
    # Model errors - some retryable
    ErrorType.CONTENT_FILTER: RetryStrategy.NO_RETRY,
    ErrorType.CONTEXT_LENGTH_EXCEEDED: RetryStrategy.NO_RETRY,
    ErrorType.INVALID_MODEL: RetryStrategy.NO_RETRY,
    ErrorType.MODEL_OVERLOADED: RetryStrategy.EXPONENTIAL_BACKOFF,
    
    # Database errors - some retryable
    ErrorType.CONNECTION_FAILED: RetryStrategy.JITTERED_BACKOFF,
    ErrorType.QUERY_ERROR: RetryStrategy.NO_RETRY,
    ErrorType.TRANSACTION_ERROR: RetryStrategy.LINEAR_BACKOFF,
    ErrorType.CONSTRAINT_VIOLATION: RetryStrategy.NO_RETRY,
    ErrorType.DEADLOCK: RetryStrategy.JITTERED_BACKOFF,
    
    # Memory errors - not retryable
    ErrorType.OUT_OF_MEMORY: RetryStrategy.NO_RETRY,
    ErrorType.MEMORY_LEAK: RetryStrategy.NO_RETRY,
    
    # Resource errors - not retryable
    ErrorType.CPU_LIMIT_EXCEEDED: RetryStrategy.NO_RETRY,
    ErrorType.DISK_SPACE_EXHAUSTED: RetryStrategy.NO_RETRY,
    
    # Configuration errors - not retryable
    ErrorType.MISSING_CONFIG: RetryStrategy.NO_RETRY,
    ErrorType.INVALID_CONFIG: RetryStrategy.NO_RETRY,
    ErrorType.ENV_VAR_MISSING: RetryStrategy.NO_RETRY,
    
    # Logic errors - not retryable
    ErrorType.INVALID_STATE: RetryStrategy.NO_RETRY,
    ErrorType.ASSERTION_FAILED: RetryStrategy.NO_RETRY,
    ErrorType.CIRCULAR_DEPENDENCY: RetryStrategy.NO_RETRY,
    
    # Unknown errors - retry with caution
    ErrorType.UNKNOWN_ERROR: RetryStrategy.LINEAR_BACKOFF,
}

# Mapping of HTTP status codes to error types
HTTP_STATUS_TO_ERROR_TYPE: Dict[int, ErrorType] = {
    400: ErrorType.INVALID_INPUT,
    401: ErrorType.INVALID_API_KEY,
    403: ErrorType.INSUFFICIENT_PERMISSIONS,
    404: ErrorType.RESOURCE_NOT_FOUND,
    409: ErrorType.RESOURCE_CONFLICT,
    422: ErrorType.INVALID_FORMAT,
    429: ErrorType.RATE_LIMIT_EXCEEDED,
    500: ErrorType.API_ERROR,
    502: ErrorType.API_ERROR,
    503: ErrorType.MODEL_OVERLOADED,
    504: ErrorType.TIMEOUT_ERROR,
}

# Mapping of error categories to severity levels
DEFAULT_SEVERITY_LEVELS: Dict[ErrorCategory, ErrorSeverity] = {
    ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,
    ErrorCategory.NETWORK: ErrorSeverity.WARNING,
    ErrorCategory.AUTHENTICATION: ErrorSeverity.ERROR,
    ErrorCategory.VALIDATION: ErrorSeverity.WARNING,
    ErrorCategory.INTEGRATION: ErrorSeverity.ERROR,
    ErrorCategory.MODEL: ErrorSeverity.ERROR,
    ErrorCategory.DATABASE: ErrorSeverity.ERROR,
    ErrorCategory.MEMORY: ErrorSeverity.CRITICAL,
    ErrorCategory.TIMEOUT: ErrorSeverity.WARNING,
    ErrorCategory.RESOURCE: ErrorSeverity.CRITICAL,
    ErrorCategory.CONFIGURATION: ErrorSeverity.ERROR,
    ErrorCategory.LOGIC: ErrorSeverity.ERROR,
    ErrorCategory.UNKNOWN: ErrorSeverity.ERROR,
}

class ErrorInfo:
    """
    Comprehensive error information class
    """
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        error_type: ErrorType,
        source: ErrorSource = ErrorSource.UNKNOWN,
        severity: Optional[ErrorSeverity] = None,
        status_code: Optional[int] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize error information
        
        Args:
            message: Technical error message
            category: Error category
            error_type: Specific error type
            source: Error source
            severity: Error severity level (defaults based on category)
            status_code: HTTP status code if applicable
            operation: Operation being performed when error occurred
            context: Additional context information
            exception: Original exception if available
            retry_strategy: Retry strategy (defaults based on error type)
            user_message: User-friendly error message
        """
        self.message = message
        self.category = category
        self.error_type = error_type
        self.source = source
        self.severity = severity or DEFAULT_SEVERITY_LEVELS.get(category, ErrorSeverity.ERROR)
        self.status_code = status_code
        self.operation = operation
        self.context = context or {}
        self.exception = exception
        self.retry_strategy = retry_strategy or DEFAULT_RETRY_STRATEGIES.get(error_type, RetryStrategy.NO_RETRY)
        self.user_message = user_message or self._generate_user_message()
        self.timestamp = None  # Will be set when error is recorded
        
    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message based on error type"""
        if self.category == ErrorCategory.NETWORK:
            return "A network error occurred. Please check your internet connection and try again."
        elif self.category == ErrorCategory.AUTHENTICATION:
            return "Authentication failed. Please check your credentials and try again."
        elif self.category == ErrorCategory.VALIDATION:
            return "Invalid input provided. Please check your input and try again."
        elif self.category == ErrorCategory.INTEGRATION:
            return f"An error occurred while communicating with {self.source}. Please try again later."
        elif self.category == ErrorCategory.MODEL:
            return "The AI model encountered an error. Please try again with a different query."
        elif self.category == ErrorCategory.DATABASE:
            return "A database error occurred. Please try again later."
        elif self.category == ErrorCategory.MEMORY:
            return "The system is running low on memory. Please try again later."
        elif self.category == ErrorCategory.TIMEOUT:
            return "The operation timed out. Please try again later."
        elif self.category == ErrorCategory.RESOURCE:
            return "The system is running low on resources. Please try again later."
        elif self.category == ErrorCategory.CONFIGURATION:
            return "A configuration error occurred. Please contact support."
        elif self.category == ErrorCategory.LOGIC:
            return "An internal error occurred. Please contact support."
        else:
            return "An unexpected error occurred. Please try again later."
    
    def is_retryable(self) -> bool:
        """Check if the error is retryable"""
        return self.retry_strategy != RetryStrategy.NO_RETRY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and serialization"""
        result = {
            "message": self.message,
            "category": self.category,
            "error_type": self.error_type,
            "source": self.source,
            "severity": self.severity,
            "retry_strategy": self.retry_strategy,
            "user_message": self.user_message,
        }
        
        if self.status_code is not None:
            result["status_code"] = self.status_code
            
        if self.operation is not None:
            result["operation"] = self.operation
            
        if self.context:
            result["context"] = {k: v for k, v in self.context.items() 
                               if isinstance(v, (str, int, float, bool, type(None)))}
            
        if self.exception is not None:
            result["exception"] = str(self.exception)
            
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
            
        return result
    
    def log(self) -> None:
        """Log the error with appropriate severity"""
        log_context = self.to_dict()
        
        if self.severity == ErrorSeverity.DEBUG:
            logger.debug(self.message, **log_context)
        elif self.severity == ErrorSeverity.INFO:
            logger.info(self.message, **log_context)
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(self.message, **log_context)
        elif self.severity == ErrorSeverity.ERROR:
            logger.error(self.message, **log_context)
        elif self.severity == ErrorSeverity.CRITICAL or self.severity == ErrorSeverity.FATAL:
            logger.critical(self.message, **log_context)


def classify_exception(
    exception: Exception,
    operation: Optional[str] = None,
    source: ErrorSource = ErrorSource.UNKNOWN,
    context: Optional[Dict[str, Any]] = None
) -> ErrorInfo:
    """
    Classify an exception into the error taxonomy
    
    Args:
        exception: The exception to classify
        operation: The operation being performed when the exception occurred
        source: The source of the exception
        context: Additional context information
        
    Returns:
        ErrorInfo object with classification
    """
    error_str = str(exception).lower()
    error_type = ErrorType.UNKNOWN_ERROR
    category = ErrorCategory.UNKNOWN
    status_code = None
    
    # Extract status code if available
    if hasattr(exception, 'status_code'):
        status_code = exception.status_code
    elif hasattr(exception, 'status'):
        status_code = exception.status
    elif hasattr(exception, 'code'):
        status_code = exception.code
        
    # Check for network errors
    if any(term in error_str for term in ['connection', 'network', 'socket', 'timeout', 'timed out']):
        category = ErrorCategory.NETWORK
        if 'timeout' in error_str or 'timed out' in error_str:
            error_type = ErrorType.TIMEOUT_ERROR
        elif 'ssl' in error_str:
            error_type = ErrorType.SSL_ERROR
        elif 'dns' in error_str:
            error_type = ErrorType.DNS_ERROR
        else:
            error_type = ErrorType.CONNECTION_ERROR
    
    # Check for authentication errors
    elif any(term in error_str for term in ['authentication', 'auth', 'unauthorized', 'permission', 'api key', 'token']):
        category = ErrorCategory.AUTHENTICATION
        if 'api key' in error_str:
            error_type = ErrorType.INVALID_API_KEY
        elif 'token' in error_str and 'expired' in error_str:
            error_type = ErrorType.EXPIRED_TOKEN
        elif 'permission' in error_str or 'access' in error_str:
            error_type = ErrorType.INSUFFICIENT_PERMISSIONS
        elif 'rate limit' in error_str:
            error_type = ErrorType.RATE_LIMIT_EXCEEDED
    
    # Check for database errors
    elif any(term in error_str for term in ['database', 'db', 'sql', 'query', 'mongodb', 'sqlite']):
        category = ErrorCategory.DATABASE
        if 'connection' in error_str:
            error_type = ErrorType.CONNECTION_FAILED
        elif 'query' in error_str:
            error_type = ErrorType.QUERY_ERROR
        elif 'transaction' in error_str:
            error_type = ErrorType.TRANSACTION_ERROR
        elif 'constraint' in error_str or 'violation' in error_str:
            error_type = ErrorType.CONSTRAINT_VIOLATION
        elif 'deadlock' in error_str:
            error_type = ErrorType.DEADLOCK
    
    # Check for model errors
    elif any(term in error_str for term in ['model', 'ai', 'openai', 'mistral', 'anthropic', 'gemini']):
        category = ErrorCategory.MODEL
        if 'content' in error_str and 'filter' in error_str:
            error_type = ErrorType.CONTENT_FILTER
        elif 'context' in error_str and 'length' in error_str:
            error_type = ErrorType.CONTEXT_LENGTH_EXCEEDED
        elif 'invalid model' in error_str or 'model not found' in error_str:
            error_type = ErrorType.INVALID_MODEL
        elif 'overloaded' in error_str or 'capacity' in error_str:
            error_type = ErrorType.MODEL_OVERLOADED
    
    # Use HTTP status code for classification if available
    if status_code is not None and status_code in HTTP_STATUS_TO_ERROR_TYPE:
        error_type = HTTP_STATUS_TO_ERROR_TYPE[status_code]
        
        # Set category based on status code
        if status_code == 401 or status_code == 403:
            category = ErrorCategory.AUTHENTICATION
        elif status_code == 400 or status_code == 422:
            category = ErrorCategory.VALIDATION
        elif status_code == 404 or status_code == 409:
            category = ErrorCategory.INTEGRATION
        elif status_code == 429:
            category = ErrorCategory.AUTHENTICATION
            error_type = ErrorType.RATE_LIMIT_EXCEEDED
        elif status_code >= 500:
            category = ErrorCategory.INTEGRATION
    
    # Create and return ErrorInfo
    return ErrorInfo(
        message=str(exception),
        category=category,
        error_type=error_type,
        source=source,
        status_code=status_code,
        operation=operation,
        context=context,
        exception=exception
    )


def classify_error_dict(error_dict: Dict[str, Any]) -> ErrorInfo:
    """
    Classify an error dictionary into the error taxonomy
    
    Args:
        error_dict: The error dictionary to classify
        
    Returns:
        ErrorInfo object with classification
    """
    message = error_dict.get('message', 'Unknown error')
    error_type_str = error_dict.get('error_type', 'unknown_error')
    source_str = error_dict.get('source', 'unknown')
    operation = error_dict.get('operation')
    status_code = error_dict.get('status_code')
    context = error_dict.get('context', {})
    user_message = error_dict.get('user_message')
    
    # Try to map to ErrorType enum
    try:
        error_type = ErrorType(error_type_str)
    except ValueError:
        error_type = ErrorType.UNKNOWN_ERROR
    
    # Try to map to ErrorSource enum
    try:
        source = ErrorSource(source_str)
    except ValueError:
        source = ErrorSource.UNKNOWN
    
    # Determine category based on error type
    category = ErrorCategory.UNKNOWN
    for cat in ErrorCategory:
        if cat.value in error_type_str:
            category = cat
            break
    
    # Create and return ErrorInfo
    return ErrorInfo(
        message=message,
        category=category,
        error_type=error_type,
        source=source,
        status_code=status_code,
        operation=operation,
        context=context,
        user_message=user_message
    )
