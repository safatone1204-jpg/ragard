'use client'

interface RagardScoreGaugeProps {
  score: number | null
  size?: 'sm' | 'lg'
}

export default function RagardScoreGauge({
  score,
  size = 'sm',
}: RagardScoreGaugeProps) {
  const dimensions = size === 'lg' ? { width: 192, height: 192 } : { width: 48, height: 48 }
  const strokeWidth = size === 'lg' ? 12 : 4
  const radius = size === 'lg' ? 80 : 20
  const circumference = 2 * Math.PI * radius
  const validScore = score !== null && score !== undefined ? score : 0
  const offset = circumference - (validScore / 100) * circumference

  // Smooth gradient color interpolation - INVERTED: green for low, red for high
  const getColor = (score: number | null): string => {
    if (score === null || score === undefined) return '#9CA3AF' // Gray for missing
    
    // Clamp score to 0-100
    const clampedScore = Math.max(0, Math.min(100, score))
    
    // Interpolate from green (0) -> yellow (50) -> red (100)
    // Using HSL for smoother color transitions
    let hue: number
    let saturation: number
    let lightness: number
    
    if (clampedScore <= 50) {
      // Green (120deg) to Yellow (60deg)
      const t = clampedScore / 50
      hue = 120 - (t * 60) // 120 -> 60
      saturation = 70 + (t * 10) // 70% -> 80%
      lightness = 50 - (t * 5) // 50% -> 45%
    } else {
      // Yellow (60deg) to Red (0deg)
      const t = (clampedScore - 50) / 50
      hue = 60 - (t * 60) // 60 -> 0
      saturation = 80 + (t * 15) // 80% -> 95%
      lightness = 45 - (t * 5) // 45% -> 40%
    }
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`
  }

  const color = getColor(score)

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        width={dimensions.width}
        height={dimensions.height}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={dimensions.width / 2}
          cy={dimensions.height / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-ragard-surfaceAlt"
        />
        {/* Score arc with smooth gradient color */}
        <circle
          cx={dimensions.width / 2}
          cy={dimensions.height / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      {/* Show number inside circle for both sizes */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className={`font-bold font-display transition-all duration-500 ${
            size === 'lg' ? 'text-4xl' : 'text-xs'
          }`}
          style={{ color }}
        >
          {validScore}
        </span>
      </div>
    </div>
  )
}

