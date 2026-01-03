"""Chrome extension API endpoint."""
import json
import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.social.text_utils import extract_tickers_and_keywords
from app.stocks.profile import get_company_profile, _get_narratives_for_symbol
from app.core.rate_limiter import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/extension",
    tags=["extension"],
)


class AuthorContext(BaseModel):
    """Author context extracted from page."""
    platform: str  # "reddit" | "twitter" | "stocktwits" | "article_site" | "generic"
    authorDisplayName: str | None = None
    authorHandle: str | None = None
    authorProfileUrl: str | None = None
    authorMetadata: dict | None = None


class RedditPostAnalysisRequest(BaseModel):
    url: str
    source: str | None = None
    subreddit: str | None = None
    title: str | None = None
    author: str | None = None
    body_snippet: str | None = None
    # New fields for universal page support
    contextType: str | None = None  # "reddit_social" | "twitter_social" | "article" | "generic" etc.
    authorContext: AuthorContext | None = None
    content: str | None = None  # Generic content field for non-Reddit pages
    resolvedTickers: list[str] | None = None  # Pre-resolved tickers from improved flow


class ResolveTickersRequest(BaseModel):
    """Request for ticker resolution endpoint."""
    url: str
    title: str
    contentSnippet: str
    sourceHost: str
    candidateSymbols: list[str]
    candidateCompanies: list[str] | None = None  # NEW: Company name candidates


class ResolvedTicker(BaseModel):
    """Resolved ticker with confidence score."""
    symbol: str
    confidence: float


def _compute_fallback_degen_score(
    enriched_tickers: list[dict],
    subreddit: str | None
) -> int:
    """
    Compute fallback degen score based on real data factors.
    
    Uses:
    - Max ticker Regard Score (if tickers detected)
    - Subreddit factor (high-degen subreddits boost score)
    - Volatility/price moves if available
    
    Returns deterministic score (0-100) based on actual data, not random constants.
    """
    base_score = 30  # Conservative base
    
    # Factor 1: Max ticker Regard Score
    if enriched_tickers:
        max_regard = max(t.get("regard_score", 50) for t in enriched_tickers if t.get("regard_score") is not None)
        # Regard Score contributes 0-50 points (50% weight)
        base_score += (max_regard / 100.0) * 50
    
    # Factor 2: Subreddit boost
    high_degen_subs = {
        "wallstreetbets": 25,
        "pennystocks": 20,
        "options": 15,
        "shortsqueeze": 20,
        "stockmarket": 10,
        "investing": 5,
        "stocks": 5,
    }
    
    if subreddit:
        subreddit_lower = subreddit.lower()
        if subreddit_lower in high_degen_subs:
            base_score += high_degen_subs[subreddit_lower]
    
    # Factor 3: Price volatility (if available)
    if enriched_tickers:
        max_abs_change = max(
            abs(t.get("change_1d_pct", 0) or 0) for t in enriched_tickers
        )
        # High volatility (>10% move) adds up to 15 points
        volatility_boost = min(15, (max_abs_change / 10.0) * 15)
        base_score += volatility_boost
    
    # Clamp to 0-100
    return max(0, min(100, int(round(base_score))))


def _generate_lightweight_author_analysis(author_context: AuthorContext | None) -> dict | None:
    """Generate lightweight author analysis for non-Reddit platforms."""
    if not author_context:
        return None
    
    platform = author_context.platform
    metadata = author_context.authorMetadata or {}
    
    signals = []
    summary_parts = []
    
    if platform == 'twitter':
        followers = metadata.get('followers')
        if followers:
            if followers > 100000:
                signals.append('High follower count')
                summary_parts.append(f"{followers:,} followers")
            elif followers > 10000:
                signals.append('Moderate follower count')
                summary_parts.append(f"{followers:,} followers")
            else:
                signals.append('Low follower count')
    
    elif platform == 'stocktwits':
        followers = metadata.get('followers')
        if followers:
            signals.append(f"{followers:,} followers")
            summary_parts.append(f"Stocktwits user with {followers:,} followers")
    
    elif platform == 'article_site':
        reputation = metadata.get('domainReputation', 'low')
        if reputation == 'high':
            signals.append('High reputation source')
            summary_parts.append('Published on reputable news site')
        elif reputation == 'medium':
            signals.append('Medium reputation source')
            summary_parts.append('Published on established site')
        else:
            signals.append('Low reputation source')
            summary_parts.append('Published on unknown site')
        
        if author_context.authorDisplayName:
            summary_parts.insert(0, f"Author: {author_context.authorDisplayName}")
    
    elif platform == 'generic':
        signals.append('Generic source')
        summary_parts.append(f"Content from {author_context.authorDisplayName or 'unknown source'}")
    
    summary = '. '.join(summary_parts) if summary_parts else f"Content from {platform} platform"
    
    # Compute a simple score (0-100) based on signals
    score = 50  # Neutral base
    if 'High' in ' '.join(signals):
        score = 70
    elif 'Low' in ' '.join(signals) or 'unknown' in summary.lower():
        score = 30
    
    return {
        "author": author_context.authorDisplayName or author_context.authorHandle,
        "author_regard_score": score,
        "trust_level": "medium",  # Default for non-Reddit
        "summary": summary,
        "signals": signals if signals else None,
        "platform": platform
    }


