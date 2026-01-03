"""User Report Data aggregation service - collects all data needed for PDF reports."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.supabase_client import get_supabase_admin
from app.services.user_positions import build_user_positions_and_trades

logger = logging.getLogger(__name__)


class UserReportData:
    """Complete data model for user report generation."""
    def __init__(
        self,
        user_id: str,
        display_name: str,
        member_since: Optional[str] = None,
        regard_score: Optional[float] = None,
        wins: int = 0,
        losses: int = 0,
        win_rate: Optional[float] = None,
        sample_size: int = 0,
        last_updated: Optional[str] = None,
        ai_summary: Optional[str] = None,
        total_pnl: Optional[float] = None,
        best_trade_pnl: Optional[float] = None,
        worst_trade_pnl: Optional[float] = None,
        avg_win_pnl: Optional[float] = None,
        avg_loss_pnl: Optional[float] = None,
        time_window_start: Optional[str] = None,
        time_window_end: Optional[str] = None,
        per_ticker_stats: List[Dict[str, Any]] = None,
        holding_period_stats: Dict[str, Any] = None,
        time_of_day_stats: Dict[str, Any] = None,
        cumulative_pnl_data: List[Dict[str, Any]] = None,
        cumulative_total_pnl_data: List[Dict[str, Any]] = None,  # Realized + unrealized
        pnl_distribution: List[Dict[str, Any]] = None,
        trade_list: List[Dict[str, Any]] = None,
        long_count: int = 0,
        short_count: int = 0,
        # New metrics
        longest_win_streak: int = 0,
        longest_loss_streak: int = 0,
        current_streak_type: Optional[str] = None,  # "win" or "loss"
        current_streak_length: int = 0,
        monthly_breakdown: List[Dict[str, Any]] = None,
        best_month: Optional[Dict[str, Any]] = None,
        worst_month: Optional[Dict[str, Any]] = None,
        max_drawdown: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
        avg_position_size: Optional[float] = None,
        largest_position_size: Optional[float] = None,
        winner_avg_holding_period: Optional[float] = None,
        loser_avg_holding_period: Optional[float] = None,
        ticker_deep_dive: List[Dict[str, Any]] = None,
        trades_per_week: Optional[float] = None,
        trades_per_month: Optional[float] = None,
        most_active_period: Optional[str] = None,
        degen_trades: List[Dict[str, Any]] = None,  # High PnL trades (absolute value)
        # Market-relative performance
        user_return: Optional[float] = None,
        benchmark_return: Optional[float] = None,
        relative_alpha: Optional[float] = None,
        reference_capital: Optional[float] = None,
        # Open positions
        open_positions_count: int = 0,
        open_positions_unrealized_pnl: Optional[float] = None,
        open_positions_list: List[Dict[str, Any]] = None,
    ):
        self.user_id = user_id
        self.display_name = display_name
        self.member_since = member_since
        self.regard_score = regard_score
        self.wins = wins
        self.losses = losses
        self.win_rate = win_rate
        self.sample_size = sample_size
        self.last_updated = last_updated
        self.ai_summary = ai_summary
        self.total_pnl = total_pnl
        self.best_trade_pnl = best_trade_pnl
        self.worst_trade_pnl = worst_trade_pnl
        self.avg_win_pnl = avg_win_pnl
        self.avg_loss_pnl = avg_loss_pnl
        self.time_window_start = time_window_start
        self.time_window_end = time_window_end
        self.per_ticker_stats = per_ticker_stats or []
        self.holding_period_stats = holding_period_stats or {}
        self.time_of_day_stats = time_of_day_stats or {}
        self.cumulative_pnl_data = cumulative_pnl_data or []
        self.cumulative_total_pnl_data = cumulative_total_pnl_data or []
        self.pnl_distribution = pnl_distribution or []
        self.trade_list = trade_list or []
        self.long_count = long_count
        self.short_count = short_count
        # New metrics
        self.longest_win_streak = longest_win_streak
        self.longest_loss_streak = longest_loss_streak
        self.current_streak_type = current_streak_type
        self.current_streak_length = current_streak_length
        self.monthly_breakdown = monthly_breakdown or []
        self.best_month = best_month
        self.worst_month = worst_month
        self.max_drawdown = max_drawdown
        self.risk_reward_ratio = risk_reward_ratio
        self.avg_position_size = avg_position_size
        self.largest_position_size = largest_position_size
        self.winner_avg_holding_period = winner_avg_holding_period
        self.loser_avg_holding_period = loser_avg_holding_period
        self.ticker_deep_dive = ticker_deep_dive or []
        self.trades_per_week = trades_per_week
        self.trades_per_month = trades_per_month
        self.most_active_period = most_active_period
        self.degen_trades = degen_trades or []
        # Market-relative performance
        self.user_return = user_return
        self.benchmark_return = benchmark_return
        self.relative_alpha = relative_alpha
        self.reference_capital = reference_capital
        # Open positions
        self.open_positions_count = open_positions_count
        self.open_positions_unrealized_pnl = open_positions_unrealized_pnl
        self.open_positions_list = open_positions_list or []


async def build_user_report_data(user_id: str, display_name: Optional[str] = None) -> UserReportData:
    """
    Build complete user report data from database.
    
    Args:
        user_id: Supabase user ID
        display_name: Optional display name (if not provided, will try to fetch from user metadata)
        
    Returns:
        UserReportData object with all metrics
    """
    try:
        supabase = get_supabase_admin()
        
        # Get display name from user metadata if not provided
        if not display_name:
            # Display name should be passed in from the endpoint (from AuthenticatedUser)
            # If not provided, use fallback
            display_name = "Trader"
        
        # Get member since date (approximate from user creation)
        # Note: This would require admin access to auth.users table
        # For now, we'll skip this and let it be None
        member_since = None
        
        # Fetch user regard summary
        summary_response = supabase.table("user_regard_summaries")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        summary = summary_response.data[0] if summary_response.data else None
        
        # Use canonical source from user_regard_summaries for all top-level stats
        regard_score = float(summary.get("regard_score")) if summary and summary.get("regard_score") is not None else None
        wins = summary.get("wins", 0) if summary else 0
        losses = summary.get("losses", 0) if summary else 0
        win_rate = float(summary.get("win_rate")) if summary and summary.get("win_rate") is not None else None
        sample_size = summary.get("sample_size", 0) if summary else 0
        last_updated = summary.get("last_updated") if summary else None
        ai_summary = summary.get("ai_summary") if summary else None
        
        # Market-relative fields from summary
        user_return = float(summary.get("user_return")) if summary and summary.get("user_return") is not None else None
        benchmark_return = float(summary.get("benchmark_return")) if summary and summary.get("benchmark_return") is not None else None
        relative_alpha = float(summary.get("relative_alpha")) if summary and summary.get("relative_alpha") is not None else None
        reference_capital = float(summary.get("reference_capital")) if summary and summary.get("reference_capital") is not None else None
        
        # Sanity check: ensure wins + losses = sample_size
        if wins + losses != sample_size:
            logger.warning(
                f"Data inconsistency for user {user_id}: wins({wins}) + losses({losses}) != sample_size({sample_size}). "
                f"Using corrected value."
            )
            sample_size = wins + losses
            win_rate = wins / sample_size if sample_size > 0 else None
        
        # Fetch all trades
        trades_response = supabase.table("user_trades")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("entry_time", desc=False)\
            .execute()
        
        trades = trades_response.data if trades_response.data else []
        
        if not trades:
            return UserReportData(
                user_id=user_id,
                display_name=display_name,
                member_since=member_since,
                regard_score=regard_score,
                wins=wins,
                losses=losses,
                win_rate=win_rate,
                sample_size=sample_size,
                last_updated=last_updated,
                ai_summary=ai_summary,
            )
        
        # Compute aggregate metrics
        total_pnl = 0.0
        win_pnls = []
        loss_pnls = []
        holding_periods = []
        entry_times = []
        exit_times = []
        long_count = 0
        short_count = 0
        
        # Per-ticker aggregation
        ticker_stats: Dict[str, Dict[str, Any]] = {}
        
        # Holding period buckets
        holding_buckets = {
            "<15m": {"trades": 0, "wins": 0, "losses": 0},
            "15m-1h": {"trades": 0, "wins": 0, "losses": 0},
            "1h-1d": {"trades": 0, "wins": 0, "losses": 0},
            "1d-5d": {"trades": 0, "wins": 0, "losses": 0},
            ">5d": {"trades": 0, "wins": 0, "losses": 0},
        }
        
        # Time of day buckets (market hours: 9:30-16:00 ET)
        time_buckets = {
            "pre-market": {"trades": 0, "wins": 0, "losses": 0},  # < 9:30
            "open": {"trades": 0, "wins": 0, "losses": 0},  # 9:30-11:00
            "mid": {"trades": 0, "wins": 0, "losses": 0},  # 11:00-14:00
            "close": {"trades": 0, "wins": 0, "losses": 0},  # 14:00-16:00
            "after-hours": {"trades": 0, "wins": 0, "losses": 0},  # > 16:00
        }
        
        # Process each trade
        for trade in trades:
            pnl = float(trade.get("realized_pnl", 0))
            total_pnl += pnl
            
            if pnl > 0:
                win_pnls.append(pnl)
            elif pnl < 0:
                loss_pnls.append(pnl)
            
            holding_period = trade.get("holding_period_seconds", 0)
            holding_periods.append(holding_period)
            
            # Bucket holding period
            if holding_period < 900:  # < 15 minutes
                bucket = "<15m"
            elif holding_period < 3600:  # < 1 hour
                bucket = "15m-1h"
            elif holding_period < 86400:  # < 1 day
                bucket = "1h-1d"
            elif holding_period < 432000:  # < 5 days
                bucket = "1d-5d"
            else:
                bucket = ">5d"
            
            holding_buckets[bucket]["trades"] += 1
            if pnl > 0:
                holding_buckets[bucket]["wins"] += 1
            elif pnl < 0:
                holding_buckets[bucket]["losses"] += 1
            
            # Time of day analysis (using entry time)
            entry_time_str = trade.get("entry_time")
            if entry_time_str:
                try:
                    entry_dt = datetime.fromisoformat(entry_time_str.replace("Z", "+00:00"))
                    # Convert to ET (approximate)
                    hour = entry_dt.hour
                    if hour < 9 or (hour == 9 and entry_dt.minute < 30):
                        time_bucket = "pre-market"
                    elif hour < 11:
                        time_bucket = "open"
                    elif hour < 14:
                        time_bucket = "mid"
                    elif hour < 16:
                        time_bucket = "close"
                    else:
                        time_bucket = "after-hours"
                    
                    time_buckets[time_bucket]["trades"] += 1
                    if pnl > 0:
                        time_buckets[time_bucket]["wins"] += 1
                    elif pnl < 0:
                        time_buckets[time_bucket]["losses"] += 1
                except Exception:
                    pass
            
            # Side tracking
            side = trade.get("side", "").upper()
            if side in ("LONG", "BUY"):
                long_count += 1
            elif side in ("SHORT", "SELL"):
                short_count += 1
            
            # Per-ticker stats
            ticker = trade.get("ticker", "").upper()
            if ticker:
                if ticker not in ticker_stats:
                    ticker_stats[ticker] = {
                        "ticker": ticker,
                        "trades": 0,
                        "wins": 0,
                        "losses": 0,
                        "total_pnl": 0.0,
                        "pnls": [],
                    }
                ticker_stats[ticker]["trades"] += 1
                ticker_stats[ticker]["total_pnl"] += pnl
                ticker_stats[ticker]["pnls"].append(pnl)
                if pnl > 0:
                    ticker_stats[ticker]["wins"] += 1
                elif pnl < 0:
                    ticker_stats[ticker]["losses"] += 1
            
            entry_times.append(entry_time_str)
            exit_times.append(trade.get("exit_time"))
        
        # Compute best/worst trades
        best_trade_pnl = max(win_pnls) if win_pnls else None
        worst_trade_pnl = min(loss_pnls) if loss_pnls else None
        avg_win_pnl = sum(win_pnls) / len(win_pnls) if win_pnls else None
        avg_loss_pnl = sum(loss_pnls) / len(loss_pnls) if loss_pnls else None
        
        # Time window
        time_window_start = min([t for t in entry_times if t]) if entry_times else None
        time_window_end = max([t for t in exit_times if t]) if exit_times else None
        
        # Build per-ticker stats (top 10 by trade count)
        per_ticker_list = []
        for ticker, stats in ticker_stats.items():
            ticker_wins = stats["wins"]
            ticker_losses = stats["losses"]
            ticker_total = ticker_wins + ticker_losses
            ticker_win_rate = ticker_wins / ticker_total if ticker_total > 0 else None
            avg_pnl_per_trade = stats["total_pnl"] / stats["trades"] if stats["trades"] > 0 else 0.0
            
            per_ticker_list.append({
                "ticker": ticker,
                "tradeCount": stats["trades"],
                "winRate": ticker_win_rate,
                "netPnl": stats["total_pnl"],
                "avgPnlPerTrade": avg_pnl_per_trade,
            })
        
        per_ticker_list.sort(key=lambda x: x["tradeCount"], reverse=True)
        per_ticker_list = per_ticker_list[:10]  # Top 10
        
        # Build holding period stats with win rates
        holding_period_stats = {}
        for bucket, data in holding_buckets.items():
            total = data["trades"]
            if total > 0:
                win_rate = data["wins"] / total
                holding_period_stats[bucket] = {
                    "trades": total,
                    "winRate": win_rate,
                }
        
        # Build time of day stats
        time_of_day_stats = {}
        for bucket, data in time_buckets.items():
            total = data["trades"]
            if total > 0:
                win_rate = data["wins"] / total
                time_of_day_stats[bucket] = {
                    "trades": total,
                    "winRate": win_rate,
                }
        
        # Build cumulative realized PnL data (sorted by entry time)
        cumulative_pnl_data = []
        running_total = 0.0
        sorted_trades = sorted(trades, key=lambda t: t.get("entry_time", ""))
        for trade in sorted_trades:
            pnl = float(trade.get("realized_pnl", 0))
            running_total += pnl
            entry_time = trade.get("entry_time")
            if entry_time:
                cumulative_pnl_data.append({
                    "date": entry_time,
                    "cumulativePnl": running_total,
                })
        
        # Build PnL distribution (for histogram)
        pnl_ranges = [
            (-float('inf'), -1000, "<-$1k"),
            (-1000, -500, "-$1k to -$500"),
            (-500, -100, "-$500 to -$100"),
            (-100, 0, "-$100 to $0"),
            (0, 100, "$0 to $100"),
            (100, 500, "$100 to $500"),
            (500, 1000, "$500 to $1k"),
            (1000, float('inf'), ">$1k"),
        ]
        
        pnl_distribution = []
        all_pnls = [float(t.get("realized_pnl", 0)) for t in trades]
        for min_val, max_val, label in pnl_ranges:
            count = sum(1 for pnl in all_pnls if min_val <= pnl < max_val)
            if count > 0:
                pnl_distribution.append({
                    "range": label,
                    "count": count,
                })
        
        # Build trade list (last 200 trades or all if fewer)
        trade_list = []
        for trade in sorted_trades[-200:]:  # Last 200
            trade_list.append({
                "ticker": trade.get("ticker", "").upper(),
                "side": trade.get("side", ""),
                "quantity": float(trade.get("quantity", 0)),
                "entry_time": trade.get("entry_time"),
                "exit_time": trade.get("exit_time"),
                "entry_price": float(trade.get("entry_price", 0)) if trade.get("entry_price") else None,
                "exit_price": float(trade.get("exit_price", 0)) if trade.get("exit_price") else None,
                "realized_pnl": float(trade.get("realized_pnl", 0)),
            })
        
        # ===== COMPUTE NEW METRICS =====
        
        # 1. Streak Analysis
        longest_win_streak = 0
        longest_loss_streak = 0
        current_streak_type = None
        current_streak_length = 0
        
        if sorted_trades:
            current_streak = 0
            current_type = None
            
            for trade in sorted_trades:
                pnl = float(trade.get("realized_pnl", 0))
                if pnl > 0:  # Win
                    if current_type == "win":
                        current_streak += 1
                    else:
                        # End previous streak
                        if current_type == "loss" and current_streak > longest_loss_streak:
                            longest_loss_streak = current_streak
                        # Start new win streak
                        current_streak = 1
                        current_type = "win"
                elif pnl < 0:  # Loss
                    if current_type == "loss":
                        current_streak += 1
                    else:
                        # End previous streak
                        if current_type == "win" and current_streak > longest_win_streak:
                            longest_win_streak = current_streak
                        # Start new loss streak
                        current_streak = 1
                        current_type = "loss"
                # Note: pnl == 0 is treated as breaking the streak (neutral)
                else:
                    if current_type == "win" and current_streak > longest_win_streak:
                        longest_win_streak = current_streak
                    elif current_type == "loss" and current_streak > longest_loss_streak:
                        longest_loss_streak = current_streak
                    current_streak = 0
                    current_type = None
            
            # Check final streak
            if current_type == "win" and current_streak > longest_win_streak:
                longest_win_streak = current_streak
            elif current_type == "loss" and current_streak > longest_loss_streak:
                longest_loss_streak = current_streak
            
            # Current streak (from most recent trade)
            last_pnl = float(sorted_trades[-1].get("realized_pnl", 0))
            if last_pnl > 0:
                current_streak_type = "win"
            elif last_pnl < 0:
                current_streak_type = "loss"
            
            # Count backwards to get current streak length
            if current_streak_type:
                current_streak_length = 0
                for trade in reversed(sorted_trades):
                    pnl = float(trade.get("realized_pnl", 0))
                    if (current_streak_type == "win" and pnl > 0) or (current_streak_type == "loss" and pnl < 0):
                        current_streak_length += 1
                    else:
                        break
        
        # 2. Monthly Breakdown
        monthly_stats: Dict[str, Dict[str, Any]] = {}
        for trade in sorted_trades:
            entry_time_str = trade.get("entry_time")
            if not entry_time_str:
                continue
            try:
                entry_dt = datetime.fromisoformat(entry_time_str.replace("Z", "+00:00"))
                month_key = entry_dt.strftime("%Y-%m")
                month_name = entry_dt.strftime("%B %Y")
                
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {
                        "month": month_name,
                        "trades": 0,
                        "wins": 0,
                        "losses": 0,
                        "total_pnl": 0.0,
                    }
                
                pnl = float(trade.get("realized_pnl", 0))
                monthly_stats[month_key]["trades"] += 1
                monthly_stats[month_key]["total_pnl"] += pnl
                if pnl > 0:
                    monthly_stats[month_key]["wins"] += 1
                elif pnl < 0:
                    monthly_stats[month_key]["losses"] += 1
            except Exception:
                pass
        
        monthly_breakdown = []
        for month_key in sorted(monthly_stats.keys()):
            stats = monthly_stats[month_key]
            total = stats["wins"] + stats["losses"]
            win_rate = stats["wins"] / total if total > 0 else None
            monthly_breakdown.append({
                "month": stats["month"],
                "trades": stats["trades"],
                "wins": stats["wins"],
                "losses": stats["losses"],
                "winRate": win_rate,
                "totalPnl": stats["total_pnl"],
            })
        
        # Best/worst month
        best_month = None
        worst_month = None
        if monthly_breakdown:
            best_month = max(monthly_breakdown, key=lambda x: x["totalPnl"])
            worst_month = min(monthly_breakdown, key=lambda x: x["totalPnl"])
        
        # 3. Risk Metrics
        # Max drawdown (largest peak-to-trough decline)
        max_drawdown = None
        if cumulative_pnl_data:
            peak = cumulative_pnl_data[0]["cumulativePnl"]
            max_dd = 0.0
            for point in cumulative_pnl_data:
                if point["cumulativePnl"] > peak:
                    peak = point["cumulativePnl"]
                drawdown = peak - point["cumulativePnl"]
                if drawdown > max_dd:
                    max_dd = drawdown
            max_drawdown = max_dd if max_dd > 0 else None
        
        # Risk/reward ratio (avg win / avg loss)
        risk_reward_ratio = None
        if avg_win_pnl is not None and avg_loss_pnl is not None and avg_loss_pnl != 0:
            risk_reward_ratio = abs(avg_win_pnl / avg_loss_pnl)
        
        # Position sizing
        position_sizes = [float(t.get("quantity", 0)) * float(t.get("entry_price", 0)) 
                        for t in trades if t.get("entry_price") and t.get("quantity")]
        avg_position_size = sum(position_sizes) / len(position_sizes) if position_sizes else None
        largest_position_size = max(position_sizes) if position_sizes else None
        
        # 4. Exit Timing Analysis
        winner_holding_periods = [float(t.get("holding_period_seconds", 0)) 
                                 for t in trades if float(t.get("realized_pnl", 0)) > 0]
        loser_holding_periods = [float(t.get("holding_period_seconds", 0)) 
                                for t in trades if float(t.get("realized_pnl", 0)) < 0]
        
        winner_avg_holding_period = sum(winner_holding_periods) / len(winner_holding_periods) if winner_holding_periods else None
        loser_avg_holding_period = sum(loser_holding_periods) / len(loser_holding_periods) if loser_holding_periods else None
        
        # 5. Ticker Deep Dive (top 3-5 tickers with detailed info)
        ticker_deep_dive = []
        for ticker_stat in per_ticker_list[:5]:  # Top 5
            ticker = ticker_stat["ticker"]
            ticker_trades = [t for t in sorted_trades if t.get("ticker", "").upper() == ticker]
            
            # Get entry/exit times for this ticker
            ticker_entries = []
            ticker_exits = []
            ticker_pnls = []
            for t in ticker_trades:
                entry_time = t.get("entry_time")
                exit_time = t.get("exit_time")
                pnl = float(t.get("realized_pnl", 0))
                if entry_time:
                    ticker_entries.append(entry_time)
                if exit_time:
                    ticker_exits.append(exit_time)
                ticker_pnls.append(pnl)
            
            ticker_deep_dive.append({
                "ticker": ticker,
                "tradeCount": ticker_stat["tradeCount"],
                "winRate": ticker_stat["winRate"],
                "netPnl": ticker_stat["netPnl"],
                "avgPnlPerTrade": ticker_stat["avgPnlPerTrade"],
                "firstTrade": min(ticker_entries) if ticker_entries else None,
                "lastTrade": max(ticker_entries) if ticker_entries else None,
                "bestTradePnl": max(ticker_pnls) if ticker_pnls else None,
                "worstTradePnl": min(ticker_pnls) if ticker_pnls else None,
            })
        
        # 6. Trading Velocity
        if entry_times and time_window_start and time_window_end:
            try:
                start_dt = datetime.fromisoformat(time_window_start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(time_window_end.replace("Z", "+00:00"))
                days_diff = (end_dt - start_dt).days
                weeks_diff = days_diff / 7.0
                months_diff = days_diff / 30.0
                
                if days_diff > 0:
                    trades_per_week = len(trades) / weeks_diff if weeks_diff > 0 else None
                    trades_per_month = len(trades) / months_diff if months_diff > 0 else None
                else:
                    trades_per_week = None
                    trades_per_month = None
            except Exception:
                trades_per_week = None
                trades_per_month = None
        else:
            trades_per_week = None
            trades_per_month = None
        
        # Most active period (day of week or time of day)
        day_of_week_counts: Dict[str, int] = defaultdict(int)
        for trade in sorted_trades:
            entry_time_str = trade.get("entry_time")
            if entry_time_str:
                try:
                    entry_dt = datetime.fromisoformat(entry_time_str.replace("Z", "+00:00"))
                    day_name = entry_dt.strftime("%A")
                    day_of_week_counts[day_name] += 1
                except Exception:
                    pass
        
        most_active_period = max(day_of_week_counts.items(), key=lambda x: x[1])[0] if day_of_week_counts else None
        
        # 7. Degen Moments (trades with highest absolute PnL - biggest wins and losses)
        degen_trades = []
        all_trades_with_abs_pnl = [(t, abs(float(t.get("realized_pnl", 0)))) for t in sorted_trades]
        all_trades_with_abs_pnl.sort(key=lambda x: x[1], reverse=True)
        
        for trade, abs_pnl in all_trades_with_abs_pnl[:10]:  # Top 10 by absolute PnL
            degen_trades.append({
                "ticker": trade.get("ticker", "").upper(),
                "side": trade.get("side", ""),
                "entry_time": trade.get("entry_time"),
                "realized_pnl": float(trade.get("realized_pnl", 0)),
                "quantity": float(trade.get("quantity", 0)),
            })
        
        # Reconstruct open positions from trade history
        try:
            closed_trades_objs, open_positions_objs = await build_user_positions_and_trades(user_id, trades)
            
            open_positions_count = len(open_positions_objs)
            open_positions_unrealized_pnl = sum(
                op.unrealized_pnl for op in open_positions_objs 
                if op.unrealized_pnl is not None
            ) if open_positions_objs else None
            
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
        except Exception as e:
            logger.warning(f"Could not reconstruct open positions: {e}")
            open_positions_count = 0
            open_positions_unrealized_pnl = None
            open_positions_list = []
        
        # No total PnL data needed - removed per user request
        cumulative_total_pnl_data = []
        
        return UserReportData(
            user_id=user_id,
            display_name=display_name,
            member_since=member_since,
            regard_score=regard_score,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            sample_size=sample_size,
            last_updated=last_updated,
            ai_summary=ai_summary,
            total_pnl=total_pnl if trades else None,
            best_trade_pnl=best_trade_pnl,
            worst_trade_pnl=worst_trade_pnl,
            avg_win_pnl=avg_win_pnl,
            avg_loss_pnl=avg_loss_pnl,
            time_window_start=time_window_start,
            time_window_end=time_window_end,
            per_ticker_stats=per_ticker_list,
            holding_period_stats=holding_period_stats,
            time_of_day_stats=time_of_day_stats,
            cumulative_pnl_data=cumulative_pnl_data,
            cumulative_total_pnl_data=cumulative_total_pnl_data,
            pnl_distribution=pnl_distribution,
            trade_list=trade_list,
            long_count=long_count,
            short_count=short_count,
            # New metrics
            longest_win_streak=longest_win_streak,
            longest_loss_streak=longest_loss_streak,
            current_streak_type=current_streak_type,
            current_streak_length=current_streak_length,
            monthly_breakdown=monthly_breakdown,
            best_month=best_month,
            worst_month=worst_month,
            max_drawdown=max_drawdown,
            risk_reward_ratio=risk_reward_ratio,
            avg_position_size=avg_position_size,
            largest_position_size=largest_position_size,
            winner_avg_holding_period=winner_avg_holding_period,
            loser_avg_holding_period=loser_avg_holding_period,
            ticker_deep_dive=ticker_deep_dive,
            trades_per_week=trades_per_week,
            trades_per_month=trades_per_month,
            most_active_period=most_active_period,
            degen_trades=degen_trades,
            # Market-relative performance
            user_return=user_return,
            benchmark_return=benchmark_return,
            relative_alpha=relative_alpha,
            reference_capital=reference_capital,
            # Open positions
            open_positions_count=open_positions_count,
            open_positions_unrealized_pnl=open_positions_unrealized_pnl,
            open_positions_list=open_positions_list,
        )
        
    except Exception as e:
        logger.error(f"Error building user report data for {user_id}: {e}", exc_info=True)
        raise

