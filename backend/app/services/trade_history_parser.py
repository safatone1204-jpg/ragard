"""Trade history CSV parsing and validation."""
import csv
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

logger = logging.getLogger(__name__)


class ParsedTrade:
    """Represents a single parsed and validated trade."""
    def __init__(
        self,
        ticker: str,
        side: str,  # 'LONG' or 'SHORT'
        quantity: float,
        entry_time: datetime,
        exit_time: datetime,
        entry_price: float,
        exit_price: float,
        realized_pnl: float,
        holding_period_seconds: int,
        entry_fees: float = 0.0,
        exit_fees: float = 0.0,
        regard_score_at_entry: Optional[float] = None,
        regard_score_at_exit: Optional[float] = None,
        raw_metadata: Dict[str, Any] = None,
    ):
        self.ticker = ticker
        self.side = side
        self.quantity = quantity
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.realized_pnl = realized_pnl
        self.holding_period_seconds = holding_period_seconds
        self.entry_fees = entry_fees
        self.exit_fees = exit_fees
        self.regard_score_at_entry = regard_score_at_entry
        self.regard_score_at_exit = regard_score_at_exit
        self.raw_metadata = raw_metadata or {}


class TradeAction:
    """Represents a single trade action (BUY or SELL)."""
    def __init__(
        self,
        date: datetime,
        action: str,  # 'BUY' or 'SELL'
        ticker: str,
        quantity: float,
        price: float,
        fees: float,
        amount: float,
        description: str = "",
    ):
        self.date = date
        self.action = action.upper()
        self.ticker = ticker.upper()
        self.quantity = quantity
        self.price = price
        self.fees = fees
        self.amount = amount
        self.description = description


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """
    Parse timestamp string to datetime.
    Supports ISO 8601 and common formats.
    Handles complex formats like "10/20/2025 as of 10/17/2025" by extracting the first date.
    
    Args:
        ts_str: Timestamp string
        
    Returns:
        datetime object or None if parsing fails
    """
    if not ts_str or not ts_str.strip():
        return None
    
    ts_str = ts_str.strip()
    
    # Handle "date as of date" format - extract the first date
    if ' as of ' in ts_str.lower():
        ts_str = ts_str.split(' as of ')[0].strip()
    
    # Try ISO 8601 first
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    
    # Try common formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y/%m/%d %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%m-%d-%Y',
        '%d-%m-%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse timestamp: {ts_str}")
    return None


def normalize_action(action_str: str) -> Optional[Tuple[str, bool]]:
    """
    Normalize various action types to BUY or SELL.
    
    Args:
        action_str: Raw action string from CSV
        
    Returns:
        Tuple of (normalized_action, is_trade) where:
        - normalized_action is 'BUY', 'SELL', or None
        - is_trade is True if this should be processed as a trade, False if it should be skipped
    """
    if not action_str:
        return None
    
    action_upper = action_str.strip().upper()
    
    # Direct matches
    if action_upper in ('BUY', 'SELL'):
        return (action_upper, True)
    
    # Options trades - treat as regular trades
    if action_upper in ('BUY TO OPEN', 'BUY TO CLOSE'):
        return ('BUY', True)
    if action_upper in ('SELL TO OPEN', 'SELL TO CLOSE'):
        return ('SELL', True)
    
    # Short sales - treat as SELL (will be matched with later BUYs or handled as unmatched)
    if action_upper in ('SELL SHORT', 'SHORT'):
        return ('SELL', True)
    
    # Corporate actions and dividends - skip (not trades)
    skip_actions = {
        'QUALIFIED DIVIDEND',
        'CASH DIVIDEND',
        'DIVIDEND',
        'STOCK DIVIDEND',
        'STOCK SPLIT',
        'STOCK MERGER',
        'MERGER',
        'SPIN-OFF',
        'FOREIGN TAX PAID',
        'TAX',
        'EXPIRED',  # Options expiration
        'ASSIGNED',  # Options assignment
        'EXERCISED',  # Options exercise
        'JOURNAL',  # Journal entries (transfers, adjustments)
        'TRANSFER',
        'ADJUSTMENT',
        'FEE',
        'INTEREST',
        'MARGIN INTEREST',
    }
    
    if action_upper in skip_actions:
        return (None, False)
    
    # Unknown action - log and skip
    logger.debug(f"Unknown action type: {action_str}, skipping")
    return (None, False)


