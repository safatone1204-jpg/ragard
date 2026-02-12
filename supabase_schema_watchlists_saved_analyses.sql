-- Supabase Schema for Watchlists and Saved Analyses
-- 
-- IMPORTANT: This SQL file should be run manually in the Supabase SQL Editor.
-- Do NOT execute this from the backend code.
--
-- Instructions:
-- 1. Open your Supabase project dashboard
-- 2. Go to SQL Editor
-- 3. Paste and run this entire file
-- 4. Verify the tables and RLS policies were created

-- ============================================================================
-- WATCHLISTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.watchlists (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name text NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- ============================================================================
-- WATCHLIST ITEMS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.watchlist_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id uuid NOT NULL REFERENCES public.watchlists(id) ON DELETE CASCADE,
    ticker text NOT NULL,
    created_at timestamptz DEFAULT now(),
    -- Prevent duplicate tickers in the same watchlist
    UNIQUE(watchlist_id, ticker)
);

-- ============================================================================
-- SAVED ANALYSES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.saved_analyses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker text NOT NULL,
    snapshot jsonb NOT NULL,
    tags text[] DEFAULT '{}',
    note text,
    created_at timestamptz DEFAULT now()
);

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_analyses ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES FOR WATCHLISTS
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view their own watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "Users can create their own watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "Users can update their own watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "Users can delete their own watchlists" ON public.watchlists;

-- Allow users to SELECT their own watchlists
CREATE POLICY "Users can view their own watchlists"
    ON public.watchlists
    FOR SELECT
    USING (user_id = auth.uid());

-- Allow users to INSERT their own watchlists
CREATE POLICY "Users can create their own watchlists"
    ON public.watchlists
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Allow users to UPDATE their own watchlists
CREATE POLICY "Users can update their own watchlists"
    ON public.watchlists
    FOR UPDATE
    USING (user_id = auth.uid());

-- Allow users to DELETE their own watchlists
CREATE POLICY "Users can delete their own watchlists"
    ON public.watchlists
    FOR DELETE
    USING (user_id = auth.uid());

-- ============================================================================
-- RLS POLICIES FOR WATCHLIST ITEMS
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view items from their own watchlists" ON public.watchlist_items;
DROP POLICY IF EXISTS "Users can add items to their own watchlists" ON public.watchlist_items;
DROP POLICY IF EXISTS "Users can update items in their own watchlists" ON public.watchlist_items;
DROP POLICY IF EXISTS "Users can delete items from their own watchlists" ON public.watchlist_items;

-- Allow users to SELECT items from their own watchlists
CREATE POLICY "Users can view items from their own watchlists"
    ON public.watchlist_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.watchlists w
            WHERE w.id = watchlist_id
            AND w.user_id = auth.uid()
        )
    );

-- Allow users to INSERT items into their own watchlists
CREATE POLICY "Users can add items to their own watchlists"
    ON public.watchlist_items
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.watchlists w
            WHERE w.id = watchlist_id
            AND w.user_id = auth.uid()
        )
    );

-- Allow users to UPDATE items in their own watchlists
CREATE POLICY "Users can update items in their own watchlists"
    ON public.watchlist_items
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.watchlists w
            WHERE w.id = watchlist_id
            AND w.user_id = auth.uid()
        )
    );

-- Allow users to DELETE items from their own watchlists
CREATE POLICY "Users can delete items from their own watchlists"
    ON public.watchlist_items
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.watchlists w
            WHERE w.id = watchlist_id
            AND w.user_id = auth.uid()
        )
    );

-- ============================================================================
-- RLS POLICIES FOR SAVED ANALYSES
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view their own saved analyses" ON public.saved_analyses;
DROP POLICY IF EXISTS "Users can create their own saved analyses" ON public.saved_analyses;
DROP POLICY IF EXISTS "Users can update their own saved analyses" ON public.saved_analyses;
DROP POLICY IF EXISTS "Users can delete their own saved analyses" ON public.saved_analyses;

-- Allow users to SELECT their own saved analyses
CREATE POLICY "Users can view their own saved analyses"
    ON public.saved_analyses
    FOR SELECT
    USING (user_id = auth.uid());

-- Allow users to INSERT their own saved analyses
CREATE POLICY "Users can create their own saved analyses"
    ON public.saved_analyses
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Allow users to UPDATE their own saved analyses
CREATE POLICY "Users can update their own saved analyses"
    ON public.saved_analyses
    FOR UPDATE
    USING (user_id = auth.uid());

-- Allow users to DELETE their own saved analyses
CREATE POLICY "Users can delete their own saved analyses"
    ON public.saved_analyses
    FOR DELETE
    USING (user_id = auth.uid());

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON public.watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_watchlist_id ON public.watchlist_items(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_ticker ON public.watchlist_items(ticker);
CREATE INDEX IF NOT EXISTS idx_saved_analyses_user_id ON public.saved_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_analyses_ticker ON public.saved_analyses(ticker);

-- ============================================================================
-- MIGRATION: For existing databases, add UNIQUE constraint
-- ============================================================================
-- If you already have watchlist_items table, run this to add the constraint:
-- 
-- ALTER TABLE public.watchlist_items 
-- ADD CONSTRAINT watchlist_items_watchlist_id_ticker_key 
-- UNIQUE (watchlist_id, ticker);
--
-- Note: This will fail if you have duplicate entries. Clean them up first:
-- DELETE FROM public.watchlist_items a
-- USING public.watchlist_items b
-- WHERE a.id < b.id 
-- AND a.watchlist_id = b.watchlist_id 
-- AND a.ticker = b.ticker;
