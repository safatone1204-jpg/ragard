"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel

from app.core.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/api", tags=["auth"])

# Create optional auth dependency (doesn't raise on failure)
async def get_current_user_optional(request: Request) -> AuthenticatedUser | None:
    """Get current user if authenticated, return None if not."""
    try:
        return await get_current_user(request)
    except HTTPException as e:
        # Silently handle expired/invalid tokens - this is expected for optional auth
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        # Re-raise other HTTP exceptions
        raise
    except Exception:
        # Catch any other exceptions and return None
        return None


class UserResponse(BaseModel):
    """Response model for user information."""
    id: str
    email: str | None
    firstName: str | None = None
    lastName: str | None = None
    createdAt: str | None = None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get information about the currently authenticated user.
    
    Returns:
        UserResponse with user id and email
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        firstName=getattr(current_user, 'first_name', None),
        lastName=getattr(current_user, 'last_name', None),
        createdAt=getattr(current_user, 'created_at', None)
    )


class AuthStatusResponse(BaseModel):
    """Response model for auth status check."""
    isAuthenticated: bool
    userId: str | None = None
    username: str | None = None
    email: str | None = None


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status(request: Request):
    """
    Check if the user is authenticated and return basic user info.
    Works with extension CORS requests (credentials included).
    Does NOT require authentication - returns isAuthenticated: false if not logged in.
    """
    current_user = await get_current_user_optional(request)
    if current_user:
        return AuthStatusResponse(
            isAuthenticated=True,
            userId=current_user.id,
            username=getattr(current_user, 'first_name', None) or current_user.email,
            email=current_user.email
        )
    return AuthStatusResponse(isAuthenticated=False)

