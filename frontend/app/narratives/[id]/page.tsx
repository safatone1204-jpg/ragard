'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import Card from '@/components/Card'
import NarrativeSparkline from '@/components/NarrativeSparkline'
import NarrativeRadar from '@/components/NarrativeRadar'
import RadarLoader from '@/components/RadarLoader'
import { TimeframeKey } from '@/types/narratives'
import { fetchNarratives, Narrative as APINarrative } from '@/lib/api'
import { Narrative } from '@/types/narratives'

// Transform backend API response (snake_case) to frontend format (camelCase)
function transformNarrative(apiNarrative: APINarrative): Narrative {
  return {
    id: apiNarrative.id,
    title: apiNarrative.ai_title || apiNarrative.name, // Use AI title if available
    description: apiNarrative.ai_summary || apiNarrative.description, // Use AI summary if available
    tickers: apiNarrative.tickers,
    sentiment: (apiNarrative.ai_sentiment || apiNarrative.sentiment) as 'bullish' | 'bearish' | 'neutral' | 'mixed',
    createdAt: new Date().toISOString().split('T')[0], // Use current date as fallback
    metrics: {
      '24h': {
        avgMovePct: apiNarrative.metrics['24h'].avg_move_pct,
        upCount: apiNarrative.metrics['24h'].up_count,
        downCount: apiNarrative.metrics['24h'].down_count,
        heatScore: apiNarrative.metrics['24h'].heat_score,
      },
      '7d': {
        avgMovePct: apiNarrative.metrics['7d'].avg_move_pct,
        upCount: apiNarrative.metrics['7d'].up_count,
        downCount: apiNarrative.metrics['7d'].down_count,
        heatScore: apiNarrative.metrics['7d'].heat_score,
      },
      '30d': {
        avgMovePct: apiNarrative.metrics['30d'].avg_move_pct,
        upCount: apiNarrative.metrics['30d'].up_count,
        downCount: apiNarrative.metrics['30d'].down_count,
        heatScore: apiNarrative.metrics['30d'].heat_score,
      },
    },
    ai_title: apiNarrative.ai_title,
    ai_summary: apiNarrative.ai_summary,
    ai_sentiment: apiNarrative.ai_sentiment,
  }
}

const TIMEFRAMES = [
  { key: '24h' as TimeframeKey, label: '24H' },
  { key: '7d' as TimeframeKey, label: '7D' },
  { key: '30d' as TimeframeKey, label: '30D' },
]

