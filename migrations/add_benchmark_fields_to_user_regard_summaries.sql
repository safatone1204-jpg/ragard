-- Migration: Add benchmark return and relative alpha fields to user_regard_summaries
-- Run this in Supabase SQL Editor

-- Add new columns for market-relative performance
ALTER TABLE public.user_regard_summaries
ADD COLUMN IF NOT EXISTS user_return numeric,  -- User's return over the period (e.g., 0.05 = 5%)
ADD COLUMN IF NOT EXISTS benchmark_return numeric,  -- Benchmark (SPY/VOO) return over same period
ADD COLUMN IF NOT EXISTS relative_alpha numeric,  -- user_return - benchmark_return
ADD COLUMN IF NOT EXISTS period_start timestamptz,  -- Start of trading period
ADD COLUMN IF NOT EXISTS period_end timestamptz,  -- End of trading period
ADD COLUMN IF NOT EXISTS total_pnl numeric,  -- Total PnL over period
ADD COLUMN IF NOT EXISTS reference_capital numeric DEFAULT 10000;  -- Reference capital for return calculation

-- Add comment for documentation
COMMENT ON COLUMN public.user_regard_summaries.user_return IS 'User return as decimal (0.05 = 5%)';
COMMENT ON COLUMN public.user_regard_summaries.benchmark_return IS 'Benchmark (SPY) return over same period';
COMMENT ON COLUMN public.user_regard_summaries.relative_alpha IS 'user_return - benchmark_return (positive = outperformance)';
COMMENT ON COLUMN public.user_regard_summaries.reference_capital IS 'Reference capital used for return calculation (default $10,000)';

