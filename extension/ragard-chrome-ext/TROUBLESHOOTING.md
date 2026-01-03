# Troubleshooting the Ragard Extension

## Issue: "Please refresh the Reddit page and try again"

This error means the content script hasn't loaded yet. Here's how to fix it:

### Step 1: Reload the Extension
1. Go to `chrome://extensions`
2. Find "Ragard – Reddit Analyzer"
3. Click the **reload icon** (circular arrow) on the extension card

### Step 2: Refresh the Reddit Page
1. Navigate to a Reddit post (e.g., `https://www.reddit.com/r/pennystocks/...`)
2. **Refresh the page** (F5 or Ctrl+R / Cmd+R)
3. You should now see the Ragard panel appear on the right side of the page

### Step 3: Test the Extension
1. Click the Ragard extension icon in Chrome's toolbar
2. Click "Analyze" in the popup
3. The panel should show "Analyzing post with Ragard..." and then display results

## Why This Happens

Content scripts only load when:
- The page matches the `matches` pattern in `manifest.json` (Reddit URLs)
- The page is loaded/reloaded AFTER the extension is installed/reloaded

If you reload the extension but don't refresh the Reddit page, the content script won't be injected.

## Debugging

If it still doesn't work:

1. **Check the browser console**:
   - Right-click on the Reddit page → "Inspect"
   - Go to the "Console" tab
   - Look for `[Ragard] Content script loaded` message
   - Check for any errors

2. **Check extension errors**:
   - Go to `chrome://extensions`
   - Find the Ragard extension
   - Click "Errors" if any are shown

3. **Verify the panel exists**:
   - On a Reddit page, open DevTools (F12)
   - In the Elements tab, search for `ragard-panel-root`
   - If it doesn't exist, the content script didn't load

4. **Check backend is running**:
   - Make sure FastAPI is running on `http://localhost:8000`
   - Test the endpoint directly: `curl -X POST http://localhost:8000/api/extension/analyze-reddit-post -H "Content-Type: application/json" -d '{"url":"test"}'`

## Common Issues

- **Panel not visible**: Check z-index conflicts with Reddit's UI
- **No tickers detected**: Make sure the post actually mentions ticker symbols (e.g., "ASST", "GME")
- **Backend connection error**: Ensure FastAPI is running and CORS is configured

