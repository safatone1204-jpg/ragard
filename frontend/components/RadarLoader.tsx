'use client'

import { useState, useEffect } from 'react'

interface RadarLoaderProps {
  message: string
  size?: number
}

// Meme ticker symbols to display on radar
const MEME_TICKERS = ['GME', 'AMC', 'BBBY', 'BYND', 'PLTR', 'TSLA', 'NVDA', 'MARA']

// Generate random but stable positions for tickers with guaranteed no-overlap
const generateTickerPositions = (center: number, radius: number) => {
  const positions: Array<{ ticker: string; baseAngle: number; radius: number }> = []
  // Very large minimum distance to ensure no text overlap (tickers are 3-5 chars, ~30-40px wide)
  // Account for text width + padding on both sides
  const minDistance = 75 // Minimum distance between ticker centers in pixels
  const minRadius = radius * 0.52 // Don't place too close to center
  const maxRadius = radius * 0.78 // Don't place too close to edge
  
  // Helper function to calculate distance between two positions
  const getDistance = (
    angle1: number, radius1: number,
    angle2: number, radius2: number
  ): number => {
    const x1 = center + Math.cos((angle1 * Math.PI) / 180) * radius * radius1
    const y1 = center + Math.sin((angle1 * Math.PI) / 180) * radius * radius1
    const x2 = center + Math.cos((angle2 * Math.PI) / 180) * radius * radius2
    const y2 = center + Math.sin((angle2 * Math.PI) / 180) * radius * radius2
    return Math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
  }
  
  // Helper function to check if a position collides with existing positions
  const checkCollision = (angle: number, tickerRadius: number, existingPositions: typeof positions): boolean => {
    return existingPositions.every((pos) => {
      const distance = getDistance(angle, tickerRadius, pos.baseAngle, pos.radius)
      return distance >= minDistance
    })
  }
  
  // Start with evenly distributed angles
  const baseAngleStep = 360 / MEME_TICKERS.length
  const baseRadius = 0.65 // Base radius for all tickers
  
  for (let i = 0; i < MEME_TICKERS.length; i++) {
    const ticker = MEME_TICKERS[i]
    const seed = ticker.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    
    let validPosition = false
    let baseAngle = 0
    let tickerRadius = 0
    
    // Start with evenly spaced angle
    const initialAngle = i * baseAngleStep
    
    // Try different radius layers and small angle adjustments
    for (let radiusOffset = -0.15; radiusOffset <= 0.15 && !validPosition; radiusOffset += 0.05) {
      tickerRadius = baseRadius + radiusOffset
      tickerRadius = Math.max(minRadius / radius, Math.min(maxRadius / radius, tickerRadius))
      
      // Try small angle variations
      for (let angleOffset = -25; angleOffset <= 25 && !validPosition; angleOffset += 5) {
        baseAngle = (initialAngle + angleOffset) % 360
        if (baseAngle < 0) baseAngle += 360
        
        // Check collision
        if (checkCollision(baseAngle, tickerRadius, positions)) {
          validPosition = true
          break
        }
      }
    }
    
    // If still no valid position, use evenly spaced with guaranteed spacing
    if (!validPosition) {
      baseAngle = initialAngle
      // Try different radii to find one that doesn't collide
      for (let r = 0.55; r <= 0.75; r += 0.05) {
        tickerRadius = r
        if (checkCollision(baseAngle, tickerRadius, positions)) {
          validPosition = true
          break
        }
      }
      
      // Last resort: use the base position even if it might be close
      // (but we've increased minDistance so this should be rare)
      if (!validPosition) {
        tickerRadius = baseRadius
      }
    }
    
    positions.push({
      ticker,
      baseAngle,
      radius: tickerRadius,
    })
  }
  
  return positions
}

