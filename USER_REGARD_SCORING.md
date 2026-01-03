# User Regard Scoring System

## Overview

The User Regard Score is a 0-100 metric that measures trading behavior, where:
- **100 = Full Regard** (maximum degen, YOLO machine, high-risk gambler)
- **0 = Zero Regard** (disciplined, boring, smart investor)

Higher scores indicate more aggressive, speculative trading behavior. Lower scores indicate more conservative, risk-managed approaches.

## Score Bands

| Score Range | Label | Description |
|-------------|-------|-------------|
| 80-100 | **Full Regard** | Certified YOLO machine, pure degen energy |
| 60-79 | **High Regard** | Strong degen tendencies, high-risk plays |
| 40-59 | **Mid Regard** | Half investor, half gambler |
| 20-39 | **Low Regard** | Recovering degen, mostly disciplined |
| 0-19 | **Zero Regard** | Actually doing the boring smart stuff |

## Scoring Components

### Base Score Factors

The base score is computed from:

1. **Win Rate** - Higher win rate suggests better decision-making (but not the only factor)
2. **Sample Size** - More trades = more confidence in the score
3. **Risk/Reward Ratio** - Ratio of avg win to avg loss
4. **Holding Patterns** - Scalpers vs swing traders vs position traders
5. **Ticker Regard Scores** - Trading high-regard tickers (70+) increases score

### Market-Relative Performance Adjustment

**NEW**: The score now includes a market-relative performance adjustment based on alpha.

#### Benchmark Comparison

- **Benchmark**: SPY (S&P 500 ETF) by default (configurable via `MARKET_BENCHMARK_TICKER` env var)
- **Period**: Matches the user's trading period (min entry time to max exit time)
- **User Return**: `total_pnl / reference_capital` (default reference capital: $10,000)
- **Benchmark Return**: `(end_price - start_price) / start_price` for SPY over same period
- **Relative Alpha**: `user_return - benchmark_return`

#### Alpha Adjustment

The base score is adjusted based on relative alpha (INVERTED - beating market = smarter = lower score):

```
alpha_adjustment = clamp(-relative_alpha * 100, -10, +10)  # Note the negative sign
final_score = clamp(base_score + alpha_adjustment, 0, 100)
```

**Examples:**
- User: -5%, Market: -7% → Alpha: +2% → **-2 points** (beat the market = smarter = lower score)
- User: +10%, Market: +15% → Alpha: -5% → **+5 points** (lagged the market = degen = higher score)
- User: +8%, Market: +2% → Alpha: +6% → **-6 points** (outperformed significantly = smart = lower score)

**Key Insight**: Being red while the market is redder shows discipline and skill = **LOWER** score. Being green while lagging the market shows poor decisions = **HIGHER** score.

## Data Fields

### `user_regard_summaries` Table

Core fields:
- `user_id` (uuid, primary key)
- `regard_score` (numeric, 0-100)
- `wins` (integer)
- `losses` (integer)
- `win_rate` (numeric, 0-1 decimal)
- `sample_size` (integer) - **MUST equal `wins + losses`**
- `last_updated` (timestamptz)
- `ai_summary` (text)
- `ai_raw` (jsonb)

Market-relative fields:
- `user_return` (numeric) - User's return as decimal (0.05 = 5%)
- `benchmark_return` (numeric) - Benchmark return over same period
- `relative_alpha` (numeric) - `user_return - benchmark_return`
- `period_start` (timestamptz) - Start of trading period
- `period_end` (timestamptz) - End of trading period
- `total_pnl` (numeric) - Total PnL over period
- `reference_capital` (numeric) - Reference capital for return calculation (default: $10,000)

## Data Consistency Rules

### Rule 1: Win Rate Math Must Be Correct

```python
wins = count(trades where realized_pnl > 0)
losses = count(trades where realized_pnl < 0)
sample_size = wins + losses  # Ignore exactly-zero PnL trades
win_rate = wins / sample_size if sample_size > 0 else None
```

**Sanity checks:**
- `wins + losses` MUST equal `sample_size`
- `win_rate` MUST be between 0 and 1 (inclusive)
- If inconsistency detected, log warning and fix before saving

### Rule 2: Single Canonical Source

All report numbers come from **one source**:
- Either `user_regard_summaries` (cached) OR
- Freshly computed from `user_trades`
- **NEVER** a mix of cached and recomputed values

The report builder (`build_user_report_data`) uses `user_regard_summaries` as the canonical source for:
- `wins`, `losses`, `win_rate`, `sample_size`
- `regard_score`
- `user_return`, `benchmark_return`, `relative_alpha`

### Rule 3: Consistent Formatting

- **Dates**: Use `_format_date()` helper for all dates (format: "Month DD, YYYY")
- **Currency**: Use `_format_currency()` helper for all money (format: "$X,XXX.XX" or "-$X,XXX.XX")
- **Percentages**: Use `_format_percentage()` helper (format: "XX.X%")
- **Numeric columns**: Right-aligned in tables
- **PnL values**: Color-coded (green for positive, red for negative)

