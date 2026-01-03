"""Dynamic narrative building from Reddit co-mentions."""
import logging
from typing import Dict, Set, DefaultDict
from collections import defaultdict, Counter
from app.narratives.config import TimeframeKey
from app.narratives.models import NarrativeSummary, NarrativeMetrics
from app.social.reddit import get_recent_reddit_posts, REDDIT_SUBREDDITS
from app.social.text_utils import extract_tickers_and_keywords
from app.narratives.service import _fetch_ticker_returns, _compute_heat_score

logger = logging.getLogger(__name__)

# Minimum thresholds for narrative building
MIN_MENTIONS = 3  # Minimum mentions for a ticker to be considered active
MIN_CO_MENTIONS = 2  # Minimum co-mentions for two tickers to be connected
MIN_CLUSTER_SIZE = 2  # Minimum tickers in a cluster to form a narrative
MIN_HEAT_SCORE = 20  # Minimum heat score in at least one timeframe


def _find_connected_components(
    graph: Dict[str, Set[str]]
) -> list[Set[str]]:
    """
    Find connected components in an undirected graph using DFS.
    
    Args:
        graph: Adjacency list representation (ticker -> set of connected tickers)
    
    Returns:
        List of sets, each set is a connected component (cluster)
    """
    visited: Set[str] = set()
    components: list[Set[str]] = []
    
    def dfs(node: str, component: Set[str]):
        """Depth-first search to find connected nodes."""
        if node in visited:
            return
        visited.add(node)
        component.add(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, component)
    
    for ticker in graph:
        if ticker not in visited:
            component: Set[str] = set()
            dfs(ticker, component)
            if component:  # Only add non-empty components
                components.append(component)
    
    return components


def _generate_narrative_name_and_description(
    tickers: Set[str],
    keyword_freq: Counter,
    timeframe: TimeframeKey
) -> tuple[str, str]:
    """
    Generate narrative name and description from tickers and keywords.
    
    Args:
        tickers: Set of ticker symbols in the cluster
        keyword_freq: Counter of keyword frequencies from posts
        timeframe: Current timeframe
    
    Returns:
        Tuple of (name, description)
    """
    ticker_list = sorted(list(tickers))
    
    # Get top keywords
    top_keywords = [word for word, _ in keyword_freq.most_common(3)]
    
    # Generate name
    if top_keywords:
        # Capitalize keywords nicely
        name_parts = [word.capitalize() for word in top_keywords[:2]]
        name = " ".join(name_parts)
    else:
        # Fallback: use ticker names
        if len(ticker_list) <= 3:
            name = ", ".join(ticker_list)
        else:
            name = f"{', '.join(ticker_list[:3])} +{len(ticker_list) - 3}"
    
    # Generate description
    if top_keywords:
        keyword_str = ", ".join(top_keywords[:3])
        description = (
            f"Cluster of {len(ticker_list)} tickers ({', '.join(ticker_list[:5])}"
            f"{'...' if len(ticker_list) > 5 else ''}) driven by {keyword_str} "
            f"chatter on Reddit in the last {timeframe}."
        )
    else:
        description = (
            f"Cluster of {len(ticker_list)} tickers ({', '.join(ticker_list[:5])}"
            f"{'...' if len(ticker_list) > 5 else ''}) mentioned together "
            f"on Reddit in the last {timeframe}."
        )
    
    return name, description


def _generate_narrative_id(name: str, tickers: Set[str]) -> str:
    """Generate a stable ID for a narrative from its name and tickers."""
    # Create a slug from name and sorted tickers
    name_slug = "".join(c.lower() if c.isalnum() else "-" for c in name)
    ticker_hash = "-".join(sorted(tickers))[:20]  # First 20 chars of sorted tickers
    return f"{name_slug}-{ticker_hash}".replace("--", "-").strip("-")


