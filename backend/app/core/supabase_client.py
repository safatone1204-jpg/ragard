"""Supabase client module for authentication and database operations."""
import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Supabase clients (initialized on first use)
_supabase_admin: Optional[Client] = None
_supabase_auth: Optional[Client] = None


def get_supabase_admin() -> Client:
    """
    Get or create the Supabase admin client (uses service role key).
    This client has full access and should only be used server-side.
    """
    global _supabase_admin
    
    if _supabase_admin is not None:
        return _supabase_admin
    
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is not set")
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")
    
    _supabase_admin = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
    
    logger.info("Supabase admin client initialized")
    return _supabase_admin


def get_supabase_auth() -> Client:
    """
    Get or create the Supabase auth client (uses anon key).
    This client is used to validate user access tokens.
    """
    global _supabase_auth
    
    if _supabase_auth is not None:
        return _supabase_auth
    
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is not set")
    if not settings.SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_ANON_KEY environment variable is not set")
    
    _supabase_auth = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )
    
    logger.info("Supabase auth client initialized")
    return _supabase_auth

