"""User Regard Score computation and analysis services."""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from app.core.supabase_client import get_supabase_admin
from app.services.ai_client import _get_openai_client
from app.services.benchmark_return_service import (
    get_benchmark_return,
    calculate_user_return,
    calculate_relative_alpha,
    DEFAULT_REFERENCE_CAPITAL
)
from app.services.user_positions import build_user_positions_and_trades

logger = logging.getLogger(__name__)


class UserRegardBaseStats:
    """Base statistics computed from user trades."""
    def __init__(
        self,
        user_id: str,
        wins: int,
        losses: int,
        sample_size: int,
        win_rate: Optional[float],
        avg_win_pnl: Optional[float] = None,
        avg_loss_pnl: Optional[float] = None,
        max_win_pnl: Optional[float] = None,
        max_loss_pnl: Optional[float] = None,
        avg_holding_period_seconds: Optional[float] = None,
        per_ticker_stats: Optional[List[Dict[str, Any]]] = None,
        avg_regard_score_at_entry: Optional[float] = None,
        high_regard_trades_count: int = 0,  # Trades with regard_score >= 70
        low_regard_trades_count: int = 0,  # Trades with regard_score < 30
        # Market-relative performance fields
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        total_pnl: Optional[float] = None,
        reference_capital: float = 10000.0,
        user_return: Optional[float] = None,
        benchmark_return: Optional[float] = None,
        relative_alpha: Optional[float] = None,
        # Open positions
        open_positions_count: int = 0,
        open_positions_unrealized_pnl: Optional[float] = None,
        open_positions_list: Optional[List[Dict[str, Any]]] = None,
    ):
        self.user_id = user_id
        self.wins = wins
        self.losses = losses
        self.sample_size = sample_size
        self.win_rate = win_rate
        self.avg_win_pnl = avg_win_pnl
        self.avg_loss_pnl = avg_loss_pnl
        self.max_win_pnl = max_win_pnl
        self.max_loss_pnl = max_loss_pnl
        self.avg_holding_period_seconds = avg_holding_period_seconds
        self.per_ticker_stats = per_ticker_stats or []
        self.avg_regard_score_at_entry = avg_regard_score_at_entry
        self.high_regard_trades_count = high_regard_trades_count
        self.low_regard_trades_count = low_regard_trades_count
        # Market-relative performance
        self.period_start = period_start
        self.period_end = period_end
        self.total_pnl = total_pnl
        self.reference_capital = reference_capital
        self.user_return = user_return
        self.benchmark_return = benchmark_return
        self.relative_alpha = relative_alpha
        # Open positions
        self.open_positions_count = open_positions_count
        self.open_positions_unrealized_pnl = open_positions_unrealized_pnl
        self.open_positions_list = open_positions_list or []


