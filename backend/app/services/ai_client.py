"""AI client helper for generating stock overviews and narrative labels."""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory cache with TTL
_ai_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
CACHE_TTL_MINUTES = 45  # 45 minutes TTL

# Initialize OpenAI client
_openai_client: Optional[AsyncOpenAI] = None


def _get_openai_client() -> Optional[AsyncOpenAI]:
    """Get or create OpenAI client."""
    global _openai_client
    
    # Get API key from settings (which loads from .env)
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        logger.warning("OPENAI_API_KEY not set. AI features will be disabled.")
        return None
    
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=api_key)
    
    return _openai_client


def _get_cache_key(key_type: str, identifier: str, timeframe: Optional[str] = None) -> str:
    """Generate cache key."""
    if timeframe:
        return f"{key_type}:{identifier}:{timeframe}"
    return f"{key_type}:{identifier}"


def _get_cached(key: str) -> Optional[Dict[str, Any]]:
    """Get cached value if not expired."""
    if key not in _ai_cache:
        return None
    
    cached_time, cached_value = _ai_cache[key]
    if (datetime.now() - cached_time).total_seconds() > (CACHE_TTL_MINUTES * 60):
        # Expired, remove from cache
        del _ai_cache[key]
        return None
    
    return cached_value


def _set_cached(key: str, value: Dict[str, Any]) -> None:
    """Set cached value."""
    _ai_cache[key] = (datetime.now(), value)


