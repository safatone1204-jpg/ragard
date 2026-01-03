-- ============================================
-- CREATE USER REGARD TABLES IN SUPABASE
-- ============================================
-- Copy this ENTIRE file and paste into Supabase SQL Editor
-- Then click "Run" or press Ctrl+Enter
-- ============================================

-- 1. Create user_trades table
CREATE TABLE IF NOT EXISTS public.user_trades (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker text NOT NULL,
    side text NOT NULL,
    quantity numeric NOT NULL,
    entry_time timestamptz NOT NULL,
    exit_time timestamptz NOT NULL,
    entry_price numeric NOT NULL,
    exit_price numeric NOT NULL,
    realized_pnl numeric NOT NULL,
    holding_period_seconds integer NOT NULL,
    regard_score_at_entry numeric,
    regard_score_at_exit numeric,
    raw_metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

-- 2. Create indexes for user_trades
CREATE INDEX IF NOT EXISTS idx_user_trades_user_ticker ON public.user_trades(user_id, ticker);
CREATE INDEX IF NOT EXISTS idx_user_trades_user_created ON public.user_trades(user_id, created_at);

-- 3. Enable Row Level Security for user_trades
ALTER TABLE public.user_trades ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS policies for user_trades
-- Note: If policies already exist, you may see errors - that's okay, just ignore them
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_trades' 
        AND policyname = 'Users can view their own trades.'
    ) THEN
        CREATE POLICY "Users can view their own trades." ON public.user_trades
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_trades' 
        AND policyname = 'Users can create their own trades.'
    ) THEN
        CREATE POLICY "Users can create their own trades." ON public.user_trades
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_trades' 
        AND policyname = 'Users can update their own trades.'
    ) THEN
        CREATE POLICY "Users can update their own trades." ON public.user_trades
            FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_trades' 
        AND policyname = 'Users can delete their own trades.'
    ) THEN
        CREATE POLICY "Users can delete their own trades." ON public.user_trades
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;

-- 5. Create user_regard_summaries table
CREATE TABLE IF NOT EXISTS public.user_regard_summaries (
    user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    regard_score numeric,
    wins integer NOT NULL DEFAULT 0,
    losses integer NOT NULL DEFAULT 0,
    win_rate numeric,
    sample_size integer NOT NULL DEFAULT 0,
    last_updated timestamptz DEFAULT now(),
    ai_summary text,
    ai_raw jsonb
);

-- 6. Create index for user_regard_summaries
CREATE INDEX IF NOT EXISTS idx_user_regard_summaries_user_id ON public.user_regard_summaries(user_id);

-- 7. Enable Row Level Security for user_regard_summaries
ALTER TABLE public.user_regard_summaries ENABLE ROW LEVEL SECURITY;

-- 8. Create RLS policies for user_regard_summaries
-- Note: If policies already exist, you may see errors - that's okay, just ignore them
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_regard_summaries' 
        AND policyname = 'Users can view their own regard summary.'
    ) THEN
        CREATE POLICY "Users can view their own regard summary." ON public.user_regard_summaries
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_regard_summaries' 
        AND policyname = 'Users can create their own regard summary.'
    ) THEN
        CREATE POLICY "Users can create their own regard summary." ON public.user_regard_summaries
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_regard_summaries' 
        AND policyname = 'Users can update their own regard summary.'
    ) THEN
        CREATE POLICY "Users can update their own regard summary." ON public.user_regard_summaries
            FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_regard_summaries' 
        AND policyname = 'Users can delete their own regard summary.'
    ) THEN
        CREATE POLICY "Users can delete their own regard summary." ON public.user_regard_summaries
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;

-- ============================================
-- DONE! Tables should now be created.
-- ============================================
-- Next steps:
-- 1. Go to Table Editor in Supabase to verify tables exist
-- 2. If tables don't appear, go to Settings > API > Reload schema cache
-- 3. Try uploading your CSV again
-- ============================================

