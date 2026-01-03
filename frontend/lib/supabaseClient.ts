/**
 * Supabase client for frontend authentication.
 * Uses the public anon key (safe for client-side use).
 */

import { createClient } from '@supabase/supabase-js'

// Supabase configuration - these should match your backend .env values
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://gyaqeaehpehbrrlrdsvz.supabase.co'
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5YXFlYWVocGVoYnJybHJkc3Z6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1NDkzNjYsImV4cCI6MjA4MDEyNTM2Nn0.78imA_eV1J7rXjEUNrH9clulp6quoP4WbSiw4FTe45s'

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error('Missing Supabase configuration. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

