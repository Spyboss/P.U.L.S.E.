"""
Security utilities for P.U.L.S.E.
Provides security-related functions and utilities
"""

import os
import re
import hashlib
import hmac
import secrets
import base64
import json
import time
from typing import Dict, Any, Optional, List, Set, Union, Callable, Type, Tuple
import structlog
from datetime import datetime, timedelta

# Logger
logger = structlog.get_logger("security")

# Constants
DEFAULT_KEY_LENGTH = 32  # 256 bits
DEFAULT_HASH_ALGORITHM = "sha256"
API_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{32,}$')
TOKEN_EXPIRY = 3600  # 1 hour in seconds

def generate_secure_token(length: int = DEFAULT_KEY_LENGTH) -> str:
    """
    Generate a cryptographically secure random token
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        Base64-encoded token
    """
    token_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')

def generate_api_key() -> str:
    """
    Generate a secure API key
    
    Returns:
        API key string
    """
    return generate_secure_token(DEFAULT_KEY_LENGTH)

def is_valid_api_key(api_key: str) -> bool:
    """
    Check if an API key has a valid format
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if the API key has a valid format, False otherwise
    """
    if not api_key:
        return False
    
    return bool(API_KEY_PATTERN.match(api_key))

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password with a salt
    
    Args:
        password: Password to hash
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if not salt:
        salt = secrets.token_hex(16)
    
    # Hash the password with the salt
    hash_obj = hashlib.pbkdf2_hmac(
        DEFAULT_HASH_ALGORITHM,
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # Number of iterations
    )
    
    # Convert to hex string
    hashed_password = hash_obj.hex()
    
    return hashed_password, salt

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        password: Password to verify
        hashed_password: Stored hash
        salt: Salt used for hashing
        
    Returns:
        True if the password matches, False otherwise
    """
    # Hash the password with the provided salt
    calculated_hash, _ = hash_password(password, salt)
    
    # Compare the hashes
    return hmac.compare_digest(calculated_hash, hashed_password)

def generate_hmac_signature(data: str, secret_key: str) -> str:
    """
    Generate an HMAC signature for data
    
    Args:
        data: Data to sign
        secret_key: Secret key for signing
        
    Returns:
        Hex-encoded HMAC signature
    """
    # Create HMAC
    signature = hmac.new(
        secret_key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def verify_hmac_signature(data: str, signature: str, secret_key: str) -> bool:
    """
    Verify an HMAC signature
    
    Args:
        data: Data that was signed
        signature: Signature to verify
        secret_key: Secret key used for signing
        
    Returns:
        True if the signature is valid, False otherwise
    """
    # Calculate expected signature
    expected_signature = generate_hmac_signature(data, secret_key)
    
    # Compare signatures using constant-time comparison
    return hmac.compare_digest(signature, expected_signature)

def generate_jwt(payload: Dict[str, Any], secret_key: str, expiry: int = TOKEN_EXPIRY) -> str:
    """
    Generate a simple JWT token
    
    Args:
        payload: Token payload
        secret_key: Secret key for signing
        expiry: Token expiry time in seconds
        
    Returns:
        JWT token
    """
    # Create header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    # Add expiry to payload
    payload = payload.copy()
    payload["exp"] = int(time.time()) + expiry
    
    # Encode header and payload
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    
    # Create signature
    signature_data = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        signature_data.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    # Combine to create JWT
    jwt = f"{header_b64}.{payload_b64}.{signature_b64}"
    
    return jwt

def verify_jwt(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return the payload
    
    Args:
        token: JWT token to verify
        secret_key: Secret key used for signing
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        # Split token
        header_b64, payload_b64, signature_b64 = token.split('.')
        
        # Verify signature
        signature_data = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            logger.warning("JWT signature verification failed")
            return None
        
        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + '=' * (4 - len(payload_b64) % 4))
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiry
        if "exp" in payload and payload["exp"] < int(time.time()):
            logger.warning("JWT token expired")
            return None
        
        return payload
    except Exception as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        return None

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        input_str: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>\'";`]', '', input_str)
    
    return sanitized

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Remove path separators and other dangerous characters
    sanitized = re.sub(r'[\\/:*?"<>|]', '', filename)
    
    # Ensure the filename doesn't start with a dot (hidden file)
    sanitized = sanitized.lstrip('.')
    
    # Ensure the filename isn't empty after sanitization
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized

def sanitize_path(path: str) -> str:
    """
    Sanitize a path to prevent path traversal attacks
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    if not path:
        return ""
    
    # Normalize path
    normalized = os.path.normpath(path)
    
    # Ensure the path doesn't contain parent directory references
    if '..' in normalized.split(os.path.sep):
        logger.warning(f"Attempted path traversal: {path}")
        return ""
    
    return normalized

def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe to redirect to
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is safe, False otherwise
    """
    if not url:
        return False
    
    # Check for javascript: or data: URLs
    if re.match(r'^(javascript|data|vbscript|file):', url, re.IGNORECASE):
        return False
    
    # Check for relative URLs (safe)
    if url.startswith('/') and not url.startswith('//'):
        return True
    
    # Check for absolute URLs (only allow specific domains)
    allowed_domains = [
        'pulse.example.com',
        'api.pulse.example.com',
        'localhost',
        '127.0.0.1'
    ]
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc in allowed_domains
    except Exception:
        return False

def redact_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str]) -> Dict[str, Any]:
    """
    Redact sensitive data from a dictionary
    
    Args:
        data: Dictionary containing data
        sensitive_keys: List of keys to redact
        
    Returns:
        Dictionary with sensitive data redacted
    """
    result = {}
    
    for key, value in data.items():
        if key.lower() in [k.lower() for k in sensitive_keys]:
            # Redact sensitive data
            if isinstance(value, str) and value:
                if len(value) > 8:
                    result[key] = value[:4] + '*' * (len(value) - 8) + value[-4:]
                else:
                    result[key] = '*' * len(value)
            else:
                result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            # Recursively redact nested dictionaries
            result[key] = redact_sensitive_data(value, sensitive_keys)
        elif isinstance(value, list):
            # Recursively redact lists of dictionaries
            result[key] = [
                redact_sensitive_data(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Copy non-sensitive data as is
            result[key] = value
    
    return result

def validate_api_key_format(api_key: str) -> bool:
    """
    Validate the format of an API key
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if the API key has a valid format, False otherwise
    """
    # Check if the API key is not empty
    if not api_key:
        return False
    
    # Check if the API key matches the expected pattern
    return bool(API_KEY_PATTERN.match(api_key))

def secure_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if the strings are equal, False otherwise
    """
    return hmac.compare_digest(a, b)

def generate_nonce() -> str:
    """
    Generate a nonce for use in security protocols
    
    Returns:
        Nonce string
    """
    return secrets.token_hex(16)

def is_valid_json(json_str: str) -> bool:
    """
    Check if a string is valid JSON
    
    Args:
        json_str: JSON string to validate
        
    Returns:
        True if the string is valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False
