'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { RegardHistoryEntry } from '@/lib/api'

interface RegardHistoryChartProps {
  history: RegardHistoryEntry[]
}

export default function RegardHistoryChart({ history }: RegardHistoryChartProps) {
  if (history.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center text-ragard-textSecondary">
        <p>No historical data available</p>
      </div>
    )
  }

  // Transform data for chart (date only, no time)
  const chartData = history.map((entry) => {
    const date = new Date(entry.timestamp_utc)
    return {
      time: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      timestamp: date.getTime(),
      score: entry.score_rounded,
      scoreRaw: entry.score_raw,
      price: entry.price_at_snapshot,
      mode: entry.scoring_mode,
    }
  })

  // Sort by timestamp to ensure correct order
  chartData.sort((a, b) => a.timestamp - b.timestamp)

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-ragard-surface border border-slate-800 rounded-lg p-3 shadow-lg">
          <p className="text-ragard-textSecondary text-xs mb-2">{data.time}</p>
          <div className="space-y-1">
            <p className="text-ragard-textPrimary font-semibold">
              Score: <span className="text-ragard-accent">{data.score ?? 'N/A'}</span>
            </p>
            {data.scoreRaw !== null && data.scoreRaw !== data.score && (
              <p className="text-ragard-textSecondary text-xs">
                Raw: {data.scoreRaw.toFixed(1)}
              </p>
            )}
            {data.price !== null && (
              <p className="text-ragard-textSecondary text-xs">
                Price: ${data.price.toFixed(2)}
              </p>
            )}
            <p className="text-ragard-textSecondary text-xs">
              Mode: <span className={data.mode === 'ai' ? 'text-ragard-success' : 'text-ragard-textSecondary'}>
                {data.mode}
              </span>
            </p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            tick={{ fill: '#6B7280', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: '#6B7280', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
            label={{ value: 'Regard Score', angle: -90, position: 'insideLeft', fill: '#9CA3AF', fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#22D3EE"
            strokeWidth={2}
            dot={{ fill: '#22D3EE', r: 4 }}
            activeDot={{ r: 6, fill: '#22D3EE' }}
            name="Regard Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

