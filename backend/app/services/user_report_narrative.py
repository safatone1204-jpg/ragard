"""User Report Narrative generation - AI-powered personalized text (no fake numbers)."""
import logging
import json
import asyncio
from typing import Dict, Any, Optional

from app.services.ai_client import _get_openai_client
from app.services.user_report_data import UserReportData

logger = logging.getLogger(__name__)


class UserReportNarrative:
    """Narrative content for user report (text only, no numbers)."""
    def __init__(
        self,
        executive_summary_paragraphs: list[str],
        style_summary: str,
        strengths: list[str],
        weaknesses: list[str],
        behavioural_patterns: list[str],
        recommendations: list[str],
        thirty_day_plan: list[str],
        tone_note: Optional[str] = None,
    ):
        self.executive_summary_paragraphs = executive_summary_paragraphs
        self.style_summary = style_summary
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.behavioural_patterns = behavioural_patterns
        self.recommendations = recommendations
        self.thirty_day_plan = thirty_day_plan
        self.tone_note = tone_note
        # Section-specific AI analyses (optional, added later)
        self.performance_analytics_analysis: Optional[str] = None
        self.score_breakdown_analysis: Optional[str] = None
        self.style_behavior_analysis: Optional[str] = None


def _categorize_win_rate(win_rate: Optional[float]) -> str:
    """Categorize win rate into qualitative description."""
    if win_rate is None:
        return "unknown"
    if win_rate >= 0.65:
        return "high"
    elif win_rate >= 0.50:
        return "medium-high"
    elif win_rate >= 0.35:
        return "medium"
    elif win_rate >= 0.20:
        return "low-medium"
    else:
        return "low"


def _categorize_regard_score(score: Optional[float]) -> str:
    """Categorize regard score into qualitative description."""
    if score is None:
        return "unknown"
    if score >= 80:
        return "full_regard"
    elif score >= 60:
        return "high_regard"
    elif score >= 40:
        return "mid_regard"
    elif score >= 20:
        return "low_regard"
    else:
        return "zero_regard"


def _categorize_overall_pnl(total_pnl: Optional[float]) -> str:
    """Categorize overall PnL into qualitative description."""
    if total_pnl is None:
        return "unknown"
    if total_pnl > 1000:
        return "solid_profit"
    elif total_pnl > 0:
        return "slight_profit"
    elif total_pnl > -1000:
        return "slight_loss"
    else:
        return "significant_loss"


def _categorize_holding_style(winner_avg: Optional[float], loser_avg: Optional[float]) -> str:
    """Categorize dominant holding style based on average holding periods."""
    avg_seconds = None
    if winner_avg is not None and loser_avg is not None:
        avg_seconds = (winner_avg + loser_avg) / 2
    elif winner_avg is not None:
        avg_seconds = winner_avg
    elif loser_avg is not None:
        avg_seconds = loser_avg
    
    if avg_seconds is None:
        return "unknown"
    
    if avg_seconds < 900:  # < 15 minutes
        return "scalper"
    elif avg_seconds < 86400:  # < 1 day
        return "intraday"
    elif avg_seconds < 432000:  # < 5 days
        return "swing"
    else:
        return "position"


def _describe_holding_patterns(holding_stats: Dict[str, Any]) -> str:
    """Describe holding period patterns qualitatively."""
    if not holding_stats:
        return "insufficient data"
    
    # Find best and worst buckets
    best_bucket = None
    best_win_rate = 0.0
    worst_bucket = None
    worst_win_rate = 1.0
    
    for bucket, data in holding_stats.items():
        win_rate = data.get("winRate", 0)
        if win_rate > best_win_rate:
            best_win_rate = win_rate
            best_bucket = bucket
        if win_rate < worst_win_rate:
            worst_win_rate = win_rate
            worst_bucket = bucket
    
    if best_bucket and worst_bucket:
        return f"better on {best_bucket} trades than {worst_bucket}"
    return "mixed patterns"


