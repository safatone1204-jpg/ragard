# Reddit API Setup Guide

This guide explains how to set up Reddit API credentials for the Ragard backend.

## Option 1: Using PRAW with Reddit API (Recommended)

### Step 1: Create a Reddit Application

1. Go to https://www.reddit.com/prefs/apps
2. Scroll down and click **"create another app..."** or **"create app"**
3. Fill in the form:
   - **Name**: `Ragard` (or any name you prefer)
   - **App type**: Select **"script"**
   - **Description**: Optional
   - **About URL**: Optional
   - **Redirect URI**: `http://localhost:8000` (required but not used for script apps)
4. Click **"create app"**

### Step 2: Get Your Credentials

After creating the app, you'll see:
- **Client ID**: The string under your app name (looks like: `abc123def456`)
- **Secret**: The "secret" field (looks like: `xyz789_secret_key_here`)

### Step 3: Add Credentials to `.env` File

Add these lines to your `backend/.env` file:

```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=Ragard/1.0 by YourRedditUsername

# Optional: For authenticated access (better rate limits)
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

**Important Notes:**
- Replace `your_client_id_here` and `your_client_secret_here` with your actual credentials
- Replace `YourRedditUsername` in `REDDIT_USER_AGENT` with your Reddit username
- The user agent format should be: `AppName/Version by RedditUsername`
- If you don't provide `REDDIT_USERNAME` and `REDDIT_PASSWORD`, it will use application-only OAuth (still better than read-only)

### Step 4: Install PRAW

```bash
pip install praw
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

## Option 2: Read-Only Mode (No Credentials Required)

If you don't want to set up credentials, the code will automatically use read-only mode. However, this has:
- Stricter rate limits (60 requests per minute)
- Less reliable access
- May be blocked more easily

## Rate Limits

- **Read-only mode**: 60 requests per minute
- **Application-only (OAuth)**: 60 requests per minute (more reliable)
- **Authenticated user**: 60 requests per minute (most reliable)

PRAW automatically handles rate limiting, so you don't need to worry about it.

## Testing

After setting up credentials, restart your backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The Reddit integration will automatically use your credentials if they're set in the `.env` file.

## Troubleshooting

**Error: "Invalid credentials"**
- Double-check your `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- Make sure there are no extra spaces in your `.env` file

**Error: "Rate limit exceeded"**
- PRAW handles rate limiting automatically, but if you see this, wait a minute and try again
- Consider using authenticated access for better reliability

**No posts returned**
- Check that the subreddits exist and are accessible
- Verify your timeframe is reasonable (24h, 7d, 30d)
- Check the backend logs for specific error messages

