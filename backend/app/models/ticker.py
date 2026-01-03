"""Ticker data models."""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class TickerMetrics(BaseModel):
    """Detailed metrics for a ticker."""
    symbol: str
    company_name: str
    price: Decimal
    change_pct: Decimal = Field(..., description="Percentage change")
    market_cap: Optional[Decimal] = None
    volume: Optional[int] = None
    float_shares: Optional[int] = None
    ragard_score: int = Field(..., ge=0, le=100, description="Ragard score 0-100")
    risk_level: str = Field(..., description="Risk level: low, moderate, high, extreme")
    exit_liquidity_rating: str = Field(..., description="Exit liquidity rating")
    hype_vs_price_text: str = Field(..., description="Hype vs price analysis text")
    ragard_label: Optional[str] = Field(None, description="Label like 'Certified Degen', 'Respectable Trash', etc.")


class Ticker(BaseModel):
    """Simplified ticker for trending list."""
    symbol: str
    company_name: str
    price: Decimal
    change_pct: Decimal = Field(..., description="Percentage change")
    market_cap: Optional[Decimal] = None
    ragard_score: Optional[int] = Field(None, ge=0, le=100, description="Ragard score 0-100")
    risk_level: str = Field(..., description="Risk level: low, moderate, high, extreme")


