"""Reddit author analysis service."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncpraw
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory cache for author analysis
_author_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
CACHE_TTL_MINUTES = 60  # 60 minutes TTL


def _get_reddit_client() -> Optional[asyncpraw.Reddit]:
    """Get Reddit client for fetching author history."""
    client_id = getattr(settings, 'REDDIT_CLIENT_ID', None)
    client_secret = getattr(settings, 'REDDIT_CLIENT_SECRET', None)
    user_agent = getattr(settings, 'REDDIT_USER_AGENT', 'Ragard/1.0 (Stock Analysis Bot)')
    
    if not client_id or not client_secret:
        logger.debug("Reddit credentials not set, cannot fetch author history")
        return None
    
    try:
        reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        return reddit
    except Exception as e:
        logger.warning(f"Error initializing Reddit client for author service: {e}")
        return None


async def fetch_author_post_history(username: str, limit: int = 20) -> list[dict]:
    """
    Fetch recent Reddit post history for a given username.
    
    Args:
        username: Reddit username (without 'u/' prefix)
        limit: Maximum number of posts to fetch
    
    Returns:
        List of post dicts with subreddit, title, score, created_at, url
        Returns empty list if API fails or credentials not set
    """
    # Clean username (remove 'u/' prefix if present)
    username = username.replace('u/', '').strip()
    
    if not username or username.lower() in ['[deleted]', 'deleted', '']:
        return []
    
    reddit = _get_reddit_client()
    if not reddit:
        return []
    
    posts = []
    try:
        redditor = await reddit.redditor(username)
        
        # Fetch recent submissions
        async for submission in redditor.submissions.new(limit=limit):
            try:
                post_data = {
                    "subreddit": str(submission.subreddit),
                    "title": submission.title,
                    "score": submission.score,
                    "created_at": datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                    "url": f"https://www.reddit.com{submission.permalink}",
                }
                posts.append(post_data)
            except Exception as e:
                logger.debug(f"Error processing submission for {username}: {e}")
                continue
        
        await reddit.close()
        
    except asyncpraw.exceptions.NotFound:
        logger.debug(f"Redditor {username} not found")
        await reddit.close()
        return []
    except Exception as e:
        # Log at debug level (expected when Reddit API is unavailable)
        logger.debug(f"Error fetching post history for {username}: {e}")
        try:
            await reddit.close()
        except:
            pass
        return []
    
    return posts


async def build_author_analysis_payload(username: str) -> Optional[Dict[str, Any]]:
    """
    Build payload for AI author analysis.
    
    Args:
        username: Reddit username
    
    Returns:
        Dict with username, posts, and summary stats, or None if no history
    """
    posts = await fetch_author_post_history(username, limit=20)
    
    if not posts:
        return None
    
    # Calculate summary stats
    subreddit_counts = {}
    total_score = 0
    for post in posts:
        subreddit = post.get("subreddit", "unknown")
        subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        total_score += post.get("score", 0)
    
    avg_score = total_score / len(posts) if posts else 0
    
    # Condense posts for AI payload
    condensed_posts = []
    for post in posts[:20]:  # Limit to 20 most recent
        condensed_posts.append({
            "subreddit": post.get("subreddit"),
            "title": post.get("title", "")[:200],  # Truncate long titles
            "score": post.get("score", 0),
        })
    
    return {
        "username": username,
        "posts": condensed_posts,
        "total_posts": len(posts),
        "avg_score": round(avg_score, 1),
        "top_subreddits": dict(sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
    }


def _get_cached_author_analysis(username: str) -> Optional[Dict[str, Any]]:
    """Get cached author analysis if not expired."""
    cache_key = username.lower()
    if cache_key not in _author_cache:
        return None
    
    cached_time, cached_value = _author_cache[cache_key]
    if (datetime.now() - cached_time).total_seconds() > (CACHE_TTL_MINUTES * 60):
        # Expired, remove from cache
        del _author_cache[cache_key]
        return None
    
    return cached_value


def _set_cached_author_analysis(username: str, value: Dict[str, Any]) -> None:
    """Cache author analysis."""
    cache_key = username.lower()
    _author_cache[cache_key] = (datetime.now(), value)


async def get_or_generate_author_analysis(username: str) -> Optional[Dict[str, Any]]:
    """
    Get author analysis (cached or generate new).
    
    Args:
        username: Reddit username
    
    Returns:
        Dict with author_regard_score, trust_level, summary, or None if unavailable
    """
    if not username or username.lower() in ['[deleted]', 'deleted', '']:
        return None
    
    # Check cache
    cached = _get_cached_author_analysis(username)
    if cached:
        logger.debug(f"Using cached author analysis for {username}")
        return cached
    
    # Build payload
    payload = await build_author_analysis_payload(username)
    if not payload:
        return None
    
    # Generate AI analysis
    try:
        from app.services.ai_client import generate_author_analysis_ai
        ai_result = await generate_author_analysis_ai(payload)
        
        # Compute data-based fallback if AI fails
        fallback_author_score = _compute_fallback_author_score(payload)
        
        if ai_result:
            # Use AI score if valid, otherwise use fallback
            ai_author_score = ai_result.get("author_regard_score")
            if ai_author_score is not None:
                try:
                    ai_score = int(ai_author_score)
                    if 0 <= ai_score <= 100:
                        final_author_score = ai_score
                    else:
                        final_author_score = fallback_author_score
                except (ValueError, TypeError):
                    final_author_score = fallback_author_score
            else:
                final_author_score = fallback_author_score
            
            result = {
                "author": f"u/{username}",
                "author_regard_score": final_author_score,
                "trust_level": ai_result.get("trust_level"),
                "summary": ai_result.get("summary"),
            }
            
            # Cache result
            _set_cached_author_analysis(username, result)
            return result
        else:
            # AI failed, use fallback
            return {
                "author": f"u/{username}",
                "author_regard_score": fallback_author_score,
                "trust_level": "medium",
                "summary": None,
            }
    except Exception as e:
        logger.warning(f"Error generating author analysis for {username}: {e}")
        # Return fallback on error
        fallback_author_score = _compute_fallback_author_score(payload)
        return {
            "author": f"u/{username}",
            "author_regard_score": fallback_author_score,
            "trust_level": "medium",
            "summary": None,
        }


def _compute_fallback_author_score(payload: Dict[str, Any]) -> int:
    """
    Compute data-based fallback author regard score.
    
    Uses:
    - Subreddit composition (more WSB/pennystocks = more degen)
    - Post frequency in high-degen subs
    
    Returns deterministic score (0-100) based on actual data, not hardcoded constants.
    """
    top_subreddits = payload.get("top_subreddits", {})
    
    # High-degen subreddits
    high_degen_subs = {
        "wallstreetbets": 30,
        "pennystocks": 25,
        "options": 20,
        "shortsqueeze": 25,
    }
    
    # Medium-degen subreddits
    medium_degen_subs = {
        "stockmarket": 10,
        "stocks": 5,
        "investing": 0,
    }
    
    base_score = 20  # Conservative base
    
    # Calculate weighted score based on subreddit activity
    total_posts = payload.get("total_posts", 0)
    if total_posts > 0:
        degen_points = 0
        for subreddit, count in top_subreddits.items():
            subreddit_lower = subreddit.lower()
            if subreddit_lower in high_degen_subs:
                weight = count / total_posts
                degen_points += high_degen_subs[subreddit_lower] * weight
            elif subreddit_lower in medium_degen_subs:
                weight = count / total_posts
                degen_points += medium_degen_subs[subreddit_lower] * weight
        
        base_score += int(degen_points)
    
    # Clamp to 0-100
    return max(0, min(100, base_score))

