"""Service for building trending tickers from Reddit activity and market data."""
import logging
from typing import Dict, DefaultDict
from collections import defaultdict
from decimal import Decimal
import yfinance as yf
import pandas as pd
from app.narratives.config import TimeframeKey
from app.models.ticker import Ticker
from app.social.reddit import get_recent_reddit_posts, REDDIT_SUBREDDITS
from app.social.text_utils import extract_tickers_and_keywords
from app.narratives.service import _fetch_ticker_returns
from app.scoring.ragard_score import compute_ragard_score

logger = logging.getLogger(__name__)

# Minimum mentions for a ticker to be considered (lower for shorter timeframes)
def get_min_mentions(timeframe: TimeframeKey) -> int:
    """Get minimum mentions threshold based on timeframe."""
    if timeframe == "24h":
        return 1  # Lower threshold for 24h since there's less data
    elif timeframe == "7d":
        return 2
    else:  # 30d
        return 3


def _get_timeframe_days(timeframe: TimeframeKey) -> int:
    """Convert timeframe to approximate trading days."""
    if timeframe == "24h":
        return 1
    elif timeframe == "7d":
        return 7
    elif timeframe == "30d":
        return 30
    else:
        return 1 


async def build_trending_tickers(
    timeframe: TimeframeKey,
    max_symbols: int = 10
) -> list[Ticker]:
    """
    Build trending tickers from Reddit activity and market movement.
    
    Args:
        timeframe: Timeframe key (24h, 7d, 30d)
        max_symbols: Maximum number of tickers to return
    
    Returns:
        List of Ticker objects sorted by trending_score
    """
    # Step 1: Collect Reddit posts for the specified timeframe
    logger.info(f"Fetching Reddit posts for timeframe: {timeframe}")
    posts = await get_recent_reddit_posts(REDDIT_SUBREDDITS, timeframe)
    logger.info(f"Fetched {len(posts)} Reddit posts for timeframe {timeframe}")
    
    if len(posts) == 0:
        logger.warning(f"No Reddit posts found for timeframe {timeframe}. This may indicate Reddit API issues or no recent activity.")
    
    # Step 2: Extract tickers and build stats
    ticker_stats: DefaultDict[str, Dict[str, any]] = defaultdict(lambda: {
        "mention_count": 0,
        "unique_posts_count": 0,
        "post_ids": set(),
    })
    
    for post in posts:
        # Combine title and selftext
        text = post.title
        if post.selftext:
            text += " " + post.selftext
        
        # Extract tickers
        tickers, _ = extract_tickers_and_keywords(text)
        
        # Skip posts with no tickers
        if not tickers:
            continue
        
        # Update stats
        unique_tickers_in_post = set(tickers)
        for ticker in unique_tickers_in_post:
            ticker_stats[ticker]["mention_count"] += tickers.count(ticker)
            ticker_stats[ticker]["unique_posts_count"] += 1
            ticker_stats[ticker]["post_ids"].add(post.id)
    
    # Step 3: Pick candidate tickers
    min_mentions = get_min_mentions(timeframe)
    candidate_tickers = [
        ticker for ticker, stats in ticker_stats.items()
        if stats["mention_count"] >= min_mentions
    ]
    
    logger.info(f"Found {len(candidate_tickers)} candidate tickers with >= {min_mentions} mentions for timeframe {timeframe}")
    
    if not candidate_tickers:
        logger.warning(f"No tickers found with >= {min_mentions} mentions for timeframe {timeframe}")
        # For 24h, if no candidates, try to include top tickers by mention count
        if timeframe == "24h" and len(ticker_stats) > 0:
            logger.info(f"24h timeframe: falling back to include top tickers by mention count")
            # Sort by mention count and take top candidates
            sorted_tickers = sorted(
                ticker_stats.items(),
                key=lambda x: x[1]["mention_count"],
                reverse=True
            )
            # Limit to reasonable number to avoid timeout
            candidate_tickers = [ticker for ticker, _ in sorted_tickers[:max_symbols + 10]]
            logger.info(f"Using {len(candidate_tickers)} top tickers for 24h timeframe")
        else:
            return []
    
    # If too many candidates, take top N by mention count
    # Limit to max_symbols + 10 to reduce processing time (but allow some buffer for failures)
    max_candidates = max_symbols + 10
    if len(candidate_tickers) > max_candidates:
        candidate_tickers = sorted(
            candidate_tickers,
            key=lambda t: ticker_stats[t]["mention_count"],
            reverse=True
        )[:max_candidates]
        logger.info(f"Limited candidates to top {max_candidates} by mention count")
    
    # Step 4: Fetch market data
    # Get returns for the selected timeframe
    ticker_returns = _fetch_ticker_returns(candidate_tickers, period_days=60)
    
    # Fetch additional market data (price, volume, company name)
    trending_tickers: list[Ticker] = []
    max_mention_count = max(
        ticker_stats[t]["mention_count"] for t in candidate_tickers
    ) if candidate_tickers else 1
    
    # Import here to avoid circular imports
    from app.scoring.regard_score_centralized import get_regard_score_for_symbol
    
    # Process tickers in parallel for Regard Score calculation
    import asyncio
    
    async def process_ticker(symbol: str) -> Ticker | None:
        try:
            # Run yfinance calls in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            
            def _fetch_ticker_data(sym: str):
                try:
                    t = yf.Ticker(sym)
                    return {
                        "info": t.info,
                        "fast_info": t.fast_info
                    }
                except Exception as e:
                    logger.warning(f"Error fetching ticker data for {sym}: {e}")
                    return {"info": {}, "fast_info": {}}
            
            ticker_data = await loop.run_in_executor(None, _fetch_ticker_data, symbol)
            info = ticker_data["info"]
            fast_info = ticker_data["fast_info"]
            
            # Get price data
            price = float(
                fast_info.get("lastPrice", 0.0) or
                fast_info.get("regularMarketPrice", 0.0) or
                0.0
            )
            
            # Get returns for the specific timeframe
            returns = ticker_returns.get(symbol, {})
            timeframe_return = returns.get(timeframe)
            
            if timeframe_return is None:
                # Fallback: calculate from history for the specific timeframe
                def _fetch_history(sym: str, period: str):
                    try:
                        t = yf.Ticker(sym)
                        return t.history(period=period, interval="1d")
                    except Exception as e:
                        logger.warning(f"Error fetching history for {sym}: {e}")
                        return pd.DataFrame()
                
                period_days = _get_timeframe_days(timeframe) + 5
                hist = await loop.run_in_executor(
                    None,  # Use default executor
                    _fetch_history, 
                    symbol, 
                    f"{period_days}d"
                )
                if not hist.empty and len(hist) >= 2:
                    latest_close = float(hist["Close"].iloc[-1])
                    days_back = min(_get_timeframe_days(timeframe), len(hist) - 1)
                    if days_back > 0 and len(hist) > days_back:
                        prev_close = float(hist["Close"].iloc[-days_back - 1])
                        if prev_close > 0:
                            timeframe_return = ((latest_close / prev_close) - 1) * 100
                        else:
                            timeframe_return = 0.0
                    else:
                        # Not enough history, use first vs last
                        first_close = float(hist["Close"].iloc[0])
                        if first_close > 0:
                            timeframe_return = ((latest_close / first_close) - 1) * 100
                        else:
                            timeframe_return = 0.0
                else:
                    timeframe_return = 0.0
            
            logger.debug(f"Ticker {symbol} timeframe {timeframe} return: {timeframe_return:.2f}%")
            
            # Get volume data for relative volume calculation
            current_volume = float(info.get("volume", 0) or 0)
            avg_volume_30d = float(info.get("averageVolume", current_volume) or current_volume)
            rel_volume = (current_volume / avg_volume_30d) if avg_volume_30d > 0 else 1.0
            
            # Get company name
            company_name = info.get("longName") or info.get("shortName") or symbol
            
            # Get market cap
            market_cap = float(info.get("marketCap", 0.0) or 0.0)
            
            # Step 5: Get Regard Score using centralized, timeframe-independent function
            # Regard Score is NOT affected by the selected timeframe (24H/7D/30D)
            # It represents structural degen level of the company, not trending activity
            # Use shorter timeout for trending to prevent overall request timeout
            # Cache will help avoid recalculation for recently computed scores
            try:
                regard_info = await asyncio.wait_for(
                    get_regard_score_for_symbol(symbol),
                    timeout=5.0  # Reduced to 5 seconds for trending (cache helps avoid slow calls)
                )
                ragard_score = regard_info.get("regard_score")
                logger.debug(f"Regard Score for {symbol}: {ragard_score} (completeness={regard_info.get('data_completeness')})")
            except asyncio.TimeoutError:
                logger.debug(f"Regard Score calculation timed out for {symbol} (skipping for trending)")
                ragard_score = None
            except Exception as e:
                logger.debug(f"Regard Score calculation failed for {symbol}: {e}")
                ragard_score = None
            
            # Determine risk level based on volatility and price change
            abs_change = abs(timeframe_return)
            if abs_change > 15:
                risk_level = "extreme"
            elif abs_change > 8:
                risk_level = "high"
            elif abs_change > 3:
                risk_level = "moderate"
            else:
                risk_level = "low"
            
            # Create Ticker object
            # For 24h timeframe, be more lenient - include tickers even with missing data
            # as long as we have basic info (symbol, price, or change_pct)
            if timeframe == "24h" and price == 0.0 and timeframe_return == 0.0:
                # For 24h, if we have no price data, still try to include if we have mentions
                logger.debug(f"24h: {symbol} has no price data, but including due to mentions")
            
            ticker_obj = Ticker(
                symbol=symbol,
                company_name=company_name,
                price=Decimal(str(round(price, 2))) if price > 0 else Decimal("0"),
                change_pct=Decimal(str(round(timeframe_return, 2))),
                market_cap=Decimal(str(int(market_cap))) if market_cap > 0 else None,
                ragard_score=ragard_score,  # Can be None now
                risk_level=risk_level,
            )
            return ticker_obj
            
        except Exception as e:
            # Skip tickers that fail to fetch - don't create minimal tickers as it causes issues
            logger.debug(f"Error fetching data for {symbol}: {e}")
            return None
    
    # Process all tickers in parallel (but limit concurrency to avoid overwhelming APIs)
    # Use semaphore to limit concurrent Regard Score calculations
    # Reduce concurrency if we have many candidates to avoid timeout
    max_concurrent = min(5, max(2, max_symbols // 2))  # Scale down for large batches
    semaphore = asyncio.Semaphore(max_concurrent)
    logger.info(f"Processing {len(candidate_tickers)} tickers with max {max_concurrent} concurrent operations")
    
    async def process_with_semaphore(symbol: str):
        async with semaphore:
            return await process_ticker(symbol)
    
    tasks = [process_with_semaphore(symbol) for symbol in candidate_tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    for i, result in enumerate(results):
        if isinstance(result, Ticker):
            trending_tickers.append(result)
        elif isinstance(result, Exception):
            symbol = candidate_tickers[i] if i < len(candidate_tickers) else "unknown"
            logger.debug(f"Error processing ticker {symbol}: {result}")
    
    logger.info(f"Successfully processed {len(trending_tickers)} out of {len(candidate_tickers)} candidate tickers")
    
    # Step 6: Sort by timeframe-specific trending metrics (NOT Regard Score)
    # Regard Score is timeframe-independent and should NOT be used for sorting
    # Instead, sort by a combination of mentions, price change, and volume for the selected timeframe
    def get_trending_score(t: Ticker) -> float:
        # Find the ticker's stats for this timeframe
        stats = ticker_stats.get(t.symbol, {})
        mention_count = stats.get("mention_count", 0)
        
        # Combine mentions and price change for trending ranking
        # Higher mentions + bigger moves = more trending
        price_factor = abs(float(t.change_pct)) / 100.0  # Normalize price change
        trending_score = mention_count * 10 + price_factor * 100
        return trending_score
    
    trending_tickers.sort(key=get_trending_score, reverse=True)
    
    result = trending_tickers[:max_symbols]
    logger.info(f"Returning {len(result)} trending tickers for timeframe {timeframe}")
    
    # If we have very few results for 24h, log a warning
    if timeframe == "24h" and len(result) < 3:
        logger.warning(
            f"Only {len(result)} tickers returned for 24h timeframe. "
            f"This may indicate: (1) insufficient Reddit activity, "
            f"(2) ticker processing errors, or (3) Reddit API issues."
        )
    
    return result

