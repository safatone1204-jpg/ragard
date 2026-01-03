# Detailed Environment Setup Guide

This guide walks you through setting up all environment variables for Ragard.

## Step 1: Backend Environment Variables (`backend/.env`)

### 1.1 Open the Backend .env File

**Windows:**
```powershell
# Option 1: Open in Notepad
notepad backend\.env

# Option 2: Open in VS Code (if installed)
code backend\.env

# Option 3: Open in your default editor
start backend\.env
```

**Linux/Mac:**
```bash
# Option 1: Open in nano (simple editor)
nano backend/.env

# Option 2: Open in VS Code
code backend/.env

# Option 3: Open in vim
vim backend/.env
```

### 1.2 Required Variables (MUST Fill In)

#### ENVIRONMENT
```
ENVIRONMENT=development
```
- **For local development**: `development`
- **For production**: `production`
- **What it does**: Controls whether SQLite is allowed (dev only) and other environment-specific behavior

#### SUPABASE_URL
```
SUPABASE_URL=https://your-project-id.supabase.co
```
- **How to get it**:
  1. Go to https://supabase.com
  2. Sign up or log in
  3. Create a new project (or select existing)
  4. Go to Project Settings → API
  5. Copy the "Project URL" (looks like `https://xxxxxxxxxxxxx.supabase.co`)

#### SUPABASE_ANON_KEY
```
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvdXItcmVmLWlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUxOTIwMDAsImV4cCI6MTk2MDc2ODAwMH0.your-anon-key-here
```
- **How to get it**:
  1. In Supabase Dashboard → Project Settings → API
  2. Find "anon public" key
  3. Copy the entire JWT token (starts with `eyJ...`)

#### SUPABASE_SERVICE_ROLE_KEY
```
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvdXItcmVmLWlkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY0NTE5MjAwMCwiZXhwIjoxOTYwNzY4MDAwfQ.your-service-role-key-here
```
- **How to get it**:
  1. In Supabase Dashboard → Project Settings → API
  2. Find "service_role" key (⚠️ **SECRET - never expose this**)
  3. Copy the entire JWT token
- **⚠️ WARNING**: This key has full database access. Never commit it to git or expose it publicly.

#### CORS_ORIGINS
```
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```
- **For local development**: Leave as-is (`http://localhost:3000,http://localhost:8000`)
- **For production**: Replace with your actual domains:
  ```
  CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
  ```
- **What it does**: Controls which origins can make requests to your API
- **Format**: Comma-separated list of URLs (no spaces after commas)

### 1.3 Optional Variables (Recommended)

