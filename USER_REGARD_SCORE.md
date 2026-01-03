# User Regard Score System

## Overview

The User Regard Score system allows logged-in users to upload their trade history, which is then analyzed to compute a personalized "Regard Score" (0-100) that measures trading performance.

## Database Schema

### `user_trades` Table

Stores normalized trade history for each user.

**Fields:**
- `id` (uuid, primary key)
- `user_id` (uuid, foreign key to `auth.users`)
- `ticker` (text) - Stock ticker symbol
- `side` (text) - 'LONG' or 'SHORT' (normalized)
- `quantity` (numeric) - Number of shares/contracts
- `entry_time` (timestamptz) - When the trade was opened
- `exit_time` (timestamptz) - When the trade was closed
- `entry_price` (numeric) - Entry price
- `exit_price` (numeric) - Exit price
- `realized_pnl` (numeric) - Realized profit/loss
- `holding_period_seconds` (integer) - Duration of the trade
- `raw_metadata` (jsonb) - Additional columns from CSV
- `created_at` (timestamptz) - When the record was created

**Indexes:**
- `(user_id, ticker)` - For filtering by user and ticker
- `(user_id, created_at)` - For chronological queries

**RLS Policies:**
- Users can only view/create/update/delete their own trades

### `user_regard_summaries` Table

Stores the latest computed user regard metrics (one record per user).

**Fields:**
- `user_id` (uuid, primary key, foreign key to `auth.users`)
- `regard_score` (numeric) - 0-100 score
- `wins` (integer) - Number of winning trades
- `losses` (integer) - Number of losing trades
- `win_rate` (numeric) - Win rate as decimal (0-1, e.g., 0.65 = 65%)
- `sample_size` (integer) - Total number of trades analyzed
- `last_updated` (timestamptz) - When the summary was last computed
- `ai_summary` (text) - AI-generated explanation of the score
- `ai_raw` (jsonb) - Raw AI response for debugging

**RLS Policies:**
- Users can only view/create/update/delete their own summary

## Flow

### 1. Trade History Upload

**Endpoint:** `POST /api/trade-history/upload`

**Request:**
- `multipart/form-data` with `file` field containing CSV
- Requires authentication (Bearer token)

**CSV Format:**
Required columns (case-insensitive):
- `ticker` - Stock ticker symbol
- `side` - 'BUY', 'SELL', 'LONG', or 'SHORT'
- `quantity` - Number of shares/contracts
- `entry_time` - ISO 8601 timestamp or `YYYY-MM-DD HH:MM:SS`
- `exit_time` - ISO 8601 timestamp or `YYYY-MM-DD HH:MM:SS`
- `entry_price` - Entry price
- `exit_price` - Exit price
- `realized_pnl` (optional) - If missing, computed automatically

**Process:**
1. Parse CSV file
2. Validate and normalize each row
3. Delete existing trades for user (full refresh)
4. Insert new trades in batches (500 per batch)
5. Compute base stats from trades
6. Run AI analysis to generate regard score
7. Save/update user regard summary

**Response:**
```json
{
  "success": true,
  "importedTrades": 150,
  "skippedTrades": 5,
  "message": "Trade history uploaded and your Regard Score has been updated."
}
```

### 2. Base Stats Computation

**Function:** `compute_user_regard_base_stats(user_id)`

Computes:
- Wins (trades with `realized_pnl > 0`)
- Losses (trades with `realized_pnl < 0`)
- Sample size (wins + losses)
- Win rate (wins / sample_size)
- Average win/loss PnL
- Max win/loss PnL
- Average holding period
- Per-ticker statistics (top 5 by trade count)

### 3. AI Analysis

**Function:** `run_user_regard_ai_analysis(base_stats)`

Uses OpenAI GPT-4o-mini to:
- Analyze base stats
- Generate a regard score (0-100)
- Provide a 1-2 sentence explanation

**Fallback:**
If AI fails, uses a data-based mapping:
- Low sample size (< 10 trades) → score = 50
- Otherwise: linear mapping from win rate, adjusted for sample size

### 4. Summary Storage

**Function:** `save_user_regard_summary(user_id, base_stats, ai_result)`

Upserts the computed metrics into `user_regard_summaries` table.

### 5. Get User Regard

**Endpoint:** `GET /api/user-regard`

**Request:**
- Requires authentication (Bearer token)

**Response:**
```json
{
  "regardScore": 72.5,
  "wins": 45,
  "losses": 30,
  "winRate": 0.6,
  "sampleSize": 75,
  "lastUpdated": "2025-01-15T10:30:00Z",
  "aiSummary": "Good win rate with consistent performance across multiple tickers."
}
```

If no data exists:
```json
{
  "regardScore": null,
  "wins": 0,
  "losses": 0,
  "winRate": null,
  "sampleSize": 0,
  "lastUpdated": null,
  "aiSummary": null
}
```

## Implementation Details

### CSV Parsing

- Supports case-insensitive column names
- Normalizes trade sides: 'BUY'/'LONG' → 'LONG', 'SELL'/'SHORT' → 'SHORT'
- Parses multiple timestamp formats
- Computes `realized_pnl` if not provided
- Computes `holding_period_seconds` from entry/exit times
- Skips invalid rows and logs warnings
- Stores extra columns in `raw_metadata`

### Error Handling

- Upload errors return 400 with clear messages
- Parse errors skip individual rows (counted in `skippedTrades`)
- Database errors return 500 with generic message (details logged)
- AI failures fall back to data-based scoring
- Analysis failures don't block upload success

### Performance

- Batch inserts (500 rows per batch)
- Indexed queries for fast lookups
- AI responses cached (via existing AI client cache)

## Files

- `supabase_schema_user_regard.sql` - Database schema (run manually in Supabase)
- `backend/app/services/trade_history_parser.py` - CSV parsing logic
- `backend/app/services/user_regard_service.py` - Stats computation and AI analysis
- `backend/app/api/user_regard.py` - API endpoints
- `backend/app/main.py` - Router registration

## Testing

To test the system:

1. Run the SQL schema in Supabase
2. Create a CSV file with trade history
3. Upload via `POST /api/trade-history/upload`
4. Fetch results via `GET /api/user-regard`

Example CSV:
```csv
ticker,side,quantity,entry_time,exit_time,entry_price,exit_price
AAPL,BUY,10,2024-01-01 09:30:00,2024-01-01 16:00:00,150.00,152.50
TSLA,SELL,5,2024-01-02 10:00:00,2024-01-02 15:00:00,200.00,195.00
```

