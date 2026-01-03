"""Reddit post ingestion using Async PRAW (Python Reddit API Wrapper)."""
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncpraw
from app.narratives.config import TimeframeKey
from app.core.config import settings

# Subreddits to monitor
REDDIT_SUBREDDITS = [
    "wallstreetbets",
    "pennystocks",
    "options",
    "shortsqueeze",
    "stocks",
    "stockmarket",
]


@dataclass
class RedditPost:
    """Represents a Reddit post."""
    id: str
    subreddit: str
    title: str
    selftext: str | None
    created_at: datetime


def _get_timeframe_delta(timeframe: TimeframeKey) -> timedelta:
    """Convert timeframe to timedelta."""
    if timeframe == "24h":
        return timedelta(days=1)
    elif timeframe == "7d":
        return timedelta(days=7)
    elif timeframe == "30d":
        return timedelta(days=30)
    else:
        return timedelta(days=1)


def _get_reddit_client() -> asyncpraw.Reddit:
    """
    Create and return an Async PRAW Reddit client.
    
    Requires Reddit API credentials in environment variables:
    - REDDIT_CLIENT_ID: Your Reddit application client ID
    - REDDIT_CLIENT_SECRET: Your Reddit application client secret
    - REDDIT_USER_AGENT: User agent string (e.g., "Ragard/1.0 by YourUsername")
    
    Optional (for authenticated access):
    - REDDIT_USERNAME: Reddit username
    - REDDIT_PASSWORD: Reddit password
    
    To get credentials:
    1. Go to https://www.reddit.com/prefs/apps
    2. Click "create another app..." or "create app"
    3. Choose "script" as the app type
    4. Copy the client ID (under the app name) and secret
    5. Set user_agent to something like: "Ragard/1.0 by YourUsername"
    """
    # Check if credentials are provided
    client_id = getattr(settings, 'REDDIT_CLIENT_ID', None)
    client_secret = getattr(settings, 'REDDIT_CLIENT_SECRET', None)
    user_agent = getattr(settings, 'REDDIT_USER_AGENT', 'Ragard/1.0 (Stock Analysis Bot)')
    
    # If credentials are not provided, use read-only mode (limited rate limits)
    if not client_id or not client_secret:
        # Read-only mode - no auth required, but has stricter rate limits
        # Note: Read-only mode may not work reliably for fetching posts
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Reddit API credentials not configured. Attempting read-only mode. "
            "For better reliability, set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env. "
            "See backend/REDDIT_SETUP.md for instructions."
        )
        reddit = asyncpraw.Reddit(
            client_id=None,
            client_secret=None,
            user_agent=user_agent,
        )
    else:
        # Authenticated mode - better rate limits
        username = getattr(settings, 'REDDIT_USERNAME', None)
        password = getattr(settings, 'REDDIT_PASSWORD', None)
        
        if username and password:
            # Authenticated user access
            reddit = asyncpraw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent,
            )
        else:
            # Application-only (OAuth) access - better than read-only
            reddit = asyncpraw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
    
    return reddit


async def get_recent_reddit_posts(
    subreddits: list[str],
    timeframe: TimeframeKey
) -> list[RedditPost]:
    """
    Fetch recent Reddit posts from specified subreddits within the timeframe using Async PRAW.
    
    Args:
        subreddits: List of subreddit names (without 'r/')
        timeframe: Timeframe key (24h, 7d, 30d)
    
    Returns:
        List of RedditPost objects (empty list if Reddit client fails)
    """
    posts: list[RedditPost] = []
    now = datetime.utcnow()
    cutoff_time = now - _get_timeframe_delta(timeframe)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Fetching Reddit posts for timeframe {timeframe}: cutoff_time={cutoff_time}, now={now}")
    
    reddit = None
    try:
        reddit = _get_reddit_client()
        
        # Check if we're in read-only mode
        client_id = getattr(settings, 'REDDIT_CLIENT_ID', None)
        client_secret = getattr(settings, 'REDDIT_CLIENT_SECRET', None)
        if not client_id or not client_secret:
            logger.warning(
                "Reddit API credentials not configured. Using read-only mode which has strict rate limits. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env for better performance. "
                "See backend/REDDIT_SETUP.md for instructions."
            )
        
        for subreddit_name in subreddits:
            try:
                subreddit = await reddit.subreddit(subreddit_name)
                subreddit_posts_count = 0
                
                # Fetch new posts (limit can be up to 100 per request)
                # Async PRAW handles rate limiting automatically
                async for submission in subreddit.new(limit=100):
                    # Convert Async PRAW submission to RedditPost
                    created_at = datetime.utcfromtimestamp(submission.created_utc)
                    
                    # Only include posts within timeframe
                    if created_at >= cutoff_time:
                        post = RedditPost(
                            id=submission.id,
                            subreddit=subreddit_name,
                            title=submission.title,
                            selftext=submission.selftext if submission.selftext else None,
                            created_at=created_at,
                        )
                        posts.append(post)
                        subreddit_posts_count += 1
                    else:
                        # Posts are sorted by time, so we can break early
                        # (older posts won't be in timeframe)
                        break
                
                logger.debug(f"Found {subreddit_posts_count} posts in r/{subreddit_name} for timeframe {timeframe}")
                        
            except Exception as e:
                # Log error at warning level so it's visible
                logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
                logger.debug(f"Full error details for r/{subreddit_name}:", exc_info=True)
                continue
                
    except Exception as e:
        # Log initialization errors at warning level so they're visible
        logger.warning(f"Error initializing Reddit client: {e}")
        logger.warning("Make sure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set in .env")
        logger.warning("See backend/REDDIT_SETUP.md for setup instructions")
        logger.debug("Full error details:", exc_info=True)
        # Return empty list rather than crashing
        return []
    finally:
        # Always close the Reddit client to clean up connections, even if errors occurred
        if reddit is not None:
            try:
                await reddit.close()
            except Exception as e:
                logger.warning(f"Error closing Reddit client: {e}")
    
    # Sort by created_at descending (newest first)
    posts.sort(key=lambda p: p.created_at, reverse=True)
    
    return posts