#### OPENAI_API_KEY
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
- **Required for**: AI features (post analysis, user reports, regard score refinement)
- **How to get it**:
  1. Go to https://platform.openai.com
  2. Sign up or log in
  3. Go to API Keys section
  4. Create a new secret key
  5. Copy it immediately (you won't see it again)
- **Note**: Without this, AI features will be disabled

#### REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```
- **Required for**: Authenticated Reddit API access (higher rate limits)
- **How to get them**:
  1. Go to https://www.reddit.com/prefs/apps
  2. Click "create another app..." or "create application"
  3. Fill in:
     - **Name**: Ragard (or any name)
     - **Type**: script
     - **Description**: Stock analysis bot
     - **Redirect URI**: `http://localhost:8000` (can be anything for script type)
  4. Click "create app"
  5. Copy the client ID (under the app name, looks like random characters)
  6. Copy the secret (labeled "secret")
- **Note**: Without these, the app uses read-only mode (lower rate limits)

#### REDDIT_USERNAME and REDDIT_PASSWORD
```
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```
- **Optional**: Only needed if you want authenticated Reddit access
- **Note**: Consider using a dedicated Reddit account for the bot

#### SENTRY_DSN
```
SENTRY_DSN=https://xxxxxxxxxxxxx@xxxxxxxxxxxxx.ingest.sentry.io/xxxxxxxxxxxxx
```
- **Required for**: Error tracking in production
- **How to get it**:
  1. Go to https://sentry.io
  2. Create a project
  3. Select Python as the platform
  4. Copy the DSN from the setup instructions
- **Note**: Optional but highly recommended for production

### 1.4 Example Complete Backend .env File

```env
# ============================================================================
# REQUIRED FOR PRODUCTION
# ============================================================================

ENVIRONMENT=development

SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0NTE5MjAwMCwiZXhwIjoxOTYwNzY4MDAwfQ.example-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjQ1MTkyMDAwLCJleHAiOjE5NjA3NjgwMDB9.example-service-role-key

CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ============================================================================
# OPTIONAL (but recommended for full functionality)
# ============================================================================

OPENAI_API_KEY=sk-proj-example-key-here

REDDIT_CLIENT_ID=example_client_id
REDDIT_CLIENT_SECRET=example_client_secret
REDDIT_USER_AGENT=Ragard/1.0 (Stock Analysis Bot)
REDDIT_USERNAME=
REDDIT_PASSWORD=

# ============================================================================
# SERVER CONFIGURATION (usually don't need to change)
# ============================================================================

HOST=0.0.0.0
PORT=8000

# ============================================================================
# OPTIONAL - Error Tracking
# ============================================================================

SENTRY_DSN=
SENTRY_ENVIRONMENT=development
```

## Step 2: Frontend Environment Variables (`frontend/.env.local`)

### 2.1 Open the Frontend .env.local File

**Windows:**
```powershell
notepad frontend\.env.local
# or
code frontend\.env.local
```

**Linux/Mac:**
```bash
nano frontend/.env.local
# or
code frontend/.env.local
```

### 2.2 Required Variables (MUST Fill In)

#### NEXT_PUBLIC_API_BASE_URL
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
- **For local development**: `http://localhost:8000` (leave as-is)
- **For production**: `https://api.yourdomain.com` (replace with your backend URL)
- **What it does**: Tells the frontend where to send API requests
- **Note**: Must start with `http://` or `https://`

#### NEXT_PUBLIC_SUPABASE_URL
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
```
- **How to get it**: Same as backend `SUPABASE_URL` (use the same value)
- **What it does**: Frontend uses this to authenticate users

#### NEXT_PUBLIC_SUPABASE_ANON_KEY
```
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvdXItcmVmLWlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUxOTIwMDAsImV4cCI6MTk2MDc2ODAwMH0.your-anon-key-here
```
- **How to get it**: Same as backend `SUPABASE_ANON_KEY` (use the same value)
- **What it does**: Frontend uses this to authenticate users
- **Note**: This is the "anon" key (safe for client-side use), NOT the service role key

### 2.3 Optional Variables

#### NEXT_PUBLIC_SENTRY_DSN
```
NEXT_PUBLIC_SENTRY_DSN=https://xxxxxxxxxxxxx@xxxxxxxxxxxxx.ingest.sentry.io/xxxxxxxxxxxxx
```
- **Required for**: Frontend error tracking
- **How to get it**: Same process as backend, but create a JavaScript/Next.js project in Sentry
- **Note**: Optional but recommended for production

#### NEXT_PUBLIC_SENTRY_ENVIRONMENT
```
NEXT_PUBLIC_SENTRY_ENVIRONMENT=development
```
- **For local development**: `development`
- **For production**: `production`

### 2.4 Example Complete Frontend .env.local File

```env
# ============================================================================
# REQUIRED FOR PRODUCTION
# ============================================================================

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0NTE5MjAwMCwiZXhwIjoxOTYwNzY4MDAwfQ.example-anon-key

# ============================================================================
# OPTIONAL - Error Tracking
# ============================================================================

NEXT_PUBLIC_SENTRY_DSN=
NEXT_PUBLIC_SENTRY_ENVIRONMENT=development
```

## Step 3: Verify Your Configuration

### 3.1 Test Backend Configuration

After filling in `backend/.env`, test that it works:

```bash
cd backend
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Try to start the server - it will validate env vars
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**What to look for:**
- ✅ If all required vars are set: Server starts successfully
- ❌ If vars are missing: You'll see an error listing which variables are missing

**Example success output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Example error output:**
```
ERROR: Missing required environment variables:
  - SUPABASE_URL
  - SUPABASE_ANON_KEY
Please set these variables in your .env file or environment.
```

### 3.2 Test Frontend Configuration

After filling in `frontend/.env.local`, test that it works:

```bash
cd frontend
npm install  # If you haven't already
npm run build
```

**What to look for:**
- ✅ If all required vars are set: Build completes successfully
- ❌ If vars are missing: Build will show warnings or fail

**Note**: The frontend validates env vars at build time, so missing vars will be caught during `npm run build`.

### 3.3 Test the Health Endpoint

Once backend is running, test the health endpoint:

```bash
# Using curl
curl http://localhost:8000/health

# Using PowerShell (Windows)
Invoke-WebRequest -Uri http://localhost:8000/health

# Or just open in browser
# http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "checks": {
    "database": "healthy",
    "supabase": "healthy"
  }
}
```

## Step 4: Common Issues and Solutions

### Issue: "Missing required environment variables" error

**Solution:**
1. Check that you saved the `.env` file (not just `.env.example`)
2. Verify the file is in the correct location: `backend/.env` or `frontend/.env.local`
3. Check for typos in variable names (they're case-sensitive)
4. Make sure there are no spaces around the `=` sign: `VAR=value` not `VAR = value`
5. Remove any quotes around values unless the value itself contains spaces

### Issue: Supabase connection fails

**Solution:**
1. Verify `SUPABASE_URL` is correct (should end with `.supabase.co`)
2. Verify `SUPABASE_ANON_KEY` is the full JWT token (starts with `eyJ...`)
3. Check that your Supabase project is active (not paused)
4. Verify you copied the entire key (JWT tokens are very long)

### Issue: CORS errors in browser

**Solution:**
1. Check `CORS_ORIGINS` includes your frontend URL
2. For local dev, use: `CORS_ORIGINS=http://localhost:3000,http://localhost:8000`
3. Make sure there are no spaces in the comma-separated list
4. Restart the backend server after changing CORS_ORIGINS

### Issue: Frontend can't connect to backend

**Solution:**
1. Verify `NEXT_PUBLIC_API_BASE_URL` matches where your backend is running
2. Check that backend server is actually running
3. Test the backend directly: `curl http://localhost:8000/health`
4. Make sure there's no typo in the URL (http vs https, port number, etc.)

## Step 5: Production Checklist

Before deploying to production, ensure:

- [ ] `ENVIRONMENT=production` in backend `.env`
- [ ] `CORS_ORIGINS` contains your production domain(s)
- [ ] `NEXT_PUBLIC_API_BASE_URL` points to production backend
- [ ] All Supabase keys are production keys (not test/dev)
- [ ] `OPENAI_API_KEY` is set (if using AI features)
- [ ] `SENTRY_DSN` is set (recommended for error tracking)
- [ ] All secrets are stored securely (not in git)
- [ ] Backend health endpoint returns "healthy"
- [ ] Frontend builds successfully

## Quick Reference: Where to Get Each Value

| Variable | Where to Get It |
|----------|----------------|
| `SUPABASE_URL` | Supabase Dashboard → Project Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase Dashboard → Project Settings → API → anon public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Project Settings → API → service_role key |
| `OPENAI_API_KEY` | OpenAI Platform → API Keys → Create new secret key |
| `REDDIT_CLIENT_ID` | Reddit → Preferences → Apps → Create app → Client ID |
| `REDDIT_CLIENT_SECRET` | Reddit → Preferences → Apps → Your app → Secret |
| `SENTRY_DSN` | Sentry.io → Create project → Copy DSN |

## Need Help?

- Check the example files: `backend/env.example` and `frontend/env.example`
- Review the main README.md for general setup instructions
- Check `PRODUCTION_READINESS_SUMMARY.md` for implementation details

