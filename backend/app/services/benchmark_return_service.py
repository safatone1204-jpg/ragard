"""Benchmark return fetcher - gets market return for comparison."""
import logging
import os
import asyncio
from typing import Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf

logger = logging.getLogger(__name__)

# Thread pool for yfinance calls (avoid blocking event loop)
_yfinance_executor = ThreadPoolExecutor(max_workers=3)

# Configuration
MARKET_BENCHMARK_TICKER = os.getenv("MARKET_BENCHMARK_TICKER", "SPY")
DEFAULT_REFERENCE_CAPITAL = float(os.getenv("REGARD_BASE_CAPITAL", "10000"))


def _fetch_benchmark_return_sync(
    period_start: datetime,
    period_end: datetime,
    ticker: str
) -> Optional[float]:
    """Synchronous version of benchmark return fetch (runs in thread pool)."""
    try:
        # Format dates for yfinance
        start_str = period_start.strftime("%Y-%m-%d")
        end_str = period_end.strftime("%Y-%m-%d")
        
        # Fetch historical data with timeout
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_str, end=end_str, timeout=10)
        
        if hist.empty or len(hist) < 2:
            logger.warning(f"Insufficient data for {ticker} between {start_str} and {end_str}")
            return None
        
        # Get first and last close prices
        start_price = hist.iloc[0]['Close']
        end_price = hist.iloc[-1]['Close']
        
        if start_price <= 0:
            logger.warning(f"Invalid start price for {ticker}: {start_price}")
            return None
        
        # Calculate return
        benchmark_return = (end_price - start_price) / start_price
        
        logger.info(f"Benchmark {ticker} return: {benchmark_return:.4f} ({benchmark_return * 100:.2f}%)")
        
        return float(benchmark_return)
        
    except Exception as e:
        logger.warning(f"Error fetching benchmark return for {ticker}: {e}")
        return None


async def get_benchmark_return(
    period_start: datetime,
    period_end: datetime,
    ticker: str = MARKET_BENCHMARK_TICKER
) -> Optional[float]:
    """
    Get benchmark return over a time period (async wrapper).
    
    Args:
        period_start: Start datetime
        period_end: End datetime
        ticker: Benchmark ticker (default: SPY)
        
    Returns:
        Return as decimal (e.g., 0.05 = 5% return), or None if data unavailable
    """
    try:
        logger.info(f"Fetching benchmark return for {ticker} from {period_start.date()} to {period_end.date()}")
        
        # Run in thread pool with timeout to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(_yfinance_executor, _fetch_benchmark_return_sync, period_start, period_end, ticker),
            timeout=15.0  # 15 second timeout
        )
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"Benchmark fetch timed out for {ticker}")
        return None
    except Exception as e:
        logger.error(f"Error fetching benchmark return for {ticker}: {e}")
        return None


def calculate_user_return(
    total_pnl: float,
    reference_capital: float = DEFAULT_REFERENCE_CAPITAL
) -> Optional[float]:
    """
    Calculate user's return based on total PnL and reference capital.
    
    Args:
        total_pnl: Total profit/loss
        reference_capital: Reference capital amount (default: $10,000)
        
    Returns:
        Return as decimal (e.g., 0.05 = 5%), or None if invalid
    """
    if reference_capital <= 0:
        logger.warning(f"Invalid reference capital: {reference_capital}")
        return None
    
    user_return = total_pnl / reference_capital
    return float(user_return)


def calculate_relative_alpha(
    user_return: Optional[float],
    benchmark_return: Optional[float]
) -> Optional[float]:
    """
    Calculate relative alpha (user return - benchmark return).
    
    Args:
        user_return: User's return as decimal
        benchmark_return: Benchmark return as decimal
        
    Returns:
        Relative alpha as decimal, or None if either input is None
    """
    if user_return is None or benchmark_return is None:
        return None
    
    return user_return - benchmark_return


def categorize_relative_performance(relative_alpha: Optional[float]) -> str:
    """
    Categorize relative performance into qualitative label.
    
    Args:
        relative_alpha: Relative alpha as decimal
        
    Returns:
        Category: "beat_market", "roughly_tracked", "lagged_market", or "unknown"
    """
    if relative_alpha is None:
        return "unknown"
    
    # Thresholds for categorization
    if relative_alpha >= 0.02:  # +2% or more
        return "beat_market"
    elif relative_alpha <= -0.02:  # -2% or more
        return "lagged_market"
    else:
        return "roughly_tracked"

