# User Reports Feature

## Overview

The User Reports feature allows logged-in users to download a personalized, AI-generated PDF report of their trading performance. The report combines real trading data with AI-powered narrative analysis, all styled with Ragard branding and Reddit/trader language.

## Architecture

### 1. Data Aggregation (`backend/app/services/user_report_data.py`)

The `build_user_report_data()` function aggregates all necessary data from the database:

**Data Sources:**
- `user_regard_summaries` - Regard score, wins, losses, win rate, sample size
- `user_trades` - All individual trades with PnL, entry/exit times, tickers, sides
- `auth.users` (via Supabase) - User metadata (first_name, last_name) for display name

**Computed Metrics:**
- Total PnL, best/worst trades, average win/loss
- Per-ticker statistics (top 10 by trade count)
- Holding period buckets with win rates
- Time-of-day trading patterns
- Cumulative PnL over time
- PnL distribution for histograms
- Trade list (last 200 trades for appendix)

**Key Functions:**
- `build_user_report_data(user_id, display_name)` - Main entry point
- Returns `UserReportData` object with all metrics

### 2. AI Narrative Generation (`backend/app/services/user_report_narrative.py`)

The `generate_user_report_narrative()` function creates personalized text using OpenAI:

**Critical Constraints:**
- **NO fake numbers** - AI only generates qualitative text
- **NO specific ticker names** - Only patterns and observations
- **NO invented counts or percentages** - All numeric facts come from data

**Narrative Sections:**
- `executive_summary_paragraphs` - 2-3 paragraphs summarizing performance
- `style_summary` - Description of trading style
- `strengths` - List of positive patterns
- `weaknesses` - Areas for improvement
- `behavioural_patterns` - Observed trading behaviors
- `recommendations` - Actionable advice
- `thirty_day_plan` - 5-item game plan

**Key Functions:**
- `generate_user_report_narrative(data)` - Main entry point
- `_categorize_win_rate()` - Converts numeric win rate to qualitative category
- `_categorize_regard_score()` - Converts score to category (full_regard, high_regard, etc.)
- `_describe_holding_patterns()` - Describes holding period patterns qualitatively
- `_generate_fallback_narrative()` - Fallback when AI is unavailable

**AI Prompt Strategy:**
- Provides qualitative context only (win rate category, regard category, patterns)
- Explicitly instructs model to NOT invent numbers
- Uses Reddit/trader language (YOLO, bagholding, diamond hands, etc.)
- Maintains PG-13 tone while being feral

### 3. PDF Generation (`backend/app/services/user_report_pdf.py`)

The `generate_user_report_pdf()` function creates a branded PDF using ReportLab:

**PDF Structure:**
1. **Cover Page**
   - Ragard branding
   - User's display name
   - Generation date
   - Tagline

2. **Executive Summary**
   - Large Regard Score display (0-100)
   - Score label (e.g., "Full Regard: certified YOLO machine")
   - Summary stats table (wins, losses, win rate, total trades, time span, total PnL)
   - AI-generated summary paragraphs

3. **Performance Analytics**
   - Trade extremes (best/worst, avg win/loss)
   - Top tickers table (trade count, win rate, net PnL, avg PnL)
   - Holding period stats (win rate by bucket)
   - Position distribution (long vs short)

4. **Style & Behavior**
   - Trading style summary
   - Strengths (bullet list)
   - Weaknesses (bullet list)
   - Behavioral patterns (bullet list)

5. **Recommendations & 30-Day Plan**
   - Ragard recommendations (bullet list)
   - Next 30 days game plan (bullet list)

6. **Trade Appendix**
   - Table of last 100 trades
   - Columns: Date, Ticker, Side, Quantity, Entry Price, Exit Price, PnL

**Styling:**
- Dark theme (Ragard colors: slate-900, slate-800, cyan-400)
- Professional layout with consistent typography
- Header/footer on each page with branding
- Tables with alternating row colors
- Color-coded sections (success green, danger red, accent cyan)

**Key Functions:**
- `generate_user_report_pdf(data, narrative)` - Main entry point
- `_get_regard_label(score)` - Gets label for score range
- `_format_currency(value)` - Formats as currency
- `_format_percentage(value)` - Formats as percentage
- `_format_date(date_str)` - Formats ISO date
- `_create_header_footer()` - Adds header/footer to pages

### 4. Backend Endpoint (`backend/app/api/user_regard.py`)

**Endpoint:** `GET /api/user-regard/report`

**Authentication:** Required (via `get_current_user` dependency)

**Flow:**
1. Extract user ID and display name from authenticated user
2. Call `build_user_report_data()` to aggregate data
3. Validate sufficient data (sample_size > 0)
4. Call `generate_user_report_narrative()` for AI text
5. Call `generate_user_report_pdf()` to create PDF
6. Return PDF as binary response with proper headers

**Response:**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="ragard-report-{name}-{date}.pdf"`

**Error Handling:**
- 400 if sample_size = 0 (not enough data)
- 500 for internal errors (with generic message)

### 5. Frontend Integration (`frontend/app/account/page.tsx`)

**Download Button:**
- Located in the "Your Regard Score" card
- Only visible when logged in AND sample_size > 0
- Shows loading state while generating
- Triggers browser download on success

**Implementation:**
- `downloadUserReport()` function in `frontend/lib/api.ts`
- Calls `/api/user-regard/report` with auth token
- Returns Blob, creates download link, triggers download
- Handles errors with user-friendly messages

**User Experience:**
- Button disabled if no trade history
- Loading spinner during generation
- Automatic file download with proper filename
- Error messages for failures

## Data Integrity

### Strict Rules:
1. **All numbers come from database** - No AI-generated numeric values
2. **AI only provides text** - Narrative, recommendations, patterns
3. **Consistent Regard Score scale** - 100 = full degen, 0 = disciplined investor
4. **Display name from user metadata** - Never use email in report
5. **Missing data handled gracefully** - Omit sections or show "N/A"

### Validation:
- `build_user_report_data()` validates all data exists before returning
- PDF generator handles None/null values with fallbacks
- AI prompt explicitly forbids numeric invention
- Frontend disables button if insufficient data

## Dependencies

**Backend:**
- `reportlab` - PDF generation
- `openai` - AI narrative generation (already in use)
- `supabase` - Database access (already in use)

**Frontend:**
- No new dependencies (uses existing fetch/Blob APIs)

## File Structure

```
backend/
  app/
    services/
      user_report_data.py      # Data aggregation
      user_report_narrative.py # AI narrative generation
      user_report_pdf.py       # PDF generation
    api/
      user_regard.py           # Report endpoint

frontend/
  lib/
    api.ts                     # downloadUserReport() function
  app/
    account/
      page.tsx                 # Download button UI
```

## Usage

1. User uploads trade history CSV
2. System computes User Regard Score
3. User navigates to Account page
4. User clicks "Download Full Report" button
5. Backend generates PDF (data + AI narrative)
6. PDF downloads automatically

## Future Enhancements

- Charts/graphs in PDF (cumulative PnL, distribution histograms)
- Email delivery option
- Scheduled report generation
- Comparison with previous reports
- Export to other formats (CSV, JSON)

