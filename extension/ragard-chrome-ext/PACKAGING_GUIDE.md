# Detailed Guide: Packaging the Extension for Chrome Web Store

This guide explains step-by-step how to create the ZIP file you need to submit to the Chrome Web Store.

## What is "Packaging"?

Packaging means putting all the extension files into a single ZIP file that Chrome Web Store can read. Think of it like putting all your files in a box before shipping it.

## Option 1: Using the Script (Easiest - Recommended)

### On Windows (PowerShell)

1. **Open PowerShell**
   - Press `Windows Key + X`
   - Click "Windows PowerShell" or "Terminal"
   - Or search for "PowerShell" in the Start menu

2. **Navigate to the extension folder**
   - Type this command and press Enter:
     ```powershell
     cd "C:\Users\safat\Desktop\Ragard\extension\ragard-chrome-ext"
     ```
   - (Adjust the path if your folder is in a different location)
   - You should see the prompt change to show you're in that folder

3. **Run the packaging script**
   - Type this command and press Enter:
     ```powershell
     .\package-for-store.ps1
     ```
   - The script will:
     - Read the version number from manifest.json
     - Create a ZIP file with all necessary files
     - Name it something like `ragard-extension-v0.1.1.zip`
     - Save it in the parent folder (one level up)

4. **Find your ZIP file**
   - The ZIP file will be created in: `C:\Users\safat\Desktop\Ragard\extension\`
   - You can see it in File Explorer
   - The file name will be: `ragard-extension-v0.1.1.zip` (the version number matches what's in manifest.json)

### On Mac/Linux (Terminal)

1. **Open Terminal**
   - On Mac: Press `Cmd + Space`, type "Terminal", press Enter
   - On Linux: Press `Ctrl + Alt + T` or search for "Terminal"

2. **Navigate to the extension folder**
   ```bash
   cd ~/Desktop/Ragard/extension/ragard-chrome-ext
   ```
   (Adjust the path to match where your folder is)

3. **Make the script executable** (first time only)
   ```bash
   chmod +x package-for-store.sh
   ```

4. **Run the packaging script**
   ```bash
   ./package-for-store.sh
   ```

5. **Find your ZIP file**
   - It will be in the parent folder: `~/Desktop/Ragard/extension/`
   - File name: `ragard-extension-v0.1.1.zip`

## Option 2: Manual Method (If Script Doesn't Work)

If the script doesn't work for any reason, you can create the ZIP file manually:

### On Windows

1. **Open File Explorer**
   - Press `Windows Key + E`
   - Navigate to: `C:\Users\safat\Desktop\Ragard\extension\ragard-chrome-ext`

2. **Select all the files you need**
   - Click on the first file (like `manifest.json`)
   - Hold `Ctrl` and click on each file/folder you need:
     - ✅ `manifest.json`
     - ✅ `background.js`
     - ✅ `config.js`
     - ✅ `contentScript.js`
     - ✅ `sidePanel.html`
     - ✅ `sidePanel.js`
     - ✅ `options.html`
     - ✅ `options.js`
     - ✅ `popup.html`
     - ✅ `popup.js`
     - ✅ `pageContext.js`
     - ✅ `authStatus.js`
     - ✅ `icons` folder (click once to select the whole folder)
     - ✅ `scripts` folder (if it exists)
   
   **DO NOT select:**
   - ❌ `README.md`
   - ❌ `CHROME_WEB_STORE_GUIDE.md`
   - ❌ `STORE_LISTING.md`
   - ❌ `PACKAGING_GUIDE.md`
   - ❌ `package-for-store.ps1`
   - ❌ `package-for-store.sh`
   - ❌ `package.json` or `package-lock.json` (if they exist)
   - ❌ `node_modules` folder (if it exists)
   - ❌ Any `.zip` files

3. **Create the ZIP file**
   - Right-click on one of the selected files
   - Hover over "Send to"
   - Click "Compressed (zipped) folder"
   - A ZIP file will be created
   - Rename it to: `ragard-extension-v0.1.1.zip`
   - (You can check the version in manifest.json - look for `"version": "0.1.1"`)

4. **Move the ZIP file**
   - Cut the ZIP file (`Ctrl + X`)
   - Go up one folder (click "Ragard" in the address bar, then "extension")
   - Paste it there (`Ctrl + V`)

### On Mac

1. **Open Finder**
   - Navigate to the extension folder: `~/Desktop/Ragard/extension/ragard-chrome-ext`

2. **Select files** (same list as Windows above)

3. **Create ZIP**
   - Right-click on the selected files
   - Click "Compress X Items" (X = number of files)
   - A file called "Archive.zip" will be created
   - Rename it to: `ragard-extension-v0.1.1.zip`

4. **Move the ZIP file**
   - Drag it to the parent folder (extension folder)

## What Should Be Inside the ZIP?

When you open the ZIP file (double-click it), you should see:

```
ragard-extension-v0.1.1.zip
├── manifest.json          ← Must have!
├── background.js
├── config.js
├── contentScript.js
├── sidePanel.html
├── sidePanel.js
├── options.html
├── options.js
├── popup.html
├── popup.js
├── pageContext.js
├── authStatus.js
├── icons/
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── scripts/ (if it exists)
```

**Important:** The files should be directly in the ZIP, not in a subfolder. When you open the ZIP, you should see `manifest.json` right away, not inside another folder.

## How to Check Your ZIP File

1. **Double-click the ZIP file** to open it
2. **Check the structure:**
   - You should see `manifest.json` immediately (not in a subfolder)
   - All the `.js` and `.html` files should be visible
   - The `icons` folder should be there with PNG files inside
3. **Try to open manifest.json:**
   - If you can open it directly, the structure is correct ✅
   - If it's inside another folder, the structure is wrong ❌

## Common Mistakes

### ❌ Mistake 1: ZIP contains a folder
**Wrong:**
```
ragard-extension-v0.1.1.zip
└── ragard-chrome-ext/    ← BAD! This extra folder
    ├── manifest.json
    └── ...
