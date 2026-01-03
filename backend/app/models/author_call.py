"""
Author call tracking model (scaffolding for future accuracy-based scoring).

This model tracks author predictions/calls for future reliability scoring.
Currently just logs calls without affecting scores.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuthorCall(BaseModel):
    """
    Represents a single author call/prediction about a ticker.
    
    This is a simple data model for now. In the future, we'll use this to:
    - Track forward performance of author calls
    - Compute reliability/accuracy scores
    - Adjust author trust based on actual outcomes
    """
    id: Optional[str] = None  # Will be generated if using DB
    author: str  # Reddit username
    symbol: str  # Ticker symbol
    stance: Optional[str] = None  # "bullish" | "bearish" | "neutral" | None
    source_url: str  # URL of the Reddit post
    created_at: datetime  # When the call was made
    
    # Future fields (not used yet):
    # outcome_price: Optional[float] = None  # Price after X days
    # outcome_pct: Optional[float] = None  # % change after X days
    # was_correct: Optional[bool] = None  # Whether call was accurate
    # reliability_score: Optional[float] = None  # Computed accuracy score


# TODO: If using SQLAlchemy, create a table like:
# class AuthorCallDB(Base):
#     __tablename__ = "author_calls"
#     id = Column(Integer, primary_key=True)
#     author = Column(String, index=True)
#     symbol = Column(String, index=True)
#     stance = Column(String, nullable=True)
#     source_url = Column(String)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     outcome_price = Column(Float, nullable=True)
#     outcome_pct = Column(Float, nullable=True)
#     was_correct = Column(Boolean, nullable=True)
#     reliability_score = Column(Float, nullable=True)