async def compute_user_regard_base_stats(user_id: str) -> UserRegardBaseStats:
    """
    Compute base statistics from user's trade history.
    
    Args:
        user_id: Supabase user ID
        
    Returns:
        UserRegardBaseStats object with computed metrics
    """
    try:
        supabase = get_supabase_admin()
        
        # Fetch all trades for this user
        response = supabase.table("user_trades")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=False)\
            .execute()
        
        trades = response.data if response.data else []
        
        if not trades:
            return UserRegardBaseStats(
                user_id=user_id,
                wins=0,
                losses=0,
                sample_size=0,
                win_rate=None,
            )
        
        # Classify trades and compute stats
        wins = 0
        losses = 0
        win_pnls = []
        loss_pnls = []
        holding_periods = []
        regard_scores_at_entry = []
        high_regard_count = 0
        low_regard_count = 0
        ticker_stats: Dict[str, Dict[str, Any]] = {}
        total_pnl = 0.0
        entry_times = []
        exit_times = []
        
        for trade in trades:
            pnl = float(trade.get("realized_pnl", 0))
            total_pnl += pnl
            holding_period = trade.get("holding_period_seconds", 0)
            ticker = trade.get("ticker", "").upper()
            regard_at_entry = trade.get("regard_score_at_entry")
            
            # Track entry/exit times for period calculation
            entry_time = trade.get("entry_time")
            exit_time = trade.get("exit_time")
            if entry_time:
                entry_times.append(entry_time)
            if exit_time:
                exit_times.append(exit_time)
            
            if pnl > 0:
                wins += 1
                win_pnls.append(pnl)
            elif pnl < 0:
                losses += 1
                loss_pnls.append(pnl)
            # Ignore pnl == 0 (neutral trades)
            
            holding_periods.append(holding_period)
            
            # Track Regard Scores
            if regard_at_entry is not None:
                regard_scores_at_entry.append(float(regard_at_entry))
                if float(regard_at_entry) >= 70:
                    high_regard_count += 1
                elif float(regard_at_entry) < 30:
                    low_regard_count += 1
            
            # Aggregate per-ticker stats
            if ticker not in ticker_stats:
                ticker_stats[ticker] = {"trades": 0, "wins": 0, "losses": 0}
            ticker_stats[ticker]["trades"] += 1
            if pnl > 0:
                ticker_stats[ticker]["wins"] += 1
            elif pnl < 0:
                ticker_stats[ticker]["losses"] += 1
        
        sample_size = wins + losses
        win_rate = wins / sample_size if sample_size > 0 else None
        
        # Sanity check: ensure consistency
        if wins + losses != sample_size:
            logger.warning(f"Inconsistency detected for user {user_id}: wins({wins}) + losses({losses}) != sample_size({sample_size})")
            sample_size = wins + losses  # Fix it
        
        if win_rate is not None and (win_rate < 0 or win_rate > 1):
            logger.error(f"Invalid win_rate for user {user_id}: {win_rate}. Setting to None.")
            win_rate = None
        
        # Compute averages
        avg_win_pnl = sum(win_pnls) / len(win_pnls) if win_pnls else None
        avg_loss_pnl = sum(loss_pnls) / len(loss_pnls) if loss_pnls else None
        max_win_pnl = max(win_pnls) if win_pnls else None
        max_loss_pnl = min(loss_pnls) if loss_pnls else None  # Most negative
        avg_holding_period_seconds = sum(holding_periods) / len(holding_periods) if holding_periods else None
        
        # Build per-ticker stats
        per_ticker_stats = []
        for ticker, stats in ticker_stats.items():
            ticker_wins = stats["wins"]
            ticker_losses = stats["losses"]
            ticker_total = ticker_wins + ticker_losses
            ticker_win_rate = ticker_wins / ticker_total if ticker_total > 0 else None
            
            per_ticker_stats.append({
                "ticker": ticker,
                "trades": stats["trades"],
                "winRate": ticker_win_rate,
            })
        
        # Sort by trade count and take top 5
        per_ticker_stats.sort(key=lambda x: x["trades"], reverse=True)
        per_ticker_stats = per_ticker_stats[:5]
        
        # Compute average Regard Score at entry
        avg_regard_score_at_entry = (
            sum(regard_scores_at_entry) / len(regard_scores_at_entry)
            if regard_scores_at_entry else None
        )
        
        # Calculate period start/end
        period_start = None
        period_end = None
        if entry_times:
            try:
                period_start = datetime.fromisoformat(min(entry_times).replace("Z", "+00:00"))
            except Exception as e:
                logger.warning(f"Could not parse period_start: {e}")
        if exit_times:
            try:
                period_end = datetime.fromisoformat(max(exit_times).replace("Z", "+00:00"))
            except Exception as e:
                logger.warning(f"Could not parse period_end: {e}")
        
        # Market comparison removed - no longer used for scoring
        reference_capital = DEFAULT_REFERENCE_CAPITAL
        user_return = None
        benchmark_return = None
        relative_alpha = None
        
        # Reconstruct closed trades and open positions
        try:
            closed_trades_objs, open_positions_objs = await asyncio.wait_for(
                build_user_positions_and_trades(user_id, trades),
                timeout=10.0
            )
            
            open_positions_count = len(open_positions_objs)
            open_positions_unrealized_pnl = sum(
                op.unrealized_pnl for op in open_positions_objs 
                if op.unrealized_pnl is not None
            ) if open_positions_objs else None
            
            # Convert to dict format for compatibility
            open_positions_list = [
                {
                    "ticker": op.ticker,
                    "side": op.side,
                    "quantity": op.quantity,
                    "entry_price": op.avg_entry_price,
                    "current_price": op.current_price,
                    "unrealized_pnl": op.unrealized_pnl,
                    "unrealized_return": op.unrealized_return,
                    "entry_time": op.avg_entry_time.isoformat(),
                }
                for op in open_positions_objs
            ]
            
        except asyncio.TimeoutError:
            logger.warning(f"Position reconstruction timed out for user {user_id}")
            open_positions_count = 0
            open_positions_unrealized_pnl = None
            open_positions_list = []
        except Exception as e:
            logger.warning(f"Could not reconstruct positions: {e}")
            open_positions_count = 0
            open_positions_unrealized_pnl = None
            open_positions_list = []
        
        return UserRegardBaseStats(
            user_id=user_id,
            wins=wins,
            losses=losses,
            sample_size=sample_size,
            win_rate=win_rate,
            avg_win_pnl=avg_win_pnl,
            avg_loss_pnl=avg_loss_pnl,
            max_win_pnl=max_win_pnl,
            max_loss_pnl=max_loss_pnl,
            avg_holding_period_seconds=avg_holding_period_seconds,
            per_ticker_stats=per_ticker_stats,
            avg_regard_score_at_entry=avg_regard_score_at_entry,
            high_regard_trades_count=high_regard_count,
            low_regard_trades_count=low_regard_count,
            # Market-relative fields
            period_start=period_start,
            period_end=period_end,
            total_pnl=total_pnl,
            reference_capital=reference_capital,
            user_return=user_return,
            benchmark_return=benchmark_return,
            relative_alpha=relative_alpha,
            # Open positions
            open_positions_count=open_positions_count,
            open_positions_unrealized_pnl=open_positions_unrealized_pnl,
            open_positions_list=open_positions_list,
        )
        
    except Exception as e:
        logger.error(f"Error computing base stats for user {user_id}: {e}", exc_info=True)
        # Return empty stats on error
        return UserRegardBaseStats(
            user_id=user_id,
            wins=0,
            losses=0,
            sample_size=0,
            win_rate=None,
        )


