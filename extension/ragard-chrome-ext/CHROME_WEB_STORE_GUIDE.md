# Publishing Ragard Extension to Chrome Web Store

This guide will help you publish the Ragard Chrome extension to the Chrome Web Store so anyone can install and use it.

## Prerequisites

1. **Chrome Web Store Developer Account**
   - Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
   - Pay the **one-time $5 registration fee**
   - Complete the developer account setup
   - **Important**: You'll be asked if you're a "Trader" or "Non-Trader"
     - For Ragard (production website/business), choose **"Trader"**
     - See [TRADER_VS_NON_TRADER.md](./TRADER_VS_NON_TRADER.md) for detailed explanation

2. **Privacy Policy**
   - ✅ You already have one at: `https://ragardai.com/privacy`
   - Make sure it's accessible and up-to-date

3. **Extension Assets**
   - ✅ Icons are in `icons/` folder (16x16, 32x32, 48x48, 128x128)
   - You'll need promotional images (see below)

## Step 1: Prepare the Extension Package

1. **Create a ZIP file of the extension:**
   ```bash
   # From the extension/ragard-chrome-ext/ directory
   # On Windows PowerShell:
   Compress-Archive -Path * -DestinationPath ../ragard-extension-v0.1.1.zip -Force
   
   # On Mac/Linux:
   zip -r ../ragard-extension-v0.1.1.zip . -x "*.git*" "node_modules/*" "*.md" "*.json" "package-lock.json"
   ```

2. **What to include in the ZIP:**
   - ✅ All `.js` files (background.js, config.js, contentScript.js, etc.)
   - ✅ All `.html` files (sidePanel.html, options.html, popup.html)
   - ✅ `manifest.json`
   - ✅ `icons/` folder (all icon files)
   - ✅ Any other assets needed

3. **What NOT to include:**
   - `node_modules/` (if any)
   - `.git/` folder
   - `README.md`, `CHROME_WEB_STORE_GUIDE.md` (optional, but not needed)
   - Source files if you have compiled versions

## Step 2: Update Manifest for Store Submission

The manifest is already mostly ready, but you may want to add:

```json
{
  "homepage_url": "https://ragardai.com",
  "update_url": "https://clients2.google.com/service/update2/crx"
}
```

However, `update_url` is automatically set by Chrome Web Store, so you don't need to add it.

## Step 3: Prepare Store Listing Assets

You'll need to create:

1. **Screenshots** (required):
   - At least 1 screenshot (1280x800 or 640x400)
   - Up to 5 screenshots showing the extension in action
   - Show: side panel, analyzing Reddit posts, results display

2. **Promotional Images** (optional but recommended):
   - Small promotional tile: 440x280
   - Large promotional tile: 920x680
   - Marquee promotional tile: 1400x560

3. **Store Listing Details:**
   - **Name**: "Ragard – Reddit Analyzer" (or shorter: "Ragard")
   - **Short description**: 132 characters max
   - **Detailed description**: Up to 16,000 characters
   - **Category**: Productivity or Shopping
   - **Language**: English

## Step 4: Write Store Listing Content

### Short Description (132 characters max)
```
Analyze Reddit posts with AI-powered sentiment analysis and stock ticker detection. Get insights on Reddit discussions.
```

### Detailed Description (up to 16,000 characters)
```
Ragard Chrome Extension - AI-Powered Reddit Analyzer

Analyze Reddit posts with advanced AI to extract stock tickers, sentiment analysis, and actionable insights from Reddit discussions.

KEY FEATURES:
• Automatic Stock Ticker Detection - Identifies stock symbols mentioned in Reddit posts
• AI-Powered Sentiment Analysis - Understand the sentiment and context of discussions
• Side Panel Interface - Convenient side panel for quick analysis without leaving the page
• Reddit Integration - Works seamlessly on Reddit.com posts and comments
• Real-time Analysis - Get instant insights on any Reddit post

HOW IT WORKS:
1. Navigate to any Reddit post
2. Click the Ragard extension icon
3. View AI-powered analysis in the side panel
4. Get insights on stock tickers, sentiment, and more

PERFECT FOR:
• Stock traders and investors analyzing Reddit discussions
• Researchers studying market sentiment
• Anyone wanting to extract insights from Reddit posts

PRIVACY:
Your data is secure. We only analyze the Reddit posts you explicitly request analysis for. See our privacy policy at ragardai.com/privacy

Visit ragardai.com for more features and analytics.
```