## AI Narrative Rules

### NO FAKE NUMBERS RULE

The AI narrative generator **MUST NOT**:
- Invent specific numbers, counts, or percentages
- Mention specific ticker names
- Create fake dates or time periods
- Say things like "You have 57 trades" or "Your win rate is 62%"

The AI **MUST**:
- Speak only qualitatively about patterns and directions
- Use provided category labels (e.g., "high win rate", "significant loss", "beat_market")
- Respect the data categories and not contradict them

### Reddit-Coded Voice

The AI uses a mix of professional analyst + /r/wallstreetbets language:

**Allowed:**
- Swearing (shit, fuck, damn, etc.)
- Reddit slang (degen, ape, YOLO, bagholding, diamond hands, paper hands, FOMO, copium, tilt, full send, regarded, moon, dump, pump, etc.)
- Direct callouts ("You hold losers like they owe you money")
- Brutal honesty

**NOT Allowed:**
- Slurs, hate speech, bigotry
- TOS-breaking content
- Anything beyond PG-13

**Tone**: Unfiltered but insightful. Think: brutally honest trading buddy, not corporate HR content.

### Qualitative Labels Used

The narrative receives these pre-computed labels:

**Regard Score Category:**
- `full_regard`, `high_regard`, `mid_regard`, `low_regard`, `zero_regard`

**Win Rate Category:**
- `high` (≥65%), `medium-high` (50-65%), `medium` (35-50%), `low-medium` (20-35%), `low` (<20%)

**Overall PnL Category:**
- `solid_profit` (>$1k), `slight_profit` ($0-$1k), `slight_loss` ($0 to -$1k), `significant_loss` (<-$1k)

**Market Performance:**
- `beat_market` (alpha ≥ +2%)
- `roughly_tracked` (alpha between -2% and +2%)
- `lagged_market` (alpha ≤ -2%)

**Holding Style:**
- `scalper` (<15 min avg), `intraday` (<1 day), `swing` (1-5 days), `position` (>5 days)

**Risk Profile:**
- Derived from avg_win vs avg_loss comparison
- "big_losers_issue" if losses >> wins
- "tiny_wins_issue" if wins << losses
- "balanced" otherwise

## Error Handling

### Missing Benchmark Data

If benchmark return cannot be fetched:
- Set `benchmark_return = None`
- Set `relative_alpha = None`
- No alpha adjustment applied to score
- Log warning but continue processing

### Invalid Data

If data inconsistencies detected:
- Log warning with details
- Fix the inconsistency (e.g., recalculate `sample_size = wins + losses`)
- Continue with corrected values
- Never show bogus numbers (use "N/A" instead)

## Configuration

Environment variables:
- `MARKET_BENCHMARK_TICKER` - Benchmark ticker symbol (default: "SPY")
- `REGARD_BASE_CAPITAL` - Reference capital for return calculation (default: "10000")

## Migration

To add market-relative fields to existing database:

```sql
-- Run migrations/add_benchmark_fields_to_user_regard_summaries.sql
ALTER TABLE public.user_regard_summaries
ADD COLUMN IF NOT EXISTS user_return numeric,
ADD COLUMN IF NOT EXISTS benchmark_return numeric,
ADD COLUMN IF NOT EXISTS relative_alpha numeric,
ADD COLUMN IF NOT EXISTS period_start timestamptz,
ADD COLUMN IF NOT EXISTS period_end timestamptz,
ADD COLUMN IF NOT EXISTS total_pnl numeric,
ADD COLUMN IF NOT EXISTS reference_capital numeric DEFAULT 10000;
```

## Testing Checklist

After implementing changes, verify:

1. ✅ Win rate math is correct: `wins / (wins + losses)`
2. ✅ Numbers are consistent across all pages
3. ✅ `sample_size = wins + losses` everywhere
4. ✅ Narrative matches the actual stats (no contradictions)
5. ✅ Market-relative performance is shown and explained
6. ✅ AI doesn't invent any numbers
7. ✅ Dates are formatted consistently
8. ✅ Currency is formatted consistently
9. ✅ No blank pages in PDF
10. ✅ Regard score bands are correctly applied

## Example Scenarios

### Scenario 1: Beat Market While Red (Smart)
- User: -5% return
- SPY: -7% return
- Alpha: +2%
- **Result**: Score gets -2 point adjustment (LOWER = smarter). Narrative mentions "beat the market even while red."

### Scenario 2: Green But Lagged (Degen)
- User: +8% return
- SPY: +15% return
- Alpha: -7%
- **Result**: Score gets +7 point adjustment (HIGHER = more degen). Narrative mentions "lagged the market rally."

### Scenario 3: No Benchmark Data
- User: +5% return
- SPY: Unable to fetch
- Alpha: None
- **Result**: No adjustment. Narrative doesn't mention market comparison.

