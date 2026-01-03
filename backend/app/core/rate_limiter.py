"""Rate limiter utility for endpoints."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

def get_rate_limit():
    """Get rate limit string based on environment."""
    if settings.ENVIRONMENT == "production":
        return "100/minute"  # 100 requests per minute in production
    else:
        return "1000/minute"  # Very permissive in development

