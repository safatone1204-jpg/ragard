"""Watchlists API endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
from uuid import UUID

from app.core.auth import get_current_user, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.core.rate_limiter import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["watchlists"])


# Request/Response models
class WatchlistCreate(BaseModel):
    """Request model for creating a watchlist."""
    name: str


class WatchlistUpdate(BaseModel):
    """Request model for updating a watchlist."""
    name: str


class WatchlistItemCreate(BaseModel):
    """Request model for adding an item to a watchlist."""
    ticker: str


class WatchlistResponse(BaseModel):
    """Response model for a watchlist."""
    id: str
    user_id: str
    name: str
    created_at: str


class WatchlistItemResponse(BaseModel):
    """Response model for a watchlist item."""
    id: str
    watchlist_id: str
    ticker: str
    created_at: str


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool


@router.get("/watchlists", response_model=List[WatchlistResponse])
@limiter.limit(get_rate_limit())
async def get_watchlists(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all watchlists for the current user.
    
    Returns:
        List of watchlists ordered by created_at ASC
    """
    try:
        supabase = get_supabase_admin()
        
        response = supabase.table("watchlists")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=False)\
            .execute()
        
        return [WatchlistResponse(**item) for item in response.data]
        
    except Exception as e:
        logger.error(f"Error fetching watchlists for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/watchlists", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit())
