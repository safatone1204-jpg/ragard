"""Service for computing narrative metrics from market data."""
from typing import Dict
import yfinance as yf
import pandas as pd
from app.narratives.config import NARRATIVE_CONFIG, NarrativeConfig, TimeframeKey
from app.narratives.models import NarrativeSummary, NarrativeMetrics


def _fetch_ticker_returns(tickers: list[str], period_days: int = 60) -> Dict[str, Dict[TimeframeKey, float | None]]:
    """Fetch OHLCV data and compute returns for multiple timeframes.
    
    Returns a dict mapping ticker -> timeframe -> return percentage.
    """
    if not tickers:
        return {}
    
    try:
        # Download daily data for all tickers
        data = yf.download(" ".join(tickers), period=f"{period_days}d", interval="1d", progress=False)
        
        if data.empty:
            return {ticker: {"24h": None, "7d": None, "30d": None} for ticker in tickers}
        
        # Handle single ticker case (returns Series instead of DataFrame)
        if len(tickers) == 1:
            ticker = tickers[0]
            if isinstance(data.columns, pd.MultiIndex):
                close_series = data["Close"][ticker] if ticker in data["Close"].columns else pd.Series()
            else:
                close_series = data["Close"] if "Close" in data.columns else data
            if isinstance(close_series, pd.Series):
                data = pd.DataFrame({ticker: close_series})
            else:
                data = pd.DataFrame({ticker: close_series}) if not close_series.empty else pd.DataFrame()
        
        # Extract Close prices
        if data.empty:
            return {ticker: {"24h": None, "7d": None, "30d": None} for ticker in tickers}
        
        if isinstance(data.columns, pd.MultiIndex):
            if "Close" in data.columns.levels[0]:
                close_prices = data["Close"]
            else:
                return {ticker: {"24h": None, "7d": None, "30d": None} for ticker in tickers}
        else:
            # Single column case or already close prices
            if "Close" in data.columns:
                close_prices = data["Close"]
            else:
                close_prices = data
        
        results: Dict[str, Dict[TimeframeKey, float | None]] = {}
        
        for ticker in tickers:
            if ticker not in close_prices.columns:
                results[ticker] = {"24h": None, "7d": None, "30d": None}
                continue
            
            ticker_data = close_prices[ticker].dropna()
            
            if len(ticker_data) < 2:
                results[ticker] = {"24h": None, "7d": None, "30d": None}
                continue
            
            latest_close = float(ticker_data.iloc[-1])
            
            # Calculate returns for each timeframe
            returns: Dict[TimeframeKey, float | None] = {}
            
            # 24h: 1 trading day ago
            if len(ticker_data) >= 2:
                prev_close_1d = float(ticker_data.iloc[-2])
                if prev_close_1d > 0:
                    returns["24h"] = ((latest_close / prev_close_1d) - 1) * 100
                else:
                    returns["24h"] = None
            else:
                returns["24h"] = None
            
            # 7d: ~7 trading days ago (5 calendar days -> ~4 trading days, use 5 for safety)
            trading_days_7d = min(7, len(ticker_data) - 1)
            if trading_days_7d > 0 and len(ticker_data) > trading_days_7d:
                prev_close_7d = float(ticker_data.iloc[-trading_days_7d - 1])
                if prev_close_7d > 0:
                    returns["7d"] = ((latest_close / prev_close_7d) - 1) * 100
                else:
                    returns["7d"] = None
            else:
                returns["7d"] = None
            
            # 30d: ~30 trading days ago (~21 calendar days, use 22)
            trading_days_30d = min(22, len(ticker_data) - 1)
            if trading_days_30d > 0 and len(ticker_data) > trading_days_30d:
                prev_close_30d = float(ticker_data.iloc[-trading_days_30d - 1])
                if prev_close_30d > 0:
                    returns["30d"] = ((latest_close / prev_close_30d) - 1) * 100
                else:
                    returns["30d"] = None
            else:
                returns["30d"] = None
            
            results[ticker] = returns
        
        return results
        
    except Exception as e:
        # If bulk fetch fails, try individual fetches as fallback
        results: Dict[str, Dict[TimeframeKey, float | None]] = {}
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(period=f"{period_days}d", interval="1d")
                
                if hist.empty or len(hist) < 2:
                    results[ticker] = {"24h": None, "7d": None, "30d": None}
                    continue
                
                close_prices = hist["Close"]
                latest_close = float(close_prices.iloc[-1])
                
                returns: Dict[TimeframeKey, float | None] = {}
                
                # 24h
                if len(close_prices) >= 2:
                    prev_close_1d = float(close_prices.iloc[-2])
                    returns["24h"] = ((latest_close / prev_close_1d) - 1) * 100 if prev_close_1d > 0 else None
                else:
                    returns["24h"] = None
                
                # 7d
                trading_days_7d = min(7, len(close_prices) - 1)
                if trading_days_7d > 0:
                    prev_close_7d = float(close_prices.iloc[-trading_days_7d - 1])
                    returns["7d"] = ((latest_close / prev_close_7d) - 1) * 100 if prev_close_7d > 0 else None
                else:
                    returns["7d"] = None
                
                # 30d
                trading_days_30d = min(22, len(close_prices) - 1)
                if trading_days_30d > 0:
                    prev_close_30d = float(close_prices.iloc[-trading_days_30d - 1])
                    returns["30d"] = ((latest_close / prev_close_30d) - 1) * 100 if prev_close_30d > 0 else None
                else:
                    returns["30d"] = None
                
                results[ticker] = returns
            except Exception:
                results[ticker] = {"24h": None, "7d": None, "30d": None}
        
        return results