async def run_user_regard_ai_analysis(base_stats: UserRegardBaseStats) -> Dict[str, Any]:
    """
    Use AI to convert base stats into a User Regard Score (0-100).
    
    Args:
        base_stats: UserRegardBaseStats object
        
    Returns:
        Dict with 'regardScore' (0-100), 'summary' (string), and optional 'rawAi'
    """
    client = _get_openai_client()
    
    # Build prompt
    win_rate_pct = (base_stats.win_rate * 100) if base_stats.win_rate is not None else None
    
    stats_parts = [
        f"- Wins: {base_stats.wins}",
        f"- Losses: {base_stats.losses}",
        f"- Sample size: {base_stats.sample_size}",
        f"- Win rate: {win_rate_pct:.1f}%" if win_rate_pct is not None else "- Win rate: N/A",
        f"- Average winning trade PnL: {base_stats.avg_win_pnl:.2f}" if base_stats.avg_win_pnl is not None else "- Average winning trade PnL: N/A",
        f"- Average losing trade PnL: {base_stats.avg_loss_pnl:.2f}" if base_stats.avg_loss_pnl is not None else "- Average losing trade PnL: N/A",
        f"- Max win PnL: {base_stats.max_win_pnl:.2f}" if base_stats.max_win_pnl is not None else "- Max win PnL: N/A",
        f"- Max loss PnL: {base_stats.max_loss_pnl:.2f}" if base_stats.max_loss_pnl is not None else "- Max loss PnL: N/A",
        f"- Average holding period (seconds): {base_stats.avg_holding_period_seconds:.0f}" if base_stats.avg_holding_period_seconds is not None else "- Average holding period (seconds): N/A",
    ]
    
    # Add open positions analysis
    if base_stats.open_positions_count > 0:
        stats_parts.append(f"- Open positions: {base_stats.open_positions_count}")
        if base_stats.open_positions_unrealized_pnl is not None:
            stats_parts.append(f"- Unrealized P/L from open positions: ${base_stats.open_positions_unrealized_pnl:.2f}")
        # Analyze open position types
        if base_stats.open_positions_list:
            long_opens = sum(1 for p in base_stats.open_positions_list if p.get("side") == "LONG")
            short_opens = sum(1 for p in base_stats.open_positions_list if p.get("side") == "SHORT")
            stats_parts.append(f"- Open positions breakdown: {long_opens} LONG, {short_opens} SHORT")
            
            # Check if holding losers (handle None values)
            losing_opens = sum(1 for p in base_stats.open_positions_list 
                             if p.get("unrealized_pnl") is not None and p.get("unrealized_pnl") < 0)
            winning_opens = sum(1 for p in base_stats.open_positions_list 
                              if p.get("unrealized_pnl") is not None and p.get("unrealized_pnl") > 0)
            if losing_opens > 0:
                stats_parts.append(f"- Currently holding {losing_opens} losing positions (bagholding indicator)")
            if winning_opens > 0:
                stats_parts.append(f"- Currently holding {winning_opens} winning positions")
    
    # Add Regard Score context if available
    if base_stats.avg_regard_score_at_entry is not None:
        stats_parts.append(f"- Average Regard Score at entry: {base_stats.avg_regard_score_at_entry:.1f}")
        stats_parts.append(f"- High Regard trades (score >= 70): {base_stats.high_regard_trades_count}")
        stats_parts.append(f"- Low Regard trades (score < 30): {base_stats.low_regard_trades_count}")
    
    stats_parts.append(f"- Per-ticker stats: {json.dumps(base_stats.per_ticker_stats, indent=2)}")
    
    stats_text = "\n".join(stats_parts)
    
    system_message = (
        "You are an assistant that rates a trader's REGARD SCORE from 0 to 100. "
        "NOTE: This is INVERTED - 100 = full degen gambler (high risk, YOLO plays) and 0 = disciplined smart investor. "
        "Consider: "
        "- Higher win rate and better risk/reward = LOWER score (smarter). "
        "- More trades = more data = more confidence in the score. "
        "- Very low sample sizes should keep scores closer to mid range (40-60). "
        "- Trading high Regard Score tickers (70+) = degen plays = HIGHER score. "
        "- Trading low Regard Score tickers (<30) = conservative = LOWER score. "
        "- OPEN POSITIONS: Holding many open positions, especially losing ones (bagholding), RAISES score. "
        "  Long-term holds in winning positions can LOWER score if they show patience and discipline. "
        "Score bands: 0-19 (disciplined), 20-39 (low regard), 40-59 (mid regard), 60-79 (high regard), 80-100 (full regard)."
    )
    
    user_message = (
        "You are rating a trader's REGARD SCORE from 0 to 100 (100 = full degen, 0 = disciplined).\n\n"
        f"Here are the trader's stats:\n{stats_text}\n\n"
        "Respond with a single JSON object:\n"
        '{"regardScore": <number between 0 and 100>, "summary": "<1-2 sentence explanation of this score>"}\n\n'
        "No extra text, JSON only."
    )
    
    try:
        if client:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                regard_score = result.get("regardScore", 50)
                summary = result.get("summary", "Score computed from trading performance.")
                
                # No market-relative adjustment - removed
                # Score is purely behavior-based + open position risk
                
                # Clamp to 0-100
                regard_score = max(0, min(100, int(regard_score)))
                
                return {
                    "regardScore": regard_score,
                    "summary": summary,
                    "rawAi": result,
                }
    except Exception as e:
        logger.error(f"AI analysis failed: {e}", exc_info=True)
    
    # Fallback: data-based mapping
    if base_stats.sample_size < 10 or base_stats.win_rate is None:
        regard_score = 50
        summary = "Score derived from win rate and trade count only (AI unavailable or insufficient data)."
    else:
        # Linear mapping from win rate, adjusted for sample size
        base_score = base_stats.win_rate * 100
        # Pull toward 50 if sample size is small
        sample_adjustment = min(1.0, base_stats.sample_size / 50.0)  # Full confidence at 50+ trades
        regard_score = 50 + (base_score - 50) * sample_adjustment
        regard_score = max(0, min(100, int(regard_score)))
        summary = f"Score derived from {base_stats.win_rate * 100:.1f}% win rate over {base_stats.sample_size} trades (AI unavailable)."
    
    return {
        "regardScore": regard_score,
        "summary": summary,
        "rawAi": None,
    }


