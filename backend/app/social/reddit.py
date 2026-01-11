"""Reddit post ingestion using Async PRAW with a production-safe fallback (public JSON)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Optional

import asyncpraw

from app.narratives.config import TimeframeKey
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    if timeframe == "24h":
        return timedelta(days=1)
    if timeframe == "7d":
        return timedelta(days=7)
    if timeframe == "30d":
        return timedelta(days=30)
    return timedelta(days=1)


def _get_user_agent() -> str:
    return getattr(
        settings,
        "REDDIT_USER_AGENT",
        "web:ragardai:v1.0.0 (by /u/Sahm_87)",
    )


def _get_reddit_client() -> asyncpraw.Reddit:
    """
    Async PRAW client.

    NOTE: Reddit OAuth may fail on cloud hosts (Railway) even if it works locally.
    We will fall back to public JSON if we see 401s.
    """
    client_id = getattr(settings, "REDDIT_CLIENT_ID", None)
    client_secret = getattr(settings, "REDDIT_CLIENT_SECRET", None)
    user_agent = _get_user_agent()

    if not client_id or not client_secret:
        logger.warning("Reddit client_id/secret missing; PRAW will not be used.")
        # Return a "read-only" client anyway, but it's likely not useful.
        return asyncpraw.Reddit(client_id=None, client_secret=None, user_agent=user_agent)

    # IMPORTANT: Do NOT pass username/password in production.
    # It frequently gets rejected from datacenter IPs.
    reddit = asyncpraw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    reddit.read_only = True
    return reddit


async def _fetch_subreddit_public_json(
    subreddit_name: str,
    cutoff_time: datetime,
    limit: int = 100,
) -> list[RedditPost]:
    """
    Production-safe fallback: pull from Reddit's public JSON endpoint (no OAuth).
    Endpoint: https://www.reddit.com/r/<sub>/new.json

    This avoids the common “works locally, 401 in cloud” OAuth problem.
    """
    import httpx  # ensure httpx is installed in backend deps

    url = f"https://www.reddit.com/r/{subreddit_name}/new.json"
    params = {"limit": str(limit), "raw_json": "1"}

    headers = {
        "User-Agent": _get_user_agent(),
        "Accept": "application/json",
    }

    # small retry for rate limits / transient errors
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, params=params, headers=headers)

            if resp.status_code == 429:
                # rate limited; backoff
                wait_s = 2 ** attempt
                logger.warning(f"Reddit public JSON 429 for r/{subreddit_name}. Backing off {wait_s}s.")
                await asyncio.sleep(wait_s)
                continue

            if resp.status_code != 200:
                raise RuntimeError(f"public JSON status={resp.status_code} body={resp.text[:200]}")

            data = resp.json()
            children = (data.get("data") or {}).get("children") or []

            posts: list[RedditPost] = []
            for child in children:
                p = (child or {}).get("data") or {}
                created_utc = p.get("created_utc")
                if not created_utc:
                    continue

                created_at = datetime.utcfromtimestamp(created_utc)
                if created_at < cutoff_time:
                    break  # results are newest-first

                title = p.get("title") or ""
                selftext = p.get("selftext") or None

                posts.append(
                    RedditPost(
                        id=str(p.get("id") or ""),
                        subreddit=subreddit_name,
                        title=title,
                        selftext=selftext,
                        created_at=created_at,
                    )
                )

            return posts

        except Exception as e:
            if attempt == 2:
                logger.warning(f"Public JSON fetch failed for r/{subreddit_name}: {e}")
                return []
            await asyncio.sleep(1 + attempt)

    return []


async def get_recent_reddit_posts(
    subreddits: list[str],
    timeframe: TimeframeKey,
) -> list[RedditPost]:
    posts: list[RedditPost] = []
    now = datetime.utcnow()
    cutoff_time = now - _get_timeframe_delta(timeframe)

    logger.info(f"Fetching Reddit posts for timeframe: {timeframe}")

    # Try PRAW first, but if we see 401 anywhere, switch to public JSON for all.
    use_public_only = False
    reddit: Optional[asyncpraw.Reddit] = None

    try:
        reddit = _get_reddit_client()

        for subreddit_name in subreddits:
            if use_public_only:
                posts.extend(await _fetch_subreddit_public_json(subreddit_name, cutoff_time))
                continue

            try:
                subreddit = await reddit.subreddit(subreddit_name)
                count = 0

                async for submission in subreddit.new(limit=100):
                    created_at = datetime.utcfromtimestamp(submission.created_utc)
                    if created_at < cutoff_time:
                        break

                    posts.append(
                        RedditPost(
                            id=submission.id,
                            subreddit=subreddit_name,
                            title=submission.title,
                            selftext=submission.selftext if submission.selftext else None,
                            created_at=created_at,
                        )
                    )
                    count += 1

                logger.debug(f"Found {count} posts in r/{subreddit_name} via PRAW for {timeframe}")

            except Exception as e:
                msg = str(e).lower()
                # AsyncPRAW often reports 401 like: "received 401 HTTP response"
                if "401" in msg or "unauthorized" in msg:
                    logger.warning(
                        f"PRAW got 401 in production for r/{subreddit_name}. "
                        f"Switching to public JSON fallback for all subreddits."
                    )
                    use_public_only = True
                    # fetch this subreddit via fallback too
                    posts.extend(await _fetch_subreddit_public_json(subreddit_name, cutoff_time))
                else:
                    logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
                    continue

    except Exception as e:
        logger.warning(f"Error initializing Reddit client: {e}. Using public JSON fallback.")
        use_public_only = True
        for subreddit_name in subreddits:
            posts.extend(await _fetch_subreddit_public_json(subreddit_name, cutoff_time))

    finally:
        if reddit is not None:
            try:
                await reddit.close()
            except Exception:
                pass

    posts.sort(key=lambda p: p.created_at, reverse=True)
    logger.info(f"Fetched {len(posts)} Reddit posts for timeframe {timeframe}")
    return posts
