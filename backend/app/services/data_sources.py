"""Data source service - handles fetching ticker data from real sources.

This is the central place where data fetching logic lives.
All other parts of the application should call functions here.
"""
from typing import Optional
from decimal import Decimal
import yfinance as yf
from app.core.config import settings
from app.models.ticker import Ticker, TickerMetrics
from app.services.scoring import get_ragard_label

# Default trending symbols - meme/small-cap stocks
DEFAULT_TRENDING_SYMBOLS = [
    "GME", "AMC", "BBBY", "PLTR", "TSLA", "NVDA", "CVNA", "MARA", "RIOT", "SOFI"
]


def _fetch_real_trending_tickers(symbols: list[str] | None = None) -> list[Ticker]:
    """Fetch real market data for a list of symbols using yfinance.
    
    Args:
        symbols: List of ticker symbols. If None, uses DEFAULT_TRENDING_SYMBOLS.
    
    Returns:
        List of Ticker objects with real market data.
    """
    if symbols is None:
        symbols = DEFAULT_TRENDING_SYMBOLS
    
    try:
        # Fetch data for all symbols at once
        tickers = yf.Tickers(" ".join(symbols))
        results: list[Ticker] = []
        
        for symbol in symbols:
            try:
                ticker = tickers.tickers[symbol]
                
                # Get fast info for current price data
                fast_info = ticker.fast_info
                
                # Get full info for company name and other details
                info = ticker.info
                
                # Extract price data
                price = float(fast_info.get("lastPrice", 0.0) or fast_info.get("regularMarketPrice", 0.0) or 0.0)
                prev_close = float(fast_info.get("previousClose", price) or price)
                
                # Calculate change percentage
                if prev_close and prev_close > 0:
                    change_pct = ((price - prev_close) / prev_close) * 100
                else:
                    change_pct = 0.0
                
                # Get market cap
                market_cap = float(info.get("marketCap", 0.0) or 0.0)
                
                # Get company name
                company_name = info.get("longName") or info.get("shortName") or symbol
                
                # Calculate Ragard score using centralized scoring system
                from app.scoring.regard_score_centralized import get_regard_score_for_symbol
                import asyncio
                try:
                    # Run async function in sync context
                    score_result = asyncio.run(get_regard_score_for_symbol(symbol))
                    ragard_score = score_result.get('regard_score')
                except Exception as e:
                    # No fallback - return None if scoring fails
                    ragard_score = None
                risk_level = "moderate"  # TODO: Calculate from score
                
                # Create Ticker object
                ticker_obj = Ticker(
                    symbol=symbol,
                    company_name=company_name,
                    price=Decimal(str(price)),
                    change_pct=Decimal(str(round(change_pct, 2))),
                    market_cap=Decimal(str(int(market_cap))) if market_cap > 0 else None,
                    ragard_score=ragard_score,
                    risk_level=risk_level,
                )
                results.append(ticker_obj)
                
            except Exception as e:
                # Skip symbols that fail to fetch, log error if needed
                # In production, you might want to log this
                continue
        
        return results
        
    except Exception as e:
        # If bulk fetch fails, fall back to individual fetches
        results: list[Ticker] = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if hist.empty:
                    continue
                
                # Get latest price
                price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2] if len(hist) > 1 else price)
                
                # Calculate change percentage
                if prev_close and prev_close > 0:
                    change_pct = ((price - prev_close) / prev_close) * 100
                else:
                    change_pct = 0.0
                
                # Get market cap
                market_cap = float(info.get("marketCap", 0.0) or 0.0)
                
                # Get company name
                company_name = info.get("longName") or info.get("shortName") or symbol
                
                # Calculate Ragard score using centralized scoring system
                from app.scoring.regard_score_centralized import get_regard_score_for_symbol
                import asyncio
                try:
                    # Run async function in sync context
                    score_result = asyncio.run(get_regard_score_for_symbol(symbol))
                    ragard_score = score_result.get('regard_score')
                except Exception as e:
                    # No fallback - return None if scoring fails
                    ragard_score = None
                risk_level = "moderate"  # TODO: Calculate from score
                
                ticker_obj = Ticker(
                    symbol=symbol,
                    company_name=company_name,
                    price=Decimal(str(price)),
                    change_pct=Decimal(str(round(change_pct, 2))),
                    market_cap=Decimal(str(int(market_cap))) if market_cap > 0 else None,
                    ragard_score=ragard_score,
                    risk_level=risk_level,
                )
                results.append(ticker_obj)
                
            except Exception:
                # Skip failed symbols
                continue
        
        return results


async def get_trending_tickers() -> list[Ticker]:
    """Get list of trending tickers from real data sources.
    
    Fetches real market data using yfinance.
    """
    return _fetch_real_trending_tickers()


def _fetch_real_ticker_details(symbol: str) -> Optional[TickerMetrics]:
    """Fetch real market data for a specific ticker using yfinance.
    
    Args:
        symbol: Ticker symbol to fetch.
    
    Returns:
        TickerMetrics object with real market data, or None if not found.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="5d")
        
        if hist.empty:
            return None
        
        # Get latest price data
        latest = hist.iloc[-1]
        price = float(latest["Close"])
        
        # Calculate change percentage (today vs yesterday)
        if len(hist) > 1:
            prev_close = float(hist["Close"].iloc[-2])
            change_pct = ((price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
        else:
            change_pct = 0.0
        
        # Get market data
        market_cap = float(info.get("marketCap", 0.0) or 0.0)
        volume = int(info.get("volume", 0) or latest.get("Volume", 0) or 0)
        float_shares = int(info.get("sharesOutstanding", 0) or 0)
        
        # Get company name
        company_name = info.get("longName") or info.get("shortName") or symbol
        
        # Calculate Ragard score using centralized scoring system
        from app.scoring.regard_score_centralized import get_regard_score_for_symbol
        import asyncio
        try:
            score_result = asyncio.run(get_regard_score_for_symbol(symbol))
            ragard_score = score_result.get('regard_score')
        except Exception as e:
            # No fallback - return None if scoring fails
            ragard_score = None
        risk_level = "moderate"  # TODO: Calculate from score
        
        # Generate placeholder text fields
        exit_liquidity_rating = "Moderate - Real-time data available"
        hype_vs_price_text = "Real-time market data. Analysis pending."
        
        # Get ragard label
        ragard_label = get_ragard_label(ragard_score)
        
        return TickerMetrics(
            symbol=symbol.upper(),
            company_name=company_name,
            price=Decimal(str(price)),
            change_pct=Decimal(str(round(change_pct, 2))),
            market_cap=Decimal(str(int(market_cap))) if market_cap > 0 else None,
            volume=volume if volume > 0 else None,
            float_shares=float_shares if float_shares > 0 else None,
            ragard_score=ragard_score,
            risk_level=risk_level,
            exit_liquidity_rating=exit_liquidity_rating,
            hype_vs_price_text=hype_vs_price_text,
            ragard_label=ragard_label,
        )
        
    except Exception:
        return None


async def get_ticker_details(symbol: str) -> Optional[TickerMetrics]:
    """Get detailed metrics for a specific ticker from real data sources.
    
    Fetches real market data using yfinance.
    """
    return _fetch_real_ticker_details(symbol)