async def create_watchlist(
    request: Request,
    watchlist_data: WatchlistCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a new watchlist for the current user.
    
    Args:
        watchlist_data: Watchlist name
        
    Returns:
        Created watchlist
    """
    # Validate name
    if not watchlist_data.name or not watchlist_data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watchlist name cannot be empty"
        )
    
    try:
        supabase = get_supabase_admin()
        
        response = supabase.table("watchlists")\
            .insert({
                "user_id": current_user.id,
                "name": watchlist_data.name.strip()
            })\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create watchlist"
            )
        
        return WatchlistResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating watchlist for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/watchlists/{watchlist_id}", response_model=SuccessResponse)
@limiter.limit(get_rate_limit())
async def delete_watchlist(
    request: Request,
    watchlist_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete a watchlist (and all its items via CASCADE).
    
    Args:
        watchlist_id: UUID of the watchlist to delete
        
    Returns:
        Success response
    """
    try:
        supabase = get_supabase_admin()
        
        # Verify ownership and delete
        response = supabase.table("watchlists")\
            .delete()\
            .eq("id", watchlist_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist not found"
            )
        
        return SuccessResponse(success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting watchlist {watchlist_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/watchlists/{watchlist_id}", response_model=WatchlistResponse)
@limiter.limit(get_rate_limit())
async def update_watchlist(
    request: Request,
    watchlist_id: str,
    watchlist_data: WatchlistUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Update a watchlist name.
    
    Args:
        watchlist_id: UUID of the watchlist
        watchlist_data: New watchlist name
        
    Returns:
        Updated watchlist
    """
    # Validate name
    if not watchlist_data.name or not watchlist_data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watchlist name cannot be empty"
        )
    
    try:
        supabase = get_supabase_admin()
        
        # Verify ownership and update
        response = supabase.table("watchlists")\
            .update({"name": watchlist_data.name.strip()})\
            .eq("id", watchlist_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist not found"
            )
        
        return WatchlistResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating watchlist {watchlist_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _validate_ticker(ticker: str) -> str:
    """Validate and normalize ticker symbol."""
    if not ticker or not ticker.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker cannot be empty"
        )
    
    normalized = ticker.strip().upper()
    
    # Basic validation: 1-10 characters, alphanumeric only
    if len(normalized) < 1 or len(normalized) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker must be between 1 and 10 characters"
        )
    
    if not normalized.replace('.', '').replace('-', '').isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker contains invalid characters"
        )
    
    return normalized


@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit())
async def add_watchlist_item(
    request: Request,
    watchlist_id: str,
    item_data: WatchlistItemCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Add a ticker to a watchlist.
    
    Args:
        watchlist_id: UUID of the watchlist
        item_data: Ticker to add
        
    Returns:
        Created watchlist item
    """
    # Validate and normalize ticker
    normalized_ticker = _validate_ticker(item_data.ticker)
    
    try:
        supabase = get_supabase_admin()
        
        # Verify watchlist exists and belongs to user
        watchlist_response = supabase.table("watchlists")\
            .select("id")\
            .eq("id", watchlist_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist not found"
            )
        
        # Check if ticker already exists in this watchlist
        existing_item = supabase.table("watchlist_items")\
            .select("id, ticker")\
            .eq("watchlist_id", watchlist_id)\
            .eq("ticker", normalized_ticker)\
            .execute()
        
        if existing_item.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ticker {normalized_ticker} is already in this watchlist"
            )
        
        # Insert item
        response = supabase.table("watchlist_items")\
            .insert({
                "watchlist_id": watchlist_id,
                "ticker": normalized_ticker
            })\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add item to watchlist"
            )
        
        return WatchlistItemResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        # Check for unique constraint violation (PostgreSQL error code 23505)
        error_str = str(e).lower()
        if 'unique' in error_str or 'duplicate' in error_str or '23505' in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ticker {normalized_ticker} is already in this watchlist"
            )
        logger.error(f"Error adding item to watchlist {watchlist_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/watchlists/{watchlist_id}/items", response_model=List[WatchlistItemResponse])
@limiter.limit(get_rate_limit())
async def get_watchlist_items(
    request: Request,
    watchlist_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all items for a watchlist.
    
    Args:
        watchlist_id: UUID of the watchlist
        
    Returns:
        List of watchlist items
    """
    try:
        supabase = get_supabase_admin()
        
        # Verify the watchlist belongs to the user
        watchlist_response = supabase.table("watchlists")\
            .select("id")\
            .eq("id", watchlist_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist not found"
            )
        
        # Get all items for this watchlist
        response = supabase.table("watchlist_items")\
            .select("*")\
            .eq("watchlist_id", watchlist_id)\
            .order("created_at", desc=False)\
            .execute()
        
        return [WatchlistItemResponse(**item) for item in response.data]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching items for watchlist {watchlist_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/watchlists/{watchlist_id}/items/{item_id}", response_model=SuccessResponse)
@limiter.limit(get_rate_limit())
async def delete_watchlist_item(
    request: Request,
    watchlist_id: str,
    item_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Remove a ticker from a watchlist.
    
    Args:
        watchlist_id: UUID of the watchlist
        item_id: UUID of the item to remove
        
    Returns:
        Success response
    """
    try:
        supabase = get_supabase_admin()
        
        # Verify the watchlist belongs to the user
        watchlist_response = supabase.table("watchlists")\
            .select("id")\
            .eq("id", watchlist_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist not found"
            )
        
        # Delete the item
        response = supabase.table("watchlist_items")\
            .delete()\
            .eq("id", item_id)\
            .eq("watchlist_id", watchlist_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        return SuccessResponse(success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id} from watchlist {watchlist_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/watchlists/items/status", response_model=dict)
@limiter.limit(get_rate_limit())
async def get_ticker_watchlist_status(
    request: Request,
    ticker: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get which watchlists contain a specific ticker.
    Useful for extensions to check watchlist status efficiently.
    
    Args:
        ticker: Ticker symbol to check
        
    Returns:
        Dictionary with ticker and list of watchlist IDs that contain it
    """
    try:
        normalized_ticker = _validate_ticker(ticker)
        supabase = get_supabase_admin()
        
        # Get all user's watchlists
        watchlists_response = supabase.table("watchlists")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        watchlist_ids = [wl["id"] for wl in watchlists_response.data]
        
        if not watchlist_ids:
            return {"ticker": normalized_ticker, "watchlist_ids": []}
        
        # Check which watchlists contain this ticker
        items_response = supabase.table("watchlist_items")\
            .select("watchlist_id")\
            .in_("watchlist_id", watchlist_ids)\
            .eq("ticker", normalized_ticker)\
            .execute()
        
        watchlist_ids_with_ticker = [item["watchlist_id"] for item in items_response.data]
        
        return {
            "ticker": normalized_ticker,
            "watchlist_ids": watchlist_ids_with_ticker
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking ticker status for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