@router.post("/analyze-reddit-post")
@limiter.limit(get_rate_limit())
async def analyze_reddit_post(request: Request, req: RedditPostAnalysisRequest):
    """
    Analyze a Reddit post from the Chrome extension.
    
    Receives Reddit post data (URL, subreddit, title, author, body snippet)
    and returns structured analysis including:
    - Enriched ticker data (Regard Score, price, change %, narratives)
    - AI-generated post analysis (summary, degen score, sentiment, narrative name)
    """
    # Use resolved tickers if provided (from improved flow), otherwise extract from text
    if req.resolvedTickers and len(req.resolvedTickers) > 0:
        # Use pre-resolved tickers from improved flow
        unique_tickers = list(set(req.resolvedTickers))[:10]  # Limit to 10 tickers max
        logger.info(f"Using pre-resolved tickers: {unique_tickers}")
    else:
        # Legacy path: extract tickers from text
        text_parts = []
        if req.title:
            text_parts.append(req.title)
        if req.body_snippet:
            text_parts.append(req.body_snippet)
        if req.content:  # Generic content field
            text_parts.append(req.content)
        
        combined_text = " ".join(text_parts)
        
        # Extract tickers using existing utility
        tickers, keywords = extract_tickers_and_keywords(combined_text)
        
        # Remove duplicates and limit to reasonable number
        unique_tickers = list(set(tickers))[:10]  # Limit to 10 tickers max
    
    # Format detected tickers (simple list for response)
    detected_tickers = [{"symbol": ticker, "is_known": True} for ticker in unique_tickers]
    
    # Enrich tickers with Regard Score, price, change %
    # NOTE: Narratives removed for performance - they were causing timeouts
    enriched_tickers = []
    for symbol in unique_tickers:
        try:
            # Use existing company profile service to get ticker data
            profile = await get_company_profile(symbol)
            
            # Get Regard Score using centralized function (timeframe-independent)
            from app.scoring.regard_score_centralized import get_regard_score_for_symbol
            regard_info = await get_regard_score_for_symbol(symbol)
            
            # Handle case where regard_info might be None
            if regard_info is None:
                regard_info = {}
            
            enriched_ticker = {
                "symbol": symbol,
                "regard_score": regard_info.get("regard_score") if regard_info else None,
                "regard_data_completeness": regard_info.get("data_completeness") if regard_info else "unknown",
                "regard_missing_factors": regard_info.get("missing_factors", []) if regard_info else [],
                "price": float(profile.price) if profile.price is not None else None,
                "change_1d_pct": float(profile.change_pct) if profile.change_pct is not None else 0.0,
                "narratives": [],  # Narratives removed for performance
            }
            enriched_tickers.append(enriched_ticker)
        except Exception as e:
            logger.warning(f"Error enriching ticker {symbol}: {e}")
            # Add basic entry even if enrichment fails (no fallback 50)
            enriched_tickers.append({
                "symbol": symbol,
                "regard_score": None,
                "regard_data_completeness": "unknown",
                "regard_missing_factors": ["market_data"],
                "price": None,
                "change_1d_pct": 0.0,
                "narratives": [],
            })
    
    # Compute fallback degen score based on real data
    fallback_degen_score = _compute_fallback_degen_score(
        enriched_tickers,
        req.subreddit
    )
    
    # Build AI payload (include content and contextType for non-Reddit pages)
    ai_payload = {
        "url": req.url,
        "subreddit": req.subreddit,
        "title": req.title,
        "author": req.author,
        "body_snippet": req.body_snippet,
        "content": req.content,  # Include generic content field for non-Reddit pages
        "detected_tickers": unique_tickers,
        "enriched_tickers": enriched_tickers,
        "fallback_degen_score": fallback_degen_score,
    }
    
    # Call AI for post analysis
    ai_result = None
    try:
        from app.services.ai_client import generate_post_analysis_ai
        ai_result = await generate_post_analysis_ai(ai_payload)
    except Exception as e:
        logger.warning(f"Error generating AI analysis: {e}")
        ai_result = None
    
    # Determine final post degen score
    # Use AI degen_score if available and valid, otherwise use fallback
    final_post_degen_score = fallback_degen_score
    if ai_result and ai_result.get("degen_score") is not None:
        try:
            ai_degen = int(ai_result["degen_score"])
            if 0 <= ai_degen <= 100:
                final_post_degen_score = ai_degen
        except (ValueError, TypeError):
            pass  # Use fallback
    
    # Get author analysis (type-aware)
    author_analysis = None
    author_context = req.authorContext
    
    # Determine author identifier based on context
    author_identifier = None
    if author_context and author_context.platform == 'reddit':
        # Reddit: use existing service
        author_identifier = author_context.authorHandle or author_context.authorDisplayName
        if author_identifier:
            author_identifier = author_identifier.replace('u/', '').strip()
    elif author_context and author_context.platform in ['twitter', 'stocktwits']:
        # Social platforms: use handle
        author_identifier = author_context.authorHandle or author_context.authorDisplayName
    elif author_context and author_context.platform == 'article_site':
        # Article: use display name or domain
        author_identifier = author_context.authorDisplayName
    elif req.author and req.author.lower() not in ['[deleted]', 'deleted', '']:
        # Fallback to existing author field for backward compatibility
        author_identifier = req.author.replace('u/', '').strip()
    
    # Fetch author analysis if we have an identifier
    if author_identifier:
        if author_context and author_context.platform == 'reddit':
            # Reddit: use full analysis service
            try:
                from app.services.reddit_author_service import get_or_generate_author_analysis
                author_analysis = await get_or_generate_author_analysis(author_identifier)
            except Exception as e:
                logger.warning(f"Error getting author analysis for {author_identifier}: {e}")
                author_analysis = None
        else:
            # Non-Reddit: generate lightweight analysis
            author_analysis = _generate_lightweight_author_analysis(author_context)
    
    # Build response
    response = {
        "ok": True,
        "url": req.url,
        "subreddit": req.subreddit,
        "title": req.title,
        "author": req.author,
        "detected_tickers": detected_tickers,
        "tickers": enriched_tickers,
        "post_degen_score": final_post_degen_score,
        "post_analysis": {
            "ai_summary": ai_result.get("summary") if ai_result else None,
            "ai_degen_score": ai_result.get("degen_score") if ai_result else None,
            "ai_sentiment": ai_result.get("sentiment") if ai_result else None,
            "ai_narrative_name": ai_result.get("narrative_name") if ai_result else None,
        },
        "author_analysis": author_analysis,
        "author_context": author_context.dict() if author_context else None,  # Include author context in response
        "message": "Post analysis generated by Ragard (AI-assisted).",
    }
    
    # Log author calls for future reliability scoring (scaffolding)
    if ai_result and ai_result.get("sentiment") and unique_tickers:
        try:
            from app.models.author_call import AuthorCall
            from datetime import datetime
            
            # Map sentiment to stance
            sentiment = ai_result.get("sentiment")
            stance = None
            if sentiment == "bullish":
                stance = "bullish"
            elif sentiment == "bearish":
                stance = "bearish"
            elif sentiment == "neutral":
                stance = "neutral"
            # "mixed" stays None for now
            
            # Log a call for each detected ticker
            for symbol in unique_tickers:
                author_call = AuthorCall(
                    author=req.author or "unknown",
                    symbol=symbol,
                    stance=stance,
                    source_url=req.url,
                    created_at=datetime.now()
                )
                # TODO: Store in database or file-based log
                # For now, just log to console (scaffolding only)
                logger.debug(f"Author call logged: {author_call.author} -> {author_call.symbol} ({author_call.stance})")
        except Exception as e:
            logger.debug(f"Error logging author call: {e}")
            # Don't fail the request if call logging fails
    
    return response


