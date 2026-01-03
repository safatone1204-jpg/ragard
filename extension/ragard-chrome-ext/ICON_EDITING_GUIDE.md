# How to Manually Edit the Ragard Icon

## Quick Steps

1. **Edit the SVG file**: `extension/ragard-chrome-ext/icons/ragard-icon.svg`
2. **Regenerate PNGs**: Run `npm run generate:icons` from the extension folder
3. **Reload extension in Chrome**: Remove and re-add the extension

## SVG File Structure

The icon is built from these parts (in order, bottom to top):

### 1. Background
- **Gradient**: Lines 4-8 - Controls the dark background gradient
- **Radial highlight**: Lines 10-15 - The subtle glow from top-left
- **Rounded square**: Lines 28-30 - The main background shape

### 2. Candlesticks (Background)
- **Lines 36-48**: Three candlestick bars behind the R
- **Opacity**: Currently `0.15` - lower = more subtle
- **Position**: `translate(512, 512)` centers them, adjust x/y values to move

### 3. The "R" Letter
- **Left vertical stem**: Line 52 - Thick vertical bar on left
- **Top horizontal bar**: Line 55 - Top part of R
- **Upper loop**: Lines 58-60 - The rounded top-right part
- **Middle bar**: Line 63 - Horizontal bar in middle
- **Diagonal leg**: Line 66 - Bottom-right diagonal part
- **Bottom leg**: Line 69 - Horizontal bottom part

### 4. Accents
- **Cyan dot**: Line 72 - The blue dot inside R's counter space
- **Cyan line**: Lines 75-77 - Thin line at bottom-right corner

## Common Edits

### Make R Thicker/Bolder
- Increase `width` values in the R rectangles (lines 52, 55, 63, 66, 69)
- Example: Change `width="140"` to `width="160"`

### Change Colors
- **Background**: Change `#0F1115` and `#1A2030` in lines 5-6
- **R color**: Change `#F5F7FA` to any color (lines 52, 55, etc.)
- **Cyan accent**: Change `#4CC9F0` to any color (lines 72, 75)

### Move Elements
- **R position**: Adjust `translate(512, 512)` on line 50
- **Cyan dot**: Change `cx` and `cy` values on line 72
- **Candlesticks**: Adjust x/y values in the `<rect>` tags (lines 39-47)

### Make Candlesticks More Visible
- Increase `opacity="0.15"` to `opacity="0.3"` on line 37

### Remove Elements
- Comment out or delete the `<g>` blocks you don't want
- Example: Delete lines 36-48 to remove candlesticks

## After Editing

1. Save the SVG file
2. Open terminal in `extension/ragard-chrome-ext/`
3. Run: `npm run generate:icons`
4. Check `icons/preview.html` in browser to see changes
5. Reload extension in Chrome

## Regenerate Command

```powershell
cd extension\ragard-chrome-ext
npm run generate:icons
```

