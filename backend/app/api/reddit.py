"""Reddit-related API endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Query
from app.services.reddit_author_service import get_or_generate_author_analysis

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/reddit",
    tags=["reddit"],
)


@router.get("/author-analysis")
async def get_author_analysis(
    author: str = Query(..., description="Reddit username (without 'u/' prefix)")
):
    """
    Get author analysis for a Reddit user.
    
    Returns author_regard_score, trust_level, and summary based on their posting history.
    Uses the same service as the extension endpoint to ensure consistency.
    
    Args:
        author: Reddit username (e.g., "No-Plenty-1470" or "u/No-Plenty-1470")
    
    Returns:
        Dict with author_regard_score, trust_level, summary, or null fields if unavailable
    """
    if not author or author.lower() in ['[deleted]', 'deleted', '']:
        return {
            "author": None,
            "author_regard_score": None,
            "trust_level": None,
            "summary": None,
        }
    
    # Clean username (remove 'u/' prefix if present)
    author_username = author.replace('u/', '').strip()
    
    try:
        author_analysis = await get_or_generate_author_analysis(author_username)
        
        if author_analysis:
            return author_analysis
        else:
            # Return null fields if analysis unavailable
            return {
                "author": f"u/{author_username}",
                "author_regard_score": None,
                "trust_level": None,
                "summary": None,
            }
    except Exception as e:
        logger.error(f"Error fetching author analysis for {author_username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching author analysis: {str(e)}"
        )

