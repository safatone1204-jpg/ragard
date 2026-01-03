'use client'

import { RegardHistoryEntry } from '@/lib/api'

interface RegardHistoryTableProps {
  history: RegardHistoryEntry[]
}

export default function RegardHistoryTable({ history }: RegardHistoryTableProps) {
  if (history.length === 0) {
    return (
      <div className="text-center py-8 text-ragard-textSecondary">
        <p>No historical data available</p>
      </div>
    )
  }

  // Format date for display (date only, no time)
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  // Format scoring mode badge
  const getModeBadge = (mode: string, aiSuccess: boolean) => {
    if (mode === 'ai' && aiSuccess) {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-ragard-success/20 text-ragard-success border border-ragard-success/30">
          AI
        </span>
      )
    } else if (mode === 'fallback') {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
          Fallback
        </span>
      )
    } else {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-ragard-danger/20 text-ragard-danger border border-ragard-danger/30">
          Error
        </span>
      )
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="text-left py-3 px-4 text-ragard-textSecondary font-medium">Date</th>
            <th className="text-right py-3 px-4 text-ragard-textSecondary font-medium">Score</th>
            <th className="text-right py-3 px-4 text-ragard-textSecondary font-medium">Raw</th>
            <th className="text-center py-3 px-4 text-ragard-textSecondary font-medium">Mode</th>
            <th className="text-right py-3 px-4 text-ragard-textSecondary font-medium">Price</th>
            <th className="text-right py-3 px-4 text-ragard-textSecondary font-medium">24h Change</th>
            <th className="text-right py-3 px-4 text-ragard-textSecondary font-medium">Volume</th>
            <th className="text-right py-3 px-4 text-ragard-textSecondary font-medium">Version</th>
          </tr>
        </thead>
        <tbody>
          {history.map((entry, index) => (
            <tr
              key={index}
              className="border-b border-slate-800/50 hover:bg-ragard-surfaceAlt transition-colors"
            >
              <td className="py-3 px-4 text-ragard-textSecondary">
                {formatDate(entry.timestamp_utc)}
              </td>
              <td className="py-3 px-4 text-right">
                {entry.score_rounded !== null ? (
                  <span className="text-ragard-textPrimary font-semibold">
                    {entry.score_rounded}
                  </span>
                ) : (
                  <span className="text-ragard-textSecondary">—</span>
                )}
              </td>
              <td className="py-3 px-4 text-right text-ragard-textSecondary">
                {entry.score_raw !== null ? entry.score_raw.toFixed(1) : '—'}
              </td>
              <td className="py-3 px-4 text-center">
                {getModeBadge(entry.scoring_mode, entry.ai_success)}
              </td>
              <td className="py-3 px-4 text-right text-ragard-textPrimary">
                {entry.price_at_snapshot !== null ? `$${entry.price_at_snapshot.toFixed(2)}` : '—'}
              </td>
              <td className="py-3 px-4 text-right">
                {entry.change_24h_pct !== null ? (
                  <span
                    className={
                      entry.change_24h_pct >= 0 ? 'text-ragard-success' : 'text-ragard-danger'
                    }
                  >
                    {entry.change_24h_pct >= 0 ? '+' : ''}
                    {entry.change_24h_pct.toFixed(2)}%
                  </span>
                ) : (
                  <span className="text-ragard-textSecondary">—</span>
                )}
              </td>
              <td className="py-3 px-4 text-right text-ragard-textSecondary">
                {entry.volume_24h !== null
                  ? `${(entry.volume_24h / 1e6).toFixed(1)}M`
                  : '—'}
              </td>
              <td className="py-3 px-4 text-right text-ragard-textSecondary text-xs">
                {entry.scoring_version}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

