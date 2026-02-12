# PowerShell script to package the Ragard Chrome extension for Chrome Web Store submission
# Run this from the extension/ragard-chrome-ext/ directory

$version = (Get-Content manifest.json | ConvertFrom-Json).version
$zipName = "../ragard-extension-v$version.zip"

Write-Host "Packaging Ragard Chrome Extension v$version for Chrome Web Store..." -ForegroundColor Green

# Remove old ZIP if exists
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
    Write-Host "Removed existing ZIP file" -ForegroundColor Yellow
}

# Files and folders to include
$itemsToInclude = @(
    "manifest.json",
    "background.js",
    "config.js",
    "contentScript.js",
    "sidePanel.html",
    "sidePanel.js",
    "options.html",
    "options.js",
    "popup.html",
    "popup.js",
    "pageContext.js",
    "authStatus.js",
    "icons",
    "scripts"
)

# Create ZIP
$itemsToInclude | ForEach-Object {
    if (Test-Path $_) {
        Write-Host "Adding: $_" -ForegroundColor Gray
    } else {
        Write-Host "Warning: $_ not found" -ForegroundColor Yellow
    }
}

Compress-Archive -Path $itemsToInclude -DestinationPath $zipName -Force

Write-Host ""
Write-Host "Extension packaged successfully!" -ForegroundColor Green
Write-Host "  Location: $zipName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to https://chrome.google.com/webstore/devconsole" -ForegroundColor White
Write-Host "2. Click New Item and upload the ZIP file" -ForegroundColor White
Write-Host "3. Use content from STORE_LISTING.md for the store listing" -ForegroundColor White
Write-Host "4. See CHROME_WEB_STORE_GUIDE.md for complete instructions" -ForegroundColor White

