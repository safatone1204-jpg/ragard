#!/usr/bin/env node
/**
 * Generate PNG icon sizes from SVG source
 * Outputs: icon16.png, icon32.png, icon48.png, icon128.png
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const SIZES = [16, 32, 48, 128];
const SVG_PATH = path.join(__dirname, '..', 'icons', 'ragard-icon.svg');
const ICONS_DIR = path.join(__dirname, '..', 'icons');

// Ensure icons directory exists
if (!fs.existsSync(ICONS_DIR)) {
  fs.mkdirSync(ICONS_DIR, { recursive: true });
}

// Check if SVG exists
if (!fs.existsSync(SVG_PATH)) {
  console.error(`Error: SVG source not found at ${SVG_PATH}`);
  process.exit(1);
}

async function generateIcons() {
  console.log('Generating icon PNGs from SVG...');
  console.log(`Source: ${SVG_PATH}`);
  console.log(`Output directory: ${ICONS_DIR}\n`);

  try {
    // Read SVG
    const svgBuffer = fs.readFileSync(SVG_PATH);
    
    const generatedFiles = [];
    
    // Generate each size
    for (const size of SIZES) {
      const outputPath = path.join(ICONS_DIR, `icon${size}.png`);
      
      await sharp(svgBuffer)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 15, g: 17, b: 21, alpha: 1 } // #0F1115
        })
        .png()
        .toFile(outputPath);
      
      // Get file stats
      const stats = fs.statSync(outputPath);
      const fileSizeKB = (stats.size / 1024).toFixed(2);
      
      console.log(`✓ Generated icon${size}.png (${size}x${size}) - ${fileSizeKB} KB`);
      generatedFiles.push({ size, path: outputPath, sizeKB: fileSizeKB });
    }
    
    // Verification: Check all files exist
    console.log('\n--- Verification ---');
    let allExist = true;
    for (const file of generatedFiles) {
      if (fs.existsSync(file.path)) {
        console.log(`✓ icon${file.size}.png exists (${file.sizeKB} KB)`);
      } else {
        console.error(`✗ icon${file.size}.png MISSING!`);
        allExist = false;
      }
    }
    
    if (allExist) {
      console.log('\n✓ All icons generated and verified successfully!');
    } else {
      console.error('\n✗ Verification failed - some files are missing!');
      process.exit(1);
    }
  } catch (error) {
    console.error('Error generating icons:', error.message);
    process.exit(1);
  }
}

generateIcons();