async def build_dynamic_narratives(timeframe: TimeframeKey) -> list[NarrativeSummary]:
    """
    Build dynamic narratives from Reddit co-mentions.
    
    This is the core pipeline that:
    1. Fetches recent Reddit posts
    2. Extracts tickers and keywords
    3. Builds co-mention clusters
    4. Auto-labels clusters
    5. Computes Ragard-style metrics
    
    Args:
        timeframe: Timeframe key (24h, 7d, 30d)
    
    Returns:
        List of NarrativeSummary objects
    """
    # Step 1: Gather posts
    posts = await get_recent_reddit_posts(REDDIT_SUBREDDITS, timeframe)
    
    # Step 2: Extract tickers and keywords from posts
    ticker_stats: DefaultDict[str, Dict[str, any]] = defaultdict(lambda: {
        "mention_count": 0,
        "post_ids": set(),
        "keywords": []
    })
    keyword_stats: Counter = Counter()
    co_mention_counts: DefaultDict[tuple[str, str], int] = defaultdict(int)
    
    for post in posts:
        # Combine title and selftext
        text = post.title
        if post.selftext:
            text += " " + post.selftext
        
        # Extract tickers and keywords
        tickers, keywords = extract_tickers_and_keywords(text)
        
        # Skip posts with no tickers
        if not tickers:
            continue
        
        # Update ticker stats
        for ticker in tickers:
            ticker_stats[ticker]["mention_count"] += 1
            ticker_stats[ticker]["post_ids"].add(post.id)
            ticker_stats[ticker]["keywords"].extend(keywords)
        
        # Update keyword stats
        keyword_stats.update(keywords)
        
        # Update co-mention counts
        # For each unique pair of tickers in this post
        unique_tickers = sorted(set(tickers))
        for i in range(len(unique_tickers)):
            for j in range(i + 1, len(unique_tickers)):
                ticker_a, ticker_b = unique_tickers[i], unique_tickers[j]
                # Use sorted tuple as key for undirected graph
                pair = tuple(sorted([ticker_a, ticker_b]))
                co_mention_counts[pair] += 1
    
    # Step 3: Filter to active tickers
    active_tickers = {
        ticker for ticker, stats in ticker_stats.items()
        if stats["mention_count"] >= MIN_MENTIONS
    }
    
    if not active_tickers:
        return []  # No active tickers found
    
    # Step 4: Build co-mention graph
    graph: Dict[str, Set[str]] = defaultdict(set)
    
    for (ticker_a, ticker_b), count in co_mention_counts.items():
        if count >= MIN_CO_MENTIONS:
            if ticker_a in active_tickers and ticker_b in active_tickers:
                graph[ticker_a].add(ticker_b)
                graph[ticker_b].add(ticker_a)
    
    # Step 5: Find connected components (clusters)
    clusters = _find_connected_components(graph)
    
    # Also consider single-ticker narratives if they have very high mention count
    # (e.g., >= MIN_MENTIONS * 3)
    single_ticker_clusters = {
        ticker for ticker in active_tickers
        if ticker_stats[ticker]["mention_count"] >= MIN_MENTIONS * 3
        and not any(ticker in cluster for cluster in clusters)
    }
    
    for ticker in single_ticker_clusters:
        clusters.append({ticker})
    
    # Step 6: Build narratives from clusters
    narratives: list[NarrativeSummary] = []
    
    # Fetch price data for all active tickers at once
    all_cluster_tickers = set()
    for cluster in clusters:
        all_cluster_tickers.update(cluster)
    
    ticker_returns = _fetch_ticker_returns(list(all_cluster_tickers), period_days=60)
    
    for cluster in clusters:
        if len(cluster) < MIN_CLUSTER_SIZE:
            continue  # Skip clusters that are too small
        
        # Collect keywords from posts mentioning any ticker in this cluster
        cluster_keywords: Counter = Counter()
        for ticker in cluster:
            cluster_keywords.update(ticker_stats[ticker]["keywords"])
        
        # Generate name and description
        name, description = _generate_narrative_name_and_description(
            cluster, cluster_keywords, timeframe
        )
        
        # Generate ID
        narrative_id = _generate_narrative_id(name, cluster)
        
        # Compute metrics for all timeframes
        metrics_by_timeframe: Dict[TimeframeKey, NarrativeMetrics] = {}
        
        for tf in ["24h", "7d", "30d"]:
            tf_key: TimeframeKey = tf  # type: ignore
            
            # Collect returns for this timeframe
            returns: list[float] = []
            up_count = 0
            down_count = 0
            
            for ticker in cluster:
                ticker_return = ticker_returns.get(ticker, {}).get(tf_key)
                if ticker_return is not None:
                    returns.append(ticker_return)
                    if ticker_return > 0:
                        up_count += 1
                    elif ticker_return < 0:
                        down_count += 1
            
            # Calculate average move
            if returns:
                avg_move_pct = sum(returns) / len(returns)
            else:
                avg_move_pct = 0.0
            
            # Compute heat score
            heat_score = _compute_heat_score(avg_move_pct)
            
            metrics_by_timeframe[tf_key] = NarrativeMetrics(
                avg_move_pct=round(avg_move_pct, 2),
                up_count=up_count,
                down_count=down_count,
                heat_score=round(heat_score, 1),
                social_buzz_score=None,  # TODO: Incorporate Reddit buzz
            )
        
        # Filter: require at least one timeframe with heat score above minimum
        max_heat = max(m.heat_score for m in metrics_by_timeframe.values())
        if max_heat < MIN_HEAT_SCORE:
            continue  # Skip narratives that are too weak
        
        # Determine sentiment from average move across all timeframes
        avg_move_all = sum(m.avg_move_pct for m in metrics_by_timeframe.values()) / len(metrics_by_timeframe)
        if avg_move_all > 2:
            sentiment = "bullish"
        elif avg_move_all < -2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        # Generate AI label for narrative
        ai_title = None
        ai_summary = None
        ai_sentiment = None
        
        try:
            from app.services.ai_client import generate_narrative_label_ai
            
            # Collect sample post titles for this cluster
            sample_post_titles = []
            cluster_ticker_set = set(cluster)
            
            # Only collect post titles if we have posts (Reddit might be unavailable)
            if posts:
                for post in posts:
                    text = post.title
                    if post.selftext:
                        text += " " + post.selftext
                    tickers, _ = extract_tickers_and_keywords(text)
                    # Check if any ticker in this cluster is mentioned
                    if any(t in cluster_ticker_set for t in tickers):
                        sample_post_titles.append(post.title[:150])  # Limit length
                        if len(sample_post_titles) >= 20:  # Max 20 samples
                            break
            
            # Get overall regard score (average of ticker regard scores if available)
            overall_regard = None
            try:
                # Try to get regard scores for tickers in cluster
                # For now, use heat score as proxy
                overall_regard = max(m.heat_score for m in metrics_by_timeframe.values())
            except Exception:
                pass
            
            # Build payload for AI (works even with empty post titles)
            ai_payload = {
                "timeframe": timeframe,
                "tickers": sorted(list(cluster))[:10],  # Limit to 10 tickers
                "sample_post_titles": sample_post_titles[:20],  # Can be empty if Reddit unavailable
                "avg_move_pct": avg_move_all,
                "heat_score": max(m.heat_score for m in metrics_by_timeframe.values()),
                "overall_regard": overall_regard,
            }
            
            # Call AI (with timeout protection - don't block too long)
            # AI can still generate labels from tickers and metrics even without post titles
            ai_result = await generate_narrative_label_ai(ai_payload)
            
            if ai_result:
                ai_title = ai_result.get("title")
                ai_summary = ai_result.get("summary")
                ai_sentiment = ai_result.get("sentiment")
                
        except Exception as e:
            logger.warning(f"Error generating AI label for narrative {narrative_id}: {e}")
            # Continue with fallback name/description
        
        # Create narrative summary
        narrative = NarrativeSummary(
            id=narrative_id,
            name=name,
            description=description,
            sentiment=sentiment,
            tickers=sorted(list(cluster)),
            metrics=metrics_by_timeframe,
            ai_title=ai_title,
            ai_summary=ai_summary,
            ai_sentiment=ai_sentiment,
        )
        narratives.append(narrative)
    
    # Sort by heat score for the selected timeframe (descending)
    narratives.sort(
        key=lambda n: n.metrics[timeframe].heat_score,
        reverse=True
    )
    
    return narratives

