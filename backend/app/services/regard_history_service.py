"""Service for logging Regard score history."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import json
import pytz

from app.core.database import get_db
from app.scoring.config import SCORING_VERSION, AI_MODEL_VERSION, LOW_SAMPLE_SIZE_THRESHOLD

logger = logging.getLogger(__name__)

# Default timezone (UTC for consistency, but we'll also store local)
UTC_TZ = pytz.UTC
# For local time, use US Eastern (market timezone)
LOCAL_TZ = pytz.timezone("America/New_York")


async def log_regard_history(
    ticker: str,
    score_raw: Optional[float],
    score_rounded: Optional[int],
    scoring_mode: str,  # "ai" | "fallback" | "error"
    ai_success: bool,
    base_score: Optional[float] = None,
    ai_score: Optional[int] = None,
    market_data: Optional[Dict[str, Any]] = None,
    post_counts: Optional[Dict[str, int]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a Regard score snapshot to history.
    
    This is a fire-and-forget operation - errors are logged but don't affect the scoring response.
    
    Args:
        ticker: Ticker symbol
        score_raw: Raw score before rounding (float)
        score_rounded: Final rounded score (int)
        scoring_mode: "ai" | "fallback" | "error"
        ai_success: True if AI was successfully used
        base_score: Base data-driven score (optional)
        ai_score: AI overlay score (optional)
        market_data: Dict with price, change_24h_pct, volume_24h, market_cap (optional)
        post_counts: Dict with total_posts, posts_reddit, posts_twitter, etc. (optional)
        config_snapshot: Dict with scoring config weights (optional)
    """
    try:
        # Get current timestamps (timezone-aware)
        now_utc = datetime.now(UTC_TZ)
        now_local = datetime.now(LOCAL_TZ)
        
        # Convert to ISO format strings for storage
        timestamp_utc_str = now_utc.isoformat()
        timestamp_local_str = now_local.isoformat()
        
        # Extract market data
        price_at_snapshot = None
        change_24h_pct = None
        volume_24h = None
        market_cap = None
        
        if market_data:
            price_at_snapshot = market_data.get("price")
            change_24h_pct = market_data.get("change_24h_pct")
            volume_24h = market_data.get("volume_24h")
            market_cap = market_data.get("market_cap")
        
        # Extract post counts
        total_posts = 0
        posts_reddit = 0
        posts_twitter = 0
        posts_discord = 0
        posts_news = 0
        
        if post_counts:
            total_posts = post_counts.get("total_posts", 0)
            posts_reddit = post_counts.get("posts_reddit", 0)
            posts_twitter = post_counts.get("posts_twitter", 0)
            posts_discord = post_counts.get("posts_discord", 0)
            posts_news = post_counts.get("posts_news", 0)
        
        # Determine if low sample size
        low_sample_size = total_posts < LOW_SAMPLE_SIZE_THRESHOLD
        
        # Determine if weekend (Saturday or Sunday)
        is_weekend = now_local.weekday() >= 5
        
        # For now, is_holiday is False (can be enhanced later with holiday calendar)
        is_holiday = False
        
        # For now, has_data_gap is False (can be enhanced later)
        has_data_gap = False
        
        # Serialize config snapshot to JSON string
        config_snapshot_json = None
        if config_snapshot:
            try:
                config_snapshot_json = json.dumps(config_snapshot)
            except Exception as e:
                logger.warning(f"Error serializing config_snapshot: {e}")
        
        # Insert into database (with timeout to prevent hanging)
        import asyncio
        db = await get_db()
        
        # Use timeout to prevent hanging if database is slow
        try:
            await asyncio.wait_for(
                db.execute("""
            INSERT INTO regard_history (
                ticker, timestamp_utc, timestamp_local, window_label,
                score_raw, score_rounded, scoring_mode, ai_success,
                total_posts, posts_reddit, posts_twitter, posts_discord, posts_news,
                low_sample_size, is_weekend, is_holiday, has_data_gap,
                price_at_snapshot, change_24h_pct, volume_24h, market_cap,
                model_version, scoring_version, config_snapshot,
                forward_return_24h, forward_return_3d, forward_return_7d
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker.upper(),
            timestamp_utc_str,
            timestamp_local_str,
            "current",  # Regard score is timeframe-independent, so use "current"
            score_raw,
            score_rounded,
            scoring_mode,
            ai_success,
            total_posts,
            posts_reddit,
            posts_twitter,
            posts_discord,
            posts_news,
            low_sample_size,
            is_weekend,
            is_holiday,
            has_data_gap,
            price_at_snapshot,
            change_24h_pct,
            volume_24h,
            market_cap,
            AI_MODEL_VERSION,
            SCORING_VERSION,
            config_snapshot_json,
            None,  # forward_return_24h
            None,  # forward_return_3d
            None,  # forward_return_7d
        )),
                timeout=5.0
            )
            await asyncio.wait_for(db.commit(), timeout=2.0)
            logger.debug(f"Logged Regard history for {ticker}: score={score_rounded}, mode={scoring_mode}")
        except asyncio.TimeoutError:
            logger.warning(f"Database operation timed out for {ticker} history logging")
        except asyncio.CancelledError:
            # Task was cancelled during shutdown, this is expected
            logger.debug(f"History logging cancelled for {ticker} during shutdown")
            raise  # Re-raise to properly handle cancellation
        
    except Exception as e:
        # Log error but don't raise - this is fire-and-forget
        logger.error(f"Error logging Regard history for {ticker}: {e}", exc_info=True)