export default function RadarLoader({ message, size = 140 }: RadarLoaderProps) {
  const center = size / 2
  const radius = size / 2 - 10
  const [sweepAngle, setSweepAngle] = useState(0)
  const [tickerConfigs] = useState(() => generateTickerPositions(center, radius))
  
  // Animate sweep line - continuous rotation (slower)
  useEffect(() => {
    let animationFrame: number
    let startTime = Date.now()
    
    const animate = () => {
      const elapsed = Date.now() - startTime
      // 6 seconds per full rotation (slower)
      const newAngle = (elapsed / 6000) * 360 % 360
      setSweepAngle(newAngle)
      animationFrame = requestAnimationFrame(animate)
    }
    
    animationFrame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationFrame)
  }, [])
  
  // Calculate positions for tickers around the radar
  const tickerPositions = tickerConfigs.map(({ ticker, baseAngle, radius: tickerRadius }) => {
    const tickerRadiusPx = radius * tickerRadius
    const x = center + Math.cos((baseAngle * Math.PI) / 180) * tickerRadiusPx
    const y = center + Math.sin((baseAngle * Math.PI) / 180) * tickerRadiusPx
    
    // Calculate angle difference from sweep line (for fade effect)
    const sweepAngleRad = (sweepAngle * Math.PI) / 180
    const tickerAngleRad = (baseAngle * Math.PI) / 180
    
    // Calculate shortest angle difference (normalized to 0-180 degrees)
    let angleDiff = Math.abs(sweepAngleRad - tickerAngleRad)
    if (angleDiff > Math.PI) {
      angleDiff = 2 * Math.PI - angleDiff
    }
    
    // Convert to degrees
    const angleDiffDeg = (angleDiff * 180) / Math.PI
    
    // Tickers are invisible until swept over, then fade in
    // Narrower window for more dramatic effect
    const fadeWindow = 30 // degrees
    const opacity = angleDiffDeg < fadeWindow
      ? Math.max(0, 1 - (angleDiffDeg / fadeWindow)) // Fade from 1.0 to 0.0
      : 0 // Completely invisible when not in sweep
    
    return {
      ticker,
      x,
      y,
      opacity,
      angle: baseAngle,
    }
  })
  
  // Calculate sweep line endpoint
  const sweepX = center + Math.cos((sweepAngle * Math.PI) / 180) * radius
  const sweepY = center + Math.sin((sweepAngle * Math.PI) / 180) * radius
  
  // Calculate sweep wedge endpoints - only behind the sweep line
  const sweepSpread = 30 // degrees - how far back the fade extends
  const sweepAngleBack = sweepAngle - sweepSpread // Start of faded area (behind)
  const wedgeX1 = center + Math.cos((sweepAngleBack * Math.PI) / 180) * radius
  const wedgeY1 = center + Math.sin((sweepAngleBack * Math.PI) / 180) * radius
  const wedgeX2 = sweepX // End at current sweep position
  const wedgeY2 = sweepY
  
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-6">
      {/* Radar SVG */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="absolute inset-0"
          viewBox={`0 0 ${size} ${size}`}
        >
          {/* Outer circle - radar screen border */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgba(34, 211, 238, 0.3)"
            strokeWidth="2"
            className="drop-shadow-[0_0_4px_rgba(34,211,238,0.3)]"
          />
          
          {/* Inner rings - radar range rings */}
          <circle
            cx={center}
            cy={center}
            r={radius * 0.75}
            fill="none"
            stroke="rgba(34, 211, 238, 0.2)"
            strokeWidth="1"
          />
          <circle
            cx={center}
            cy={center}
            r={radius * 0.5}
            fill="none"
            stroke="rgba(34, 211, 238, 0.15)"
            strokeWidth="1"
          />
          <circle
            cx={center}
            cy={center}
            r={radius * 0.25}
            fill="none"
            stroke="rgba(34, 211, 238, 0.1)"
            strokeWidth="1"
          />
          
          {/* Crosshairs - center lines */}
          <line
            x1={center}
            y1={0}
            x2={center}
            y2={size}
            stroke="rgba(34, 211, 238, 0.2)"
            strokeWidth="1"
          />
          <line
            x1={0}
            y1={center}
            x2={size}
            y2={center}
            stroke="rgba(34, 211, 238, 0.2)"
            strokeWidth="1"
          />
          
          {/* Sweep area - faded wedge behind sweep line */}
          <defs>
            <linearGradient id="sweepGradient" x1={`${(wedgeX2 / size) * 100}%`} y1={`${(wedgeY2 / size) * 100}%`} x2={`${(wedgeX1 / size) * 100}%`} y2={`${(wedgeY1 / size) * 100}%`}>
              <stop offset="0%" stopColor="rgba(34, 211, 238, 0.25)" stopOpacity="1" />
              <stop offset="100%" stopColor="rgba(34, 211, 238, 0)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d={`M ${center} ${center} L ${wedgeX1} ${wedgeY1} A ${radius} ${radius} 0 ${sweepSpread > 180 ? 1 : 0} 1 ${wedgeX2} ${wedgeY2} Z`}
            fill="url(#sweepGradient)"
            opacity="0.8"
          />
          
          {/* Sweep line - rotating radar sweep */}
          <line
            x1={center}
            y1={center}
            x2={sweepX}
            y2={sweepY}
            stroke="rgba(34, 211, 238, 0.8)"
            strokeWidth="2"
            strokeLinecap="round"
            className="drop-shadow-[0_0_4px_rgba(34,211,238,0.5)]"
            style={{
              transition: 'none',
            }}
          />
          
          {/* Ticker symbols - positioned around the radar */}
          {tickerPositions.map(({ ticker, x, y, opacity, angle }) => (
            <g key={ticker} style={{ opacity: opacity > 0 ? 1 : 0 }}>
              {/* Ticker text */}
              <text
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#22D3EE"
                fontSize="10"
                fontWeight="bold"
                className="font-mono"
                style={{
                  opacity,
                  transition: 'opacity 0.15s ease-out',
                  filter: opacity > 0.5 ? 'drop-shadow(0 0 4px rgba(34,211,238,0.8))' : 'none',
                }}
              >
                {ticker}
              </text>
            </g>
          ))}
          
          {/* Center dot - radar origin */}
          <circle
            cx={center}
            cy={center}
            r="3"
            fill="#22D3EE"
            className="drop-shadow-[0_0_4px_rgba(34,211,238,0.8)]"
          />
        </svg>
      </div>
      
      {/* Message */}
      <p className="text-ragard-textSecondary text-sm font-medium text-center max-w-md">
        {message}
      </p>
    </div>
  )
}
