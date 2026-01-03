"""
Company profile service for assembling rich stock profiles.

Fetches company data from multiple sources:
- yfinance for fundamentals and market data
- SEC EDGAR API for filings
- Reddit stats and narratives
- Ragard scoring
"""
import logging
from datetime import datetime
from typing import Optional
import yfinance as yf
import requests
from pydantic import BaseModel

from app.data.tickers import TICKER_TO_CIK
from app.scoring.ragard_score import RagardScoreBreakdown, compute_ragard_score

logger = logging.getLogger(__name__)

# Simple in-memory cache for profiles (TTL: 5 minutes)
_profile_cache: dict[str, tuple[datetime, 'CompanyProfile']] = {}
CACHE_TTL_SECONDS = 300


class FilingSummary(BaseModel):
    """SEC filing summary."""
    form_type: str  # e.g. "10-K", "10-Q", "8-K"
    filed_at: datetime
    description: str | None
    edgar_url: str


class ValuationSnapshot(BaseModel):
    """Valuation metrics snapshot."""
    market_cap: float | None
    pe_ttm: float | None
    forward_pe: float | None
    price_to_sales: float | None
    ev_to_ebitda: float | None
    beta: float | None
    sector_pe_vs_market: float | None  # optional relative multiple
    valuation_label: str | None  # e.g. "Cheap vs sector", "Rich vs sector"


class FinancialHealth(BaseModel):
    """Financial health metrics."""
    revenue_ttm: float | None
    revenue_yoy_growth_pct: float | None
    net_income_ttm: float | None
    net_margin_pct: float | None
    debt_to_equity: float | None
    free_cash_flow_ttm: float | None


class RedditStatsForTicker(BaseModel):
    """Reddit activity stats for a ticker."""
    mention_count_24h: int
    mention_count_7d: int
    mention_count_30d: int
    top_subreddits: list[str]
    top_keywords: list[str]


class StockAIOverview(BaseModel):
    """AI-generated overview for a stock."""
    headline: str
    summary_bullets: list[str]
    risk_label: str  # "low" | "medium" | "high"
    timeframe_hint: str | None = None  # e.g. "day trade", "swing trade", "longer-term"


class CompanyProfile(BaseModel):
    """Complete company profile with all data."""
    symbol: str
    company_name: str | None
    cik: str | None
    sector: str | None
    industry: str | None
    country: str | None
    website: str | None
    description: str | None
    price: float | None  # Current price
    change_pct: float | None  # Daily % change
    valuation: ValuationSnapshot | None
    financials: FinancialHealth | None
    filings: list[FilingSummary]
    reddit_stats: RedditStatsForTicker | None
    narratives: list[str]  # narrative names this ticker belongs to
    ragard_score: int | None  # Always an integer (0-100) when present
    regard_data_completeness: str | None = None  # "full" | "partial" | "unknown"
    regard_missing_factors: list[str] | None = None  # List of missing data fields
    risk_level: str | None  # "low"/"medium"/"high"
    ragard_breakdown: RagardScoreBreakdown | None = None
    ai_overview: StockAIOverview | None = None


def _get_form_description(form_type: str) -> str:
    """Get a human-readable description for a form type."""
    form_descriptions = {
        "10-K": "Annual Report",
        "10-Q": "Quarterly Report",
        "8-K": "Current Report",
        "DEF 14A": "Proxy Statement",
        "S-1": "Registration Statement",
    }
    return form_descriptions.get(form_type, form_type)


async def _fetch_sec_filings(cik: str, limit: int = 5) -> list[FilingSummary]:
    """
    Fetch recent SEC filings for a CIK.
    
    Uses SEC EDGAR API: https://data.sec.gov/submissions/CIK{10-digit}.json
    
    Args:
        cik: CIK identifier (string, may need zero-padding)
        limit: Maximum number of filings to return
    
    Returns:
        List of FilingSummary objects
    """
    filings: list[FilingSummary] = []
    
    try:
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)
        
        # SEC EDGAR API endpoint
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        # SEC requires a User-Agent header
        headers = {
            "User-Agent": "Ragard/1.0 (Stock Analysis Tool) contact@ragard.com",
            "Accept": "application/json",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract recent filings
        recent_filings = data.get("filings", {}).get("recent", {})
        form_types = recent_filings.get("form", [])
        filing_dates = recent_filings.get("reportDate", [])
        filing_nums = recent_filings.get("reportDate", [])  # Using reportDate as identifier
        
        # Build filing summaries
        for i, form_type in enumerate(form_types[:limit]):
            if i >= len(filing_dates):
                break
            
            filed_date_str = filing_dates[i]
            try:
                filed_at = datetime.strptime(filed_date_str, "%Y-%m-%d")
            except ValueError:
                continue
            
            # Build EDGAR URL
            accession_nums = recent_filings.get("accessionNumber", [])
            accession_num = accession_nums[i] if i < len(accession_nums) else None
            
            if accession_num:
                # Format EDGAR URL for viewing the filing
                edgar_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik_padded}&accession_number={accession_num}&xbrl_type=v"
            else:
                # Fallback to company filings page
                edgar_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik_padded}&action=getcompany"
            
            filing = FilingSummary(
                form_type=form_type,
                filed_at=filed_at,
                description=_get_form_description(form_type),
                edgar_url=edgar_url,
            )
            filings.append(filing)
    
    except Exception as e:
        logger.warning(f"Error fetching SEC filings for CIK {cik}: {e}")
        # Return empty list on error - don't fail the whole profile
    
    return filings


