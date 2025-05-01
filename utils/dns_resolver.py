"""
DNS Resolver Utility for P.U.L.S.E.
Provides DNS resolution with proper timeouts and fallbacks
"""

import socket
import asyncio
import structlog
import time
from typing import List, Optional, Tuple, Dict, Any
from functools import lru_cache

# Configure logger
logger = structlog.get_logger("dns_resolver")

# Constants
DEFAULT_TIMEOUT = 5.0  # 5 seconds
MAX_RETRIES = 3
CACHE_TTL = 300  # 5 minutes

# DNS cache
_dns_cache = {}

async def resolve_hostname(hostname: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    Resolve hostname to IP address with timeout
    
    Args:
        hostname: Hostname to resolve
        timeout: Timeout in seconds
        
    Returns:
        IP address or None if resolution failed
    """
    # Check cache first
    cache_key = hostname
    current_time = time.time()
    
    if cache_key in _dns_cache:
        ip_address, timestamp = _dns_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            logger.debug(f"Using cached DNS resolution for {hostname}: {ip_address}")
            return ip_address
    
    # Create a future for the DNS resolution
    loop = asyncio.get_event_loop()
    
    try:
        # Use getaddrinfo which is more robust than gethostbyname
        future = loop.run_in_executor(
            None, 
            lambda: socket.getaddrinfo(hostname, None, socket.AF_INET)
        )
        
        # Wait for the future with timeout
        result = await asyncio.wait_for(future, timeout=timeout)
        
        # Extract the first IPv4 address
        if result and len(result) > 0:
            ip_address = result[0][4][0]
            
            # Cache the result
            _dns_cache[cache_key] = (ip_address, current_time)
            
            logger.debug(f"Resolved {hostname} to {ip_address}")
            return ip_address
        
        return None
    except asyncio.TimeoutError:
        logger.warning(f"DNS resolution timed out for {hostname} after {timeout}s")
        return None
    except socket.gaierror as e:
        logger.warning(f"DNS resolution failed for {hostname}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error resolving {hostname}: {str(e)}")
        return None

async def resolve_with_retry(hostname: str, max_retries: int = MAX_RETRIES) -> Optional[str]:
    """
    Resolve hostname with retry
    
    Args:
        hostname: Hostname to resolve
        max_retries: Maximum number of retries
        
    Returns:
        IP address or None if resolution failed
    """
    for attempt in range(max_retries):
        # Increase timeout with each retry
        timeout = DEFAULT_TIMEOUT * (attempt + 1)
        
        # Try to resolve
        ip_address = await resolve_hostname(hostname, timeout)
        
        if ip_address:
            return ip_address
        
        # If this is not the last attempt, wait before retrying
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.info(f"Retrying DNS resolution for {hostname} in {wait_time}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
    
    logger.error(f"DNS resolution failed for {hostname} after {max_retries} attempts")
    return None

@lru_cache(maxsize=100)
def get_hostname_from_uri(uri: str) -> Optional[str]:
    """
    Extract hostname from URI
    
    Args:
        uri: URI to extract hostname from
        
    Returns:
        Hostname or None if extraction failed
    """
    try:
        # Handle mongodb+srv:// URIs
        if uri.startswith("mongodb+srv://"):
            # Extract the hostname part
            parts = uri.split("@")
            if len(parts) > 1:
                hostname_part = parts[1].split("/")[0]
                return hostname_part
        
        # Handle other URIs
        import urllib.parse
        parsed = urllib.parse.urlparse(uri)
        return parsed.hostname
    except Exception as e:
        logger.error(f"Failed to extract hostname from URI: {str(e)}")
        return None

async def check_mongodb_dns(mongodb_uri: str) -> Dict[str, Any]:
    """
    Check MongoDB DNS resolution
    
    Args:
        mongodb_uri: MongoDB URI
        
    Returns:
        Dictionary with status and details
    """
    hostname = get_hostname_from_uri(mongodb_uri)
    
    if not hostname:
        return {
            "status": "error",
            "message": "Failed to extract hostname from MongoDB URI",
            "resolvable": False
        }
    
    ip_address = await resolve_with_retry(hostname)
    
    if ip_address:
        return {
            "status": "success",
            "hostname": hostname,
            "ip_address": ip_address,
            "resolvable": True
        }
    else:
        return {
            "status": "error",
            "hostname": hostname,
            "message": f"Failed to resolve {hostname}",
            "resolvable": False
        }
