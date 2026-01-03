'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Card from '@/components/Card'
import NarrativesBubbleChart from '@/components/NarrativesBubbleChart'
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
    title: apiNarrative.ai_title || apiNarrative.name, // Use AI title if available, fallback to name
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

// Cache key for sessionStorage
const getCacheKey = (timeframe: TimeframeKey) => `narratives_${timeframe}`

export default function NarrativesPage() {
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeKey>('24h')
  const [sentimentFilter, setSentimentFilter] = useState<'all' | 'bullish' | 'bearish' | 'neutral'>('all')
  const [narratives, setNarratives] = useState<Narrative[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadNarratives = async (forceRefresh = false) => {
    try {
      setLoading(true)
      setError(null)
      
      const cacheKey = getCacheKey(selectedTimeframe)
      
      // Check cache first (unless forcing refresh)
      if (!forceRefresh) {
        const cached = sessionStorage.getItem(cacheKey)
        if (cached) {
          try {
            const cachedData = JSON.parse(cached)
            setNarratives(cachedData)
            setLoading(false)
            return
          } catch (e) {
            // Invalid cache, continue to fetch
            console.warn('Invalid cache data, fetching fresh data')
          }
        }
      }
      
      // Add timeout to prevent hanging
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout (Reddit API can be slow)
      
      try {
        // Fetch narratives for the selected timeframe
        const apiNarratives = await fetchNarratives(selectedTimeframe, controller.signal)
        clearTimeout(timeoutId)
        const transformed = apiNarratives.map(transformNarrative)
        setNarratives(transformed)
        
        // Cache the data
        sessionStorage.setItem(cacheKey, JSON.stringify(transformed))
      } catch (fetchErr: any) {
        clearTimeout(timeoutId)
        if (fetchErr.name === 'AbortError') {
          throw new Error('Request timed out. Please check your backend server.')
        }
        throw fetchErr
      }
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Failed to load narratives'
      setError(errorMessage)
      console.error('Error loading narratives:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNarratives(false) // Load from cache if available
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTimeframe]) // Refetch when timeframe changes

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-5xl font-bold mb-3 font-display text-ragard-textPrimary">
          Narratives
        </h1>
        <p className="text-ragard-textSecondary">
          Track market narratives and their impact on trending stocks
        </p>
      </div>

      {/* Timeframe Toggle and Refresh Button */}
      <div className="flex items-center gap-4">
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
        <button
          onClick={() => loadNarratives(true)}
          disabled={loading}
          className="px-4 py-2 rounded-lg border border-slate-800 text-sm font-medium transition-colors bg-ragard-surface text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg
            className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <RadarLoader message="Scanning Reddit for fresh narratives..." />
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-lg bg-ragard-danger/20 border border-ragard-danger/30 text-ragard-danger">
          <p className="font-medium">Error loading narratives</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Content */}
      {!loading && !error && narratives.length > 0 && (() => {
        // Filter narratives by sentiment (use AI sentiment if available, otherwise fallback to regular sentiment)
        const visibleNarratives = sentimentFilter === 'all' 
          ? narratives 
          : narratives.filter(n => {
              const sentimentToUse = n.ai_sentiment || n.sentiment
              return sentimentToUse === sentimentFilter
            })
        
        return (
          <>
            {/* Bubble Chart Overview */}
            <NarrativesBubbleChart narratives={visibleNarratives} timeframe={selectedTimeframe} />

            {/* Filters */}
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => setSentimentFilter('all')}
                className={`px-4 py-2 rounded-lg border border-slate-800 text-sm font-medium transition-colors ${
                  sentimentFilter === 'all'
                    ? 'bg-ragard-accent text-ragard-background font-semibold'
                    : 'bg-ragard-surface text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setSentimentFilter('bullish')}
                className={`px-4 py-2 rounded-lg border border-slate-800 text-sm font-medium transition-colors ${
                  sentimentFilter === 'bullish'
                    ? 'bg-ragard-accent text-ragard-background font-semibold'
                    : 'bg-ragard-surface text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary'
                }`}
              >
                Bullish
              </button>
              <button
                onClick={() => setSentimentFilter('bearish')}
                className={`px-4 py-2 rounded-lg border border-slate-800 text-sm font-medium transition-colors ${
                  sentimentFilter === 'bearish'
                    ? 'bg-ragard-accent text-ragard-background font-semibold'
                    : 'bg-ragard-surface text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary'
                }`}
              >
                Bearish
              </button>
              <button
                onClick={() => setSentimentFilter('neutral')}
                className={`px-4 py-2 rounded-lg border border-slate-800 text-sm font-medium transition-colors ${
                  sentimentFilter === 'neutral'
                    ? 'bg-ragard-accent text-ragard-background font-semibold'
                    : 'bg-ragard-surface text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary'
                }`}
              >
                Neutral
              </button>
            </div>

            {/* Narratives Grid */}
            {visibleNarratives.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-ragard-textSecondary">No narratives found for this filter.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {visibleNarratives.map((narrative) => {
                const metrics = narrative.metrics[selectedTimeframe]
                const isPositive = metrics.avgMovePct >= 0

                return (
                  <Card key={narrative.id} className="hover:shadow-ragard-glow-sm transition-shadow cursor-pointer">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-xl font-semibold text-ragard-textPrimary font-display">
                        {narrative.title}
                      </h3>
                      {(() => {
                        const sentimentToUse = narrative.ai_sentiment || narrative.sentiment
                        return (
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
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

                    <p className="text-ragard-textSecondary mb-4 text-sm leading-relaxed">
                      {narrative.description}
                    </p>

                    {/* Metrics for Selected Timeframe */}
                    <div className="flex items-center gap-4 mb-4 p-3 rounded-lg bg-ragard-surfaceAlt/50 border border-slate-800/50">
                      <div>
                        <div className="text-xs text-ragard-textSecondary mb-1">Avg Move ({selectedTimeframe.toUpperCase()})</div>
                        <div
                          className={`text-lg font-bold ${
                            isPositive ? 'text-ragard-success' : 'text-ragard-danger'
                          }`}
                        >
                          {isPositive ? '+' : ''}
                          {metrics.avgMovePct.toFixed(1)}%
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="text-xs text-ragard-textSecondary mb-1">Heat Score</div>
                        <div className="text-lg font-bold text-ragard-accent">
                          {metrics.heatScore}/100
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-ragard-textSecondary mb-1">Tickers</div>
                        <div className="text-sm text-ragard-textPrimary">
                          <span className="text-ragard-success">{metrics.upCount} up</span>
                          {' · '}
                          <span className="text-ragard-danger">{metrics.downCount} down</span>
                        </div>
                      </div>
                    </div>

                    {/* Sparkline - Heat Trend */}
                    <div className="mb-4 p-3 rounded-lg bg-ragard-surfaceAlt/30 border border-slate-800/30">
                      <div className="text-xs text-ragard-textSecondary mb-2">Heat Trend (24H → 7D → 30D)</div>
                      <NarrativeSparkline metrics={narrative.metrics} mode="heat" />
                    </div>

                    {/* Radar Chart - Profile */}
                    <div className="mb-4 p-3 rounded-lg bg-ragard-surfaceAlt/30 border border-slate-800/30">
                      <div className="text-xs text-ragard-textSecondary mb-2">Profile ({selectedTimeframe.toUpperCase()})</div>
                      <NarrativeRadar metricsForTimeframe={metrics} />
                    </div>

                    {/* Tickers */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {narrative.tickers.map((ticker) => (
                        <Link
                          key={ticker}
                          href={`/stocks/${ticker}`}
                          className="px-3 py-1 rounded-md bg-ragard-surfaceAlt border border-slate-800 text-ragard-accent hover:bg-ragard-surface hover:border-ragard-accent/30 transition-colors text-sm font-medium"
                        >
                          {ticker}
                        </Link>
                      ))}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                      <span className="text-ragard-textMuted text-xs">
                        {narrative.createdAt}
                      </span>
                      <Link
                        href={`/narratives/${narrative.id}`}
                        className="text-ragard-accent hover:text-ragard-accent/80 text-sm font-medium transition-colors"
                      >
                        View Details →
                      </Link>
                    </div>
                  </Card>
                )
              })}
              </div>
            )}
          </>
        )
      })()}
    </div>
  )
}
