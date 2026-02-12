"""
Centralized Regard Score calculation - THE SINGLE SOURCE OF TRUTH.

Regard Score is a 0-100 "degen meter" for investing in a company RIGHT NOW.
- 0 = extremely solid, boring, low-degen investment
- 100 = full casino, hyper-speculative, "you actually have brain damage" level degen
- Higher ALWAYS means MORE degen/risk, never the opposite

Regard Score is ticker-centric and timeframe-independent.
Trending timeframes (24H/7D/30D) affect which stocks appear and how they're ranked,
but NEVER alter the Regard Score value for a given ticker.
"""
import logging
from typing import Optional, Dict, Any
import yfinance as yf
from app.scoring.ragard_score import RagardScoreBreakdown

logger = logging.getLogger(__name__)

# In-memory cache for Regard Scores (short TTL to keep scores fresh)
# Now stores full dict: {symbol: (timestamp, regard_info_dict)}
_regard_cache: Dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 10 * 60  # 10 minutes

def clear_regard_cache():
    """Clear the in-memory Regard Score cache. Useful for testing or forcing recalculation."""
    global _regard_cache
    _regard_cache.clear()
    logger.info("Regard Score cache cleared")

# Semaphore to limit concurrent yfinance calls (prevent rate limiting)
_yfinance_semaphore = None

def _get_yfinance_semaphore():
    """Get or create semaphore for limiting concurrent yfinance calls."""
    global _yfinance_semaphore
    if _yfinance_semaphore is None:
        import asyncio
        _yfinance_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent yfinance calls
    return _yfinance_semaphore