def _compute_heat_score(avg_move_pct: float) -> float:
    """Compute heat score from average move percentage.
    
    TODO: Enhance with volume-weighted metrics and social buzz score when available.
    Currently uses simple price-only formula.
    """
    # Baseline at 50, scale by average move
    # Clamp between 0 and 100
    heat = 50 + (avg_move_pct * 5)
    return max(0.0, min(100.0, heat))


def _compute_narrative_metrics(
    config: NarrativeConfig,
    ticker_returns: Dict[str, Dict[TimeframeKey, float | None]]
) -> Dict[TimeframeKey, NarrativeMetrics]:
    """Compute metrics for a narrative across all timeframes."""
    metrics_by_timeframe: Dict[TimeframeKey, NarrativeMetrics] = {}
    
    for timeframe in ["24h", "7d", "30d"]:
        timeframe_key: TimeframeKey = timeframe  # type: ignore
        
        # Collect returns for this timeframe
        returns: list[float] = []
        up_count = 0
        down_count = 0
        
        for ticker in config.tickers:
            ticker_return = ticker_returns.get(ticker, {}).get(timeframe_key)
            if ticker_return is not None:
                returns.append(ticker_return)
                if ticker_return > 0:
                    up_count += 1
                elif ticker_return < 0:
                    down_count += 1
        
        # Calculate average move
        if returns:
            avg_move_pct = sum(returns) / len(returns)
        else:
            avg_move_pct = 0.0
        
        # Compute heat score
        heat_score = _compute_heat_score(avg_move_pct)
        
        metrics_by_timeframe[timeframe_key] = NarrativeMetrics(
            avg_move_pct=round(avg_move_pct, 2),
            up_count=up_count,
            down_count=down_count,
            heat_score=round(heat_score, 1),
            social_buzz_score=None,  # TODO: Add when social data is available
        )
    
    return metrics_by_timeframe


def get_narrative_summaries() -> list[NarrativeSummary]:
    """Get all narrative summaries with computed metrics.
    
    Returns a list of NarrativeSummary objects with metrics for all timeframes.
    """
    summaries: list[NarrativeSummary] = []
    
    # Collect all unique tickers from all narratives
    all_tickers: list[str] = []
    for config in NARRATIVE_CONFIG:
        all_tickers.extend(config.tickers)
    all_tickers = list(set(all_tickers))  # Remove duplicates
    
    # Fetch returns for all tickers at once
    ticker_returns = _fetch_ticker_returns(all_tickers)
    
    # Compute metrics for each narrative
    for config in NARRATIVE_CONFIG:
        metrics = _compute_narrative_metrics(config, ticker_returns)
        
        summary = NarrativeSummary(
            id=config.id,
            name=config.name,
            description=config.description,
            sentiment=config.sentiment,
            tickers=config.tickers,
            metrics=metrics,
        )
        summaries.append(summary)
    
    return summaries

