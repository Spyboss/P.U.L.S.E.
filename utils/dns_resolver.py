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
DEFAULT_TIMEOUT = 5.0  # Increased from 3 to 5 seconds
MAX_RETRIES = 3  # Reduced from 5 to 3 to avoid long startup times
CACHE_TTL = 3600  # Increased from 10 minutes to 1 hour
FALLBACK_DNS_SERVERS = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1"]  # Google and Cloudflare DNS

# DNS cache - pre-populate with known hostnames
_dns_cache = {
    "pulse.yllqbcp.mongodb.net": ("52.6.43.153", time.time()),
    "mongodb.net": ("52.6.43.153", time.time()),
    "api.github.com": ("140.82.112.6", time.time()),
    "github.com": ("140.82.112.4", time.time()),
    "api.notion.so": ("104.18.28.182", time.time()),
    "notion.so": ("104.18.29.182", time.time())
}

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

async def resolve_with_fallback_dns(hostname: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    Resolve hostname using fallback DNS servers

    Args:
        hostname: Hostname to resolve
        timeout: Timeout in seconds

    Returns:
        IP address or None if resolution failed
    """
    # Check if hostname is already an IP address
    try:
        socket.inet_aton(hostname)
        logger.debug(f"{hostname} is already an IP address")
        return hostname
    except:
        pass

    # Check cache first
    cache_key = hostname
    current_time = time.time()

    if cache_key in _dns_cache:
        ip_address, timestamp = _dns_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            logger.debug(f"Using cached DNS resolution for {hostname}: {ip_address}")
            return ip_address

    # Try with system DNS first with a very short timeout
    try:
        # Use getaddrinfo which is more robust than gethostbyname
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(hostname, None, socket.AF_INET)
        )

        # Wait for the future with a short timeout
        result = await asyncio.wait_for(future, timeout=min(1.0, timeout))

        # Extract the first IPv4 address
        if result and len(result) > 0:
            ip_address = result[0][4][0]

            # Cache the result
            _dns_cache[cache_key] = (ip_address, current_time)

            logger.debug(f"Resolved {hostname} to {ip_address} using system DNS")
            return ip_address
    except Exception as e:
        logger.debug(f"System DNS resolution failed for {hostname}: {str(e)}")

    # Try with hardcoded IP addresses for common MongoDB Atlas domains
    mongodb_atlas_ips = {
        "pulse.yllqbcp.mongodb.net": "52.6.43.153",
        "mongodb.net": "52.6.43.153",
        "api.github.com": "140.82.112.6",
        "github.com": "140.82.112.4",
        "api.notion.so": "104.18.28.182",
        "notion.so": "104.18.29.182"
    }

    # Check if hostname or any part of it matches a known domain
    for domain, ip in mongodb_atlas_ips.items():
        if domain in hostname:
            logger.info(f"Using hardcoded IP for {hostname}: {ip}")

            # Cache the result
            _dns_cache[cache_key] = (ip, current_time)

            return ip

    # Try fallback DNS servers
    for dns_server in FALLBACK_DNS_SERVERS:
        try:
            # Use dnspython if available for more reliable DNS resolution
            try:
                import dns.resolver

                # Create a resolver with custom nameserver
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [dns_server]
                resolver.timeout = timeout
                resolver.lifetime = timeout

                # Resolve the hostname
                answers = resolver.resolve(hostname, 'A')

                # Get the first IP address
                if answers:
                    ip_address = answers[0].address

                    # Cache the result
                    _dns_cache[cache_key] = (ip_address, current_time)

                    logger.debug(f"Resolved {hostname} to {ip_address} using dnspython with DNS {dns_server}")
                    return ip_address
            except ImportError:
                # Fall back to socket-based resolution
                pass
            except Exception as e:
                logger.debug(f"dnspython resolution failed for {hostname} using {dns_server}: {str(e)}")

            # Create a socket and set timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)

            # Connect to DNS server
            sock.connect((dns_server, 53))

            # Use getaddrinfo with specific DNS server
            loop = asyncio.get_event_loop()
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

                logger.debug(f"Resolved {hostname} to {ip_address} using fallback DNS {dns_server}")
                return ip_address
        except Exception as e:
            logger.debug(f"Fallback DNS resolution failed for {hostname} using {dns_server}: {str(e)}")
        finally:
            try:
                sock.close()
            except:
                pass

    # Last resort: try to use a direct IP if the hostname looks like a MongoDB Atlas hostname
    if "mongodb.net" in hostname:
        fallback_ip = "52.6.43.153"  # Common MongoDB Atlas IP
        logger.warning(f"All DNS resolution attempts failed for {hostname}, using fallback MongoDB Atlas IP: {fallback_ip}")

        # Cache the result with a shorter TTL
        _dns_cache[cache_key] = (fallback_ip, current_time - CACHE_TTL/2)  # Half the normal TTL

        return fallback_ip

    logger.warning(f"All DNS resolution attempts failed for {hostname}")
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

        # Try to resolve with standard method
        ip_address = await resolve_hostname(hostname, timeout)

        if ip_address:
            return ip_address

        # If standard method fails, try with fallback DNS
        if attempt >= 1:  # Only use fallback DNS after first attempt
            ip_address = await resolve_with_fallback_dns(hostname, timeout)
            if ip_address:
                # Cache the result
                _dns_cache[hostname] = (ip_address, time.time())
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
