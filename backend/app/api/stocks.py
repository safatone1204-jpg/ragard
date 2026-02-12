"""Stock profile API endpoint."""
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import yfinance as yf
from app.stocks.profile import get_company_profile, CompanyProfile
from app.core.rate_limiter import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["stocks"])


class BasicStockInfo(BaseModel):
    """Lightweight stock info for quick display."""
    symbol: str
    company_name: str | None
    price: float | None
    change_pct: float | None


@router.get("/stocks/{symbol}/basic", response_model=BasicStockInfo)
@limiter.limit(get_rate_limit())
async def get_stock_basic_info(request: Request, symbol: str):
    """
    Get basic stock information quickly (price, name, change).
    This is a lightweight endpoint that returns fast without calculating regard scores.
    """
    try:
        symbol = symbol.upper()
        ticker = yf.Ticker(symbol)
        
        # Get basic info quickly
        info = ticker.info
        company_name = info.get("longName") or info.get("shortName")
        
        # Get price and change
        price = None
        change_pct = None
        try:
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest = hist.iloc[-1]
                price = float(latest["Close"])
                if len(hist) > 1:
                    prev_close = float(hist["Close"].iloc[-2])
                    if prev_close > 0:
                        change_pct = ((price - prev_close) / prev_close) * 100
        except Exception as e:
            logger.warning(f"Error fetching price data for {symbol}: {e}")
            # Try fast_info as fallback
            try:
                fast_info = ticker.fast_info
                price = float(fast_info.get("lastPrice", 0.0) or fast_info.get("regularMarketPrice", 0.0) or 0.0)
            except Exception:
                pass
        
        return BasicStockInfo(
            symbol=symbol,
            company_name=company_name,
            price=price,
            change_pct=change_pct,
        )
    
    except Exception as e:
        logger.error(f"Error fetching basic stock info for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching basic stock info: {str(e)}"
        )


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

