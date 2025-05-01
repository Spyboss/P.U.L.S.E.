"""
Direct Connection Utility for P.U.L.S.E.
Provides direct connection capabilities when DNS resolution fails
"""

import os
import structlog
from typing import Dict, Optional, Any
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logger
logger = structlog.get_logger("direct_connection")

# Hardcoded IP addresses for common services
HARDCODED_IPS = {
    "mongodb": {
        "pulse.yllqbcp.mongodb.net": "52.6.43.153",
        "mongodb.net": "52.6.43.153"
    },
    "github": {
        "api.github.com": "140.82.112.6",
        "github.com": "140.82.112.4"
    },
    "notion": {
        "api.notion.so": "104.18.28.182",
        "notion.so": "104.18.29.182"
    }
}

def get_mongodb_direct_connection(mongodb_uri: str) -> Optional[AsyncIOMotorClient]:
    """
    Create a direct MongoDB connection using hardcoded IP addresses

    Args:
        mongodb_uri: MongoDB connection string

    Returns:
        MongoDB client or None if connection failed
    """
    try:
        # Check if this is already a direct connection
        if "directConnection=true" in mongodb_uri and "@" in mongodb_uri:
            # Already a direct connection, use as is
            logger.info("Using existing direct connection string")
            direct_uri = mongodb_uri
        else:
            # Parse the connection string
            parsed_uri = urlparse(mongodb_uri)

            # Extract hostname
            hostname = parsed_uri.netloc.split('@')[-1].split('/')[0].split(':')[0]

            # Extract username and password
            auth_part = parsed_uri.netloc.split('@')[0]
            username = auth_part.split(':')[0]
            password = auth_part.split(':')[1] if ':' in auth_part else ''

            # Find IP address for the hostname
            ip_address = None
            for domain, ip in HARDCODED_IPS["mongodb"].items():
                if domain in hostname:
                    ip_address = ip
                    break

            if not ip_address:
                logger.warning(f"No hardcoded IP found for {hostname}")
                return None

            # Create a direct connection string
            direct_uri = f"mongodb://{username}:{password}@{ip_address}:27017/?retryWrites=true&w=majority&directConnection=true&tlsAllowInvalidCertificates=true"

        # Create MongoDB client with direct connection
        client = AsyncIOMotorClient(
            direct_uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=15000,
            maxIdleTimeMS=60000,
            retryWrites=True,
            retryReads=True,
            waitQueueTimeoutMS=10000,
            appName="P.U.L.S.E.",
            directConnection=True,
            tlsAllowInvalidCertificates=True,
            maxPoolSize=10,
            minPoolSize=1,
            maxConnecting=2,
            heartbeatFrequencyMS=10000
        )

        logger.info(f"Created direct MongoDB connection to {ip_address}")
        return client
    except Exception as e:
        logger.error(f"Failed to create direct MongoDB connection: {str(e)}")
        return None

def get_direct_url(url: str, service_type: str) -> Optional[str]:
    """
    Get direct URL using hardcoded IP address

    Args:
        url: Original URL
        service_type: Service type (github, notion)

    Returns:
        Direct URL or None if conversion failed
    """
    try:
        # Parse the URL
        parsed_url = urlparse(url)

        # Extract hostname
        hostname = parsed_url.netloc

        # Find IP address for the hostname
        ip_address = None
        if service_type in HARDCODED_IPS:
            for domain, ip in HARDCODED_IPS[service_type].items():
                if domain in hostname:
                    ip_address = ip
                    break

        if not ip_address:
            logger.warning(f"No hardcoded IP found for {hostname}")
            return None

        # Create direct URL
        direct_url = url.replace(hostname, ip_address)

        logger.info(f"Created direct URL: {url} -> {direct_url}")
        return direct_url
    except Exception as e:
        logger.error(f"Failed to create direct URL: {str(e)}")
        return None
