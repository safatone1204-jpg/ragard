"""Trending tickers API endpoint."""
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Query, Request
from app.models.ticker import Ticker
from app.narratives.config import TimeframeKey
from app.services import data_sources
from app.core.config import settings
from app.core.rate_limiter import limiter, get_rate_limit
from app.trending import service as trending_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["trending"])


@router.get("/trending", response_model=list[Ticker])
@limiter.limit(get_rate_limit())
async def get_trending(
    request: Request,
    timeframe: TimeframeKey = Query(
        default="24h",
        description="Timeframe for trending tickers (24h, 7d, 30d)"
    )
):
    """
    Get list of trending tickers derived from Reddit activity and market movement.
    
    Args:
        timeframe: Timeframe key (24h, 7d, 30d). Defaults to "24h".
    
    Returns:
        List of Ticker objects sorted by trending score
    """
    try:
        # Use real trending builder to respect timeframe
        # Add timeout to prevent hanging (60 seconds max)
        tickers = await asyncio.wait_for(
            trending_service.build_trending_tickers(timeframe, max_symbols=10),
            timeout=60.0
        )
        return tickers
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Trending tickers request timed out. Please try again or use a different timeframe."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending tickers: {str(e)}")