```

**Right:**
```
ragard-extension-v0.1.1.zip
├── manifest.json         ← Good! Files directly in ZIP
└── ...
```

**How to fix:** Open the ZIP, select everything inside the inner folder, extract it, then create a new ZIP with those files.

### ❌ Mistake 2: Including unnecessary files
**Wrong:** Including README.md, guides, scripts, etc.
**Right:** Only include the files listed in the "What Should Be Inside" section above.

### ❌ Mistake 3: Wrong file name
**Wrong:** `ragard-extension.zip`, `extension.zip`, `my-extension-v1.zip`
**Right:** `ragard-extension-v0.1.1.zip` (version matches manifest.json)

## Still Having Trouble?

### If the script gives an error:

1. **"Cannot find path" error:**
   - Make sure you're in the correct folder
   - Type `pwd` (Mac/Linux) or `cd` (Windows) to see where you are
   - Make sure the script file exists: type `ls package-for-store.ps1` (or `dir` on Windows)

2. **"Execution policy" error (Windows):**
   - Run PowerShell as Administrator
   - Or run this first: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
   - Then try the script again

3. **Script not found:**
   - Make sure you're in the `ragard-chrome-ext` folder
   - Type `ls` (Mac/Linux) or `dir` (Windows) to see files
   - Make sure `package-for-store.ps1` or `package-for-store.sh` is there

### If manual method doesn't work:

- Try selecting files one at a time if selecting multiple doesn't work
- Make sure you're selecting the files, not copying them somewhere else
- Check that your ZIP file opener (like WinRAR or 7-Zip) isn't interfering

## Next Steps

Once you have your ZIP file:

1. ✅ ZIP file created and named correctly
2. ✅ ZIP contains files directly (not in a subfolder)
3. ✅ Only necessary files included
4. ✅ Ready to upload to Chrome Web Store!

See `CHROME_WEB_STORE_GUIDE.md` for instructions on uploading to the store.

