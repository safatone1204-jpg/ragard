"""Authentication middleware and helpers for Supabase."""
import logging
from typing import Optional
from fastapi import HTTPException, Request, status
from supabase import Client

from app.core.supabase_client import get_supabase_auth

# Import Supabase auth errors
try:
    from supabase_auth.errors import AuthApiError
except ImportError:
    # Fallback if import fails
    AuthApiError = Exception

logger = logging.getLogger(__name__)


class AuthenticatedUser:
    """Represents an authenticated user from Supabase."""
    def __init__(self, user_id: str, email: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None, created_at: Optional[str] = None):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = created_at


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    Extract and validate the Bearer token from the Authorization header.
    Returns the authenticated user or raises HTTPException.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AuthenticatedUser object with user id and email
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth token"
        )
    
    # Parse Bearer token
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )
    
    token = parts[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth token"
        )
    
    # Validate token with Supabase
    try:
        supabase_auth = get_supabase_auth()
        logger.debug(f"Validating token (length: {len(token)})")
        
        try:
            response = supabase_auth.auth.get_user(token)
        except AuthApiError as supabase_error:
            # Handle expired/invalid tokens gracefully
            error_msg = str(supabase_error)
            if "expired" in error_msg.lower() or "invalid" in error_msg.lower():
                logger.debug(f"Token expired or invalid: {error_msg}")
            else:
                logger.warning(f"Supabase auth error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid. Please log in again."
            )
        except Exception as supabase_error:
            logger.warning(f"Unexpected auth error: {supabase_error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
        
        if not response:
            logger.error("Supabase returned None response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid response from auth service"
            )
        
        if not hasattr(response, 'user') or not response.user:
            logger.warning("Supabase returned no user in response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user = response.user
        user_metadata = getattr(user, 'user_metadata', {}) or {}
        first_name = user_metadata.get('first_name') if isinstance(user_metadata, dict) else None
        last_name = user_metadata.get('last_name') if isinstance(user_metadata, dict) else None
        
        # Convert created_at datetime to ISO string
        created_at_raw = getattr(user, 'created_at', None)
        created_at = None
        if created_at_raw:
            try:
                # If it's a datetime object, convert to ISO string
                if hasattr(created_at_raw, 'isoformat'):
                    created_at = created_at_raw.isoformat()
                else:
                    created_at = str(created_at_raw)
            except Exception as e:
                logger.warning(f"Could not parse created_at: {e}")
                created_at = None
        
        logger.info(f"Successfully authenticated user: {user.id} ({user.email})")
        return AuthenticatedUser(
            user_id=user.id,
            email=user.email,
            first_name=first_name,
            last_name=last_name,
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating auth token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}"
        )