async def generate_user_report_narrative(data: UserReportData) -> UserReportNarrative:
    """
    Generate AI-powered narrative for user report.
    
    CRITICAL: AI must NOT invent any numbers, tickers, or specific counts.
    All numeric facts come from the data model, not from AI.
    
    Args:
        data: UserReportData object with all metrics
        
    Returns:
        UserReportNarrative with personalized text
    """
    client = _get_openai_client()
    
    if not client:
        logger.warning("OpenAI client not available, using fallback narrative")
        return _generate_fallback_narrative(data)
    
    # Build qualitative descriptions (no specific numbers)
    win_rate_category = _categorize_win_rate(data.win_rate)
    regard_category = _categorize_regard_score(data.regard_score)
    holding_pattern = _describe_holding_patterns(data.holding_period_stats)
    pnl_category = _categorize_overall_pnl(data.total_pnl)
    holding_style = _categorize_holding_style(data.winner_avg_holding_period, data.loser_avg_holding_period)
    
    # Build context string (qualitative only)
    context_parts = [
        f"User: {data.display_name}",
        f"Regard Score category: {regard_category} (where 100 = full degen YOLO machine, 0 = boring disciplined boomer)",
        f"Win rate category: {win_rate_category}",
        f"Overall PnL outcome: {pnl_category}",
        f"Dominant holding style: {holding_style}",
        f"Holding pattern: {holding_pattern}",
    ]
    
    if data.long_count > data.short_count * 2:
        context_parts.append("Almost exclusively trades long (rarely shorts)")
    elif data.short_count > data.long_count * 2:
        context_parts.append("Heavy on short positions (bear gang)")
    elif data.long_count > data.short_count:
        context_parts.append("Primarily trades long positions")
    elif data.short_count > data.long_count:
        context_parts.append("Primarily trades short positions")
    else:
        context_parts.append("Balanced long/short mix")
    
    if data.per_ticker_stats:
        top_ticker = data.per_ticker_stats[0]["ticker"]
        context_parts.append(f"Most traded ticker: {top_ticker} (but do NOT mention specific ticker names in narrative)")
    
    if data.avg_win_pnl and data.avg_loss_pnl:
        if abs(data.avg_win_pnl) > abs(data.avg_loss_pnl) * 1.5:
            context_parts.append("Wins are significantly larger than losses (good risk/reward, lets winners run)")
        elif abs(data.avg_loss_pnl) > abs(data.avg_win_pnl) * 1.5:
            context_parts.append("Losses are significantly larger than wins (poor risk/reward, cuts winners early, holds losers)")
        else:
            context_parts.append("Win and loss sizes are relatively balanced")
    
    if data.longest_win_streak and data.longest_win_streak >= 5:
        context_parts.append(f"Has gone on hot streaks (longest win streak is solid)")
    if data.longest_loss_streak and data.longest_loss_streak >= 5:
        context_parts.append(f"Has experienced brutal losing streaks (tilt risk)")
    
    # Open positions analysis
    if data.open_positions_count > 0:
        context_parts.append(f"Currently has {data.open_positions_count} aggregated open positions")
        if data.open_positions_unrealized_pnl is not None:
            if data.open_positions_unrealized_pnl < -500:
                context_parts.append("Bagholding significant unrealized losers (classic degen behavior)")
            elif data.open_positions_unrealized_pnl > 500:
                context_parts.append("Letting winners run in open positions with unrealized gains (disciplined)")
            elif data.open_positions_unrealized_pnl < 0:
                context_parts.append("Open positions showing unrealized losses")
            else:
                context_parts.append("Open positions showing unrealized gains")
    else:
        context_parts.append("No open positions - everything is closed (all P/L is realized)")
    
    context_text = "\n".join(context_parts)
    
    system_message = (
        "You are a trading coach who writes like a mix of a professional analyst and a /r/wallstreetbets regular. "
        "Your voice: unfiltered, Reddit-coded, slightly feral, but still coherent and insightful. "
        "You can swear, use slang (degen, ape, YOLO, bagholding, diamond hands, paper hands, FOMO, copium, tilt, full send, regarded, etc.), "
        "and call out bad decisions directly. Think: brutally honest friend who trades, not corporate HR-approved content.\n\n"
        "IMPORTANT: The Regard Score measures how 'regarded' a trader is (higher score = more regarded/degen). "
        "Use 'regarded' as an adjective when appropriate (e.g., 'pretty regarded move', 'highly regarded behavior').\n\n"
        "TONE EXAMPLES:\n"
        "- 'You YOLOd into some absolute trash and somehow came out slightly green. Respect.'\n"
        "- 'Your risk management is non-existent. You hold losers like they owe you money.'\n"
        "- 'Classic paper hands energy - you cut winners early and let losers ride. Fix that.'\n"
        "- 'You're bagholding some serious losers. Diamond hands or denial?'\n\n"
        "CRITICAL RULES:\n"
        "1. DO NOT invent any specific numbers, counts, percentages, ticker names, or dates. EVER.\n"
        "2. DO NOT say things like 'You have 57 trades' or 'Your win rate is 62%' or 'You traded TSLA 12 times'.\n"
        "3. Only speak qualitatively about patterns and directions.\n"
        "4. RESPECT THE PROVIDED LABELS:\n"
        "   - If pnl_category = 'significant_loss', you MUST acknowledge they're deep red.\n"
        "   - If holding_style = 'scalper', don't call them a 'swing trader'.\n"
        "   - If they have open positions with unrealized losses, mention bagholding.\n"
        "5. NO slurs, hate speech, or TOS-breaking content. Swearing is fine, bigotry is not.\n"
        "6. Keep it PG-13 max - edgy but not offensive.\n"
        "7. Remember: 100 Regard Score = full degen gambler, 0 = disciplined boring investor.\n"
        "8. All numeric facts will be displayed separately - your job is narrative and interpretation only.\n"
        "9. DO NOT mention market performance, SPY, or benchmark comparisons."
    )
    
    user_message = (
        f"Generate a personalized trading performance report narrative for {data.display_name}.\n\n"
        f"Context (qualitative only - NO SPECIFIC NUMBERS ALLOWED):\n{context_text}\n\n"
        "Respond with a JSON object containing:\n"
        "{\n"
        '  "executiveSummaryParagraphs": ["paragraph 1", "paragraph 2"],  // 2-3 paragraphs max, Reddit-coded but coherent\n'
        '  "styleSummary": "2-3 sentences describing their trading style with personality",\n'
        '  "strengths": ["strength 1", "strength 2", "strength 3"],  // What they do well\n'
        '  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],  // What they fuck up\n'
        '  "behaviouralPatterns": ["pattern 1", "pattern 2", "pattern 3"],  // Observed patterns\n'
        '  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],  // Actionable advice\n'
        '  "thirtyDayPlan": ["action 1", "action 2", "action 3", "action 4", "action 5"],  // 30-day game plan\n'
        '  "toneNote": "optional short tagline"\n'
        "}\n\n"
        "Remember: NO specific numbers, tickers, or counts. Only qualitative observations. Be unfiltered but insightful."
    )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,  # Higher temperature for more personality and Reddit energy
            max_tokens=2000,  # More tokens for detailed Reddit-style commentary
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            
            # Validate and extract fields
            executive_summary = result.get("executiveSummaryParagraphs", [])
            if isinstance(executive_summary, str):
                executive_summary = [executive_summary]
            
            narrative = UserReportNarrative(
                executive_summary_paragraphs=executive_summary[:3],  # Max 3 paragraphs
                style_summary=result.get("styleSummary", "Trading style analysis unavailable."),
                strengths=result.get("strengths", [])[:5],  # Max 5
                weaknesses=result.get("weaknesses", [])[:5],
                behavioural_patterns=result.get("behaviouralPatterns", [])[:5],
                recommendations=result.get("recommendations", [])[:5],
                thirty_day_plan=result.get("thirtyDayPlan", [])[:5],
                tone_note=result.get("toneNote"),
            )
            
            # Generate section-specific analyses
            try:
                section_analyses = await _generate_section_analyses(client, data)
                narrative.performance_analytics_analysis = section_analyses.get("performance_analytics")
                narrative.score_breakdown_analysis = section_analyses.get("score_breakdown")
                narrative.style_behavior_analysis = section_analyses.get("style_behavior")
            except Exception as e:
                logger.warning(f"Could not generate section analyses: {e}")
            
            return narrative
    
    except Exception as e:
        logger.error(f"AI narrative generation failed: {e}", exc_info=True)
        return _generate_fallback_narrative(data)
    
    return _generate_fallback_narrative(data)


