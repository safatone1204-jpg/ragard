"""Open positions management and analysis."""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf

from app.core.supabase_client import get_supabase_admin
from app.services.trade_history_parser import OpenPosition

logger = logging.getLogger(__name__)

# Thread pool for yfinance calls
_price_fetch_executor = ThreadPoolExecutor(max_workers=5)


async def save_open_positions(user_id: str, open_positions: List[OpenPosition]) -> None:
    """
    Save open positions to database, replacing any existing ones.
    
    Args:
        user_id: User ID
        open_positions: List of OpenPosition objects
    """
    try:
        supabase = get_supabase_admin()
        
        # Check if table exists first
        try:
            test_response = supabase.table("user_open_positions")\
                .select("id")\
                .limit(1)\
                .execute()
        except Exception as e:
            error_msg = str(e)
            if "Could not find the table" in error_msg or "PGRST" in error_msg:
                logger.warning(f"Table 'user_open_positions' does not exist. Run migration: migrations/create_open_positions_table.sql")
                return  # Gracefully skip if table doesn't exist
            raise
        
        # Delete existing open positions for this user
        try:
            supabase.table("user_open_positions")\
                .delete()\
                .eq("user_id", user_id)\
                .execute()
        except Exception as e:
            logger.warning(f"Could not delete existing open positions: {e}")
        
        if not open_positions:
            logger.info(f"No open positions to save for user {user_id}")
            return
        
        # Insert new open positions
        positions_data = []
        for pos in open_positions:
            positions_data.append({
                "user_id": user_id,
                "ticker": pos.ticker,
                "side": pos.side,
                "quantity": float(pos.quantity),
                "entry_price": float(pos.entry_price),
                "entry_time": pos.entry_time.isoformat(),
                "entry_fees": float(pos.entry_fees),
                "description": pos.description,
            })
        
        if positions_data:
            supabase.table("user_open_positions")\
                .insert(positions_data)\
                .execute()
            
            logger.info(f"Saved {len(positions_data)} open positions for user {user_id}")
    
    except Exception as e:
        logger.warning(f"Error saving open positions for user {user_id}: {e}")
        # Don't raise - open positions are supplementary data


def _fetch_price_sync(ticker: str) -> Optional[float]:
    """Synchronous price fetch (runs in thread pool)."""
    try:
        ticker_obj = yf.Ticker(ticker)
        # Get most recent price with timeout
        hist = ticker_obj.history(period="1d", timeout=5)
        
        if hist.empty:
            return None
        
        current_price = float(hist.iloc[-1]['Close'])
        return current_price
        
    except Exception as e:
        logger.warning(f"Could not fetch price for {ticker}: {e}")
        return None


async def fetch_current_price(ticker: str) -> Optional[float]:
    """
    Fetch current price for a ticker using yfinance (async wrapper).
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        Current price or None if unavailable
    """
    try:
        # Run in thread pool with timeout to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(_price_fetch_executor, _fetch_price_sync, ticker),
            timeout=10.0  # 10 second timeout per ticker
        )
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"Price fetch timed out for {ticker}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching price for {ticker}: {e}")
        return None


async def update_open_positions_prices(user_id: str) -> None:
    """
    Update current prices and unrealized P/L for all open positions.
    
    Args:
        user_id: User ID
    """
    try:
        supabase = get_supabase_admin()
        
        # Fetch all open positions for this user
        response = supabase.table("user_open_positions")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        positions = response.data if response.data else []
        
        if not positions:
            return
        
        logger.info(f"Updating prices for {len(positions)} open positions for user {user_id}")
        
        # Fetch prices concurrently with overall timeout
        async def update_single_position(position):
            try:
                ticker = position.get("ticker")
                side = position.get("side")
                quantity = float(position.get("quantity", 0))
                entry_price = float(position.get("entry_price", 0))
                entry_fees = float(position.get("entry_fees", 0))
                
                # Fetch current price
                current_price = await fetch_current_price(ticker)
                
                if current_price is None:
                    return
                
                # Calculate unrealized P/L
                if side == "LONG":
                    unrealized_pnl = (current_price - entry_price) * quantity - entry_fees
                elif side == "SHORT":
                    unrealized_pnl = (entry_price - current_price) * quantity - entry_fees
                else:
                    unrealized_pnl = 0.0
                
                # Update the position
                supabase.table("user_open_positions")\
                    .update({
                        "current_price": current_price,
                        "unrealized_pnl": unrealized_pnl,
                        "last_price_update": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    })\
                    .eq("id", position["id"])\
                    .execute()
            except Exception as e:
                logger.warning(f"Could not update position {position.get('ticker')}: {e}")
        
        # Update all positions concurrently with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*[update_single_position(pos) for pos in positions], return_exceptions=True),
                timeout=30.0  # 30 second total timeout for all positions
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timed out updating open position prices for user {user_id}")
        
        logger.info(f"Finished updating prices for open positions")
        
    except Exception as e:
        logger.error(f"Error updating open position prices: {e}", exc_info=True)


async def get_open_positions_summary(user_id: str) -> Dict[str, Any]:
    """
    Get summary of open positions with current values.
    
    Args:
        user_id: User ID
        
    Returns:
        Dict with open position metrics
    """
    try:
        supabase = get_supabase_admin()
        
        # Check if table exists first
        try:
            response = supabase.table("user_open_positions")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            positions = response.data if response.data else []
        except Exception as e:
            error_msg = str(e)
            if "Could not find the table" in error_msg or "PGRST" in error_msg:
                logger.warning(f"Table 'user_open_positions' does not exist. Returning empty summary.")
                return {
                    "count": 0,
                    "total_unrealized_pnl": 0.0,
                    "positions": [],
                }
            raise
        
        if not positions:
            return {
                "count": 0,
                "total_unrealized_pnl": 0.0,
                "positions": [],
            }
        
        # Update prices if stale (older than 1 hour)
        needs_update = False
        for pos in positions:
            last_update = pos.get("last_price_update")
            if not last_update:
                needs_update = True
                break
            try:
                last_update_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                if (datetime.utcnow() - last_update_dt).total_seconds() > 3600:
                    needs_update = True
                    break
            except Exception:
                needs_update = True
                break
        
        if needs_update:
            # Update prices in background - don't wait for completion
            try:
                await asyncio.wait_for(
                    update_open_positions_prices(user_id),
                    timeout=20.0
                )
                # Re-fetch after update
                response = supabase.table("user_open_positions")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .execute()
                positions = response.data if response.data else []
            except asyncio.TimeoutError:
                logger.warning(f"Price update timed out for user {user_id}, using stale prices")
            except Exception as e:
                logger.warning(f"Could not update prices: {e}, using existing data")
        
        # Calculate summary
        total_unrealized_pnl = sum(float(p.get("unrealized_pnl", 0)) for p in positions)
        
        # Build position list
        position_list = []
        for pos in positions:
            position_list.append({
                "ticker": pos.get("ticker"),
                "side": pos.get("side"),
                "quantity": float(pos.get("quantity", 0)),
                "entry_price": float(pos.get("entry_price", 0)),
                "current_price": float(pos.get("current_price", 0)) if pos.get("current_price") else None,
                "unrealized_pnl": float(pos.get("unrealized_pnl", 0)) if pos.get("unrealized_pnl") else None,
                "entry_time": pos.get("entry_time"),
            })
        
        return {
            "count": len(positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "positions": position_list,
        }
        
    except Exception as e:
        logger.error(f"Error getting open positions summary: {e}", exc_info=True)
        return {
            "count": 0,
            "total_unrealized_pnl": 0.0,
            "positions": [],
        }