def parse_numeric(value: str) -> Optional[float]:
    """
    Parse numeric string to float.
    
    Args:
        value: Numeric string (may include commas, $, parentheses for negative, etc.)
        
    Returns:
        float or None if parsing fails
    """
    if not value or not value.strip():
        return None
    
    # Remove common formatting
    cleaned = value.strip().replace(',', '').replace('$', '').replace(' ', '')
    
    # Handle parentheses for negative (accounting format)
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]
    
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not parse numeric: {value}")
        return None


class OpenPosition:
    """Represents an open (unclosed) position."""
    def __init__(
        self,
        ticker: str,
        side: str,  # 'LONG' or 'SHORT'
        quantity: float,
        entry_price: float,
        entry_time: datetime,
        entry_fees: float = 0.0,
        description: str = "",
    ):
        self.ticker = ticker
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.entry_fees = entry_fees
        self.description = description


def match_trades(actions: List[TradeAction]) -> Tuple[List[ParsedTrade], List[OpenPosition]]:
    """
    Match BUY and SELL actions to create complete trades.
    Uses FIFO (First In, First Out) matching for LONG trades.
    Handles SHORT sales by matching SELL-first with later BUY-to-cover.
    
    Args:
        actions: List of TradeAction objects sorted by date
        
    Returns:
        Tuple of (List of ParsedTrade objects, List of OpenPosition objects)
    """
    parsed_trades: List[ParsedTrade] = []
    all_open_positions: List[OpenPosition] = []
    
    # Group actions by ticker
    ticker_actions: Dict[str, List[TradeAction]] = defaultdict(list)
    for action in actions:
        ticker_actions[action.ticker].append(action)
    
    # Process each ticker separately
    for ticker, ticker_actions_list in ticker_actions.items():
        # Sort by date
        ticker_actions_list.sort(key=lambda x: x.date)
        
        # Track open LONG positions (FIFO queue)
        open_long_positions: List[TradeAction] = []
        # Track open SHORT positions (FIFO queue)
        open_short_positions: List[TradeAction] = []
        
        for action in ticker_actions_list:
            if action.action == 'BUY':
                # First, try to close SHORT positions (buy-to-cover)
                remaining_quantity = action.quantity
                
                while remaining_quantity > 0 and open_short_positions:
                    short_action = open_short_positions[0]
                    
                    # Determine how much to match
                    match_quantity = min(remaining_quantity, short_action.quantity)
                    
                    # Calculate P/L for SHORT
                    # For SHORT: (entry_price - exit_price) * quantity - fees
                    entry_price = short_action.price  # Price when shorted
                    exit_price = action.price  # Price when covered
                    entry_fees = short_action.fees * (match_quantity / short_action.quantity)
                    exit_fees = action.fees * (match_quantity / action.quantity)
                    
                    # P/L = (entry - exit) * quantity - total fees
                    realized_pnl = (entry_price - exit_price) * match_quantity - entry_fees - exit_fees
                    
                    # Calculate holding period
                    holding_period_seconds = int((action.date - short_action.date).total_seconds())
                    
                    # Create SHORT trade
                    trade = ParsedTrade(
                        ticker=ticker,
                        side='SHORT',
                        quantity=match_quantity,
                        entry_time=short_action.date,
                        exit_time=action.date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        realized_pnl=realized_pnl,
                        holding_period_seconds=holding_period_seconds,
                        entry_fees=entry_fees,
                        exit_fees=exit_fees,
                        regard_score_at_entry=None,
                        regard_score_at_exit=None,
                        raw_metadata={
                            'entry_description': short_action.description,
                            'exit_description': action.description,
                        }
                    )
                    
                    parsed_trades.append(trade)
                    
                    # Update quantities
                    remaining_quantity -= match_quantity
                    short_action.quantity -= match_quantity
                    
                    # Remove short action if fully matched
                    if short_action.quantity <= 0.0001:
                        open_short_positions.pop(0)
                
                # Any remaining quantity opens a LONG position
                if remaining_quantity > 0.0001:
                    # Create a new BUY action for the remaining quantity
                    remaining_buy = TradeAction(
                        date=action.date,
                        action='BUY',
                        ticker=action.ticker,
                        quantity=remaining_quantity,
                        price=action.price,
                        fees=action.fees * (remaining_quantity / action.quantity),
                        amount=action.price * remaining_quantity,
                        description=action.description,
                    )
                    open_long_positions.append(remaining_buy)
                    
            elif action.action == 'SELL':
                # First, try to close LONG positions
                remaining_quantity = action.quantity
                
                while remaining_quantity > 0 and open_long_positions:
                    buy_action = open_long_positions[0]
                    
                    # Determine how much to match
                    match_quantity = min(remaining_quantity, buy_action.quantity)
                    
                    # Calculate P/L for LONG
                    # For LONG: (exit_price - entry_price) * quantity - fees
                    entry_price = buy_action.price
                    exit_price = action.price
                    entry_fees = buy_action.fees * (match_quantity / buy_action.quantity)
                    exit_fees = action.fees * (match_quantity / action.quantity)
                    
                    # P/L = (exit - entry) * quantity - total fees
                    realized_pnl = (exit_price - entry_price) * match_quantity - entry_fees - exit_fees
                    
                    # Calculate holding period
                    holding_period_seconds = int((action.date - buy_action.date).total_seconds())
                    
                    # Create LONG trade
                    trade = ParsedTrade(
                        ticker=ticker,
                        side='LONG',
                        quantity=match_quantity,
                        entry_time=buy_action.date,
                        exit_time=action.date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        realized_pnl=realized_pnl,
                        holding_period_seconds=holding_period_seconds,
                        entry_fees=entry_fees,
                        exit_fees=exit_fees,
                        regard_score_at_entry=None,
                        regard_score_at_exit=None,
                        raw_metadata={
                            'entry_description': buy_action.description,
                            'exit_description': action.description,
                        }
                    )
                    
                    parsed_trades.append(trade)
                    
                    # Update quantities
                    remaining_quantity -= match_quantity
                    buy_action.quantity -= match_quantity
                    
                    # Remove buy action if fully matched
                    if buy_action.quantity <= 0.0001:
                        open_long_positions.pop(0)
                
                # Any remaining quantity opens a SHORT position
                if remaining_quantity > 0.0001:
                    # Create a new SELL action for the remaining quantity (short sale)
                    remaining_sell = TradeAction(
                        date=action.date,
                        action='SELL',
                        ticker=action.ticker,
                        quantity=remaining_quantity,
                        price=action.price,
                        fees=action.fees * (remaining_quantity / action.quantity),
                        amount=action.price * remaining_quantity,
                        description=action.description,
                    )
                    open_short_positions.append(remaining_sell)
                    logger.info(f"Opened SHORT position for {ticker}: {remaining_quantity} shares at ${action.price}")
        
        # After processing all actions for this ticker, collect any remaining open positions
        for open_long in open_long_positions:
            all_open_positions.append(OpenPosition(
                ticker=ticker,
                side='LONG',
                quantity=open_long.quantity,
                entry_price=open_long.price,
                entry_time=open_long.date,
                entry_fees=open_long.fees,
                description=open_long.description,
            ))
        
        for open_short in open_short_positions:
            all_open_positions.append(OpenPosition(
                ticker=ticker,
                side='SHORT',
                quantity=open_short.quantity,
                entry_price=open_short.price,
                entry_time=open_short.date,
                entry_fees=open_short.fees,
                description=open_short.description,
            ))
    
    if all_open_positions:
        logger.info(f"Found {len(all_open_positions)} open positions across all tickers")
    
    return parsed_trades, all_open_positions