async def _get_reddit_stats_for_symbol(symbol: str) -> RedditStatsForTicker:
    """
    Get Reddit stats for a symbol across all timeframes.
    
    Fetches Reddit posts for each timeframe and counts mentions.
    """
    from app.social.reddit import get_recent_reddit_posts, REDDIT_SUBREDDITS
    from app.social.text_utils import extract_tickers_and_keywords
    from app.narratives.config import TimeframeKey
    from collections import Counter, defaultdict
    
    stats_24h = {"mentions": 0, "subreddits": Counter(), "keywords": Counter()}
    stats_7d = {"mentions": 0, "subreddits": Counter(), "keywords": Counter()}
    stats_30d = {"mentions": 0, "subreddits": Counter(), "keywords": Counter()}
    
    # Fetch posts for each timeframe independently
    timeframes: list[tuple[TimeframeKey, dict]] = [
        ("24h", stats_24h),
        ("7d", stats_7d),
        ("30d", stats_30d),
    ]
    
    for timeframe_key, stats in timeframes:
        try:
            logger.debug(f"Fetching Reddit posts for {symbol} in timeframe {timeframe_key}")
            posts = await get_recent_reddit_posts(REDDIT_SUBREDDITS, timeframe_key)
            logger.debug(f"Found {len(posts)} posts for {symbol} in timeframe {timeframe_key}")
            
            for post in posts:
                text = post.title
                if post.selftext:
                    text += " " + post.selftext
                
                tickers, keywords = extract_tickers_and_keywords(text)
                
                if symbol in tickers:
                    stats["mentions"] += tickers.count(symbol)
                    stats["subreddits"][post.subreddit] += 1
                    stats["keywords"].update(keywords)
        except Exception as e:
            logger.warning(f"Error fetching Reddit stats for {symbol} ({timeframe_key}): {e}")
            continue
    
    # Get top subreddits and keywords (across all timeframes)
    all_subreddits = Counter()
    all_keywords = Counter()
    all_subreddits.update(stats_24h["subreddits"])
    all_subreddits.update(stats_7d["subreddits"])
    all_subreddits.update(stats_30d["subreddits"])
    all_keywords.update(stats_24h["keywords"])
    all_keywords.update(stats_7d["keywords"])
    all_keywords.update(stats_30d["keywords"])
    
    top_subreddits = [sub for sub, _ in all_subreddits.most_common(5)]
    top_keywords = [kw for kw, _ in all_keywords.most_common(10)]
    
    # Log the counts for debugging
    logger.debug(
        f"Reddit stats for {symbol}: 24h={stats_24h['mentions']}, "
        f"7d={stats_7d['mentions']}, 30d={stats_30d['mentions']}"
    )
    
    return RedditStatsForTicker(
        mention_count_24h=stats_24h["mentions"],
        mention_count_7d=stats_7d["mentions"],
        mention_count_30d=stats_30d["mentions"],
        top_subreddits=top_subreddits,
        top_keywords=top_keywords,
    )


async def _get_narratives_for_symbol(symbol: str) -> list[str]:
    """
    Get narrative names that include this symbol.
    
    TODO: Query from narratives cache/database for better performance.
    For now, queries the latest narratives and filters by ticker membership.
    """
    try:
        # Query the latest narratives (24h timeframe as default)
        from app.narratives.dynamic import build_dynamic_narratives
        from app.narratives.config import TimeframeKey
        
        narratives = await build_dynamic_narratives("24h")
        
        # Filter narratives that include this symbol
        narrative_names = []
        for narrative in narratives:
            if symbol in narrative.tickers:
                narrative_names.append(narrative.name)
        
        return narrative_names
    except Exception as e:
        logger.warning(f"Error fetching narratives for {symbol}: {e}")
        return []