async def get_regard_score_for_symbol(symbol: str) -> dict:
    """
    Return the current Regard Score (0-100, higher = more degen) for a ticker symbol.
    
    This function is the ONLY place the core Regard logic lives.
    All endpoints (Trending, Stock profile, Chrome extension, etc.) must call this.
    
    The score is timeframe-independent and represents "how retarded investing in this
    company would be right now" based on structural factors (fundamentals, volatility,
    hype, etc.) plus AI refinement.
    
    Args:
        symbol: Ticker symbol (e.g., "GME", "TSLA")
    
    Returns:
        Dict with:
        - regard_score: int | None (0-100, higher = more degen)
        - data_completeness: "full" | "partial" | "unknown"
        - missing_factors: list[str] (e.g. ["market_cap", "profit_margins"])
        - base_score: float | None (internal structural score 0-100)
        - ai_regard_score: int | None (AI overlay score 0-100)
    """
    import time
    
    # Check cache (now stores full dict)
    current_time = time.time()
    cache_key = symbol.upper()
    if cache_key in _regard_cache:
        cached_time, cached_result = _regard_cache[cache_key]
        if current_time - cached_time < CACHE_TTL_SECONDS:
            logger.debug(f"Using cached Regard Score for {symbol}: {cached_result.get('regard_score')}")
            return cached_result
    
    try:
        # Step 1: Get fundamental data (timeframe-independent)
        import asyncio
        try:
            base_score, missing_factors, data_completeness = await asyncio.wait_for(
                _compute_data_driven_base_score(symbol),
                timeout=10.0  # 10 second timeout for data-driven score
            )
        except asyncio.TimeoutError:
            logger.warning(f"Data-driven base score calculation timed out for {symbol}")
            base_score = None
            missing_factors = ["market_cap", "profit_margins", "beta", "avg_volume", "short_ratio"]
            data_completeness = "unknown"
        except Exception as e:
            logger.error(f"Error computing base score for {symbol}: {e}")
            base_score = None
            missing_factors = ["market_data"]
            data_completeness = "unknown"
        
        # Step 2: Get AI overlay score (with retries and longer timeout)
        ai_score = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ai_score = await asyncio.wait_for(
                    _get_ai_regard_score(symbol, base_score, missing_factors, data_completeness),
                    timeout=10.0  # 10 second timeout for AI call (increased from 3s)
                )
                if ai_score is not None:
                    break  # Success, exit retry loop
                else:
                    logger.warning(f"AI Regard Score returned None for {symbol}, attempt {attempt + 1}/{max_retries}")
            except asyncio.TimeoutError:
                logger.warning(f"AI Regard Score call timed out for {symbol}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            except Exception as e:
                logger.warning(f"AI Regard Score call failed for {symbol}, attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        if ai_score is None:
            logger.error(f"AI Regard Score failed after {max_retries} attempts for {symbol}")
        
        # Step 3: Blend data + AI (AI-heavy: 65% AI, 35% data)
        final_score = None
        if base_score is not None and ai_score is not None:
            # AI-heavy blend
            final_score = 0.35 * base_score + 0.65 * ai_score
        elif ai_score is not None:
            # Only AI available
            final_score = float(ai_score)
        elif base_score is not None:
            # Only data available
            final_score = float(base_score)
        # else: both None, final_score stays None
        
        # Clamp and round
        score_raw = final_score  # Store raw before rounding
        if final_score is not None:
            final_score = int(max(0, min(100, round(final_score))))
        
        # Build result dict
        result = {
            "regard_score": final_score,
            "data_completeness": data_completeness,
            "missing_factors": missing_factors or [],
            "base_score": base_score,
            "ai_regard_score": ai_score,
        }
        
        # Cache result
        _regard_cache[cache_key] = (current_time, result)
        
        logger.info(
            f"Computed Regard Score for {symbol}: {final_score} "
            f"(base={base_score}, ai={ai_score}, completeness={data_completeness})"
        )
        
        # Log to history (fire-and-forget, don't block response)
        try:
            # Determine scoring mode and AI success
            if ai_score is not None:
                scoring_mode = "ai"
                ai_success = True
            elif base_score is not None:
                scoring_mode = "fallback"
                ai_success = False
            else:
                scoring_mode = "error"
                ai_success = False
            
            # Fetch market data for history (non-blocking, with timeout)
            market_data = None
            try:
                market_data = await asyncio.wait_for(
                    _fetch_market_data_for_history(symbol),
                    timeout=3.0  # Short timeout to avoid blocking
                )
            except Exception as e:
                logger.debug(f"Could not fetch market data for history logging {symbol}: {e}")
            
            # Build config snapshot
            config_snapshot = {
                "ai_weight": 0.65,
                "base_weight": 0.35,
            }
            
            # Log history (fire-and-forget, but tracked for cleanup)
            from app.services.regard_history_service import log_regard_history
            from app.core.background_tasks import create_background_task
            # Use tracked background task that will be cancelled on shutdown
            create_background_task(log_regard_history(
                ticker=symbol,
                score_raw=score_raw,
                score_rounded=final_score,
                scoring_mode=scoring_mode,
                ai_success=ai_success,
                base_score=base_score,
                ai_score=ai_score,
                market_data=market_data,
                post_counts=None,  # Regard score doesn't use post counts directly
                config_snapshot=config_snapshot,
            ))
        except Exception as e:
            # Don't let history logging errors affect the response
            logger.warning(f"Error setting up history logging for {symbol}: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error computing Regard Score for {symbol}: {e}", exc_info=True)
        # Return unknown result (no fallback 50)
        return {
            "regard_score": None,
            "data_completeness": "unknown",
            "missing_factors": ["market_data", "ai_score"],
            "base_score": None,
            "ai_regard_score": None,
        }


async def _compute_data_driven_base_score(symbol: str) -> tuple[float | None, list[str], str]:
    """
    Compute data-driven base Regard Score (0-100) from structural factors.
    
    Uses timeframe-independent metrics:
    - Market cap (smaller = more degen)
    - Profitability (unprofitable = more degen)
    - Volatility/beta (higher = more degen)
    - Liquidity (illiquid = more degen)
    - Short interest (high = more degen/meme potential)
    
    Returns:
        Tuple of (base_score, missing_factors, data_completeness):
        - base_score: float | None (0-100 if calculated, None if no data)
        - missing_factors: list[str] (names of missing data fields)
        - data_completeness: "full" | "partial" | "unknown"
    """
    try:
        # Run yfinance calls in thread pool to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _fetch_ticker_info(sym: str):
            try:
                # Use fast_info first for speed, fallback to info if needed
                t = yf.Ticker(sym)
                # Try to get basic info quickly
                info = {}
                try:
                    # Get key fields we need
                    fast_info = t.fast_info
                    if fast_info:
                        info['lastPrice'] = fast_info.get('lastPrice')
                        info['regularMarketPrice'] = fast_info.get('regularMarketPrice')
                except:
                    pass
                
                # Get full info (this is the slow part)
                full_info = t.info
                if full_info:
                    info.update(full_info)
                
                # Also try to get historical data for fallback calculations
                try:
                    hist = t.history(period="1y", interval="1d")
                    if not hist.empty:
                        info['_hist_data'] = hist
                except:
                    pass
                
                return info
            except Exception as e:
                logger.warning(f"Error fetching info for {sym}: {e}")
                return {}
        
        # Use semaphore to limit concurrent yfinance calls
        semaphore = _get_yfinance_semaphore()
        async with semaphore:
            # Use default executor (thread pool) with longer timeout
            info = await asyncio.wait_for(
                loop.run_in_executor(None, _fetch_ticker_info, symbol),
                timeout=8.0  # 8 second timeout for yfinance call
            )
        
        # Check if we got valid data
        if not info or len(info) == 0:
            logger.warning(f"No data returned from yfinance for {symbol}")
            missing_factors = ["market_cap", "profit_margins", "beta", "avg_volume", "short_ratio"]
            return None, missing_factors, "unknown"
        
        # Track missing factors
        missing_factors = []
        degen_points = 0.0
        
        # Factor 1: Market Cap (smaller = more degen)
        market_cap_raw = info.get("marketCap")
        if market_cap_raw is None or market_cap_raw == 0:
            # Try alternative market cap fields
            market_cap_raw = info.get("totalAssets") or info.get("enterpriseValue")
        
        # Calculate market cap from shares outstanding * price if still missing
        if (market_cap_raw is None or market_cap_raw == 0) and "_hist_data" in info:
            try:
                hist = info["_hist_data"]
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
                    shares_outstanding = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
                    if shares_outstanding and current_price:
                        market_cap_raw = float(shares_outstanding) * current_price
            except:
                pass
        
        # Try calculating from shares outstanding and current price
        if (market_cap_raw is None or market_cap_raw == 0):
            shares_outstanding = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
            current_price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("lastPrice")
            if shares_outstanding and current_price:
                try:
                    market_cap_raw = float(shares_outstanding) * float(current_price)
                except:
                    pass
        
        if market_cap_raw is None or market_cap_raw == 0:
            missing_factors.append("market_cap")
        else:
            market_cap = float(market_cap_raw)
            if market_cap > 0:
                if market_cap < 50_000_000:  # < $50M = microcap
                    degen_points += 30
                elif market_cap < 300_000_000:  # < $300M = small cap
                    degen_points += 20
                elif market_cap < 2_000_000_000:  # < $2B = mid cap
                    degen_points += 10
                # Large cap (> $2B) = 0 points (less degen)
        
        # Factor 2: Profitability (unprofitable = more degen)
        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        profit_margins_raw = info.get("profitMargins")
        
        # Try to calculate profit margins from revenue and net income if missing
        if profit_margins_raw is None:
            total_revenue = info.get("totalRevenue")
            net_income = info.get("netIncomeToCommon") or info.get("netIncome")
            if total_revenue and net_income and total_revenue != 0:
                try:
                    profit_margins_raw = float(net_income) / float(total_revenue)
                except:
                    pass
        
        # Try operating margins as fallback
        if profit_margins_raw is None:
            profit_margins_raw = info.get("operatingMargins")
        
        # Use earnings growth as indicator if margins still missing
        earnings_growth = None
        if profit_margins_raw is None:
            earnings_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
        
        if profit_margins_raw is None and trailing_pe is None and forward_pe is None and earnings_growth is None:
            missing_factors.append("profit_margins")
        else:
            profit_margins = float(profit_margins_raw) if profit_margins_raw is not None else 0.0
            # If we have negative PE, that's a strong signal of unprofitability
            if trailing_pe is not None and trailing_pe < 0:
                degen_points += 20
            elif profit_margins < 0:
                # Negative margins = unprofitable
                degen_points += 20
            elif profit_margins > 0 and profit_margins < 0.05:
                # Very low margins
                degen_points += 10
            elif earnings_growth is not None and earnings_growth < -0.2:
                # Significant negative earnings growth
                degen_points += 15
            # Positive margins > 5% = 0 points (profitable)
        
        # Factor 3: Volatility/Beta (higher = more degen)
        beta_raw = info.get("beta")
        
        # Try alternative beta fields
        if beta_raw is None:
            beta_raw = info.get("beta3Year") or info.get("beta5Year")
        
        # Calculate beta from historical data if still missing
        if beta_raw is None and "_hist_data" in info:
            try:
                hist = info["_hist_data"]
                if not hist.empty and len(hist) > 20:  # Need enough data points
                    # Calculate returns
                    ticker_returns = hist["Close"].pct_change().dropna()
                    
                    # Try to get SPY data for comparison (simplified - use variance as proxy)
                    # For now, use standard deviation of returns as volatility proxy
                    if len(ticker_returns) > 0:
                        volatility = ticker_returns.std()
                        # High volatility (>5% daily std) suggests high beta
                        if volatility > 0.05:
                            beta_raw = 2.0  # High volatility proxy
                        elif volatility > 0.03:
                            beta_raw = 1.5  # Medium-high volatility
                        elif volatility > 0.02:
                            beta_raw = 1.2  # Medium volatility
                        else:
                            beta_raw = 0.8  # Low volatility
            except Exception as e:
                logger.debug(f"Error calculating beta from historical data for {symbol}: {e}")
        
        if beta_raw is None:
            missing_factors.append("beta")
        else:
            beta = float(beta_raw)
            if beta > 2.0:
                degen_points += 20
            elif beta > 1.5:
                degen_points += 15
            elif beta > 1.2:
                degen_points += 10
            # Beta < 1.2 = 0 points (less volatile)
        
        # Factor 4: Liquidity (illiquid = more degen)
        avg_volume_raw = info.get("averageVolume")
        
        # Try alternative volume fields
        if avg_volume_raw is None or avg_volume_raw == 0:
            avg_volume_raw = info.get("volume") or info.get("regularMarketVolume") or info.get("averageVolume10days")
        
        # Calculate average volume from historical data if still missing
        if (avg_volume_raw is None or avg_volume_raw == 0) and "_hist_data" in info:
            try:
                hist = info["_hist_data"]
                if not hist.empty and "Volume" in hist.columns:
                    avg_volume_raw = float(hist["Volume"].mean())
            except:
                pass
        
        if avg_volume_raw is None or avg_volume_raw == 0:
            missing_factors.append("avg_volume")
        else:
            avg_volume = float(avg_volume_raw)
            if avg_volume < 100_000:  # Very low volume
                degen_points += 15
            elif avg_volume < 500_000:  # Low volume
                degen_points += 10
            elif avg_volume < 1_000_000:  # Moderate volume
                degen_points += 5
            # High volume = 0 points (liquid)
        
        # Factor 5: Short Interest (high short interest = more degen/meme potential)
        short_ratio_raw = info.get("shortRatio")
        
        # Try alternative short interest fields
        if short_ratio_raw is None:
            short_ratio_raw = info.get("shortPercentOfFloat") or info.get("shortPercentOfSharesOutstanding")
        
        # Calculate short ratio from shares short and shares outstanding if available
        if short_ratio_raw is None:
            shares_short = info.get("sharesShort") or info.get("sharesShortPriorMonth")
            shares_outstanding = info.get("sharesOutstanding") or info.get("floatShares")
            if shares_short and shares_outstanding and shares_outstanding > 0:
                try:
                    short_ratio_raw = float(shares_short) / float(shares_outstanding)
                except:
                    pass
        
        # Try short ratio as percentage (convert to ratio)
        if short_ratio_raw is None:
            short_percent = info.get("shortPercentOfFloat")
            if short_percent is not None:
                try:
                    # If it's a percentage (0-100), convert to ratio
                    if short_percent > 1:
                        short_ratio_raw = short_percent / 100.0
                    else:
                        short_ratio_raw = short_percent
                except:
                    pass
        
        if short_ratio_raw is None:
            missing_factors.append("short_ratio")
        else:
            short_ratio = float(short_ratio_raw)
            # Normalize: if it's a percentage (0-100), convert to ratio
            if short_ratio > 1 and short_ratio <= 100:
                short_ratio = short_ratio / 100.0
            
            if short_ratio > 10:
                degen_points += 15
            elif short_ratio > 5:
                degen_points += 10
            elif short_ratio > 2:
                degen_points += 5
            # Low short ratio = 0 points
        
        # Factor 6: Structural Reddit Hype (timeframe-independent)
        # Skip Reddit call in base score to avoid timeouts - this will be handled by AI if available
        # Or we can add a cached Reddit stats lookup later
        # For now, skip to keep base score fast
        
        # Determine data completeness and finalize base score
        if len(missing_factors) == 5:  # All factors missing
            data_completeness = "unknown"
            base_score = None
        elif len(missing_factors) == 0:  # All factors present
            data_completeness = "full"
            base_score = max(0.0, min(100.0, degen_points))
        else:  # Some factors missing
            data_completeness = "partial"
            base_score = max(0.0, min(100.0, degen_points))
        
        # Log detailed breakdown for debugging
        logger.info(
            f"Data-driven base score for {symbol}: {base_score} "
            f"(completeness={data_completeness}, missing={missing_factors}, points={degen_points:.1f})"
        )
        return base_score, missing_factors, data_completeness
        
    except Exception as e:
        logger.error(f"Error computing data-driven base score for {symbol}: {e}", exc_info=True)
        # Return unknown (no fallback 50)
        missing_factors = ["market_cap", "profit_margins", "beta", "avg_volume", "short_ratio"]
        return None, missing_factors, "unknown"


async def _get_ai_regard_score(
    symbol: str, 
    base_score: float | None, 
    missing_factors: list[str], 
    data_completeness: str
) -> Optional[int]:
    """
    Get AI-refined Regard Score.
    
    Args:
        symbol: Ticker symbol
        base_score: Data-driven base score (0-100) or None
        missing_factors: List of missing data fields
        data_completeness: "full" | "partial" | "unknown"
    
    Returns:
        AI Regard Score (0-100) or None if AI fails
    """
    try:
        # Get ticker context for AI (run in thread pool to avoid blocking)
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _fetch_ticker_info(sym: str):
            try:
                t = yf.Ticker(sym)
                return t.info
            except Exception as e:
                logger.warning(f"Error fetching info for {sym}: {e}")
                return {}
        
        # Use semaphore to limit concurrent yfinance calls
        semaphore = _get_yfinance_semaphore()
        async with semaphore:
            info = await loop.run_in_executor(None, _fetch_ticker_info, symbol)
        
        # Get recent price/volume context for hype detection
        recent_context = {}
        try:
            hist = await loop.run_in_executor(None, lambda: yf.Ticker(symbol).history(period="30d", interval="1d"))
            if not hist.empty and len(hist) >= 2:
                latest_close = float(hist["Close"].iloc[-1])
                week_ago_close = float(hist["Close"].iloc[-7]) if len(hist) >= 7 else latest_close
                month_ago_close = float(hist["Close"].iloc[0])
                
                if week_ago_close > 0:
                    recent_context["change_7d_pct"] = ((latest_close / week_ago_close) - 1) * 100
                if month_ago_close > 0:
                    recent_context["change_30d_pct"] = ((latest_close / month_ago_close) - 1) * 100
                
                # Volume context
                recent_volume = float(hist["Volume"].iloc[-7:].mean()) if len(hist) >= 7 else 0
                avg_volume_30d = float(hist["Volume"].mean()) if len(hist) > 0 else 0
                if avg_volume_30d > 0:
                    recent_context["volume_spike_7d"] = recent_volume / avg_volume_30d
        except Exception as e:
            logger.debug(f"Error fetching recent context for {symbol}: {e}")
        
        # Build context payload
        context = {
            "symbol": symbol,
            "company_name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": float(info.get("marketCap", 0) or 0) if "market_cap" not in missing_factors else None,
            "profit_margins": float(info.get("profitMargins", 0) or 0) if "profit_margins" not in missing_factors else None,
            "beta": float(info.get("beta", 1.0) or 1.0) if "beta" not in missing_factors else None,
            "average_volume": float(info.get("averageVolume", 0) or 0) if "avg_volume" not in missing_factors else None,
            "short_ratio": float(info.get("shortRatio", 0) or 0) if "short_ratio" not in missing_factors else None,
            "base_score": base_score,
            "data_completeness": data_completeness,
            "missing_factors": missing_factors,
            **recent_context,  # Add recent price/volume changes
        }
        
        # Call AI helper
        from app.services.ai_client import generate_ticker_regard_ai
        ai_result = await generate_ticker_regard_ai(context)
        
        if ai_result and ai_result.get("ai_regard_score") is not None:
            try:
                ai_score = int(ai_result["ai_regard_score"])
                if 0 <= ai_score <= 100:
                    return ai_score
            except (ValueError, TypeError):
                pass
        
        return None
        
    except Exception as e:
        logger.warning(f"Error getting AI Regard Score for {symbol}: {e}")
        return None


async def _fetch_market_data_for_history(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch market data (price, change_24h_pct, volume_24h, market_cap) for history logging.
    
    Returns dict with price, change_24h_pct, volume_24h, market_cap, or None if fetch fails.
    """
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        def _fetch_data(sym: str):
            try:
                t = yf.Ticker(sym)
                info = t.info
                
                # Get price
                price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
                
                # Get 24h change (use regularMarketChangePercent if available)
                change_24h_pct = info.get("regularMarketChangePercent")
                if change_24h_pct is None:
                    # Calculate from previousClose if available
                    prev_close = info.get("previousClose")
                    if price and prev_close and prev_close > 0:
                        change_24h_pct = ((price / prev_close) - 1) * 100
                
                # Get volume (24h volume)
                volume_24h = info.get("regularMarketVolume") or info.get("volume")
                
                # Get market cap
                market_cap = info.get("marketCap")
                
                return {
                    "price": float(price) if price else None,
                    "change_24h_pct": float(change_24h_pct) if change_24h_pct is not None else None,
                    "volume_24h": float(volume_24h) if volume_24h else None,
                    "market_cap": float(market_cap) if market_cap else None,
                }
            except Exception as e:
                logger.debug(f"Error fetching market data for {sym}: {e}")
                return None
        
        semaphore = _get_yfinance_semaphore()
        async with semaphore:
            market_data = await loop.run_in_executor(None, _fetch_data, symbol)
            return market_data
            
    except Exception as e:
        logger.debug(f"Error in _fetch_market_data_for_history for {symbol}: {e}")
        return None


async def get_regard_score_breakdown(symbol: str) -> tuple[int, RagardScoreBreakdown]:
    """
    Get Regard Score with breakdown for display purposes.
    
    For now, returns the score with a simplified breakdown.
    In the future, we can enhance this to show component contributions.
    
    Args:
        symbol: Ticker symbol
    
    Returns:
        Tuple of (regard_score: int, breakdown: RagardScoreBreakdown)
    """
    score = await get_regard_score_for_symbol(symbol)
    
    # For now, return simplified breakdown
    # In the future, we can track component contributions
    breakdown = RagardScoreBreakdown(
        hype=None,
        volatility=None,
        liquidity=None,
        risk=None,
        hype_score=None,
        volatility_score=None,
        liquidity_score=None,
        risk_score=None,
    )
    
    return score, breakdown

