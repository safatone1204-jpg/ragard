"""
Ticker universe module.

Loads the official US ticker list from CSV and provides validation functions.
"""
import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to the CSV file (in the same directory as this module)
CSV_PATH = Path(__file__).parent / "us_tickers.csv"

# Ticker universe data structures
TICKER_TO_CIK: dict[str, str | None] = {}
TICKER_SET: set[str] = set()


def _load_ticker_universe() -> None:
    """
    Load ticker universe from CSV file.
    
    This function is called at module import time to populate TICKER_SET and TICKER_TO_CIK.
    If the CSV file is not found or cannot be parsed, logs an error and falls back to
    empty sets/dicts (so the system doesn't crash in dev).
    
    In production, the CSV file should be present at backend/app/data/us_tickers.csv.
    """
    global TICKER_TO_CIK, TICKER_SET
    
    if not CSV_PATH.exists():
        logger.error(
            f"Ticker universe CSV not found at {CSV_PATH}. "
            "Ticker validation will be disabled. "
            "In production, ensure the CSV file is present."
        )
        TICKER_TO_CIK = {}
        TICKER_SET = set()
        return
    
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Normalize symbol
                symbol = row.get("Symbol", "").strip().upper()
                if not symbol:
                    continue
                
                # Normalize CIK
                cik_raw = row.get("CIK", "").strip()
                if cik_raw.lower() == "none" or not cik_raw:
                    cik = None
                else:
                    cik = cik_raw
                
                TICKER_SET.add(symbol)
                TICKER_TO_CIK[symbol] = cik
        
        logger.info(f"Loaded {len(TICKER_SET)} tickers from {CSV_PATH}")
    
    except Exception as e:
        logger.error(
            f"Error loading ticker universe from {CSV_PATH}: {e}. "
            "Ticker validation will be disabled."
        )
        TICKER_TO_CIK = {}
        TICKER_SET = set()


def is_known_ticker(symbol: str) -> bool:
    """
    Check if a symbol is a known ticker in the universe.
    
    Args:
        symbol: Ticker symbol to check (will be normalized to uppercase)
    
    Returns:
        True if the symbol is in the ticker universe, False otherwise
    """
    return symbol.upper() in TICKER_SET


# Load ticker universe at module import time
_load_ticker_universe()