async def get_company_profile(symbol: str) -> CompanyProfile:
    """
    Assemble a complete company profile from multiple data sources.
    
    Args:
        symbol: Ticker symbol (will be normalized to uppercase)
    
    Returns:
        CompanyProfile with all available data
    """
    symbol = symbol.upper()
    
    # Check cache
    now = datetime.now()
    if symbol in _profile_cache:
        cached_time, cached_profile = _profile_cache[symbol]
        if (now - cached_time).total_seconds() < CACHE_TTL_SECONDS:
            return cached_profile
    
    # Get CIK from ticker universe
    cik = TICKER_TO_CIK.get(symbol)
    
    # Initialize profile with basic info
    profile = CompanyProfile(
        symbol=symbol,
        company_name=None,
        cik=cik,
        sector=None,
        industry=None,
        country=None,
        website=None,
        description=None,
        price=None,
        change_pct=None,
        valuation=None,
        financials=None,
        filings=[],
        reddit_stats=None,
        narratives=[],
        ragard_score=None,
        regard_data_completeness=None,
        regard_missing_factors=None,
        risk_level=None,
    )
    
    # Fetch fundamentals from yfinance
    try:
        # TODO: move to a dedicated fundamentals provider if needed
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get current price and change
        try:
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest = hist.iloc[-1]
                profile.price = float(latest["Close"])
                if len(hist) > 1:
                    prev_close = float(hist["Close"].iloc[-2])
                    if prev_close > 0:
                        profile.change_pct = ((profile.price - prev_close) / prev_close) * 100
        except Exception as e:
            logger.warning(f"Error fetching price data for {symbol}: {e}")
            # Try fast_info as fallback
            try:
                fast_info = ticker.fast_info
                profile.price = float(fast_info.get("lastPrice", 0.0) or fast_info.get("regularMarketPrice", 0.0) or 0.0)
            except Exception:
                pass
        
        # Basic company info
        profile.company_name = info.get("longName") or info.get("shortName")
        profile.sector = info.get("sector")
        profile.industry = info.get("industry")
        profile.country = info.get("country")
        profile.website = info.get("website")
        profile.description = info.get("longBusinessSummary")
        
        # Valuation metrics
        market_cap = info.get("marketCap")
        pe_ttm = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        price_to_sales = info.get("priceToSalesTrailing12Months")
        ev_to_ebitda = info.get("enterpriseToEbitda")
        beta = info.get("beta")
        
        # Calculate valuation label
        valuation_label = None
        if pe_ttm and info.get("sectorPE"):
            sector_pe = info.get("sectorPE")
            if pe_ttm < sector_pe * 0.8:
                valuation_label = "Cheap vs sector"
            elif pe_ttm > sector_pe * 1.2:
                valuation_label = "Rich vs sector"
            else:
                valuation_label = "Fairly valued vs sector"
        
        profile.valuation = ValuationSnapshot(
            market_cap=float(market_cap) if market_cap else None,
            pe_ttm=float(pe_ttm) if pe_ttm else None,
            forward_pe=float(forward_pe) if forward_pe else None,
            price_to_sales=float(price_to_sales) if price_to_sales else None,
            ev_to_ebitda=float(ev_to_ebitda) if ev_to_ebitda else None,
            beta=float(beta) if beta else None,
            sector_pe_vs_market=float(info.get("sectorPE")) if info.get("sectorPE") else None,
            valuation_label=valuation_label,
        )
        
        # Financial health metrics
        revenue_ttm = info.get("totalRevenue")
        net_income_ttm = info.get("netIncomeToCommon")
        net_margin = info.get("profitMargins")
        debt_to_equity = info.get("debtToEquity")
        free_cash_flow = info.get("freeCashflow")
        
        # Calculate YoY revenue growth (if available)
        revenue_yoy_growth = None
        if revenue_ttm and info.get("revenueGrowth"):
            revenue_yoy_growth = info.get("revenueGrowth") * 100
        
        profile.financials = FinancialHealth(
            revenue_ttm=float(revenue_ttm) if revenue_ttm else None,
            revenue_yoy_growth_pct=float(revenue_yoy_growth) if revenue_yoy_growth else None,
            net_income_ttm=float(net_income_ttm) if net_income_ttm else None,
            net_margin_pct=float(net_margin * 100) if net_margin else None,
            debt_to_equity=float(debt_to_equity) if debt_to_equity else None,
            free_cash_flow_ttm=float(free_cash_flow) if free_cash_flow else None,
        )
        
        
        # Compute risk level from beta/volatility (used for scoring)
        if beta:
            if beta < 0.8:
                profile.risk_level = "low"
            elif beta < 1.2:
                profile.risk_level = "medium"
            else:
                profile.risk_level = "high"
        else:
            profile.risk_level = "medium"  # Default
    
    except Exception as e:
        logger.warning(f"Error fetching yfinance data for {symbol}: {e}")
        # Continue with partial profile
    
    # Fetch SEC filings if CIK is available
    if cik:
        try:
            # TODO: add caching for filings to avoid rate limits and repeated calls
            profile.filings = await _fetch_sec_filings(cik, limit=5)
        except Exception as e:
            logger.warning(f"Error fetching SEC filings for {symbol}: {e}")
            profile.filings = []
    
    # Get Reddit stats
    try:
        profile.reddit_stats = await _get_reddit_stats_for_symbol(symbol)
    except Exception as e:
        logger.warning(f"Error fetching Reddit stats for {symbol}: {e}")
        profile.reddit_stats = None
    
    # Get narratives
    try:
        profile.narratives = await _get_narratives_for_symbol(symbol)
    except Exception as e:
        logger.warning(f"Error fetching narratives for {symbol}: {e}")
        profile.narratives = []
    
    # Get Regard Score using centralized, timeframe-independent function
    # Regard Score represents structural degen level, not timeframe-dependent trending activity
    try:
        from app.scoring.regard_score_centralized import get_regard_score_for_symbol, get_regard_score_breakdown
        regard_info = await get_regard_score_for_symbol(symbol)
        
        # Set score, breakdown, and metadata
        profile.ragard_score = regard_info.get("regard_score")
        profile.regard_data_completeness = regard_info.get("data_completeness")
        profile.regard_missing_factors = regard_info.get("missing_factors", [])
        
        # Get breakdown for display
        if profile.ragard_score is not None:
            _, ragard_breakdown = await get_regard_score_breakdown(symbol)
            profile.ragard_breakdown = ragard_breakdown
        
    except Exception as e:
        logger.warning(f"Error computing Regard Score for {symbol}: {e}")
        # Continue without score/breakdown
    
    # Generate AI overview
    try:
        from app.services.ai_client import generate_stock_overview_ai
        
        # Get recent Reddit post samples for this ticker
        reddit_samples = []
        try:
            from app.social.reddit import get_recent_reddit_posts, REDDIT_SUBREDDITS
            posts = await get_recent_reddit_posts(REDDIT_SUBREDDITS, "24h")
            for post in posts[:20]:  # Get up to 20 recent posts
                text = post.title
                if post.selftext:
                    text += " " + post.selftext[:200]  # Limit selftext length
                # Check if symbol is mentioned
                if symbol.upper() in text.upper():
                    reddit_samples.append(post.title[:100])  # Limit title length
                    if len(reddit_samples) >= 10:  # Max 10 samples
                        break
        except Exception as e:
            logger.debug(f"Error fetching Reddit samples for AI: {e}")
        
        # Get percent changes for different timeframes
        percent_changes = {}
        try:
            from app.narratives.service import _fetch_ticker_returns
            ticker_returns = _fetch_ticker_returns([symbol], period_days=60)
            returns = ticker_returns.get(symbol, {})
            percent_changes["1d"] = returns.get("24h")
            percent_changes["7d"] = returns.get("7d")
            percent_changes["30d"] = returns.get("30d")
        except Exception:
            # Fallback to daily change if available
            if profile.change_pct is not None:
                percent_changes["1d"] = float(profile.change_pct)
        
        # Build payload for AI
        ai_payload = {
            "symbol": symbol,
            "company_name": profile.company_name,
            "sector": profile.sector,
            "industry": profile.industry,
            "price": profile.price,
            "percent_changes": percent_changes,
            "market_cap": profile.valuation.market_cap if profile.valuation else None,
            "regard_score": profile.ragard_score,
            "regard_breakdown": profile.ragard_breakdown.model_dump() if profile.ragard_breakdown else None,
            "narratives": profile.narratives,
            "reddit_samples": reddit_samples,
        }
        
        # Call AI (with timeout protection - don't block too long)
        ai_result = await generate_stock_overview_ai(ai_payload)
        
        if ai_result:
            profile.ai_overview = StockAIOverview(
                headline=ai_result["headline"],
                summary_bullets=ai_result["summary_bullets"],
                risk_label=ai_result["risk_label"],
                timeframe_hint=ai_result.get("timeframe_hint"),
            )
        else:
            profile.ai_overview = None
            
    except Exception as e:
        logger.warning(f"Error generating AI overview for {symbol}: {e}")
        profile.ai_overview = None
        # Don't fail the whole profile if AI fails
    
    # Cache the profile
    _profile_cache[symbol] = (now, profile)
    
    return profile

