# Ragard Chrome Extension

V1 test extension for analyzing Reddit posts with Ragard AI.

## Setup

1. Open Chrome and navigate to `chrome://extensions`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this folder: `extension/ragard-chrome-ext/`

## Usage

1. Navigate to a Reddit post (e.g., `https://www.reddit.com/r/wallstreetbets/...`)
2. Click the Ragard extension icon in the toolbar
3. Click "Analyze" in the popup
4. View the JSON response from the backend

## Development

- `manifest.json`: Extension configuration (Manifest V3)
- `popup.html`: Popup UI
- `popup.js`: Logic for sending requests to backend
- `icon*.png`: Extension icons (TODO: add actual icons)

## Backend Endpoint

The extension calls: `POST http://localhost:8000/api/extension/analyze-reddit-post`

See `backend/app/api/extension.py` for the endpoint implementation.

