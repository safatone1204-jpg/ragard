"""Helper to fetch historical Regard Scores for trades."""
import logging
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db

logger = logging.getLogger(__name__)


async def get_regard_score_at_date(ticker: str, date: datetime) -> Optional[float]:
    """
    Get the Regard Score for a ticker at or near a specific date.
    Looks for the closest score within 7 days of the target date.
    
    Args:
        ticker: Ticker symbol
        date: Target date
        
    Returns:
        Regard Score (0-100) or None if not found
    """
    try:
        db = await get_db()
        
        # Look for scores within 7 days of the target date
        date_start = (date - timedelta(days=7)).isoformat()
        date_end = (date + timedelta(days=7)).isoformat()
        target_iso = date.isoformat()
        
        # Query for the closest score
        cursor = await db.execute("""
            SELECT 
                score_rounded,
                timestamp_utc,
                ABS(JULIANDAY(timestamp_utc) - JULIANDAY(?)) as days_diff
            FROM regard_history
            WHERE ticker = ? 
                AND timestamp_utc >= ?
                AND timestamp_utc <= ?
            ORDER BY days_diff ASC
            LIMIT 1
        """, (target_iso, ticker.upper(), date_start, date_end))
        
        try:
            row = await cursor.fetchone()
            
            if row and row["score_rounded"] is not None:
                return float(row["score_rounded"])
            
            return None
        finally:
            # Always close cursor to prevent resource leaks
            await cursor.close()
        
    except Exception as e:
        logger.warning(f"Could not fetch Regard Score for {ticker} at {date}: {e}")
        return None


async def enrich_trades_with_regard_scores(trades: list) -> list:
    """
    Enrich a list of ParsedTrade objects with Regard Scores at entry/exit.
    Uses concurrent fetching for better performance.
    
    Args:
        trades: List of ParsedTrade objects
        
    Returns:
        Same list with regard_score_at_entry and regard_score_at_exit populated
    """
    import asyncio
    
    async def enrich_single_trade(trade):
        """Enrich a single trade with Regard Scores."""
        # Check if we need to fetch scores
        needs_entry = not hasattr(trade, 'regard_score_at_entry') or trade.regard_score_at_entry is None
        needs_exit = not hasattr(trade, 'regard_score_at_exit') or trade.regard_score_at_exit is None
        
        # Fetch both scores concurrently if needed
        if needs_entry and needs_exit:
            entry_score, exit_score = await asyncio.gather(
                get_regard_score_at_date(trade.ticker, trade.entry_time),
                get_regard_score_at_date(trade.ticker, trade.exit_time)
            )
            trade.regard_score_at_entry = entry_score
            trade.regard_score_at_exit = exit_score
        elif needs_entry:
            trade.regard_score_at_entry = await get_regard_score_at_date(trade.ticker, trade.entry_time)
        elif needs_exit:
            trade.regard_score_at_exit = await get_regard_score_at_date(trade.ticker, trade.exit_time)
        
        return trade
    
    # Process trades in batches to avoid overwhelming the database
    batch_size = 20  # Process 20 trades at a time
    enriched_trades = []
    
    for i in range(0, len(trades), batch_size):
        batch = trades[i:i + batch_size]
        batch_results = await asyncio.gather(*[enrich_single_trade(trade) for trade in batch])
        enriched_trades.extend(batch_results)
        logger.debug(f"Enriched batch {i//batch_size + 1}: {len(batch)} trades")
    
    return enriched_trades

