"""Pydantic models for narrative data."""
from typing import Literal
from pydantic import BaseModel, Field

TimeframeKey = Literal["24h", "7d", "30d"]


class NarrativeMetrics(BaseModel):
    """Metrics for a narrative in a specific timeframe."""
    avg_move_pct: float = Field(..., description="Average % move for narrative's tickers")
    up_count: int = Field(..., description="Number of tickers with positive returns")
    down_count: int = Field(..., description="Number of tickers with negative returns")
    heat_score: float = Field(..., ge=0, le=100, description="Heat score 0-100")
    # TODO: Add social buzz score when social data integration is implemented
    social_buzz_score: float | None = Field(None, description="Social buzz score (future)")


class NarrativeMetricsByTimeframe(BaseModel):
    """Metrics for all timeframes."""
    timeframe_24h: NarrativeMetrics = Field(..., alias="24h")
    timeframe_7d: NarrativeMetrics = Field(..., alias="7d")
    timeframe_30d: NarrativeMetrics = Field(..., alias="30d")

    class Config:
        populate_by_name = True


class NarrativeSummary(BaseModel):
    """Complete narrative summary with metrics."""
    id: str
    name: str
    description: str
    sentiment: Literal["bullish", "bearish", "neutral"]
    tickers: list[str]
    metrics: dict[TimeframeKey, NarrativeMetrics]
    ai_title: str | None = None  # AI-generated human-readable title
    ai_summary: str | None = None  # AI-generated 2-4 sentence summary
    ai_sentiment: Literal["bullish", "bearish", "mixed", "neutral"] | None = None  # AI-generated sentiment

