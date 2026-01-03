# Quick Setup: Create User Regard Tables

## The Problem
You're getting this error:
```
Database table 'user_trades' does not exist
```

## The Solution (3 Steps)

### Step 1: Open Supabase SQL Editor
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **"SQL Editor"** in the left sidebar
4. Click **"New query"**

### Step 2: Run the SQL
1. Open the file `CREATE_USER_REGARD_TABLES.sql` in this folder
2. **Copy the ENTIRE contents** (Ctrl+A, Ctrl+C)
3. **Paste into the SQL Editor** (Ctrl+V)
4. Click **"Run"** button (or press Ctrl+Enter)

### Step 3: Verify It Worked
1. Look for a success message in the SQL Editor (should say "Success. No rows returned")
2. Go to **"Table Editor"** in the left sidebar
3. You should see two new tables:
   - `user_trades`
   - `user_regard_summaries`

## If Tables Don't Appear

**Option A: Refresh Schema Cache**
1. Go to **Settings** → **API**
2. Scroll to **"PostgREST"** section
3. Click **"Reload schema cache"** or **"Refresh schema"**

**Option B: Restart Project**
1. Go to **Settings** → **General**
2. Click **"Restart project"**
3. Wait 1-2 minutes for restart

## Test It

After creating the tables, try uploading your CSV again. It should work!

## Still Having Issues?

1. Check the SQL Editor for any error messages
2. Make sure you're in the correct Supabase project
3. Verify your `.env` file has the correct `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

