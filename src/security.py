"""
Security utilities for MCP PowerShell Exec Server.

This module provides security features for the server:
- API key authentication
- PowerShell command security checking
- Rate limiting
"""

import re
import secrets
import time
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS

# Import config without creating circular dependency
import config as config_module
from logging_setup import get_logger

# Initialize logger
logger = get_logger("mcp.security")

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Simple in-memory rate limiting storage
# Maps IP address to list of timestamp requests
_rate_limit_storage: Dict[str, List[float]] = {}


def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Verify if the provided API key is valid.

    Args:
        api_key: API key from the request header

    Returns:
        The verified API key

    Raises:
        HTTPException: If the API key is invalid or missing
    """
    config = config_module.get_config()

    # Skip verification if authentication is disabled
    if not config.security.require_api_key:
        return "api_key_not_required"

    # Check if API key is provided
    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    # Check if API key is valid
    if api_key not in config.security.api_keys:
        logger.warning(f"Invalid API key: {api_key[:5]}...")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key


def check_security(code: str) -> Tuple[bool, str]:
    """
    Check if the PowerShell code contains potentially dangerous commands.

    Args:
        code: The PowerShell code to check

    Returns:
        Tuple of (is_safe, message)
    """
    config = config_module.get_config()

    # Check against configured dangerous patterns
    for pattern in config.security.dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            logger.warning(f"Potentially dangerous command pattern detected: {pattern}")
            return (False, f"Potentially dangerous command pattern detected: {pattern}")

    return (True, "")


def rate_limit(request: Request, limit: int = 60, window: int = 60) -> None:
    """
    Implement rate limiting for API requests.

    Args:
        request: FastAPI request object
        limit: Maximum number of requests allowed in the time window
        window: Time window in seconds

    Raises:
        HTTPException: If rate limit is exceeded
    """
    client_ip = request.client.host if request.client else "unknown"

    # Get current time
    current_time = time.time()

    # Initialize or update request history for this client
    if client_ip not in _rate_limit_storage:
        _rate_limit_storage[client_ip] = []

    # Remove timestamps that are outside the window
    _rate_limit_storage[client_ip] = [
        ts for ts in _rate_limit_storage[client_ip] if current_time - ts < window
    ]

    # Check if limit is exceeded
    if len(_rate_limit_storage[client_ip]) >= limit:
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
        )

    # Add current request timestamp
    _rate_limit_storage[client_ip].append(current_time)


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        A secure random API key string
    """
    return secrets.token_urlsafe(32)
