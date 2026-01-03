'use client'

import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import { Narrative, TimeframeKey } from '@/types/narratives'

interface NarrativesBubbleChartProps {
  narratives: Narrative[]
  timeframe: TimeframeKey
}

interface BubbleData {
  x: number // avgMovePct
  y: number // heatScore
  z: number // bubble size (ticker count)
  name: string
  shortName: string
  id: string
  tickers: string[]
}

export default function NarrativesBubbleChart({
  narratives,
  timeframe,
}: NarrativesBubbleChartProps) {
  // Build data array for the bubble chart
  const data: BubbleData[] = narratives.map((narrative) => {
    const metrics = narrative.metrics[timeframe]
    // Use ticker count as bubble size proxy
    // TODO: Replace with real liquidity/buzz metric later
    const bubbleSize = Math.max(1, narrative.tickers.length * 20)
    
    return {
      x: metrics.avgMovePct,
      y: metrics.heatScore,
      z: bubbleSize,
      name: narrative.title,
      shortName: narrative.title.length > 12 
        ? narrative.title.substring(0, 12) + '...' 
        : narrative.title,
      id: narrative.id,
      tickers: narrative.tickers,
    }
  })

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as BubbleData
      return (
        <div className="bg-ragard-surface border border-slate-800 rounded-lg p-3 shadow-lg">
          <p className="text-ragard-textPrimary font-semibold mb-2">{data.name}</p>
          <p className="text-ragard-textSecondary text-sm">
            Avg Move: <span className="text-ragard-textPrimary">{data.x.toFixed(2)}%</span>
          </p>
          <p className="text-ragard-textSecondary text-sm">
            Heat: <span className="text-ragard-textPrimary">{data.y.toFixed(1)}/100</span>
          </p>
          <p className="text-ragard-textSecondary text-sm">
            Tickers: <span className="text-ragard-textPrimary">{data.tickers.length}</span>
          </p>
        </div>
      )
    }
    return null
  }

  // Get color based on heat score with Ragard accent theme
  const getBubbleColor = (heatScore: number) => {
    if (heatScore < 30) {
      return '#EF4444' // red
    } else if (heatScore < 60) {
      return '#F97316' // amber
    } else if (heatScore < 80) {
      return '#22C55E' // green
    } else {
      return '#22D3EE' // cyan - Ragard accent
    }
  }

  // Get opacity based on heat score for visual depth
  const getBubbleOpacity = (heatScore: number) => {
    if (heatScore < 30) {
      return 0.6
    } else if (heatScore < 60) {
      return 0.7
    } else if (heatScore < 80) {
      return 0.8
    } else {
      return 0.9
    }
  }

  return (
    <div className="w-full h-[320px] bg-ragard-surface rounded-lg border border-slate-800 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          margin={{
            top: 30,
            right: 20,
            bottom: 50,
            left: 50,
          }}
        >
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="rgba(148, 163, 184, 0.2)" 
          />
          <XAxis
            type="number"
            dataKey="x"
            name="Avg Move"
            label={{ 
              value: 'Avg Move (%)', 
              position: 'insideBottom', 
              offset: -10, 
              fill: '#9CA3AF',
              style: { fontSize: '12px' }
            }}
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Heat"
            label={{ 
              value: 'Heat Score', 
              angle: -90, 
              position: 'insideLeft', 
              fill: '#9CA3AF',
              style: { fontSize: '12px' }
            }}
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
          />
          <ZAxis
            type="number"
            dataKey="z"
            range={[80, 500]}
            // Increased range to make bubbles larger and more prominent visually
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter name="Narratives" data={data} fill="#22D3EE">
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={getBubbleColor(entry.y)}
                opacity={getBubbleOpacity(entry.y)}
              />
            ))}
            <LabelList
              dataKey="shortName"
              position="top"
              fontSize={11}
              fill="#F9FAFB"
              fontWeight={500}
              offset={8}
            />
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
