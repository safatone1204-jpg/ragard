# Setting Up User Regard Score Tables in Supabase

The `user_trades` and `user_regard_summaries` tables need to be created in your Supabase database before you can upload trade history.

## Quick Setup Steps

1. **Open Supabase Dashboard**
   - Go to https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Run the Schema**
   - Copy the entire contents of `supabase_schema_user_regard.sql`
   - Paste it into the SQL Editor
   - Click "Run" (or press Ctrl+Enter)

4. **Verify Tables Created**
   - Go to "Table Editor" in the left sidebar
   - You should see `user_trades` and `user_regard_summaries` tables

## What the Schema Creates

- **`user_trades`**: Stores your parsed trade history
- **`user_regard_summaries`**: Stores your computed Regard Score and stats

Both tables have Row Level Security (RLS) enabled, so users can only see their own data.

## Troubleshooting

If you get permission errors:
- Make sure you're using the SQL Editor (not the Table Editor)
- The SQL should run with your project's admin privileges

If tables still don't appear:
- Check the "Table Editor" and refresh
- Look for any error messages in the SQL Editor output

