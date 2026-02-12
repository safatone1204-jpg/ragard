#!/bin/bash
# Bash script to package the Ragard Chrome extension for Chrome Web Store submission
# Run this from the extension/ragard-chrome-ext/ directory

VERSION=$(grep -o '"version": "[^"]*"' manifest.json | cut -d'"' -f4)
ZIP_NAME="../ragard-extension-v${VERSION}.zip"

echo "Packaging Ragard Chrome Extension v${VERSION} for Chrome Web Store..."

# Remove old ZIP if exists
if [ -f "$ZIP_NAME" ]; then
    rm "$ZIP_NAME"
    echo "Removed existing ZIP file"
fi

# Create ZIP (exclude unnecessary files)
zip -r "$ZIP_NAME" . \
    -x "*.git*" \
    -x "node_modules/*" \
    -x "*.md" \
    -x "package*.json" \
    -x "*.ps1" \
    -x "*.sh" \
    -x "*.zip"

echo ""
echo "✓ Extension packaged successfully!"
echo "  Location: $ZIP_NAME"
echo ""
echo "Next steps:"
echo "1. Go to https://chrome.google.com/webstore/devconsole"
echo "2. Click 'New Item' and upload: $ZIP_NAME"
echo "3. Use content from STORE_LISTING.md for the store listing"
echo "4. See CHROME_WEB_STORE_GUIDE.md for complete instructions"

