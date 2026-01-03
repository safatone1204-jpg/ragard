'use client'

interface RiskBadgesProps {
  riskLevel: string
}

export default function RiskBadges({ riskLevel }: RiskBadgesProps) {
  const riskConfig: Record<
    string,
    { label: string; className: string }
  > = {
    low: {
      label: 'Low',
      className: 'bg-ragard-success/20 text-ragard-success border-ragard-success/30',
    },
    moderate: {
      label: 'Moderate',
      className: 'bg-ragard-warning/20 text-ragard-warning border-ragard-warning/30',
    },
    high: {
      label: 'High',
      className: 'bg-ragard-score-ultra/20 text-ragard-score-ultra border-ragard-score-ultra/30',
    },
    extreme: {
      label: 'Extreme',
      className: 'bg-ragard-danger/20 text-ragard-danger border-ragard-danger/30',
    },
  }

  const config = riskConfig[riskLevel.toLowerCase()] || {
    label: riskLevel,
    className: 'bg-ragard-surfaceAlt/50 text-ragard-textSecondary border-slate-800',
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.className}`}
    >
      {config.label}
    </span>
  )
}

