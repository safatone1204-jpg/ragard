"""
Regard Score computation with breakdown.

THIS IS THE SINGLE SOURCE OF TRUTH FOR REGARD SCORE CALCULATION.

All Regard Score values throughout the application must be computed using
the compute_ragard_score() function in this module. No other code should
implement its own Regard Score calculation logic.
"""
from typing import Optional
from pydantic import BaseModel


class RagardScoreBreakdown(BaseModel):
    """Breakdown of Regard Score components."""
    # Component contributions (weighted values that sum to ragard_score)
    hype: float | None = None  # Reddit/social buzz contribution
    volatility: float | None = None  # Price action/volatility contribution
    liquidity: float | None = None  # Microcap/liquidity contribution
    risk: float | None = None  # Risk adjustment (usually negative)
    
    # Raw component scores (0-100 scale) for reference
    hype_score: float | None = None
    volatility_score: float | None = None
    liquidity_score: float | None = None
    risk_score: float | None = None


def compute_ragard_score(
    social_score: Optional[float] = None,  # Reddit mentions (0-1 normalized)
    price_score: Optional[float] = None,  # Price change score (-1 to 1)
    volume_score: Optional[float] = None,  # Volume score (0-1)
    risk_score: Optional[float] = None,  # Risk score (0-100, higher = riskier)
) -> tuple[int, RagardScoreBreakdown]:
    """
    SINGLE SOURCE OF TRUTH for Regard Score calculation.
    
    This matches the trending page formula exactly:
    - 60% social (hype)
    - 40% market (70% price, 30% volume)
    - Risk adjustment applied
    
    Args:
        social_score: Normalized social score (0-1)
        price_score: Price change score (-1 to 1)
        volume_score: Volume score (0-1)
        risk_score: Risk score (0-100, higher = riskier)
    
    Returns:
        Tuple of (ragard_score: int, breakdown: RagardScoreBreakdown)
        ragard_score is always an integer (0-100)
    """
    # Normalize missing inputs
    social = social_score if social_score is not None else 0.0
    price = price_score if price_score is not None else 0.0
    volume = volume_score if volume_score is not None else 0.0
    risk = risk_score if risk_score is not None else 0.0
    
    # Market score: 70% price, 30% volume
    market_score = (price * 0.7 + volume * 0.3)
    market_score = max(0.0, min(1.0, market_score))  # Clamp to 0-1
    
    # Combined trending score: 60% social, 40% market
    base_score = (0.6 * social + 0.4 * market_score) * 100
    
    # Risk adjustment: higher risk reduces score
    # Risk score is 0-100, convert to penalty (0-10 points)
    risk_penalty = (risk / 100.0) * 10.0
    risk_adjustment = -risk_penalty
    
    # Final score
    final_score = base_score + risk_adjustment
    
    # Clamp to 0-100 and round to integer
    final_score = max(0.0, min(100.0, final_score))
    final_score = int(round(final_score))
    
    # Compute component contributions for breakdown
    # These should sum to final_score (within rounding)
    hype_contribution = (0.6 * social) * 100  # 60% of total
    volatility_contribution = (0.4 * market_score * 0.7) * 100  # 40% * 70% = 28% of total
    liquidity_contribution = (0.4 * market_score * 0.3) * 100  # 40% * 30% = 12% of total
    
    breakdown = RagardScoreBreakdown(
        hype=round(hype_contribution, 1),
        volatility=round(volatility_contribution, 1),
        liquidity=round(liquidity_contribution, 1),
        risk=round(risk_adjustment, 1),
        hype_score=round(social * 100, 1) if social_score is not None else None,
        volatility_score=round(price * 100, 1) if price_score is not None else None,
        liquidity_score=round(volume * 100, 1) if volume_score is not None else None,
        risk_score=round(risk, 1) if risk_score is not None else None,
    )
    
    return final_score, breakdown

