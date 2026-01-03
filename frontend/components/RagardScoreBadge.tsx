'use client'

interface RagardScoreBadgeProps {
  score: number | null
  showLabel?: boolean
}

export default function RagardScoreBadge({ score, showLabel = true }: RagardScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border border-slate-600 bg-slate-800/20 text-slate-400">
        N/A
      </span>
    )
  }
  
  const getScoreBand = (score: number) => {
    // INVERTED: High scores = red (danger), Low scores = green (safe)
    if (score >= 91) {
      return {
        bg: 'bg-red-500/20',
        text: 'text-red-500',
        border: 'border-red-500/30',
        label: 'Elite Setup',
      }
    }
    if (score >= 76) {
      return {
        bg: 'bg-orange-500/20',
        text: 'text-orange-500',
        border: 'border-orange-500/30',
        label: 'Respectable Trash',
      }
    }
    if (score >= 51) {
      return {
        bg: 'bg-yellow-500/20',
        text: 'text-yellow-500',
        border: 'border-yellow-500/30',
        label: 'Spicy but Tradeable',
      }
    }
    if (score >= 26) {
      return {
        bg: 'bg-green-500/20',
        text: 'text-green-500',
        border: 'border-green-500/30',
        label: 'Ultra Degen',
      }
    }
    return {
      bg: 'bg-green-500/20',
      text: 'text-green-500',
      border: 'border-green-500/30',
      label: 'Dumpster Fire',
    }
  }

  const band = getScoreBand(score)

  return (
    <span
      className={`
        inline-flex items-center px-3 py-1 rounded-full text-xs font-medium
        border ${band.border} ${band.bg} ${band.text}
      `}
    >
      {showLabel ? band.label : score}
    </span>
  )
}

