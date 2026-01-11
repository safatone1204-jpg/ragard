"""
Reddit post ingestion for Trending via OAuth (no PRAW).

This is designed for the exact situation you're in:
- Works locally
- Fails on Railway with 401/403
- Need better diagnostics + more compatible OAuth flow for "personal use script"

Env vars used:
Required:
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT  (e.g. "web:ragardai:v1.0.0 (by /u/Sahm_87)")

Optional (recommended for script apps):
- REDDIT_USERNAME
- REDDIT_PASSWORD
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import asyncio
import base64
import json
import logging
import time
import urllib.parse
import urllib.request
import urllib.error

from app.narratives.config import TimeframeKey
from app.core.config import settings

logger = logging.getLogger(__name__)

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


def _ua() -> str:
    return getattr(settings, "REDDIT_USER_AGENT", None) or "web:ragardai:v1.0.0 (by /u/Sahm_87)"


def _require_creds() -> Tuple[str, str]:
    cid = getattr(settings, "REDDIT_CLIENT_ID", None)
    sec = getattr(settings, "REDDIT_CLIENT_SECRET", None)
    if not cid or not sec:
        raise RuntimeError("Missing REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET")
    return str(cid).strip(), str(sec).strip()


def _optional_userpass() -> Tuple[Optional[str], Optional[str]]:
    u = getattr(settings, "REDDIT_USERNAME", None)
    p = getattr(settings, "REDDIT_PASSWORD", None)
    u = str(u).strip() if u else None
    p = str(p) if p else None
    return u, p


# token cache
_TOKEN: Optional[str] = None
_TOKEN_EXPIRES_AT: int = 0


def _post_form(url: str, headers: Dict[str, str], data: Dict[str, str], timeout: int = 20) -> Tuple[int, str]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        # Important: read the response body; Reddit will tell us invalid_client/invalid_grant/etc.
        try:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception:
            return e.code, str(e)
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


def _get_token_sync() -> str:
    """
    Tries password grant first (best for 'script' apps),
    then falls back to client_credentials.

    Logs the Reddit error body so we can see invalid_client vs invalid_grant.
    """
    global _TOKEN, _TOKEN_EXPIRES_AT

    now = int(time.time())
    if _TOKEN and now < (_TOKEN_EXPIRES_AT - 60):
        return _TOKEN

    cid, sec = _require_creds()
    user_agent = _ua()
    basic = base64.b64encode(f"{cid}:{sec}".encode("utf-8")).decode("utf-8")

    token_url = "https://www.reddit.com/api/v1/access_token"
    common_headers = {
        "Authorization": f"Basic {basic}",
        "User-Agent": user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    # 1) password grant (script-friendly)
    username, password = _optional_userpass()
    if username and password:
        status, text = _post_form(
            token_url,
            headers=common_headers,
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "read",
            },
        )
        if status == 200:
            payload = json.loads(text)
            _TOKEN = payload.get("access_token")
            _TOKEN_EXPIRES_AT = now + int(payload.get("expires_in", 3600))
            if not _TOKEN:
                raise RuntimeError(f"Token response missing access_token: {str(payload)[:200]}")
            logger.info("Reddit OAuth token acquired using password grant.")
            return _TOKEN
        else:
            logger.warning(f"Reddit token (password grant) failed: status={status} body={text[:200]}")

    # 2) client_credentials (sometimes works, sometimes not, but try it)
    status, text = _post_form(
        token_url,
        headers=common_headers,
        data={
            "grant_type": "client_credentials",
            "scope": "read",
        },
    )
    if status == 200:
        payload = json.loads(text)
        _TOKEN = payload.get("access_token")
        _TOKEN_EXPIRES_AT = now + int(payload.get("expires_in", 3600))
        if not _TOKEN:
            raise RuntimeError(f"Token response missing access_token: {str(payload)[:200]}")
        logger.info("Reddit OAuth token acquired using client_credentials grant.")
        return _TOKEN

    logger.warning(f"Reddit token (client_credentials) failed: status={status} body={text[:200]}")
    raise RuntimeError("Failed to obtain Reddit OAuth token (see logs above for invalid_client/invalid_grant details).")


def _get_json(url: str, headers: Dict[str, str], timeout: int = 20) -> Tuple[int, str]:
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception:
            return e.code, str(e)


def _fetch_subreddit_new_sync(subreddit_name: str, cutoff_time: datetime, limit: int = 100) -> list[RedditPost]:
    token = _get_token_sync()
    user_agent = _ua()

    qs = urllib.parse.urlencode({"limit": str(limit), "raw_json": "1"})
    url = f"https://oauth.reddit.com/r/{subreddit_name}/new?{qs}"

    status, text = _get_json(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )

    # If token got rejected, clear cache once and retry
    if status == 401:
        global _TOKEN, _TOKEN_EXPIRES_AT
        _TOKEN = None
        _TOKEN_EXPIRES_AT = 0
        token = _get_token_sync()
        status, text = _get_json(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )

    if status != 200:
        raise RuntimeError(f"OAuth listing failed for r/{subreddit_name}: status={status} body={text[:200]}")

    payload = json.loads(text)
    children = (payload.get("data") or {}).get("children") or []

    posts: list[RedditPost] = []
    for child in children:
        p = (child or {}).get("data") or {}
        created_utc = p.get("created_utc")
        if not created_utc:
            continue

        created_at = datetime.utcfromtimestamp(float(created_utc))
        if created_at < cutoff_time:
            break

        posts.append(
            RedditPost(
                id=str(p.get("id") or ""),
                subreddit=subreddit_name,
                title=p.get("title") or "",
                selftext=p.get("selftext") or None,
                created_at=created_at,
            )
        )

    return posts


async def get_recent_reddit_posts(subreddits: list[str], timeframe: TimeframeKey) -> list[RedditPost]:
    posts: list[RedditPost] = []
    now = datetime.utcnow()
    cutoff_time = now - _get_timeframe_delta(timeframe)

    logger.info(f"Fetching Reddit posts for timeframe: {timeframe}")

    for subreddit_name in subreddits:
        try:
            chunk = await asyncio.to_thread(_fetch_subreddit_new_sync, subreddit_name, cutoff_time, 100)
            posts.extend(chunk)
            logger.debug(f"Fetched {len(chunk)} posts from r/{subreddit_name}")
        except Exception as e:
            logger.warning(str(e))
            continue

    posts.sort(key=lambda p: p.created_at, reverse=True)
    logger.info(f"Fetched {len(posts)} Reddit posts for timeframe {timeframe}")
    return posts
