'use client'

import { Narrative, TimeframeKey } from '@/types/narratives'

interface NarrativeHeatmapProps {
  narratives: Narrative[]
  timeframe: TimeframeKey
}

export default function NarrativeHeatmap({
  narratives,
  timeframe,
}: NarrativeHeatmapProps) {
  const getHeatBackgroundClass = (heatScore: number) => {
    if (heatScore < 30) {
      return 'bg-red-950/80'
    } else if (heatScore < 60) {
      return 'bg-amber-950/80'
    } else if (heatScore < 80) {
      return 'bg-emerald-950/80'
    } else {
      return 'bg-cyan-950/80'
    }
  }

  // Calculate grid span based on heat score (1-4 spans for size variation)
  const getGridSpan = (heatScore: number) => {
    if (heatScore < 30) {
      return 1 // Smallest tiles
    } else if (heatScore < 60) {
      return 2 // Medium tiles
    } else if (heatScore < 80) {
      return 3 // Large tiles
    } else {
      return 4 // Largest tiles
    }
  }

  return (
    <div className="mt-6 grid grid-cols-12 gap-0.5 auto-rows-[50px]">
      {narratives.map((narrative) => {
        const metrics = narrative.metrics[timeframe]
        const isPositive = metrics.avgMovePct >= 0
        const heatBgClass = getHeatBackgroundClass(metrics.heatScore)
        const gridSpan = getGridSpan(metrics.heatScore)

        return (
          <div
            key={narrative.id}
            className={`
              border border-slate-800/30 p-1.5
              flex flex-col justify-between overflow-hidden
              bg-slate-900 ${heatBgClass}
              transition-all hover:border-ragard-accent/50 hover:shadow-ragard-glow-sm cursor-pointer
              relative
            `}
            style={{
              gridColumn: `span ${gridSpan}`,
              gridRow: `span ${gridSpan}`,
            }}
          >
            {/* Top Row: Name + Heat Score */}
            <div className="flex items-start justify-between gap-1">
              <h4 className="text-[10px] font-semibold text-ragard-textPrimary leading-tight line-clamp-2 flex-1">
                {narrative.title}
              </h4>
              <span className="text-[9px] text-ragard-textSecondary whitespace-nowrap">
                {Math.round(metrics.heatScore)}
              </span>
            </div>

            {/* Middle/Bottom: Avg Move + Up/Down */}
            <div className="flex flex-col gap-0.5">
              <span
                className={`text-xs font-semibold ${
                  isPositive ? 'text-ragard-success' : 'text-ragard-danger'
                }`}
              >
                {isPositive ? '+' : ''}
                {metrics.avgMovePct.toFixed(1)}%
              </span>
              <span className="text-[9px] text-ragard-textMuted">
                {metrics.upCount}↑ {metrics.downCount}↓
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
