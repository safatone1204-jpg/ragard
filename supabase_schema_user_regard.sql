-- Supabase Schema for User Regard Score System
--
-- To be run manually in the Supabase SQL Editor.
-- DO NOT run this from the backend code.

-- 1. User Trades Table
-- Stores normalized trade history for each user
CREATE TABLE public.user_trades (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker text NOT NULL,
    side text NOT NULL,  -- 'LONG' or 'SHORT' (normalized)
    quantity numeric NOT NULL,
    entry_time timestamptz NOT NULL,
    exit_time timestamptz NOT NULL,
    entry_price numeric NOT NULL,
    exit_price numeric NOT NULL,
    realized_pnl numeric NOT NULL,
    holding_period_seconds integer NOT NULL,
    regard_score_at_entry numeric,  -- Regard Score of ticker when trade was entered (0-100)
    regard_score_at_exit numeric,   -- Regard Score of ticker when trade was exited (0-100)
    raw_metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_user_trades_user_ticker ON public.user_trades(user_id, ticker);
CREATE INDEX idx_user_trades_user_created ON public.user_trades(user_id, created_at);

-- Enable Row Level Security
ALTER TABLE public.user_trades ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_trades
-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view their own trades." ON public.user_trades;
DROP POLICY IF EXISTS "Users can create their own trades." ON public.user_trades;
DROP POLICY IF EXISTS "Users can update their own trades." ON public.user_trades;
DROP POLICY IF EXISTS "Users can delete their own trades." ON public.user_trades;

CREATE POLICY "Users can view their own trades." ON public.user_trades
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own trades." ON public.user_trades
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own trades." ON public.user_trades
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own trades." ON public.user_trades
    FOR DELETE USING (auth.uid() = user_id);


-- 2. User Regard Summaries Table
-- Stores the latest computed user regard metrics
CREATE TABLE public.user_regard_summaries (
    user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    regard_score numeric,  -- 0-100
    wins integer NOT NULL DEFAULT 0,
    losses integer NOT NULL DEFAULT 0,
    win_rate numeric,  -- 0-1 (0-100% as decimal)
    sample_size integer NOT NULL DEFAULT 0,
    last_updated timestamptz DEFAULT now(),
    ai_summary text,
    ai_raw jsonb
);

-- Index for performance
CREATE INDEX idx_user_regard_summaries_user_id ON public.user_regard_summaries(user_id);

-- Enable Row Level Security
ALTER TABLE public.user_regard_summaries ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_regard_summaries
-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view their own regard summary." ON public.user_regard_summaries;
DROP POLICY IF EXISTS "Users can create their own regard summary." ON public.user_regard_summaries;
DROP POLICY IF EXISTS "Users can update their own regard summary." ON public.user_regard_summaries;
DROP POLICY IF EXISTS "Users can delete their own regard summary." ON public.user_regard_summaries;

CREATE POLICY "Users can view their own regard summary." ON public.user_regard_summaries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own regard summary." ON public.user_regard_summaries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own regard summary." ON public.user_regard_summaries
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own regard summary." ON public.user_regard_summaries
    FOR DELETE USING (auth.uid() = user_id);

