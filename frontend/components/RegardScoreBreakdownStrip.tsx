'use client'

import type { RagardScoreBreakdown } from '@/lib/api'

interface RegardScoreBreakdownStripProps {
  score?: number | null
  breakdown?: RagardScoreBreakdown | null
}

export default function RegardScoreBreakdownStrip({
  score,
  breakdown,
}: RegardScoreBreakdownStripProps) {
  // If no breakdown, don't render
  if (!breakdown) {
    return null
  }

  // Extract component values
  const hype = breakdown.hype ?? 0
  const volatility = breakdown.volatility ?? 0
  const liquidity = breakdown.liquidity ?? 0
  const risk = breakdown.risk ?? 0

  // Filter out components with near-zero absolute values
  const components = [
    { name: 'Hype', value: hype, color: 'bg-fuchsia-500' },
    { name: 'Volatility', value: volatility, color: 'bg-ragard-accent' },
    { name: 'Liquidity', value: liquidity, color: 'bg-amber-500' },
    { name: 'Risk', value: risk, color: risk >= 0 ? 'bg-green-500' : 'bg-red-500' },
  ].filter((comp) => Math.abs(comp.value) >= 0.1)

  if (components.length === 0) {
    return null
  }

  // Compute total absolute contribution for proportional widths
  const totalAbs = components.reduce((sum, comp) => sum + Math.abs(comp.value), 0)

  if (totalAbs === 0) {
    return null
  }

  return (
    <div className="space-y-2 w-full">

      {/* Segmented Bar */}
      <div className="flex h-2 rounded-full overflow-hidden bg-ragard-surfaceAlt">
        {components.map((comp) => {
          const width = (Math.abs(comp.value) / totalAbs) * 100
          return (
            <div
              key={comp.name}
              className={`${comp.color} transition-all`}
              style={{ width: `${width}%` }}
              title={`${comp.name}: ${comp.value >= 0 ? '+' : ''}${comp.value.toFixed(1)}`}
            />
          )
        })}
      </div>

      {/* Component Labels with Color Squares */}
      <div className="flex flex-wrap gap-2 justify-center text-xs">
        {components.map((comp) => {
          const isPositive = comp.value >= 0
          const textColor = comp.name === 'Risk'
            ? isPositive
              ? 'text-green-500'
              : 'text-ragard-danger'
            : isPositive
              ? 'text-ragard-success'
              : 'text-ragard-danger'
          
          return (
            <span
              key={comp.name}
              className={`${textColor} font-medium flex items-center gap-1.5`}
            >
              <span
                className={`w-3 h-3 rounded ${comp.color} border border-slate-800/50 flex-shrink-0`}
                title={comp.name}
              />
              <span className="whitespace-nowrap">
                {comp.name} {comp.value >= 0 ? '+' : ''}
                {comp.value.toFixed(1)}
              </span>
            </span>
          )
        })}
      </div>
    </div>
  )
}