export default function NarrativeDetailPage() {
  const params = useParams()
  const narrativeId = params.id as string
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeKey>('24h')
  const [narrative, setNarrative] = useState<Narrative | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadNarrative() {
      try {
        setLoading(true)
        setError(null)
        
        // Try to find narrative in all timeframes (check cache first, then fetch)
        const timeframes: TimeframeKey[] = ['24h', '7d', '30d']
        let found: Narrative | null = null
        
        // First, check sessionStorage cache for all timeframes
        for (const tf of timeframes) {
          const cacheKey = `narratives_${tf}`
          const cached = sessionStorage.getItem(cacheKey)
          if (cached) {
            try {
              const cachedData: Narrative[] = JSON.parse(cached)
              const cachedNarrative = cachedData.find((n) => n.id === narrativeId)
              if (cachedNarrative) {
                found = cachedNarrative
                break
              }
            } catch (e) {
              // Invalid cache, continue
            }
          }
        }
        
        // If not found in cache, fetch from API (try all timeframes)
        if (!found) {
          for (const tf of timeframes) {
            try {
              const apiNarratives = await fetchNarratives(tf)
              const transformed = apiNarratives.map(transformNarrative)
              const narrative = transformed.find((n) => n.id === narrativeId)
              if (narrative) {
                found = narrative
                // Cache it for future use
                const cacheKey = `narratives_${tf}`
                sessionStorage.setItem(cacheKey, JSON.stringify(transformed))
                break
              }
            } catch (err) {
              // Continue to next timeframe if this one fails
              console.warn(`Failed to fetch narratives for ${tf}:`, err)
            }
          }
        }
        
        if (found) {
          setNarrative(found)
        } else {
          setError(`Narrative not found. It may not be active in any timeframe.`)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load narrative')
        console.error('Error loading narrative:', err)
      } finally {
        setLoading(false)
      }
    }

    if (narrativeId) {
      loadNarrative()
    }
  }, [narrativeId]) // Only run once when narrativeId changes

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <RadarLoader message="Loading narrative details..." />
      </div>
    )
  }

  if (error || !narrative) {
    return (
      <div className="space-y-8">
        <div className="text-center py-12">
          <p className="text-ragard-danger mb-4">Narrative not found</p>
          <Link
            href="/narratives"
            className="text-ragard-accent hover:text-ragard-accent/80 text-sm font-medium transition-colors"
          >
            ← Back to Narratives
          </Link>
        </div>
      </div>
    )
  }

  const metrics = narrative.metrics[selectedTimeframe]
  const isPositive = metrics.avgMovePct >= 0

  return (
    <main className="space-y-8">
      {/* Header - Overview */}
      <div>
        <Link
          href="/narratives"
          className="text-ragard-accent hover:text-ragard-accent/80 text-sm font-medium transition-colors mb-4 inline-block"
        >
          ← Back to Narratives
        </Link>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-5xl font-bold mb-3 font-display text-ragard-textPrimary">
              {narrative.title}
            </h1>
            <p className="text-ragard-textSecondary text-lg leading-relaxed max-w-3xl">
              {narrative.description}
            </p>
          </div>
          {(() => {
            const sentimentToUse = narrative.ai_sentiment || narrative.sentiment
            return (
              <span
                className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                  sentimentToUse === 'bullish'
                    ? 'bg-ragard-success/20 text-ragard-success border border-ragard-success/30'
                    : sentimentToUse === 'bearish'
                    ? 'bg-ragard-danger/20 text-ragard-danger border border-ragard-danger/30'
                    : sentimentToUse === 'mixed'
                    ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'
                    : 'bg-ragard-textMuted/20 text-ragard-textSecondary border border-slate-800'
                }`}
              >
                {sentimentToUse.charAt(0).toUpperCase() + sentimentToUse.slice(1)}
              </span>
            )
          })()}
        </div>

        {/* Tickers List */}
        <div className="flex flex-wrap gap-2 mt-4">
          {narrative.tickers.map((ticker) => (
            <Link
              key={ticker}
              href={`/stocks/${ticker}`}
              className="px-3 py-1.5 rounded-md bg-ragard-surfaceAlt border border-slate-800 text-ragard-accent hover:bg-ragard-surface hover:border-ragard-accent/30 transition-colors text-sm font-medium"
            >
              {ticker}
            </Link>
          ))}
        </div>
      </div>

      {/* Timeframe Toggle */}
      <div className="flex gap-2">
        {TIMEFRAMES.map((tf) => {
          const isActive = selectedTimeframe === tf.key
          return (
            <button
              key={tf.key}
              onClick={() => setSelectedTimeframe(tf.key)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium transition-all
                ${
                  isActive
                    ? 'bg-ragard-accent text-ragard-background font-semibold'
                    : 'bg-ragard-surface border border-slate-800 text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary'
                }
              `}
            >
              {tf.label}
            </button>
          )
        })}
      </div>

      {/* Metrics Overview - Timeframe Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {TIMEFRAMES.map((tf) => {
          const tfMetrics = narrative.metrics[tf.key]
          const tfIsPositive = tfMetrics.avgMovePct >= 0
          const isSelected = selectedTimeframe === tf.key
          
          return (
            <Card
              key={tf.key}
              className={`p-3 ${
                isSelected
                  ? 'border-ragard-accent/50 bg-ragard-surfaceAlt/30'
                  : 'border-slate-800'
              }`}
            >
              <div className="text-xs text-ragard-textSecondary mb-2 font-semibold">
                {tf.label}
              </div>
              <div className="space-y-2">
                <div>
                  <div className="text-[10px] text-ragard-textMuted mb-0.5">Avg Move</div>
                  <div
                    className={`text-lg font-bold ${
                      tfIsPositive ? 'text-ragard-success' : 'text-ragard-danger'
                    }`}
                  >
                    {tfIsPositive ? '+' : ''}
                    {tfMetrics.avgMovePct.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-ragard-textMuted mb-0.5">Heat Score</div>
                  <div className="text-lg font-bold text-ragard-accent">
                    {tfMetrics.heatScore.toFixed(1)}/100
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-ragard-textMuted mb-0.5">Tickers</div>
                  <div className="text-xs text-ragard-textPrimary">
                    <span className="text-ragard-success">{tfMetrics.upCount} up</span>
                    {' · '}
                    <span className="text-ragard-danger">{tfMetrics.downCount} down</span>
                  </div>
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Sparklines */}
        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-ragard-textPrimary mb-4 font-display">
              Heat Trend (24H → 7D → 30D)
            </h3>
            <NarrativeSparkline metrics={narrative.metrics} mode="heat" />
          </Card>
          <Card>
            <h3 className="text-lg font-semibold text-ragard-textPrimary mb-4 font-display">
              Move Trend (24H → 7D → 30D)
            </h3>
            <NarrativeSparkline metrics={narrative.metrics} mode="move" />
          </Card>
        </div>

        {/* Right: Radar Chart */}
        <div>
          <Card>
            <h3 className="text-lg font-semibold text-ragard-textPrimary mb-4 font-display">
              Profile ({selectedTimeframe.toUpperCase()})
            </h3>
            <NarrativeRadar metricsForTimeframe={metrics} />
          </Card>
        </div>
      </div>

      {/* Current Timeframe Highlights */}
      <Card>
        <h3 className="text-lg font-semibold text-ragard-textPrimary mb-4 font-display">
          Current Metrics ({selectedTimeframe.toUpperCase()})
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-ragard-surfaceAlt/50 border border-slate-800/50">
            <div className="text-xs text-ragard-textSecondary mb-1">Avg Move</div>
            <div
              className={`text-2xl font-bold ${
                isPositive ? 'text-ragard-success' : 'text-ragard-danger'
              }`}
            >
              {isPositive ? '+' : ''}
              {metrics.avgMovePct.toFixed(1)}%
            </div>
          </div>
          <div className="p-4 rounded-lg bg-ragard-surfaceAlt/50 border border-slate-800/50">
            <div className="text-xs text-ragard-textSecondary mb-1">Heat Score</div>
            <div className="text-2xl font-bold text-ragard-accent">
              {metrics.heatScore.toFixed(1)}/100
            </div>
          </div>
          <div className="p-4 rounded-lg bg-ragard-surfaceAlt/50 border border-slate-800/50">
            <div className="text-xs text-ragard-textSecondary mb-1">Up Tickers</div>
            <div className="text-2xl font-bold text-ragard-success">
              {metrics.upCount}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-ragard-surfaceAlt/50 border border-slate-800/50">
            <div className="text-xs text-ragard-textSecondary mb-1">Down Tickers</div>
            <div className="text-2xl font-bold text-ragard-danger">
              {metrics.downCount}
            </div>
          </div>
        </div>
      </Card>
    </main>
  )
}