async def _generate_section_analyses(client, data: UserReportData) -> Dict[str, str]:
    """Generate AI analyses for specific sections with real ticker data."""
    
    # Build Performance Analytics context with REAL tickers and numbers
    perf_context = f"User: {data.display_name}, Regard Score: {data.regard_score}/100\n\n"
    perf_context += "TOP TICKERS BY NET P/L:\n"
    
    if data.per_ticker_stats:
        sorted_tickers = sorted(data.per_ticker_stats, key=lambda x: abs(x.get("netPnl", 0)), reverse=True)[:8]
        for t in sorted_tickers:
            wr = f"{t.get('winRate', 0) * 100:.1f}%" if t.get('winRate') is not None else "N/A"
            perf_context += f"- {t['ticker']}: {t['tradeCount']} trades, {wr} win rate, ${t.get('netPnl', 0):,.2f} net P/L\n"
    
    perf_prompt = (
        f"{perf_context}\n\n"
        "Write 1-2 short paragraphs directly addressing the trader (use 'you', 'your'). "
        "NO greetings - get straight to the point. "
        "Professional but heavy Reddit tone (degen, ape, YOLO, regarded, bagholding, etc.). "
        "Reference SPECIFIC tickers and their actual numbers. Explain which you're printing on vs donating to. "
        "How does this affect your Regard score (higher = more regarded)? Under 150 words."
    )
    
    # Score Breakdown context
    score_context = f"User: {data.display_name}, Regard Score: {data.regard_score}/100\n"
    score_context += f"Win Rate: {data.win_rate * 100:.1f}% ({data.wins}W / {data.losses}L)\n"
    if data.avg_win_pnl and data.avg_loss_pnl:
        score_context += f"Avg Win: ${data.avg_win_pnl:,.2f}, Avg Loss: ${data.avg_loss_pnl:,.2f}\n"
    if data.open_positions_count > 0 and data.open_positions_unrealized_pnl:
        score_context += f"Open: {data.open_positions_count} positions, ${data.open_positions_unrealized_pnl:,.2f} unrealized\n"
    
    score_prompt = (
        f"{score_context}\n\n"
        "Write 1-2 short paragraphs directly to the trader (use 'you', 'your') explaining their Regard score. "
        "NO greetings - start with analysis immediately. "
        "Professional but heavy Reddit tone (regarded, degen, ape, etc.). Use actual numbers provided. "
        "What's pushing your score up (more regarded/degen) vs down (less regarded/smart)? Under 150 words."
    )
    
    # Style & Behavior context
    style_context = f"User: {data.display_name}\n"
    if data.winner_avg_holding_period:
        style_context += f"Winners held: {data.winner_avg_holding_period / 86400:.1f} days avg\n"
    if data.loser_avg_holding_period:
        style_context += f"Losers held: {data.loser_avg_holding_period / 86400:.1f} days avg\n"
    style_context += f"Long: {data.long_count}, Short: {data.short_count}\n"
    
    style_prompt = (
        f"{style_context}\n\n"
        "Write 1-2 short paragraphs directly to the trader (use 'you', 'your') about their trading style. "
        "NO greetings - get right to the analysis. "
        "Professional but heavy Reddit tone (degen, regarded, ape, paper hands, diamond hands, etc.). "
        "Use the actual numbers provided. Under 150 words."
    )
    
    try:
        # Generate all three in parallel
        responses = await asyncio.gather(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": perf_prompt}],
                temperature=0.8,
                max_tokens=250
            ),
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": score_prompt}],
                temperature=0.8,
                max_tokens=250
            ),
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": style_prompt}],
                temperature=0.8,
                max_tokens=250
            ),
        )
        
        return {
            "performance_analytics": responses[0].choices[0].message.content,
            "score_breakdown": responses[1].choices[0].message.content,
            "style_behavior": responses[2].choices[0].message.content,
        }
    except Exception as e:
        logger.error(f"Section analysis generation failed: {e}")
        return {}


