"""User position reconstruction from trade history.

This module reconstructs closed trades and open positions from raw trade executions.
Calculates both realized PnL (closed) and unrealized PnL (open).
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ClosedTrade:
    """Represents a completed trade with realized PnL."""
    ticker: str
    side: str  # 'LONG' or 'SHORT'
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    realized_pnl: float
    trade_return: float  # Percent return on this trade
    holding_period_seconds: int


@dataclass
class OptionMetadata:
    """Metadata for option contracts."""
    underlying: str
    strike: float
    option_type: str  # 'CALL' or 'PUT'
    expiration: datetime


@dataclass
class OpenPosition:
    """Represents an open (unclosed) position with unrealized PnL."""
    ticker: str
    side: str  # 'LONG' or 'SHORT'
    quantity: float
    avg_entry_price: float
    avg_entry_time: datetime  # Weighted average or earliest
    total_cost_basis: float
    current_price: Optional[float]  # Fetched from market
    unrealized_pnl: Optional[float]  # Based on current price
    unrealized_return: Optional[float]  # Percent return if closed now
    is_option: bool = False
    option_meta: Optional[OptionMetadata] = None
    pricing_is_estimated: bool = False


async def build_user_positions_and_trades(
    user_id: str,
    trades_data: List[Dict[str, Any]]
) -> Tuple[List[ClosedTrade], List[OpenPosition]]:
    """
    Reconstruct closed trades and open positions from trade history.
    
    This function takes raw trade executions and matches them using FIFO
    to create closed trades (with realized PnL) and identify open positions
    (with unrealized PnL based on current market prices).
    
    Args:
        user_id: User ID
        trades_data: List of trade dicts from user_trades table
        
    Returns:
        Tuple of (closed_trades, open_positions)
    """
    from app.core.supabase_client import get_supabase_admin
    
    closed_trades: List[ClosedTrade] = []
    open_positions_dict: Dict[str, List[Dict]] = defaultdict(list)  # ticker -> list of open lots
    
    # Group by ticker
    ticker_trades: Dict[str, List[Dict]] = defaultdict(list)
    for trade in trades_data:
        ticker = trade.get("ticker", "").upper()
        ticker_trades[ticker].append(trade)
    
    # Process each ticker separately
    for ticker, ticker_trade_list in ticker_trades.items():
        # Sort by entry time
        ticker_trade_list.sort(key=lambda t: t.get("entry_time", ""))
        
        # These are already matched closed trades from the database
        # Just convert to ClosedTrade objects
        for trade in ticker_trade_list:
            try:
                entry_time = datetime.fromisoformat(trade.get("entry_time").replace("Z", "+00:00"))
                exit_time = datetime.fromisoformat(trade.get("exit_time").replace("Z", "+00:00"))
                entry_price = float(trade.get("entry_price", 0))
                exit_price = float(trade.get("exit_price", 0))
                quantity = float(trade.get("quantity", 0))
                realized_pnl = float(trade.get("realized_pnl", 0))
                side = trade.get("side", "LONG")
                
                # Calculate trade return
                if side == "LONG":
                    trade_return = (exit_price - entry_price) / entry_price if entry_price > 0 else 0.0
                elif side == "SHORT":
                    trade_return = (entry_price - exit_price) / entry_price if entry_price > 0 else 0.0
                else:
                    trade_return = 0.0
                
                holding_period = int(trade.get("holding_period_seconds", 0))
                
                closed_trade = ClosedTrade(
                    ticker=ticker,
                    side=side,
                    entry_time=entry_time,
                    exit_time=exit_time,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=quantity,
                    realized_pnl=realized_pnl,
                    trade_return=trade_return,
                    holding_period_seconds=holding_period,
                )
                
                closed_trades.append(closed_trade)
                
            except Exception as e:
                logger.warning(f"Could not convert trade to ClosedTrade: {e}")
                continue
    
    # Get open positions from database and aggregate by ticker+side
    open_positions: List[OpenPosition] = []
    try:
        supabase = get_supabase_admin()
        
        # Check if table exists
        try:
            open_response = supabase.table("user_open_positions")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            open_data = open_response.data if open_response.data else []
        except Exception as e:
            error_msg = str(e)
            if "Could not find" in error_msg or "PGRST" in error_msg:
                logger.info(f"Table 'user_open_positions' doesn't exist yet. Skipping open positions.")
                return closed_trades, []
            raise
        
        # Aggregate positions by ticker+side (multiple buys into same ticker = one position)
        aggregated: Dict[Tuple[str, str], List[Dict]] = defaultdict(list)
        for pos in open_data:
            ticker = pos.get("ticker", "").upper()
            side = pos.get("side", "LONG")
            aggregated[(ticker, side)].append(pos)
        
        # For each ticker+side, create one aggregated OpenPosition
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        for (ticker, side), positions in aggregated.items():
            try:
                # Calculate quantity-weighted averages
                total_qty = 0.0
                total_cost = 0.0
                earliest_time = None
                
                for pos in positions:
                    qty = float(pos.get("quantity", 0))
                    price = float(pos.get("entry_price", 0))
                    entry_time = datetime.fromisoformat(pos.get("entry_time").replace("Z", "+00:00"))
                    
                    total_qty += qty
                    total_cost += qty * price
                    
                    if earliest_time is None or entry_time < earliest_time:
                        earliest_time = entry_time
                
                avg_entry_price = total_cost / total_qty if total_qty > 0 else 0.0
                
                # Check if this is an option
                option_meta = _parse_option_ticker(ticker)
                is_option = option_meta is not None
                
                # Handle expired options - treat as closed at $0
                # Make sure both datetimes are timezone-aware for comparison
                if is_option and option_meta:
                    expiration_aware = option_meta.expiration if option_meta.expiration.tzinfo else option_meta.expiration.replace(tzinfo=timezone.utc)
                    if expiration_aware < now:
                        logger.info(f"Option {ticker} expired on {option_meta.expiration.date()}, treating as closed at $0")
                        
                        # Create synthetic closed trade for expired option
                        if side == "LONG":
                            # Bought option, expired worthless
                            realized_pnl = -total_cost  # Lost the premium paid
                            trade_return = -1.0  # 100% loss
                        else:  # SHORT
                            # Sold option, expired worthless (we keep the premium)
                            realized_pnl = total_cost  # Kept the premium received
                            trade_return = 1.0  # 100% gain
                        
                        # Ensure earliest_time is timezone-aware for subtraction
                        entry_time_aware = earliest_time or now
                        if entry_time_aware.tzinfo is None:
                            entry_time_aware = entry_time_aware.replace(tzinfo=timezone.utc)
                        
                        closed_trade = ClosedTrade(
                            ticker=ticker,
                            side=side,
                            entry_time=entry_time_aware,
                            exit_time=expiration_aware,
                            entry_price=avg_entry_price,
                            exit_price=0.0,  # Expired worthless
                            quantity=total_qty,
                            realized_pnl=realized_pnl,
                            trade_return=trade_return,
                            holding_period_seconds=int((expiration_aware - entry_time_aware).total_seconds()),
                        )
                        closed_trades.append(closed_trade)
                        continue  # Don't add to open positions
                
                # Fetch current price / value
                current_price = None
                pricing_is_estimated = False
                
                if is_option and option_meta:
                    # For open options, use intrinsic value (estimated)
                    underlying_price = await _fetch_current_price_for_position(option_meta.underlying)
                    if underlying_price:
                        if option_meta.option_type == 'CALL':
                            intrinsic = max(0, underlying_price - option_meta.strike)
                        else:  # PUT
                            intrinsic = max(0, option_meta.strike - underlying_price)
                        current_price = intrinsic
                        pricing_is_estimated = True
                        logger.info(f"Option {ticker}: underlying=${underlying_price:.2f}, intrinsic=${intrinsic:.2f}")
                else:
                    # Regular stock
                    current_price = await _fetch_current_price_for_position(ticker)
                
                # Calculate unrealized P/L and return
                unrealized_pnl = None
                unrealized_return = None
                
                if current_price is not None and avg_entry_price > 0:
                    if side == "LONG":
                        unrealized_pnl = (current_price - avg_entry_price) * total_qty
                        unrealized_return = (current_price - avg_entry_price) / avg_entry_price
                    elif side == "SHORT":
                        unrealized_pnl = (avg_entry_price - current_price) * total_qty
                        unrealized_return = (avg_entry_price - current_price) / avg_entry_price
                
                open_position = OpenPosition(
                    ticker=ticker,
                    side=side,
                    quantity=total_qty,
                    avg_entry_price=avg_entry_price,
                    avg_entry_time=earliest_time or now,
                    total_cost_basis=total_cost,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_return=unrealized_return,
                    is_option=is_option,
                    option_meta=option_meta,
                    pricing_is_estimated=pricing_is_estimated or is_option,
                )
                
                open_positions.append(open_position)
                logger.info(f"Aggregated open position: {ticker} {side} {total_qty} qty, unrealized P/L: {unrealized_pnl}")
                
            except Exception as e:
                logger.warning(f"Could not aggregate open position for {ticker} {side}: {e}")
                continue
        
        return closed_trades, open_positions
        
    except Exception as e:
        logger.warning(f"Could not fetch open positions (table may not exist): {e}")
        return closed_trades, []


def _parse_option_ticker(ticker: str) -> Optional[OptionMetadata]:
    """
    Parse option ticker format to extract metadata.
    Format: "UNDERLYING MM/DD/YYYY STRIKE C/P"
    Example: "BAC 11/28/2025 53.00 C"
    
    Returns:
        OptionMetadata or None if not an option or can't parse
    """
    try:
        parts = ticker.split()
        if len(parts) < 4:
            return None
        
        underlying = parts[0]
        date_str = parts[1]
        strike_str = parts[2]
        type_str = parts[3].upper()
        
        # Parse date
        expiration = datetime.strptime(date_str, "%m/%d/%Y")
        
        # Parse strike
        strike = float(strike_str)
        
        # Parse type
        if type_str not in ['C', 'P', 'CALL', 'PUT']:
            return None
        
        option_type = 'CALL' if type_str in ['C', 'CALL'] else 'PUT'
        
        return OptionMetadata(
            underlying=underlying,
            strike=strike,
            option_type=option_type,
            expiration=expiration
        )
    except Exception as e:
        logger.debug(f"Could not parse option ticker {ticker}: {e}")
        return None


def _is_option_ticker(ticker: str) -> bool:
    """Check if ticker appears to be an option."""
    return _parse_option_ticker(ticker) is not None


async def _fetch_current_price_for_position(ticker: str) -> Optional[float]:
    """Fetch current market price for a ticker (used for marking positions to market)."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    import yfinance as yf
    
    executor = ThreadPoolExecutor(max_workers=1)
    
    def _fetch_sync():
        try:
            # Check if it's an options ticker
            if any(char in ticker for char in ['/', ' C', ' P']) and any(char.isdigit() for char in ticker):
                # Options - extract underlying
                parts = ticker.split()
                if parts:
                    underlying = parts[0]
                    logger.info(f"Options ticker {ticker}, using underlying {underlying}")
                    ticker_obj = yf.Ticker(underlying)
                else:
                    return None
            else:
                ticker_obj = yf.Ticker(ticker)
            
            hist = ticker_obj.history(period="1d", timeout=5)
            if hist.empty:
                return None
            
            return float(hist.iloc[-1]['Close'])
        except Exception as e:
            logger.warning(f"Could not fetch price for {ticker}: {e}")
            return None
    
    try:
        loop = asyncio.get_event_loop()
        price = await asyncio.wait_for(
            loop.run_in_executor(executor, _fetch_sync),
            timeout=8.0
        )
        return price
    except asyncio.TimeoutError:
        logger.warning(f"Price fetch timed out for {ticker}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching price for {ticker}: {e}")
        return None

