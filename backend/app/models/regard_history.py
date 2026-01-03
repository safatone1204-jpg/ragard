"""Regard History model for tracking historical Regard score snapshots."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
import json


class RegardHistory(BaseModel):
    """Model for Regard score history records."""
    
    id: Optional[int] = None
    ticker: str
    timestamp_utc: datetime
    timestamp_local: datetime
    window_label: str = "current"
    
    # Score metrics
    score_raw: Optional[float] = None
    score_rounded: Optional[int] = None
    scoring_mode: str  # "ai" | "fallback" | "error"
    ai_success: bool
    
    # Data quality / context
    total_posts: int = 0
    posts_reddit: int = 0
    posts_twitter: int = 0
    posts_discord: int = 0
    posts_news: int = 0
    low_sample_size: bool = False
    is_weekend: bool = False
    is_holiday: bool = False
    has_data_gap: bool = False
    
    # Market snapshot
    price_at_snapshot: Optional[float] = None
    change_24h_pct: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    
    # Versioning / reproducibility
    model_version: Optional[str] = None
    scoring_version: str
    config_snapshot: Optional[Dict[str, Any]] = None
    
    # Backtesting hooks (optional / placeholders)
    forward_return_24h: Optional[float] = None
    forward_return_3d: Optional[float] = None
    forward_return_7d: Optional[float] = None
    
    created_at: Optional[datetime] = None


class RegardHistoryResponse(BaseModel):
    """Response model for Regard history API endpoint."""
    
    timestamp_utc: str
    score_raw: Optional[float] = None
    score_rounded: Optional[int] = None
    scoring_mode: str
    ai_success: bool
    total_posts: int
    price_at_snapshot: Optional[float] = None
    change_24h_pct: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    model_version: Optional[str] = None
    scoring_version: str

