"""Stock profile API endpoint."""
import logging
from fastapi import APIRouter, HTTPException, Request
from app.stocks.profile import get_company_profile, CompanyProfile
from app.core.rate_limiter import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/stocks/{symbol}", response_model=CompanyProfile)
@limiter.limit(get_rate_limit())
async def get_stock_profile(request: Request, symbol: str):
    """
    Get comprehensive company profile for a stock.
    
    Includes:
    - Company overview (name, sector, industry, description)
    - Valuation metrics (P/E, P/S, EV/EBITDA, etc.)
    - Financial health metrics
    - SEC filings (if CIK available)
    - Reddit stats and narratives
    - Ragard score and risk level
    """
    try:
        # Normalize symbol to uppercase
        symbol = symbol.upper()
        
        profile = await get_company_profile(symbol)
        return profile
    
    except Exception as e:
        logger.error(f"Error fetching stock profile for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stock profile: {str(e)}"
        )