async def generate_stock_overview_ai(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate AI overview for a stock ticker.
    
    Args:
        payload: Dict containing ticker data (symbol, company_name, sector, price, 
                 percent_changes, market_cap, regard_score, regard_breakdown, narratives, reddit_samples)
    
    Returns:
        Dict with fields: headline, summary_bullets, risk_label, timeframe_hint
        Returns None if AI call fails or API key not set
    """
    client = _get_openai_client()
    if not client:
        return None
    
    symbol = payload.get("symbol", "UNKNOWN")
    cache_key = _get_cache_key("stock_overview", symbol)
    
    # Check cache
    cached = _get_cached(cache_key)
    if cached:
        logger.debug(f"Using cached AI overview for {symbol}")
        return cached
    
    try:
        # Build prompt
        system_message = (
            "You are an assistant for a trading tool called Ragard. "
            "You explain why a ticker is 'degen' or not, using simple language for retail traders. "
            "Regard Score is a 0–100 degen meter (higher = more casino). "
            "Don't give financial advice; just describe what's going on."
        )
        
        # Format payload for prompt
        payload_str = json.dumps(payload, indent=2)
        
        user_message = (
            f"Using ONLY the data below, write a short JSON object summarizing this ticker.\n\n"
            f"Data:\n{payload_str}\n\n"
            f"Fields required:\n"
            f"- headline: 1 sentence summarizing what's going on.\n"
            f"- summary_bullets: 3–5 short bullets. Focus on *why* it's hot or boring "
            f"(Regard Score, narratives, recent move, Reddit chatter).\n"
            f"- risk_label: 'low', 'medium', or 'high' based on volatility and Regard Score.\n"
            f"- timeframe_hint: 'day trade', 'swing trade', or 'longer-term' based on the patterns you see.\n\n"
            f"Respond with valid JSON only, no extra text."
        )
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model for cost efficiency
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            logger.warning(f"Empty AI response for {symbol}")
            return None
        
        result = json.loads(content)
        
        # Validate required fields
        required_fields = ["headline", "summary_bullets", "risk_label"]
        if not all(field in result for field in required_fields):
            logger.warning(f"Missing required fields in AI response for {symbol}")
            return None
        
        # Ensure risk_label is valid
        if result["risk_label"] not in ["low", "medium", "high"]:
            result["risk_label"] = "medium"  # Default fallback
        
        # Cache result
        _set_cached(cache_key, result)
        
        logger.info(f"Generated AI overview for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating AI overview for {symbol}: {e}")
        return None


async def generate_narrative_label_ai(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate AI label (title, summary, sentiment) for a narrative.
    
    Args:
        payload: Dict containing narrative data (timeframe, tickers, sample_post_titles, 
                 avg_move_pct, heat_score, overall_regard)
    
    Returns:
        Dict with fields: title, summary, sentiment
        Returns None if AI call fails or API key not set
    """
    client = _get_openai_client()
    if not client:
        return None
    
    timeframe = payload.get("timeframe", "24h")
    tickers = payload.get("tickers", [])
    narrative_id = f"{timeframe}:{','.join(sorted(tickers[:5]))}"  # Use first 5 tickers for ID
    cache_key = _get_cache_key("narrative_label", narrative_id, timeframe)
    
    # Check cache
    cached = _get_cached(cache_key)
    if cached:
        logger.debug(f"Using cached AI label for narrative {narrative_id}")
        return cached
    
    try:
        # Build prompt
        system_message = (
            "You are Ragard AI, an assistant that names and explains stock market 'narratives' "
            "seen on Reddit. A narrative is a cluster of posts and tickers that share a theme. "
            "You must respond with a short, human-readable name and a brief explanation that would "
            "make sense to a trader. Do NOT give financial advice."
        )
        
        # Format payload for prompt
        payload_str = json.dumps(payload, indent=2)
        
        user_message = (
            f"Based on the tickers, post titles, and metrics, infer:\n\n"
            f"1. A short narrative name (max 5–6 words) that a trader would immediately understand. "
            f"Examples of style: 'Short Squeeze Rotation into Small Caps', 'Post-Earnings Dip Buy the Fear', "
            f"'AI Chips Momentum Trade'.\n\n"
            f"2. A 2–4 sentence summary describing what traders are doing or betting on.\n\n"
            f"3. Overall sentiment: 'bullish', 'bearish', 'mixed', or 'neutral'.\n\n"
            f"Data:\n{payload_str}\n\n"
            f"Respond with a JSON object:\n"
            f'{{"title": "...", "summary": "...", "sentiment": "bullish | bearish | mixed | neutral"}}\n\n'
            f"No extra text, JSON only."
        )
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model for cost efficiency
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=400,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            logger.warning(f"Empty AI response for narrative {narrative_id}")
            return None
        
        result = json.loads(content)
        
        # Validate required fields
        required_fields = ["title", "summary", "sentiment"]
        if not all(field in result for field in required_fields):
            logger.warning(f"Missing required fields in AI response for narrative {narrative_id}")
            return None
        
        # Ensure sentiment is valid
        valid_sentiments = ["bullish", "bearish", "mixed", "neutral"]
        if result["sentiment"] not in valid_sentiments:
            result["sentiment"] = "neutral"  # Default fallback
        
        # Cache result
        _set_cached(cache_key, result)
        
        logger.info(f"Generated AI label for narrative {narrative_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating AI label for narrative: {e}")
        return None


async def generate_post_analysis_ai(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate AI analysis for a Reddit post.
    
    Args:
        payload: Dict containing post data (url, subreddit, title, author, body_snippet,
                 detected_tickers, enriched_tickers, fallback_degen_score)
    
    Returns:
        Dict with fields: summary, degen_score, sentiment, narrative_name
        Returns None if AI call fails or API key not set
    """
    client = _get_openai_client()
    if not client:
        return None
    
    # Create cache key from post URL
    post_url = payload.get("url", "")
    cache_key = _get_cache_key("post_analysis", post_url)
    
    # Check cache
    cached = _get_cached(cache_key)
    if cached:
        logger.debug(f"Using cached AI analysis for post {post_url[:50]}")
        return cached
    
    try:
        # Build prompt
        system_message = (
            "You are Ragard AI, an assistant that analyzes Reddit posts about stocks. "
            "Regard / Degen scores are on a 0-100 scale. "
            "0 = not degen at all (boring, low-risk, conservative). "
            "100 = maximum degen, casino-style, highly speculative, extremely 'retarded'. "
            "Higher score ALWAYS means MORE degen / risk, never the opposite. "
            "Use the full 0-100 range. DO NOT cluster everything around 75 or 85. "
            "You help retail traders understand what OP is pitching and how degen it is. "
            "Do NOT give financial advice. Focus on analyzing the post's tone, claims, and context."
        )
        
        # Format enriched tickers for prompt
        enriched_tickers = payload.get("enriched_tickers", [])
        ticker_info = []
        for ticker in enriched_tickers:
            ticker_str = f"{ticker.get('symbol', 'N/A')}: Regard Score {ticker.get('regard_score', 'N/A')}, "
            ticker_str += f"Price ${ticker.get('price', 'N/A')}, "
            ticker_str += f"Change {ticker.get('change_1d_pct', 0):.2f}%"
            if ticker.get('narratives'):
                ticker_str += f", Narratives: {', '.join(ticker.get('narratives', [])[:3])}"
            ticker_info.append(ticker_str)
        
        # Format payload for prompt (support both Reddit and generic content)
        # Use content field if available (for non-Reddit), otherwise use body_snippet
        body_content = payload.get('content') or payload.get('body_snippet', '')
        # Limit body content to 1000 chars for prompt
        body_content = body_content[:1000] if body_content else ''
        
        user_message = (
            f"Analyze this {'Reddit post' if payload.get('subreddit') else 'web page content'} and provide:\n\n"
            f"1. A 2-4 sentence plain-language summary of what the content is pitching/saying.\n"
            f"2. A degen_score (0-100 integer) where:\n"
            f"   - 0-30 = Safe, boring, conservative posts\n"
            f"   - 30-60 = Moderate risk, some speculation\n"
            f"   - 60-80 = High degen, casino-like behavior\n"
            f"   - 80-100 = Maximum degen, peak 'retarded', extreme casino\n"
            f"   Consider: How risky/casino-like the content is, the Regard Scores of mentioned tickers, "
            f"the subreddit/context, and the tone/claims in the content.\n"
            f"   Return degen_score as an integer from 0 to 100, where higher = more degen. "
            f"Use the full range; small differences in setup should produce different values.\n"
            f"3. Overall sentiment: 'bullish', 'bearish', 'mixed', or 'neutral'.\n"
            f"4. A short narrative_name (max 5-6 words) that captures the theme.\n"
            f"   Examples: 'Small-Cap Biotech Moonshot', 'Meme Stock Pump Attempt', 'Value Play Discovery'\n\n"
            f"Content Data:\n"
            f"Subreddit: r/{payload.get('subreddit', 'N/A')}\n"
            f"Title: {payload.get('title', 'N/A')}\n"
            f"Author: {payload.get('author', 'N/A')}\n"
            f"Body/Content: {body_content}\n"
            f"Detected Tickers: {', '.join(payload.get('detected_tickers', []))}\n"
            f"Enriched Ticker Data:\n" + "\n".join(ticker_info) + "\n"
            f"Fallback Degen Score: {payload.get('fallback_degen_score', 50)}\n\n"
            f"Respond with a JSON object:\n"
            f'{{"summary": "...", "degen_score": 0-100, "sentiment": "bullish | bearish | mixed | neutral", "narrative_name": "..."}}\n\n'
            f"No extra text, JSON only."
        )
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            logger.warning(f"Empty AI response for post analysis")
            return None
        
        result = json.loads(content)
        
        # Validate and normalize
        if "degen_score" in result:
            try:
                degen_score = int(result["degen_score"])
                result["degen_score"] = max(0, min(100, degen_score))  # Clamp to 0-100
            except (ValueError, TypeError):
                result["degen_score"] = None
        
        # Ensure sentiment is valid
        valid_sentiments = ["bullish", "bearish", "mixed", "neutral"]
        if result.get("sentiment") not in valid_sentiments:
            result["sentiment"] = "neutral"
        
        # Ensure required fields exist
        if "summary" not in result:
            result["summary"] = None
        if "narrative_name" not in result:
            result["narrative_name"] = None
        
        # Cache result
        _set_cached(cache_key, result)
        
        logger.info(f"Generated AI analysis for post {post_url[:50]}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating post analysis: {e}")
        return {
            "summary": None,
            "degen_score": None,
            "sentiment": None,
            "narrative_name": None,
        }


async def generate_author_analysis_ai(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate AI analysis for a Reddit author based on their posting history.
    
    Args:
        payload: Dict containing author data (username, posts, total_posts, avg_score, top_subreddits)
    
    Returns:
        Dict with fields: author_regard_score, trust_level, summary
        Returns None if AI call fails or API key not set
    """
    client = _get_openai_client()
    if not client:
        return None
    
    username = payload.get("username", "")
    cache_key = _get_cache_key("author_analysis", username.lower())
    
    # Check cache
    cached = _get_cached(cache_key)
    if cached:
        logger.debug(f"Using cached AI author analysis for {username}")
        return cached
    
    try:
        # Build prompt
        system_message = (
            "You are Ragard AI. You assess Reddit authors based on their posting history, "
            "especially around stocks and trading. "
            "Author Regard Score is on a 0-100 scale. "
            "0 = boring, safe, conservative posting style. "
            "100 = full degen / casino, highly reckless behavior. "
            "Higher Author Regard = more degen, NOT more trustworthy. "
            "Use the full 0-100 range. Do NOT just output 75 or 85. "
            "Distinguish authors with different behaviors - a conservative value investor should score 10-30, "
            "a WSB YOLO poster should score 70-95, etc. "
            "You also estimate how 'trustworthy' they are as a signal source (trust_level: low/medium/high). "
            "You do NOT give financial advice."
        )
        
        # Format payload for prompt
        posts = payload.get("posts", [])
        posts_str = "\n".join([
            f"- r/{p.get('subreddit', 'unknown')}: {p.get('title', '')} (score: {p.get('score', 0)})"
            for p in posts[:15]  # Limit to 15 posts for prompt
        ])
        
        user_message = (
            f"Analyze this Reddit author's posting history and provide:\n\n"
            f"1. author_regard_score (0-100 integer): How degen/casino-like is this author overall?\n"
            f"   - 0-30 = Conservative, value-focused, safe posting style\n"
            f"   - 30-60 = Moderate speculation, some risky plays\n"
            f"   - 60-80 = High degen, frequent casino-style posts\n"
            f"   - 80-100 = Maximum degen, peak 'retarded', constant YOLO behavior\n"
            f"   Consider: subreddits they post in (WSB/pennystocks = more degen), types of claims, "
            f"frequency of stock posts, tone and language used.\n"
            f"   Use the FULL 0-100 range. Distinguish between authors - don't cluster around 75-85.\n"
            f"2. trust_level: 'low', 'medium', or 'high' - how trustworthy/reliable as a signal source.\n"
            f"   (Note: trust_level is separate from author_regard_score. A high degen author can have low trust.)\n"
            f"3. summary: 2-4 sentence overview of this author's style and reliability.\n\n"
            f"Author: u/{username}\n"
            f"Total posts analyzed: {payload.get('total_posts', 0)}\n"
            f"Average post score: {payload.get('avg_score', 0)}\n"
            f"Top subreddits: {', '.join(payload.get('top_subreddits', {}).keys())}\n\n"
            f"Recent posts:\n{posts_str}\n\n"
            f"Respond with a JSON object:\n"
            f'{{"author_regard_score": 0-100, "trust_level": "low | medium | high", "summary": "..."}}\n\n'
            f"No extra text, JSON only."
        )
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=400,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            logger.warning(f"Empty AI response for author analysis")
            return None
        
        result = json.loads(content)
        
        # Validate and normalize
        if "author_regard_score" in result:
            try:
                score = int(result["author_regard_score"])
                result["author_regard_score"] = max(0, min(100, score))  # Clamp to 0-100
            except (ValueError, TypeError):
                result["author_regard_score"] = None
        
        # Ensure trust_level is valid
        valid_trust_levels = ["low", "medium", "high"]
        if result.get("trust_level") not in valid_trust_levels:
            result["trust_level"] = "medium"  # Default fallback
        
        # Ensure required fields exist
        if "summary" not in result:
            result["summary"] = None
        
        # Cache result
        _set_cached(cache_key, result)
        
        logger.info(f"Generated AI author analysis for {username}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating author analysis: {e}")
        return None


async def generate_ticker_regard_ai(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate AI-refined Regard Score for a ticker.
    
    Args:
        context: Dict containing ticker data (symbol, company_name, sector, industry,
                 market_cap, profit_margins, beta, average_volume, short_ratio, base_score)
    
    Returns:
        Dict with fields: ai_regard_score, summary
        Returns None if AI call fails or API key not set
    """
    client = _get_openai_client()
    if not client:
        return None
    
    symbol = context.get("symbol", "UNKNOWN")
    cache_key = _get_cache_key("ticker_regard_ai", symbol)
    
    # Check cache
    cached = _get_cached(cache_key)
    if cached:
        logger.debug(f"Using cached AI Regard Score for {symbol}")
        return cached
    
    try:
        # Build prompt
        system_message = (
            "You are Ragard AI. You compute a Regard Score for investing in this company RIGHT NOW. "
            "Regard Score is 0-100: 0 = very safe/boring/low risk, 100 = full casino, hyper-speculative, "
            "brain-damage level degen. "
            "Higher score ALWAYS means MORE degen. Do NOT invert this relationship. "
            "Use the full 0-100 range. Do NOT cluster everything around 70-80. "
            "Small differences in risk/hype should move the score. "
            "Short-term hype (volume spikes, mention spikes, recent big rallies) should increase the score, "
            "especially for weaker companies, but strong large caps (e.g. GOOG, MSFT, SPY) should rarely exceed ~30-40 "
            "even in hot periods."
        )
        
        # Format context for prompt
        missing_factors = context.get('missing_factors', [])
        data_completeness = context.get('data_completeness', 'unknown')
        base_score = context.get('base_score')
        
        user_message = (
            f"Assess this ticker's Regard Score (0-100, higher = more degen):\n\n"
            f"Symbol: {context.get('symbol', 'N/A')}\n"
            f"Company: {context.get('company_name', 'N/A')}\n"
            f"Sector: {context.get('sector', 'N/A')}\n"
            f"Industry: {context.get('industry', 'N/A')}\n"
        )
        
        # Add available data fields
        if context.get('market_cap') is not None:
            user_message += f"Market Cap: ${context.get('market_cap', 0):,.0f}\n"
        if context.get('profit_margins') is not None:
            user_message += f"Profit Margins: {context.get('profit_margins', 0):.2%}\n"
        if context.get('beta') is not None:
            user_message += f"Beta (volatility): {context.get('beta', 1.0):.2f}\n"
        if context.get('average_volume') is not None:
            user_message += f"Average Volume: {context.get('average_volume', 0):,.0f}\n"
        if context.get('short_ratio') is not None:
            user_message += f"Short Ratio: {context.get('short_ratio', 0):.2f}\n"
        
        # Add recent hype context
        if context.get('change_7d_pct') is not None:
            user_message += f"7D Price Change: {context.get('change_7d_pct', 0):.1f}%\n"
        if context.get('change_30d_pct') is not None:
            user_message += f"30D Price Change: {context.get('change_30d_pct', 0):.1f}%\n"
        if context.get('volume_spike_7d') is not None:
            user_message += f"7D Volume vs 30D Avg: {context.get('volume_spike_7d', 1.0):.2f}x\n"
        
        user_message += (
            f"\nData-driven base score: {base_score if base_score is not None else 'N/A'}\n"
            f"Data completeness: {data_completeness}\n"
            f"Missing factors: {', '.join(missing_factors) if missing_factors else 'none'}\n\n"
            f"Based on these structural factors (market cap, profitability, volatility, liquidity, short interest) "
            f"and recent hype indicators (price changes, volume spikes), return an ai_regard_score (0-100 integer) "
            f"that represents how degen investing in this company would be RIGHT NOW. "
            f"Higher = more degen. Use the full range. Consider both structural risk and current hype.\n\n"
            f"Respond with a JSON object:\n"
            f'{{"ai_regard_score": 0-100, "summary": "2-3 sentence explanation of why this score makes sense"}}\n\n'
            f"No extra text, JSON only."
        )
        
        # Call OpenAI with retry logic
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=200,
                    response_format={"type": "json_object"},
                    timeout=8.0  # 8 second timeout per request
                )
                
                # Parse response
                content = response.choices[0].message.content
                if not content:
                    logger.warning(f"Empty AI response for ticker Regard Score, attempt {attempt + 1}/{max_attempts}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    return None
                
                result = json.loads(content)
                
                # Validate and normalize
                if "ai_regard_score" in result:
                    try:
                        score = int(result["ai_regard_score"])
                        result["ai_regard_score"] = max(0, min(100, score))  # Clamp to 0-100
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid ai_regard_score in response: {result.get('ai_regard_score')}, attempt {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        result["ai_regard_score"] = None
                
                # Ensure summary exists
                if "summary" not in result:
                    result["summary"] = None
                
                # Validate we got a valid score
                if result.get("ai_regard_score") is None:
                    logger.warning(f"AI returned None score, attempt {attempt + 1}/{max_attempts}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    return None
                
                # Cache result
                _set_cached(cache_key, result)
                
                logger.info(f"Generated AI Regard Score for {symbol}: {result.get('ai_regard_score')}")
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout on attempt {attempt + 1}/{max_attempts}"
                logger.warning(f"OpenAI API timeout for {symbol}, attempt {attempt + 1}/{max_attempts}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                    continue
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                logger.warning(f"Failed to parse AI JSON response for {symbol}, attempt {attempt + 1}/{max_attempts}: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
            except Exception as e:
                last_error = f"Exception: {e}"
                logger.warning(f"Error calling OpenAI for {symbol}, attempt {attempt + 1}/{max_attempts}: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
        
        # All attempts failed, try fallback with simpler prompt
        logger.warning(f"All {max_attempts} attempts failed for {symbol}, trying fallback prompt")
        return await _generate_ticker_regard_ai_fallback(context, last_error)
        
    except Exception as e:
        logger.error(f"Error generating AI Regard Score for {symbol}: {e}")
        # Try fallback
        try:
            return await _generate_ticker_regard_ai_fallback(context, str(e))
        except:
            return None


async def _generate_ticker_regard_ai_fallback(context: Dict[str, Any], error_msg: str = "") -> Optional[Dict[str, Any]]:
    """
    Fallback AI call with simpler prompt if main call fails.
    Uses a more basic prompt that's less likely to fail.
    """
    client = _get_openai_client()
    if not client:
        return None
    
    symbol = context.get("symbol", "UNKNOWN")
    base_score = context.get('base_score')
    
    try:
        # Much simpler prompt for fallback
        system_message = (
            "You are Ragard AI. Return a Regard Score 0-100 where 0=safe, 100=full casino degen. "
            "Higher = more degen. Use full range."
        )
        
        user_message = (
            f"Symbol: {symbol}\n"
            f"Company: {context.get('company_name', 'N/A')}\n"
        )
        
        if context.get('market_cap') is not None:
            user_message += f"Market Cap: ${context.get('market_cap', 0):,.0f}\n"
        if base_score is not None:
            user_message += f"Base score: {base_score:.1f}\n"
        
        user_message += (
            f"\nReturn JSON: {{\"ai_regard_score\": 0-100, \"summary\": \"brief reason\"}}\n"
            f"JSON only, no extra text."
        )
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150,
            response_format={"type": "json_object"},
            timeout=8.0
        )
        
        content = response.choices[0].message.content
        if not content:
            logger.error(f"Fallback AI returned empty response for {symbol}")
            return None
        
        result = json.loads(content)
        
        if "ai_regard_score" in result:
            try:
                score = int(result["ai_regard_score"])
                result["ai_regard_score"] = max(0, min(100, score))
            except (ValueError, TypeError):
                logger.error(f"Fallback AI returned invalid score for {symbol}")
                return None
        
        if "summary" not in result:
            result["summary"] = f"Fallback calculation (original error: {error_msg[:50]})"
        
        logger.info(f"Fallback AI Regard Score for {symbol}: {result.get('ai_regard_score')}")
        return result
        
    except Exception as e:
        logger.error(f"Fallback AI call also failed for {symbol}: {e}")
        return None