async def save_user_regard_summary(
    user_id: str,
    base_stats: UserRegardBaseStats,
    ai_result: Dict[str, Any]
) -> None:
    """
    Save or update user regard summary in the database.
    
    Args:
        user_id: Supabase user ID
        base_stats: UserRegardBaseStats object
        ai_result: Dict from run_user_regard_ai_analysis
    """
    try:
        supabase = get_supabase_admin()
        
        regard_score = ai_result.get("regardScore")
        summary = ai_result.get("summary", "")
        raw_ai = ai_result.get("rawAi")
        
        # Sanity check: ensure wins + losses = sample_size
        if base_stats.wins + base_stats.losses != base_stats.sample_size:
            logger.warning(
                f"Inconsistency for user {user_id}: wins({base_stats.wins}) + losses({base_stats.losses}) != "
                f"sample_size({base_stats.sample_size}). Fixing before save."
            )
            base_stats.sample_size = base_stats.wins + base_stats.losses
        
        # Upsert the summary - only include fields that exist in the schema
        data = {
            "user_id": user_id,
            "regard_score": regard_score,
            "wins": base_stats.wins,
            "losses": base_stats.losses,
            "win_rate": base_stats.win_rate,
            "sample_size": base_stats.sample_size,
            "last_updated": datetime.utcnow().isoformat(),
            "ai_summary": summary,
            "ai_raw": raw_ai if raw_ai else None,
        }
        
        # Market-relative fields removed from scoring - no longer saved
        
        # Use upsert (insert or update on conflict)
        try:
            response = supabase.table("user_regard_summaries")\
                .upsert(data, on_conflict="user_id")\
                .execute()
        except Exception as e:
            # If error is about missing columns, retry without market-relative fields
            if "Could not find the" in str(e) and "column" in str(e):
                logger.warning(f"Market-relative columns don't exist yet. Saving without them. Run migration: migrations/add_benchmark_fields_to_user_regard_summaries.sql")
                # Remove market-relative fields and retry
                data_minimal = {
                    "user_id": user_id,
                    "regard_score": regard_score,
                    "wins": base_stats.wins,
                    "losses": base_stats.losses,
                    "win_rate": base_stats.win_rate,
                    "sample_size": base_stats.sample_size,
                    "last_updated": datetime.utcnow().isoformat(),
                    "ai_summary": summary,
                    "ai_raw": raw_ai if raw_ai else None,
                }
                response = supabase.table("user_regard_summaries")\
                    .upsert(data_minimal, on_conflict="user_id")\
                    .execute()
            else:
                raise
        
        logger.info(f"Saved user regard summary for user {user_id}: score={regard_score}, sample_size={base_stats.sample_size}")
        
    except Exception as e:
        logger.error(f"Error saving user regard summary for user {user_id}: {e}", exc_info=True)
        raise

