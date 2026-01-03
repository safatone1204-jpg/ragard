# How to Use Your Own PNG Icon

## Quick Steps

1. **Place your PNG file** anywhere (desktop, downloads, etc.)
   - Your PNG can be any size (the script will resize it)
   - Square images work best (e.g., 512x512, 1024x1024)

2. **Convert to required sizes:**
   ```powershell
   cd extension\ragard-chrome-ext
   npm run convert:icon "C:\path\to\your\icon.png"
   ```
   
   Example:
   ```powershell
   cd extension\ragard-chrome-ext
   npm run convert:icon "C:\Users\safat\Desktop\my-icon.png"
   ```

3. **Reload extension in Chrome:**
   - Go to `chrome://extensions/`
   - Remove the Ragard extension
   - Click "Load unpacked"
   - Select `extension/ragard-chrome-ext` folder
   - Your new icon should appear!

## Alternative: Manual Replacement

If you prefer to do it manually:

1. **Resize your PNG** to these sizes:
   - 16x16 pixels → save as `icon16.png`
   - 32x32 pixels → save as `icon32.png`
   - 48x48 pixels → save as `icon48.png`
   - 128x128 pixels → save as `icon128.png`

2. **Replace the files:**
   - Copy all 4 PNG files to: `extension/ragard-chrome-ext/icons/`
   - Overwrite the existing `icon16.png`, `icon32.png`, `icon48.png`, `icon128.png`

3. **Reload extension** in Chrome (same steps as above)

## Tips

- **Square images work best** - Chrome icons should be square
- **High resolution** - Start with at least 128x128 or larger
- **Preview**: Open `icons/preview.html` in browser to see all sizes
- **Transparency**: PNG supports transparency, which will show as dark background

