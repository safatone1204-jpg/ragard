"""Narrative definitions and configuration."""
from typing import Literal
from dataclasses import dataclass

TimeframeKey = Literal["24h", "7d", "30d"]


@dataclass
class NarrativeConfig:
    """Internal configuration for a narrative definition."""
    id: str
    name: str
    description: str
    sentiment: Literal["bullish", "bearish", "neutral"]
    tickers: list[str]


# Static list of narratives to track
# TODO: Consider moving this to a database or config file in the future
NARRATIVE_CONFIG: list[NarrativeConfig] = [
    NarrativeConfig(
        id="meme-renaissance",
        name="Meme Stock Renaissance",
        description="Retail traders are returning to classic meme stocks with renewed enthusiasm.",
        sentiment="bullish",
        tickers=["GME", "AMC", "BBBY"],
    ),
    NarrativeConfig(
        id="crypto-miners",
        name="Crypto Miners Surge",
        description="Bitcoin ETF approval drives renewed interest in mining stocks.",
        sentiment="bullish",
        tickers=["MARA", "RIOT"],
    ),
    NarrativeConfig(
        id="ev-correction",
        name="EV Sector Correction",
        description="Electric vehicle stocks face headwinds as competition intensifies.",
        sentiment="bearish",
        tickers=["TSLA"],
    ),
    NarrativeConfig(
        id="ai-infrastructure",
        name="AI Infrastructure Play",
        description="Companies building AI infrastructure see increased demand.",
        sentiment="bullish",
        tickers=["NVDA", "PLTR"],
    ),
]

