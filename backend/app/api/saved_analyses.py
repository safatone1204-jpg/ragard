"""Saved analyses API endpoints."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from pydantic import BaseModel
from uuid import UUID

from app.core.auth import get_current_user, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.core.rate_limiter import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["saved-analyses"])


# Request/Response models
class SavedAnalysisCreate(BaseModel):
    """Request model for creating a saved analysis."""
    ticker: str
    snapshot: Dict[str, Any]
    tags: Optional[List[str]] = None
    note: Optional[str] = None


class SavedAnalysisResponse(BaseModel):
    """Response model for a saved analysis."""
    id: str
    user_id: str
    ticker: str
    snapshot: Dict[str, Any]
    tags: List[str]
    note: Optional[str]
    created_at: str
    # Extracted fields from snapshot for convenience (optional)
    url: Optional[str] = None
    title: Optional[str] = None
    hostname: Optional[str] = None
    score: Optional[float] = None
    summaryText: Optional[str] = None
    contentType: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool


@router.get("/saved-analyses", response_model=List[SavedAnalysisResponse])
@limiter.limit(get_rate_limit())
async def get_saved_analyses(
    request: Request,
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all saved analyses for the current user.
    
    Args:
        ticker: Optional ticker symbol to filter by
        
    Returns:
        List of saved analyses ordered by created_at DESC
    """
    try:
        supabase = get_supabase_admin()
        
        query = supabase.table("saved_analyses")\
            .select("*")\
            .eq("user_id", current_user.id)
        
        if ticker:
            query = query.eq("ticker", ticker.upper())
        
        response = query.order("created_at", desc=True).execute()
        
        # Convert to response models, extracting metadata from snapshot
        result = []
        for item in response.data:
            snapshot = item.get("snapshot", {})
            if isinstance(snapshot, dict):
                # Add extracted fields to response for convenience
                item["url"] = snapshot.get("url")
                item["title"] = snapshot.get("title")
                item["hostname"] = snapshot.get("hostname")
                item["score"] = snapshot.get("score")
                item["summaryText"] = snapshot.get("summaryText")
                item["contentType"] = snapshot.get("contentType")
            result.append(SavedAnalysisResponse(**item))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching saved analyses for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/saved-analyses", response_model=SavedAnalysisResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit())
async def create_saved_analysis(
    request: Request,
    analysis_data: SavedAnalysisCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a new saved analysis.
    
    Args:
        analysis_data: Analysis data including ticker, snapshot, tags, and note
        
    Returns:
        Created saved analysis
    """
    # Validate ticker
    if not analysis_data.ticker or not analysis_data.ticker.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker cannot be empty"
        )
    
    # Validate snapshot
    if not analysis_data.snapshot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot cannot be null"
        )
    
    try:
        supabase = get_supabase_admin()
        
        # Extract metadata from snapshot if available (keep in snapshot too for compatibility)
        snapshot = analysis_data.snapshot.copy() if analysis_data.snapshot else {}
        url = snapshot.get("url")
        title = snapshot.get("title")
        
        # Check if analysis with same URL and ticker exists (upsert behavior)
        # Use simpler query that doesn't require JSONB operators (more compatible)
        existing_query = supabase.table("saved_analyses")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .eq("ticker", analysis_data.ticker.strip().upper())\
            .limit(1)
        
        existing = existing_query.execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing analysis (keep original created_at)
            analysis_id = existing.data[0]["id"]
            response = supabase.table("saved_analyses")\
                .update({
                    "snapshot": snapshot,
                    "tags": analysis_data.tags or [],
                    "note": analysis_data.note
                })\
                .eq("id", analysis_id)\
                .eq("user_id", current_user.id)\
                .execute()
        else:
            # Insert new analysis
            response = supabase.table("saved_analyses")\
                .insert({
                    "user_id": current_user.id,
                    "ticker": analysis_data.ticker.strip().upper(),
                    "snapshot": snapshot,
                    "tags": analysis_data.tags or [],
                    "note": analysis_data.note
                })\
                .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create saved analysis"
            )
        
        return SavedAnalysisResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Check if it's a table not found error
        if "saved_analyses" in error_msg.lower() and ("not found" in error_msg.lower() or "PGRST205" in error_msg):
            logger.error(f"Table 'saved_analyses' does not exist. Please run the SQL schema from supabase_schema_watchlists_saved_analyses.sql")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database table 'saved_analyses' does not exist. Please run the SQL schema from supabase_schema_watchlists_saved_analyses.sql in your Supabase SQL Editor."
            )
        logger.error(f"Error creating saved analysis for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/saved-analyses/{analysis_id}", response_model=SuccessResponse)
@limiter.limit(get_rate_limit())
async def delete_saved_analysis(
    request: Request,
    analysis_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete a saved analysis.
    
    Args:
        analysis_id: UUID of the saved analysis to delete
        
    Returns:
        Success response
    """
    try:
        supabase = get_supabase_admin()
        
        response = supabase.table("saved_analyses")\
            .delete()\
            .eq("id", analysis_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved analysis not found"
            )
        
        return SuccessResponse(success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting saved analysis {analysis_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

