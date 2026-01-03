"""Regard history API endpoint."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging

from app.core.database import get_db
from app.models.regard_history import RegardHistoryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["regard-history"])


@router.get("/regard-history", response_model=list[RegardHistoryResponse])
async def get_regard_history(
    ticker: str = Query(..., description="Ticker symbol"),
    days: int = Query(default=7, ge=1, le=365, description="Number of days to retrieve")
):
    """
    Get historical Regard score records for a ticker.
    Returns one score per day (the latest record for each day).
    
    Args:
        ticker: Ticker symbol (required)
        days: Number of days to retrieve (default: 7, max: 365)
    
    Returns:
        List of Regard history records (one per day) sorted by timestamp_utc ascending
    """
    try:
        db = await get_db()
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        # Query database - get all records, then group by day in Python
        cursor = await db.execute("""
            SELECT 
                timestamp_utc,
                score_raw,
                score_rounded,
                scoring_mode,
                ai_success,
                total_posts,
                price_at_snapshot,
                change_24h_pct,
                volume_24h,
                market_cap,
                model_version,
                scoring_version
            FROM regard_history
            WHERE ticker = ? AND timestamp_utc >= ?
            ORDER BY timestamp_utc ASC
        """, (ticker.upper(), cutoff_iso))
        
        try:
            rows = await cursor.fetchall()
            
            # Group by day and keep only the latest record for each day
            # Use UTC date to ensure consistent grouping regardless of timezone
            daily_records = {}
            
            for row in rows:
                # Parse timestamp to extract date (always use UTC)
                timestamp_str = row["timestamp_utc"]
                try:
                    # Parse ISO timestamp and normalize to UTC
                    if "T" in timestamp_str:
                        # Handle ISO format with or without timezone
                        if timestamp_str.endswith("Z"):
                            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        elif "+" in timestamp_str or timestamp_str.count("-") > 2:
                            # Has timezone info
                            dt = datetime.fromisoformat(timestamp_str)
                        else:
                            # No timezone, assume UTC
                            dt = datetime.fromisoformat(timestamp_str + "+00:00")
                    else:
                        # Format: "YYYY-MM-DD HH:MM:SS" - assume UTC
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        # Make it timezone-aware (UTC)
                        dt = dt.replace(tzinfo=timezone.utc)
                    
                    # Convert to UTC if not already
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    
                    # Get date key (YYYY-MM-DD) in UTC
                    date_key = dt.date().isoformat()
                    
                    # Keep only the latest record for each date
                    if date_key not in daily_records:
                        daily_records[date_key] = {
                            "timestamp_utc": timestamp_str,
                            "timestamp_dt": dt,
                            "score_raw": row["score_raw"],
                            "score_rounded": row["score_rounded"],
                            "scoring_mode": row["scoring_mode"],
                            "ai_success": row["ai_success"],
                            "total_posts": row["total_posts"],
                            "price_at_snapshot": row["price_at_snapshot"],
                            "change_24h_pct": row["change_24h_pct"],
                            "volume_24h": row["volume_24h"],
                            "market_cap": row["market_cap"],
                            "model_version": row["model_version"],
                            "scoring_version": row["scoring_version"],
                        }
                    else:
                        # If this timestamp is newer, replace the existing record
                        if dt > daily_records[date_key]["timestamp_dt"]:
                            daily_records[date_key] = {
                                "timestamp_utc": timestamp_str,
                                "timestamp_dt": dt,
                                "score_raw": row["score_raw"],
                                "score_rounded": row["score_rounded"],
                                "scoring_mode": row["scoring_mode"],
                                "ai_success": row["ai_success"],
                                "total_posts": row["total_posts"],
                                "price_at_snapshot": row["price_at_snapshot"],
                                "change_24h_pct": row["change_24h_pct"],
                                "volume_24h": row["volume_24h"],
                                "market_cap": row["market_cap"],
                                "model_version": row["model_version"],
                                "scoring_version": row["scoring_version"],
                            }
                except (ValueError, AttributeError) as e:
                    # If parsing fails, fall back to string-based date extraction
                    logger.warning(f"Could not parse timestamp {timestamp_str}: {e}")
                    # Extract just the date part (YYYY-MM-DD) from the string
                    date_key = timestamp_str.split("T")[0] if "T" in timestamp_str else timestamp_str.split(" ")[0]
                    # Ensure it's a valid date format (YYYY-MM-DD)
                    if len(date_key) >= 10:
                        date_key = date_key[:10]
                    
                    if date_key not in daily_records or timestamp_str > daily_records[date_key].get("timestamp_utc", ""):
                        daily_records[date_key] = {
                            "timestamp_utc": timestamp_str,
                            "score_raw": row["score_raw"],
                            "score_rounded": row["score_rounded"],
                            "scoring_mode": row["scoring_mode"],
                            "ai_success": row["ai_success"],
                            "total_posts": row["total_posts"],
                            "price_at_snapshot": row["price_at_snapshot"],
                            "change_24h_pct": row["change_24h_pct"],
                            "volume_24h": row["volume_24h"],
                            "market_cap": row["market_cap"],
                            "model_version": row["model_version"],
                            "scoring_version": row["scoring_version"],
                        }
            
            # Convert to response models, sorted by timestamp
            # Also add a final deduplication step to ensure no duplicates
            seen_dates = set()
            results = []
            for date_key in sorted(daily_records.keys()):
                # Final check: ensure we don't have duplicate dates
                if date_key in seen_dates:
                    logger.warning(f"Duplicate date key detected: {date_key}, skipping")
                    continue
                seen_dates.add(date_key)
                
                row = daily_records[date_key]
                results.append(RegardHistoryResponse(
                    timestamp_utc=row["timestamp_utc"],
                    score_raw=row["score_raw"],
                    score_rounded=row["score_rounded"],
                    scoring_mode=row["scoring_mode"],
                    ai_success=bool(row["ai_success"]),
                    total_posts=row["total_posts"],
                    price_at_snapshot=row["price_at_snapshot"],
                    change_24h_pct=row["change_24h_pct"],
                    volume_24h=row["volume_24h"],
                    market_cap=row["market_cap"],
                    model_version=row["model_version"],
                    scoring_version=row["scoring_version"],
                ))
            
            return results
        finally:
            # Always close cursor to prevent resource leaks
            await cursor.close()
        
    except Exception as e:
        logger.error(f"Error fetching Regard history for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching Regard history: {str(e)}")

