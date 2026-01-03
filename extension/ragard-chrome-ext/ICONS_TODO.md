# Extension Icons

✅ Icons are now implemented!

## Icon Files

Icons are located in `icons/` directory:
- `ragard-icon.svg` - Source SVG file
- `icon16.png` - 16x16 pixels (toolbar icon)
- `icon32.png` - 32x32 pixels
- `icon48.png` - 48x48 pixels (extension management page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Regenerating Icons

To regenerate PNG icons from the SVG source:

```bash
cd extension/ragard-chrome-ext
npm run generate:icons
```

This will regenerate all PNG sizes from `icons/ragard-icon.svg`.

