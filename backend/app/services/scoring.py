"""Ragard score calculation logic.

This module provides a compatibility wrapper for the centralized scoring system.
The real scoring logic is in app.scoring.regard_score_centralized.
"""
import logging
from app.models.ticker import TickerMetrics
from app.scoring.regard_score_centralized import get_regard_score_for_symbol

logger = logging.getLogger(__name__)


async def calculate_ragard_score(ticker: TickerMetrics) -> int | None:
    """Calculate Ragard score for a ticker (0-100).
    
    Higher score = more degenerate / meme potential
    Lower score = more respectable / safe
    
    This function uses the centralized scoring system.
    """
    try:
        result = await get_regard_score_for_symbol(ticker.symbol)
        score = result.get('regard_score')
        if score is not None:
            return int(score)
        # No fallback to placeholder - return None if scoring fails
        logger.warning(f"Regard score calculation returned None for {ticker.symbol}")
        return None
    except Exception as e:
        logger.error(f"Error calculating regard score for {ticker.symbol}: {e}", exc_info=True)
        # No fallback to placeholder - return None on error
        return None


def get_ragard_label(score: int) -> str:
    """Get a label based on Ragard score."""
    if score >= 80:
        return "Certified Degen"
    elif score >= 60:
        return "Respectable Trash"
    elif score >= 40:
        return "No Go Zone"
    else:
        return "Boring but Safe"


