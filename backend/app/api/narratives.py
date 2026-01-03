"""Narratives API endpoint."""
from fastapi import APIRouter, HTTPException, Query, Request
from app.narratives.models import NarrativeSummary
from app.narratives.config import TimeframeKey
from app.narratives import dynamic
from app.core.rate_limiter import limiter, get_rate_limit

router = APIRouter(prefix="/api", tags=["narratives"])


@router.get("/narratives", response_model=list[NarrativeSummary])
@limiter.limit(get_rate_limit())
async def get_narratives(
    request: Request,
    timeframe: TimeframeKey = Query(
        default="24h",
        description="Timeframe for discovering narratives (24h, 7d, 30d)"
    )
):
    """
    Get dynamically discovered narrative summaries for the specified timeframe.
    
    Narratives are built from Reddit co-mentions, not hard-coded templates.
    Each narrative includes metrics for all timeframes (24h, 7d, 30d).
    
    Args:
        timeframe: Timeframe key (24h, 7d, 30d). Defaults to "24h".
    
    Returns:
        List of NarrativeSummary objects, sorted by heat score for the selected timeframe
    """
    try:
        summaries = await dynamic.build_dynamic_narratives(timeframe)
        return summaries
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching narrative summaries: {str(e)}"
        )

