"""API Key authentication middleware."""

from fastapi import Header, HTTPException, status
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Skip authentication if no API key is configured
    if not settings.api_key:
        logger.debug("api_key_not_configured", message="API authentication disabled")
        return "anonymous"
    
    # Check if API key was provided
    if not x_api_key:
        logger.warning("api_key_missing", message="No API key provided in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Verify API key matches configured value
    if x_api_key != settings.api_key:
        logger.warning(
            "api_key_invalid",
            message="Invalid API key provided",
            provided_key_prefix=x_api_key[:8] if x_api_key else None
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    logger.debug("api_key_verified", message="Valid API key provided")
    return x_api_key
