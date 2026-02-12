# Fixing PowerShell Execution Policy Error

If you see this error:
```
running scripts is disabled on this system
```

Here's how to fix it:

## Quick Fix (Recommended)

1. **Open PowerShell as Administrator** (important!)
   - Press `Windows Key + X`
   - Click "Windows PowerShell (Admin)" or "Terminal (Admin)"
   - Click "Yes" when asked for permission

2. **Run this command:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   - Type `Y` and press Enter when asked

3. **Close the admin PowerShell**

4. **Try the script again** in your regular PowerShell:
   ```powershell
   .\package-for-store.ps1
   ```

## What This Does

- `RemoteSigned` = Allows local scripts to run (like your script), but requires signed scripts from the internet
- `Scope CurrentUser` = Only affects your user account (safer, no admin needed)

This is safe and only affects your user account.

## Alternative: Manual Packaging (If You Don't Want to Change Settings)

If you don't want to change PowerShell settings, you can package manually:

1. **Open File Explorer**
   - Go to: `C:\Users\safat\Desktop\Ragard\extension\ragard-chrome-ext`

2. **Select all the files** (hold Ctrl and click each):
   - `manifest.json`
   - `background.js`
   - `config.js`
   - `contentScript.js`
   - `sidePanel.html`
   - `sidePanel.js`
   - `options.html`
   - `options.js`
   - `popup.html`
   - `popup.js`
   - `pageContext.js`
   - `authStatus.js`
   - The `icons` folder (click once to select the whole folder)
   - The `scripts` folder (if it exists)

3. **Right-click** on one of the selected files
   - Click "Send to" → "Compressed (zipped) folder"

4. **Rename** the ZIP file to: `ragard-extension-v0.1.1.zip`

5. **Move** it to the parent folder (`extension` folder)

That's it! See PACKAGING_GUIDE.md for more detailed instructions.
