# Open Positions Implementation

## Overview

Open positions (unclosed trades) are now fully tracked, analyzed, and factored into the Regard Score. This provides a complete picture of the user's portfolio, including both realized trades and current holdings.

## Database Schema

**New Table**: `user_open_positions`

```sql
CREATE TABLE public.user_open_positions (
    id uuid PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id),
    ticker text NOT NULL,
    side text NOT NULL,  -- 'LONG' or 'SHORT'
    quantity numeric NOT NULL,
    entry_price numeric NOT NULL,
    entry_time timestamptz NOT NULL,
    entry_fees numeric DEFAULT 0,
    current_price numeric,  -- Fetched from market
    unrealized_pnl numeric,  -- Calculated: (current - entry) * qty for LONG
    last_price_update timestamptz,
    regard_score_at_entry numeric,
    description text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
```

**Migration**: `migrations/create_open_positions_table.sql`

## How It Works

### 1. Parsing & Detection

**File**: `backend/app/services/trade_history_parser.py`

- `match_trades()` now returns `Tuple[List[ParsedTrade], List[OpenPosition]]`
- Tracks separate queues for LONG and SHORT positions
- After matching all actions:
  - Remaining BUYs without SELLs = open LONG positions
  - Remaining SELLs without BUYs = open SHORT positions
- Returns both closed trades and open positions

### 2. Saving Open Positions

**File**: `backend/app/services/open_positions_service.py` (NEW)

Functions:
- `save_open_positions(user_id, open_positions)` - Saves to database (replaces existing)
- `fetch_current_price(ticker)` - Gets current market price via yfinance
- `update_open_positions_prices(user_id)` - Updates prices and calculates unrealized P/L
- `get_open_positions_summary(user_id)` - Returns summary with current values

**Upload Flow**:
1. Parse CSV → get closed trades + open positions
2. Save closed trades to `user_trades`
3. Save open positions to `user_open_positions`
4. Compute base stats (includes open positions)

### 3. Price Updates

Prices are automatically updated when:
- User views their report (if prices are stale > 1 hour)
- Prices are fetched on-demand via yfinance

**Unrealized P/L Calculation**:
- **LONG**: `(current_price - entry_price) * quantity - entry_fees`
- **SHORT**: `(entry_price - current_price) * quantity - entry_fees`

### 4. Scoring Impact

**File**: `backend/app/services/user_regard_service.py`

Open positions affect the Regard Score:

**Raises Score (more degen)**:
- Holding many open positions (overexposure)
- Significant unrealized losses (bagholding)
- Holding losing positions for extended periods

**Lowers Score (more disciplined)**:
- Few or no open positions (taking profits/cutting losses)
- Significant unrealized gains (letting winners run)
- Balanced portfolio with manageable risk

**AI Prompt Includes**:
- Number of open positions
- Total unrealized P/L
- Breakdown of LONG vs SHORT opens
- Count of losing vs winning open positions
- Bagholding indicator

### 5. PDF Report

**File**: `backend/app/services/user_report_pdf.py`

**Score Calculation Section**:
- Section 5 now analyzes open positions in detail
- Explains impact on score
- Discusses bagholding vs diamond hands
- Analyzes long-term holds (>30 days)

**New Section**: "Current Open Positions"
- Table showing all open positions (up to 20)
- Columns: Ticker, Side, Qty, Entry Price, Current Price, Unrealized P/L, Days Held
- Total unrealized P/L displayed
- Appears before Trade Appendix

### 6. Narrative Generation

**File**: `backend/app/services/user_report_narrative.py`

AI narrative now receives:
- Open positions count
- Unrealized P/L status
- Bagholding indicators

AI can reference:
- "You're bagholding significant losers"
- "You're letting winners run"
- "Everything is closed - disciplined or inactive?"

## Examples

### Example 1: Bagholding Degen
- 5 open positions
- Total unrealized P/L: -$2,500
- Days held: 45+ days average
- **Impact**: Significantly RAISES score (holding losers = degen behavior)

### Example 2: Patient Winner
- 3 open positions
- Total unrealized P/L: +$1,800
- Days held: 60+ days
- **Impact**: LOWERS score (letting winners run = discipline)

### Example 3: Active Trader
- 0 open positions
- Everything closed
- **Impact**: Neutral (could be disciplined or just inactive)

## Options Support

Options trades are already fully supported:
- Recognized action types: "BUY TO OPEN", "SELL TO CLOSE", etc.
- Ticker format includes strike/expiry: "BAC 11/28/2025 53.00 C"
- Matched and analyzed like regular trades
- P/L calculated correctly for options contracts

## Testing

To test open positions:

1. Upload CSV with unclosed positions (BUY without SELL)
2. Check logs for "Found X open positions"
3. Verify they appear in database: `SELECT * FROM user_open_positions WHERE user_id = '...'`
4. Generate PDF report - should show open positions section
5. Verify unrealized P/L is calculated correctly

## Migration Required

Run in Supabase SQL Editor:
```sql
-- migrations/create_open_positions_table.sql
```

The system will work without it (just won't track open positions until migration is run).

