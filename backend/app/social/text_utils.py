"""Text processing utilities for extracting tickers and keywords."""
import os
import re
import logging
from typing import Tuple, Optional

from app.data.tickers import TICKER_SET, is_known_ticker

logger = logging.getLogger(__name__)

# Debug flag for ticker parser logging
DEBUG_TICKER_PARSER = os.getenv("DEBUG_TICKER_PARSER", "").lower() in ("1", "true", "yes")

# Common stopwords to filter out
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "must", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "now", "then", "here", "there", "when", "where", "why", "how",
}

# Ticker pattern: 1-5 uppercase letters
TICKER_RE = re.compile(r"^[A-Z]{1,5}$")


def is_valid_ticker_token(raw: str) -> Optional[str]:
    """
    Validate and normalize a raw token into a ticker symbol.
    
    Rules:
    - Strips leading '$' if present, remembers if it had '$'
    - Uppercases and validates format (1-5 A-Z letters)
    - Checks if candidate is in TICKER_SET
    - For 1-2 letter symbols: only accepts if original had '$' prefix
    - For 3-5 letter symbols: accepts if in TICKER_SET
    
    Args:
        raw: Raw token from text (e.g., "$TSLA", "TSLA", "A", "$A")
    
    Returns:
        Normalized ticker symbol (uppercase) if valid, None otherwise
    """
    if not raw:
        return None
    
    # Remember if it was explicitly prefixed with '$'
    has_dollar = raw.startswith("$")
    
    # Strip '$' and normalize
    token = raw.lstrip("$").strip().upper()
    
    # Reject if not A-Z or length not in [1, 5]
    if not TICKER_RE.match(token):
        return None
    
    # Reject if not in TICKER_SET
    if token not in TICKER_SET:
        if DEBUG_TICKER_PARSER:
            logger.debug(f"Rejected '{raw}' -> '{token}': not in TICKER_SET")
        return None
    
    # If len >= 3: accept (already validated it's in TICKER_SET)
    if len(token) >= 3:
        if DEBUG_TICKER_PARSER:
            logger.debug(f"Accepted '{raw}' -> '{token}': 3+ letters, in TICKER_SET")
        return token
    
    # If len <= 2: only accept if original had '$' prefix
    if len(token) <= 2:
        if has_dollar:
            if DEBUG_TICKER_PARSER:
                logger.debug(f"Accepted '{raw}' -> '{token}': 1-2 letters with $ prefix, in TICKER_SET")
            return token
        else:
            if DEBUG_TICKER_PARSER:
                logger.debug(f"Rejected '{raw}' -> '{token}': 1-2 letters without $ prefix")
            return None
    
    return None


def extract_tickers_and_keywords(text: str) -> Tuple[list[str], list[str]]:
    """
    Extract ticker symbols and keywords from text.
    
    This is the CANONICAL ticker parser used throughout the application.
    Uses the official ticker universe from CSV to validate tickers.
    
    Rules:
    - Only real tickers from the CSV are recognized
    - 1-2 letter words are NOT treated as tickers unless prefixed with '$' AND in TICKER_SET
    - 3-5 letter words can be tickers if they're in the universe
    
    Args:
        text: Input text to process
    
    Returns:
        Tuple of (tickers, keywords) where:
        - tickers: List of uppercase ticker symbols (e.g., ["TSLA", "GME"])
        - keywords: List of lowercase keywords (e.g., ["ai", "chips", "squeeze"])
    """
    if not text:
        return [], []
    
    if DEBUG_TICKER_PARSER:
        logger.debug(f"Parsing text: {text[:100]}...")
    
    # Extract tickers
    tickers = set()
    
    # Find all $TICKER patterns explicitly (these are always candidates)
    dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
    
    # Find standalone ALLCAPS words (1-5 letters) that might be tickers
    # Only match uppercase to avoid matching regular words
    standalone_caps = re.findall(r'\b([A-Z]{1,5})\b', text)
    
    if DEBUG_TICKER_PARSER:
        logger.debug(f"Found {len(dollar_tickers)} dollar-prefixed tokens, {len(standalone_caps)} standalone ALLCAPS tokens")
    
    # Process dollar-prefixed tickers
    for raw_token in dollar_tickers:
        raw_with_dollar = f"${raw_token}"
        ticker = is_valid_ticker_token(raw_with_dollar)
        if ticker:
            tickers.add(ticker)
            if DEBUG_TICKER_PARSER:
                logger.debug(f"  -> Added ticker: {ticker} (from '{raw_with_dollar}')")
    
    # Process standalone ALLCAPS words (skip if already found as dollar-prefixed)
    for raw_token in standalone_caps:
        # Skip if already found as dollar-prefixed
        if raw_token in tickers:
            continue
        
        # Process as non-dollar-prefixed token
        ticker = is_valid_ticker_token(raw_token)
        if ticker:
            tickers.add(ticker)
            if DEBUG_TICKER_PARSER:
                logger.debug(f"  -> Added ticker: {ticker} (from '{raw_token}')")
    
    # Convert to sorted list
    tickers_list = sorted(list(tickers))
    
    if DEBUG_TICKER_PARSER:
        logger.debug(f"Final tickers: {tickers_list}")
    
    # Extract keywords
    # Normalize text to lowercase
    text_lower = text.lower()
    
    # Remove ticker mentions and dollar signs
    # Remove $TICKER patterns
    for ticker in tickers_list:
        text_lower = re.sub(rf'\${re.escape(ticker)}\b', '', text_lower, flags=re.IGNORECASE)
        text_lower = re.sub(rf'\b{re.escape(ticker)}\b', '', text_lower, flags=re.IGNORECASE)
    
    # Tokenize: split on whitespace and punctuation
    tokens = re.findall(r'\b[a-z]+\b', text_lower)
    
    # Filter out stopwords and very short words
    keywords = [
        token for token in tokens
        if len(token) >= 3 and token not in STOPWORDS
    ]
    
    # Remove duplicates while preserving order
    keywords_list = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            keywords_list.append(keyword)
            seen.add(keyword)
    
    if DEBUG_TICKER_PARSER:
        logger.debug(f"Final keywords: {keywords_list}")
    
    return tickers_list, keywords_list