@router.post("/resolve-tickers")
@limiter.limit(get_rate_limit())
async def resolve_tickers(request: Request, req: ResolveTickersRequest):
    """
    Resolve ticker candidates using AI/contextual logic.
    
    Takes candidate symbols extracted locally and uses AI to determine which ones
    actually correspond to companies discussed in the page context.
    
    Returns resolved tickers with confidence scores.
    """
    try:
        from app.services.ai_client import _get_openai_client
        from app.data.tickers import TICKER_SET
        
        client = _get_openai_client()
        if not client:
            # If AI client not available, fall back to simple validation
            logger.warning("AI client not available, using simple ticker validation")
            validated = []
            for symbol in req.candidateSymbols:
                symbol_upper = symbol.upper()
                if symbol_upper in TICKER_SET:
                    validated.append({
                        "symbol": symbol_upper,
                        "confidence": 0.6  # Lower confidence without AI
                    })
            return {"resolvedTickers": validated}
        
        # Build prompt for AI ticker resolution
        system_message = (
            "You are an assistant that identifies which stock ticker symbols are actually "
            "relevant to a given web page. You analyze the page context (title, content) "
            "and candidate symbols to determine which ones are truly discussed, filtering out "
            "random capitalized words that happen to look like tickers."
        )
        
        # Format candidate symbols and companies
        candidates_str = ", ".join(req.candidateSymbols[:20])  # Limit to 20 candidates
        companies_str = ", ".join(req.candidateCompanies[:10]) if req.candidateCompanies else "None"
        
        user_message = (
            f"Analyze this web page and determine which stock ticker symbols are actually "
            f"relevant to the content. You may need to map company names to their ticker symbols.\n\n"
            f"URL: {req.url}\n"
            f"Host: {req.sourceHost}\n"
            f"Title: {req.title}\n"
            f"Content snippet: {req.contentSnippet[:2000]}\n\n"
            f"Candidate ticker symbols: {candidates_str}\n"
            f"Candidate company names: {companies_str}\n\n"
            f"For each ticker symbol that is ACTUALLY discussed in the page content, "
            f"return a JSON object with:\n"
            f"- symbol: the ticker symbol (uppercase, e.g., 'NVDA' for Nvidia, 'TSLA' for Tesla)\n"
            f"- confidence: a float 0.0-1.0 indicating how confident you are this ticker "
            f"  is relevant (0.5 = somewhat relevant, 0.7+ = clearly relevant, 0.9+ = central topic)\n"
            f"- role: 'primary' if this is the main company/ticker the article is about, "
            f"  'secondary' if mentioned but not the main focus\n\n"
            f"Rules:\n"
            f"- Map company names to their ticker symbols (e.g., 'Nvidia' → 'NVDA', 'Apple' → 'AAPL')\n"
            f"- Only include symbols that are genuinely discussed in the content\n"
            f"- Filter out random capitalized words (e.g., 'THE', 'AND', 'FOR')\n"
            f"- The PRIMARY ticker should be the main subject of the article (usually appears in title, "
            f"  first paragraph, or is the central topic)\n"
            f"- SECONDARY tickers are mentioned but not the main focus\n"
            f"- Higher confidence for symbols that are central to the article's topic\n"
            f"- Lower confidence (0.5-0.6) for symbols mentioned but not the main focus\n\n"
            f"Respond with a JSON object:\n"
            f'{{"resolvedTickers": [{{"symbol": "NVDA", "confidence": 0.96, "role": "primary"}}, {{"symbol": "AMD", "confidence": 0.75, "role": "secondary"}}]}}\n\n'
            f"No extra text, JSON only."
        )
        
        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,  # Lower temperature for more deterministic results
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            logger.warning("Empty AI response for ticker resolution")
            # Fall back to simple validation
            validated = []
            for symbol in req.candidateSymbols:
                symbol_upper = symbol.upper()
                if symbol_upper in TICKER_SET:
                    validated.append({
                        "symbol": symbol_upper,
                        "confidence": 0.6
                    })
            return {"resolvedTickers": validated}
        
        result = json.loads(content)
        resolved = result.get("resolvedTickers", [])
        
        # Validate and normalize resolved tickers
        validated = []
        for item in resolved:
            if not isinstance(item, dict):
                continue
            symbol = item.get("symbol", "").upper().strip()
            confidence = item.get("confidence", 0.0)
            role = item.get("role", "secondary")  # Default to secondary if not specified
            
            # Validate symbol is in TICKER_SET
            if symbol and symbol in TICKER_SET:
                # Clamp confidence to 0.0-1.0
                confidence = max(0.0, min(1.0, float(confidence)))
                # Validate role
                if role not in ["primary", "secondary"]:
                    role = "secondary"
                validated.append({
                    "symbol": symbol,
                    "confidence": confidence,
                    "role": role
                })
        
        # Ensure at least one primary if we have results
        if validated and not any(t.get("role") == "primary" for t in validated):
            # Make highest confidence ticker primary
            validated.sort(key=lambda x: x["confidence"], reverse=True)
            if validated:
                validated[0]["role"] = "primary"
        
        logger.info(f"Resolved {len(validated)} tickers from {len(req.candidateSymbols)} candidates and {len(req.candidateCompanies or [])} company names")
        return {"resolvedTickers": validated}
        
    except Exception as e:
        logger.error(f"Error resolving tickers: {e}")
        # Fall back to simple validation on error
        from app.data.tickers import TICKER_SET
        validated = []
        for symbol in req.candidateSymbols:
            symbol_upper = symbol.upper()
            if symbol_upper in TICKER_SET:
                validated.append({
                    "symbol": symbol_upper,
                    "confidence": 0.5,  # Lower confidence on fallback
                    "role": "secondary"
                })
        # Make first one primary if we have results
        if validated:
            validated[0]["role"] = "primary"
        return {"resolvedTickers": validated}

