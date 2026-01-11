"""
Reddit post ingestion for Trending using app-only OAuth (production-safe).

Why this exists:
- PRAW often works locally but fails on cloud hosts (Railway) due to 401/403 from Reddit.
- Public endpoints like www.reddit.com/r/<sub>/new.json can also return 403 from datacenter IPs.
- This module uses OAuth + oauth.reddit.com listing endpoints, which is the most reliable server-side approach.

Env vars required:
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT  (e.g. "web:ragardai:v1.0.0 (by /u/Sahm_87)")
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import base64
import json
import logging
import time
import urllib.parse
import urllib.request

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
    """Convert timeframe to timedelta."""
    if timeframe == "24h":
        return timedelta(days=1)
    elif timeframe == "7d":
        return timedelta(days=7)
    elif timeframe == "30d":
        return timedelta(days=30)
    else:
        return timedelta(days=1)


def _get_user_agent() -> str:
    ua = getattr(settings, "REDDIT_USER_AGENT", None)
    return ua or "web:ragardai:v1.0.0 (by /u/Sahm_87)"


# Cached OAuth token (app-only)
_OAUTH_TOKEN: Optional[str] = None
_OAUTH_EXPIRES_AT: int = 0  # epoch seconds


def _require_reddit_creds() -> tuple[str, str]:
    client_id = getattr(settings, "REDDIT_CLIENT_ID", None)
    client_secret = getattr(settings, "REDDIT_CLIENT_SECRET", None)

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Reddit credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
        )

    return str(client_id), str(client_secret)


def _request_oauth_token_sync() -> str:
    """
    Get app-only OAuth token using client_credentials.
    Uses standard library urllib (no extra deps).
    """
    global _OAUTH_TOKEN, _OAUTH_EXPIRES_AT

    now = int(time.time())
    if _OAUTH_TOKEN and now < (_OAUTH_EXPIRES_AT - 60):
        return _OAUTH_TOKEN

    client_id, client_secret = _require_reddit_creds()
    user_agent = _get_user_agent()

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")

    data = urllib.parse.urlencode(
        {"grant_type": "client_credentials", "scope": "read"}
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Basic {basic}",
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            if resp.status != 200:
                raise RuntimeError(f"token status={resp.status} body={body[:200]}")
            payload = json.loads(body)

        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))

        if not token:
            raise RuntimeError(f"token missing in response: {str(payload)[:200]}")

        _OAUTH_TOKEN = token
        _OAUTH_EXPIRES_AT = now + expires_in
        return token

    except Exception as e:
        # Clear token cache on failure
        _OAUTH_TOKEN = None
        _OAUTH_EXPIRES_AT = 0
        raise RuntimeError(f"Failed to obtain Reddit OAuth token: {e}") from e


def _fetch_subreddit_new_sync(
    subreddit_name: str,
    cutoff_time: datetime,
    limit: int = 100,
) -> list[RedditPost]:
    """
    Fetch newest posts from a subreddit via oauth.reddit.com using the app-only token.
    """
    token = _request_oauth_token_sync()
    user_agent = _get_user_agent()

    qs = urllib.parse.urlencode({"limit": str(limit), "raw_json": "1"})
    url = f"https://oauth.reddit.com/r/{subreddit_name}/new?{qs}"

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")

            # If token expired or rejected, refresh once and retry
            if resp.status == 401:
                global _OAUTH_TOKEN, _OAUTH_EXPIRES_AT
                _OAUTH_TOKEN = None
                _OAUTH_EXPIRES_AT = 0
                token = _request_oauth_token_sync()

                req2 = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": user_agent,
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req2, timeout=20) as resp2:
                    body = resp2.read().decode("utf-8")
                    if resp2.status != 200:
                        raise RuntimeError(f"listing status={resp2.status} body={body[:200]}")
            elif resp.status != 200:
                raise RuntimeError(f"listing status={resp.status} body={body[:200]}")

            payload = json.loads(body)

        children = (payload.get("data") or {}).get("children") or []

        posts: list[RedditPost] = []
        for child in children:
            p = (child or {}).get("data") or {}

            created_utc = p.get("created_utc")
            if not created_utc:
                continue

            created_at = datetime.utcfromtimestamp(float(created_utc))
            if created_at < cutoff_time:
                break  # newest-first

            title = p.get("title") or ""
            selftext = p.get("selftext") or None

            posts.append(
                RedditPost(
                    id=str(p.get("id") or ""),
                    subreddit=subreddit_name,
                    title=title,
                    selftext=selftext if selftext else None,
                    created_at=created_at,
                )
            )

        return posts

    except Exception as e:
        raise RuntimeError(f"OAuth listing fetch failed for r/{subreddit_name}: {e}") from e


async def get_recent_reddit_posts(
    subreddits: list[str],
    timeframe: TimeframeKey,
) -> list[RedditPost]:
    """
    Fetch recent Reddit posts from specified subreddits within the timeframe.

    Uses app-only OAuth + oauth.reddit.com listings.
    Returns empty list if Reddit blocks the host/IP.
    """
    posts: list[RedditPost] = []
    now = datetime.utcnow()
    cutoff_time = now - _get_timeframe_delta(timeframe)

    logger.info(f"Fetching Reddit posts for timeframe: {timeframe}")

    # Fetch sequentially to be gentle; if you want faster, we can gather() with a small semaphore.
    for subreddit_name in subreddits:
        try:
            subreddit_posts = await asyncio.to_thread(
                _fetch_subreddit_new_sync, subreddit_name, cutoff_time, 100
            )
            posts.extend(subreddit_posts)
            logger.debug(f"Fetched {len(subreddit_posts)} posts from r/{subreddit_name}")
        except Exception as e:
            logger.warning(str(e))
            continue

    posts.sort(key=lambda p: p.created_at, reverse=True)
    logger.info(f"Fetched {len(posts)} Reddit posts for timeframe {timeframe}")
    return posts