def _generate_fallback_narrative(data: UserReportData) -> UserReportNarrative:
    """Generate a simple fallback narrative when AI is unavailable."""
    win_rate_desc = "moderate" if data.win_rate and 0.4 <= data.win_rate <= 0.6 else "varied"
    regard_desc = "mixed" if data.regard_score and 40 <= data.regard_score <= 60 else "distinct"
    
    return UserReportNarrative(
        executive_summary_paragraphs=[
            f"Based on your trading history, you show a {win_rate_desc} win rate with {regard_desc} regard tendencies.",
            "This report provides insights into your trading patterns and performance metrics.",
        ],
        style_summary=f"Your trading style shows {regard_desc} characteristics with a focus on building consistent performance.",
        strengths=[
            "You maintain an active trading history",
            "You track your performance systematically",
        ],
        weaknesses=[
            "Consider reviewing risk management strategies",
            "Focus on consistency in trade selection",
        ],
        behavioural_patterns=[
            "Active trading across multiple positions",
            "Systematic approach to trade tracking",
        ],
        recommendations=[
            "Continue tracking all trades for better analysis",
            "Review patterns in your best and worst trades",
            "Consider setting clear risk management rules",
        ],
        thirty_day_plan=[
            "Continue logging all trades",
            "Review this report monthly",
            "Focus on improving consistency",
            "Track progress on recommendations",
            "Re-evaluate strategies based on results",
        ],
        tone_note="Basic analysis - full AI narrative unavailable",
    )