### Category
- Primary: **Productivity**
- Secondary: Shopping (optional)

## Step 5: Submit to Chrome Web Store

1. **Go to Developer Dashboard**
   - Visit: https://chrome.google.com/webstore/devconsole
   - Click "New Item"

2. **Upload the ZIP file**
   - Click "Upload" and select your `ragard-extension-v0.1.1.zip` file
   - Wait for upload and processing

3. **Fill in Store Listing**
   - **Name**: Ragard – Reddit Analyzer
   - **Summary**: (Use short description above)
   - **Description**: (Use detailed description above)
   - **Category**: Productivity
   - **Language**: English
   - **Privacy practices**: 
     - Single purpose: No
     - Host permissions: Yes (explain: "Needed to analyze Reddit posts")
     - User data: Yes (link to https://ragardai.com/privacy)

4. **Upload Graphics**
   - Upload screenshots (at least 1, up to 5)
   - Upload promotional images (optional)

5. **Additional Information**
   - **Privacy policy URL**: `https://ragardai.com/privacy`
   - **Support site** (optional): `https://ragardai.com`
   - **Homepage URL**: `https://ragardai.com`

6. **Distribution**
   - Choose: "Public" (for everyone) or "Unlisted" (only people with link)
   - For public release, choose "Public"

7. **Submit for Review**
   - Click "Submit for Review"
   - Review process typically takes 1-3 business days
   - You'll receive email notifications about the status

## Step 6: After Approval

Once approved:

1. **Share the Store Link**
   - The extension will be available at: `https://chrome.google.com/webstore/detail/[extension-id]`
   - Share this link on your website

2. **Add Install Button to Website**
   - You can add a "Install Extension" button on ragardai.com
   - Link it to the Chrome Web Store listing

3. **Update Extension**
   - To update: Upload new ZIP, increment version in manifest.json
   - Updates go through review but are usually faster

## Important Notes

### Permissions Explanation
When submitting, you'll need to explain why you need these permissions:

- **activeTab**: To analyze the current Reddit page
- **scripting**: To inject analysis scripts into Reddit pages
- **storage**: To save user preferences (API URLs, settings)
- **tabs**: To detect which tab is active and determine environment
- **sidePanel**: To display analysis results in the side panel
- **optional_host_permissions** (http/https): To work on any website (needed for Reddit.com)

### Privacy Considerations
- Make sure your privacy policy at ragardai.com/privacy mentions the extension
- Explain what data the extension collects (if any)
- The extension stores user preferences locally (auto-detect settings, manual URLs)

### Version Updates
When you update the extension:
1. Increment version in `manifest.json` (e.g., 0.1.1 → 0.1.2)
2. Create new ZIP file
3. Upload to Chrome Web Store
4. Changes go through review (usually faster than initial submission)

## Troubleshooting

### Common Rejection Reasons
- **Missing privacy policy**: Make sure it's accessible
- **Vague permission explanations**: Be specific about why each permission is needed
- **Poor store listing**: Add good screenshots and description
- **Policy violations**: Make sure extension follows Chrome Web Store policies

### Getting Help
- Chrome Web Store Developer Support: https://support.google.com/chrome_webstore
- Chrome Extension Documentation: https://developer.chrome.com/docs/extensions/

## Cost

- **One-time registration fee**: $5 USD
- **Listing cost**: Free (unlimited submissions)
- **Updates**: Free

Good luck with your submission! 🚀

