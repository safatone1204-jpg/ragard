# Ragard Chrome Extension

Chrome extension for analyzing Reddit posts with Ragard AI. Works with both the production website (ragardai.com) and local development.

## Publishing to Chrome Web Store

To make this extension available to all users, see **[CHROME_WEB_STORE_GUIDE.md](./CHROME_WEB_STORE_GUIDE.md)** for complete publishing instructions.

**New to packaging?** See **[PACKAGING_GUIDE.md](./PACKAGING_GUIDE.md)** for a detailed, beginner-friendly guide on creating the ZIP file.

Quick steps:
1. Pay $5 one-time fee for Chrome Web Store developer account
2. Create ZIP file of the extension (see PACKAGING_GUIDE.md for help)
3. Submit to Chrome Web Store using the content in **[STORE_LISTING.md](./STORE_LISTING.md)**
4. Wait for review (1-3 business days)

## Setup

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this folder: `extension/ragard-chrome-ext/`

## Configuration

The extension **automatically detects** whether you're on the production website or localhost and uses the appropriate URLs:

- **Production** (ragardai.com): Uses `https://api.ragardai.com` and `https://ragardai.com`
- **Local development** (localhost): Uses `http://localhost:8000` and `http://localhost:3000`

### Manual Configuration (Optional)

If you need to manually configure URLs:

1. Right-click the extension icon → **Options**
2. Uncheck "Auto-detect environment" to enable manual mode
3. Enter your API and Web App URLs
4. Click "Save Settings"

## Usage

1. Navigate to a Reddit post (e.g., `https://www.reddit.com/r/wallstreetbets/...`)
2. Click the Ragard extension icon in the toolbar (or use the side panel)
3. The extension will automatically use the correct backend URL based on your current tab

## How It Works

- **Auto-detection (default)**: The extension checks the URL of your active tab
  - If you're on `ragardai.com`, it uses production URLs
  - If you're on `localhost`, it uses local development URLs
  - Otherwise, it defaults to production URLs

- **Manual mode**: You can disable auto-detection and set custom URLs in the options page

## Development

- `manifest.json`: Extension configuration (Manifest V3)
- `config.js`: Configuration and auto-detection logic
- `background.js`: Background service worker
- `sidePanel.html/js`: Side panel UI and logic
- `contentScript.js`: Content script for Reddit pages
- `options.html/js`: Options/settings page

## Backend Endpoints

The extension calls various endpoints:
- `POST /api/extension/analyze-reddit-post` - Analyze Reddit posts
- `GET /api/tickers/{symbol}` - Get ticker information
- `GET /api/narratives` - Get narratives
- And more...

See `backend/app/api/extension.py` and other API files for endpoint implementations.