def parse_trade_history_csv(csv_content: str) -> Tuple[List[ParsedTrade], List[OpenPosition], int]:
    """
    Parse CSV trade history into ParsedTrade objects and detect open positions.
    Supports the format: Date, Action, Symbol, Description, Quantity, Price, Fees & Comm, Amount
    
    Args:
        csv_content: CSV file content as string
        
    Returns:
        Tuple of (list of ParsedTrade, list of OpenPosition, number of skipped rows)
    """
    parsed_trades: List[ParsedTrade] = []
    skipped_count = 0
    actions: List[TradeAction] = []
    
    try:
        # Use csv module to parse
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Check if CSV has headers
        if reader.fieldnames is None:
            raise ValueError("CSV file appears to be empty or has no header row")
        
        # Expected columns (case-insensitive, with variations)
        required_columns_lower = {
            'date', 'action', 'symbol', 'quantity', 'price'
        }
        
        # Normalize fieldnames to lowercase for comparison
        reader_fieldnames = [f.lower().strip() for f in reader.fieldnames if f]
        
        if not reader_fieldnames:
            raise ValueError("CSV file has empty header row")
        
        # Create column mapping (case-insensitive)
        column_map = {}
        for field in reader.fieldnames:
            field_lower = field.lower().strip()
            column_map[field_lower] = field
        
        # Check for required columns
        found_columns_lower = set(column_map.keys())
        missing_columns = required_columns_lower - found_columns_lower
        
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {sorted(missing_columns)}. "
                f"Found columns: {sorted(found_columns_lower)}. "
                f"Expected columns (case-insensitive): Date, Action, Symbol, Quantity, Price"
            )
        
        # Parse each row into TradeAction
        for row_num, row in enumerate(reader, start=2):
            try:
                # Extract fields (case-insensitive)
                date_str = row.get(column_map.get('date', ''), '').strip()
                action_str = row.get(column_map.get('action', ''), '').strip().upper()
                symbol_str = row.get(column_map.get('symbol', ''), '').strip().upper()
                quantity_str = row.get(column_map.get('quantity', ''), '').strip()
                price_str = row.get(column_map.get('price', ''), '').strip()
                
                # Optional fields
                description = row.get(column_map.get('description', ''), '').strip()
                fees_str = row.get(column_map.get('fees & comm', ''), '').strip() or row.get(column_map.get('fees', ''), '').strip()
                amount_str = row.get(column_map.get('amount', ''), '').strip()
                
                # Validate required fields (be more lenient - only require date, action, and symbol)
                if not date_str or not action_str or not symbol_str:
                    # Check if it's a dividend or other non-trade row (might not have symbol)
                    action_result = normalize_action(action_str)
                    if action_result and not action_result[1]:
                        # It's a non-trade action, skip silently
                        logger.debug(f"Row {row_num}: Skipping non-trade row with action '{action_str}'")
                    else:
                        logger.warning(f"Row {row_num}: Missing required fields (date, action, or symbol), skipping")
                    skipped_count += 1
                    continue
                
                # Normalize action
                action_result = normalize_action(action_str)
                if action_result is None or not action_result[1]:
                    # Skip non-trade actions (dividends, etc.) silently
                    if action_result and not action_result[1]:
                        logger.debug(f"Row {row_num}: Skipping non-trade action '{action_str}'")
                    else:
                        logger.warning(f"Row {row_num}: Invalid or unknown action '{action_str}', skipping")
                    skipped_count += 1
                    continue
                
                normalized_action = action_result[0]
                
                # Parse values
                date = parse_timestamp(date_str)
                quantity = parse_numeric(quantity_str)
                price = parse_numeric(price_str)
                fees = parse_numeric(fees_str) if fees_str else 0.0
                amount = parse_numeric(amount_str) if amount_str else None
                
                if date is None:
                    logger.warning(f"Row {row_num}: Invalid date '{date_str}', skipping")
                    skipped_count += 1
                    continue
                
                if quantity is None or quantity <= 0:
                    logger.warning(f"Row {row_num}: Invalid quantity '{quantity_str}', skipping")
                    skipped_count += 1
                    continue
                
                if price is None or price <= 0:
                    logger.warning(f"Row {row_num}: Invalid price '{price_str}', skipping")
                    skipped_count += 1
                    continue
                
                # Create TradeAction
                action = TradeAction(
                    date=date,
                    action=normalized_action,
                    ticker=symbol_str,
                    quantity=quantity,
                    price=price,
                    fees=fees or 0.0,
                    amount=amount or (price * quantity),
                    description=description,
                )
                
                actions.append(action)
                
            except Exception as e:
                logger.warning(f"Row {row_num}: Error parsing row: {e}, skipping")
                skipped_count += 1
                continue
        
        if not actions:
            raise ValueError("No valid trade actions found in CSV file")
        
        # Match BUY/SELL pairs to create trades
        parsed_trades, open_positions = match_trades(actions)
        
        logger.info(f"Parsed {len(parsed_trades)} complete trades and {len(open_positions)} open positions from {len(actions)} actions, skipped {skipped_count} rows")
        
        return parsed_trades, open_positions, skipped_count
        
    except ValueError as e:
        # Re-raise ValueError as-is (these are user-facing errors)
        raise
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}", exc_info=True)
        raise ValueError(f"Failed to parse CSV: {str(e)}")
