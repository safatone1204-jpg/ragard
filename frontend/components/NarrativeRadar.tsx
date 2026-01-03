'use client'

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { NarrativeMetrics } from '@/types/narratives'

interface NarrativeRadarProps {
  metricsForTimeframe: NarrativeMetrics
}

export default function NarrativeRadar({ metricsForTimeframe }: NarrativeRadarProps) {
  // Normalize values to 0-100 for radar chart
  const heat = metricsForTimeframe.heatScore // Already 0-100

  // Momentum: map avgMovePct to 0-100
  // Example: clamp(50 + avgMovePct * 5, 0, 100)
  const momentum = Math.max(0, Math.min(100, 50 + metricsForTimeframe.avgMovePct * 5))

  // Breadth: percentage of "up" tickers
  const totalTickers = metricsForTimeframe.upCount + metricsForTimeframe.downCount
  const breadth = totalTickers > 0 
    ? (metricsForTimeframe.upCount / totalTickers) * 100 
    : 50 // Default to 50 if no tickers

  // Intensity: based on absolute avg move
  // TODO: Replace with real volatility metric later
  const intensity = Math.max(0, Math.min(100, Math.abs(metricsForTimeframe.avgMovePct) * 10))

  const data = [
    { metric: 'Heat', value: heat },
    { metric: 'Momentum', value: momentum },
    { metric: 'Breadth', value: breadth },
    { metric: 'Intensity', value: intensity },
  ]

  return (
    <div className="w-full h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#6B7280', fontSize: 10 }}
            axisLine={{ stroke: '#374151' }}
          />
          <Radar
            name="Profile"
            dataKey="value"
            stroke="#22D3EE"
            fill="#22D3EE"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

