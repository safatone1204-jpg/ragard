#!/usr/bin/env node
/**
 * Convert a custom PNG icon to all required sizes
 * Usage: node scripts/convert-custom-icon.js path/to/your-icon.png
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const SIZES = [16, 32, 48, 128];
const ICONS_DIR = path.join(__dirname, '..', 'icons');

// Get input file from command line
const inputFile = process.argv[2];

if (!inputFile) {
  console.error('Error: Please provide the path to your PNG file');
  console.error('Usage: node scripts/convert-custom-icon.js path/to/your-icon.png');
  process.exit(1);
}

if (!fs.existsSync(inputFile)) {
  console.error(`Error: File not found: ${inputFile}`);
  process.exit(1);
}

// Ensure icons directory exists
if (!fs.existsSync(ICONS_DIR)) {
  fs.mkdirSync(ICONS_DIR, { recursive: true });
}

async function convertIcon() {
  console.log(`Converting ${inputFile} to required icon sizes...\n`);

  try {
    // Read input image
    const inputBuffer = fs.readFileSync(inputFile);
    
    // Generate each size
    for (const size of SIZES) {
      const outputPath = path.join(ICONS_DIR, `icon${size}.png`);
      
      await sharp(inputBuffer)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 15, g: 17, b: 21, alpha: 1 } // #0F1115 fallback
        })
        .png()
        .toFile(outputPath);
      
      const stats = fs.statSync(outputPath);
      const fileSizeKB = (stats.size / 1024).toFixed(2);
      console.log(`✓ Generated icon${size}.png (${size}x${size}) - ${fileSizeKB} KB`);
    }
    
    console.log('\n✓ All icons generated successfully!');
    console.log('\nNext steps:');
    console.log('1. Go to chrome://extensions/');
    console.log('2. Remove the Ragard extension');
    console.log('3. Click "Load unpacked" and select extension/ragard-chrome-ext folder');
    console.log('4. Your new icon should appear!');
  } catch (error) {
    console.error('Error converting icon:', error.message);
    process.exit(1);
  }
}

convertIcon();

