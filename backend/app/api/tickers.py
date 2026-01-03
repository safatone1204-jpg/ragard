"""Ticker detail API endpoint."""
from fastapi import APIRouter, HTTPException, status, Request
from app.models.ticker import TickerMetrics
from app.services import data_sources
from app.core.rate_limiter import limiter, get_rate_limit
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tickers"])


@router.get("/tickers/{symbol}", response_model=TickerMetrics, status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit())
async def get_ticker(request: Request, symbol: str):
    """Get detailed metrics for a specific ticker."""
    try:
        ticker = await data_sources.get_ticker_details(symbol.upper())
        if ticker is None:
            # Return 404 - FastAPI logs this as INFO (expected for unknown tickers)
            # This is normal behavior and not an error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticker {symbol} not found"
            )
        return ticker
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticker details for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching ticker details: {str(e)}")


