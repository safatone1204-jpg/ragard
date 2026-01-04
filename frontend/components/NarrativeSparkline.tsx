'use client'

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { TimeframeKey } from '@/types/narratives'

interface NarrativeSparklineProps {
  metrics: {
    [K in TimeframeKey]: {
      avgMovePct: number
      upCount: number
      downCount: number
      heatScore: number
    }
  }
  mode?: 'heat' | 'move'
}

export default function NarrativeSparkline({ metrics, mode = 'heat' }: NarrativeSparklineProps) {
  const data = [
    { label: '24H', heat: metrics['24h'].heatScore, move: metrics['24h'].avgMovePct },
    { label: '7D', heat: metrics['7d'].heatScore, move: metrics['7d'].avgMovePct },
    { label: '30D', heat: metrics['30d'].heatScore, move: metrics['30d'].avgMovePct },
  ]

  const valueKey = mode === 'heat' ? 'heat' : 'move'
  const strokeColor = mode === 'heat' ? '#22D3EE' : (data[0].move >= 0 ? '#22C55E' : '#EF4444')

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const value = payload[0].value
      const label = payload[0].payload.label
      return (
        <div className="bg-ragard-surface border border-slate-800 rounded px-2 py-1 text-xs">
          <p className="text-ragard-textPrimary">
            {label}: {mode === 'heat' ? `${value.toFixed(1)}/100` : `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`}
          </p>
        </div>
      )
    }
    return null
  }

  // Calculate domain for better visualization (exaggerate differences)
  const values = data.map(d => d[valueKey])
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue
  
  // Add padding to domain to make differences more visible
  // For heat scores (0-100), use a tighter range around the actual values
  // For move percentages, use a wider range to show relative changes
  let domainMin: number, domainMax: number
  if (mode === 'heat') {
    // Heat scores: use 0-100 but focus on the range with 20% padding
    const padding = Math.max(range * 0.2, 5) // At least 5 points padding
    domainMin = Math.max(0, minValue - padding)
    domainMax = Math.min(100, maxValue + padding)
  } else {
    // Move percentages: use wider range to exaggerate differences
    const padding = Math.max(Math.abs(range) * 0.3, 2) // 30% padding or at least 2%
    domainMin = minValue - padding
    domainMax = maxValue + padding
  }

  return (
    <div className="w-full h-[50px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
	  <YAxis domain={[domainMin, domainMax]} />
          <XAxis
            dataKey="label"
            tick={{ fill: '#6B7280', fontSize: 10 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey={valueKey}
            stroke={strokeColor}
            strokeWidth={2.5}
            dot={{ fill: strokeColor, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

