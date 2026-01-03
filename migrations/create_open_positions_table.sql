-- Migration: Create user_open_positions table
-- Run this in Supabase SQL Editor

-- Table for tracking open (unclosed) positions
CREATE TABLE IF NOT EXISTS public.user_open_positions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker text NOT NULL,
    side text NOT NULL,  -- 'LONG' or 'SHORT'
    quantity numeric NOT NULL,
    entry_price numeric NOT NULL,
    entry_time timestamptz NOT NULL,
    entry_fees numeric DEFAULT 0,
    current_price numeric,  -- Last fetched current price
    unrealized_pnl numeric,  -- Estimated current P/L
    last_price_update timestamptz,  -- When current_price was last fetched
    regard_score_at_entry numeric,  -- Regard Score when position was opened
    description text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_open_positions_user_id ON public.user_open_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_open_positions_user_ticker ON public.user_open_positions(user_id, ticker);

-- Enable Row Level Security
ALTER TABLE public.user_open_positions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view their own open positions." ON public.user_open_positions;
DROP POLICY IF EXISTS "Users can create their own open positions." ON public.user_open_positions;
DROP POLICY IF EXISTS "Users can update their own open positions." ON public.user_open_positions;
DROP POLICY IF EXISTS "Users can delete their own open positions." ON public.user_open_positions;

CREATE POLICY "Users can view their own open positions." ON public.user_open_positions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own open positions." ON public.user_open_positions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own open positions." ON public.user_open_positions
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own open positions." ON public.user_open_positions
    FOR DELETE USING (auth.uid() = user_id);

-- Add comments
COMMENT ON TABLE public.user_open_positions IS 'Tracks open (unclosed) positions for each user';
COMMENT ON COLUMN public.user_open_positions.current_price IS 'Last fetched current market price';
COMMENT ON COLUMN public.user_open_positions.unrealized_pnl IS 'Estimated current P/L based on current_price';

