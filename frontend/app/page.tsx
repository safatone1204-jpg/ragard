'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import TrendingTable from '@/components/TrendingTable'
import Watchlist from '@/components/Watchlist'
import Card from '@/components/Card'
import RadarLoader from '@/components/RadarLoader'
import { fetchNarratives, Narrative as APINarrative } from '@/lib/api'
import { Narrative } from '@/types/narratives'

// Transform backend API response (snake_case) to frontend format (camelCase)
function transformNarrative(apiNarrative: APINarrative): Narrative {
  return {
    id: apiNarrative.id,
    title: apiNarrative.ai_title || apiNarrative.name,
    description: apiNarrative.ai_summary || apiNarrative.description,
    tickers: apiNarrative.tickers,
    sentiment: (apiNarrative.ai_sentiment || apiNarrative.sentiment) as 'bullish' | 'bearish' | 'neutral' | 'mixed',
    createdAt: new Date().toISOString().split('T')[0],
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

interface NarrativeWithTimeframe extends Narrative {
  timeframeLabel: string
}

export default function Home() {
  const [narratives, setNarratives] = useState<NarrativeWithTimeframe[]>([])
  const [narrativesLoading, setNarrativesLoading] = useState(true)

  // Cache key for the combined narratives result
  const NARRATIVES_CACHE_KEY = 'narratives_combined'

  // Load top narrative for each timeframe (24h, 7d, 30d) with no duplicates
  const loadNarratives = async (forceRefresh = false) => {
    try {
      setNarrativesLoading(true)
      
      // Check cache first (unless forcing refresh)
      if (!forceRefresh) {
        const cached = sessionStorage.getItem(NARRATIVES_CACHE_KEY)
        if (cached) {
          try {
            const cachedData = JSON.parse(cached)
            setNarratives(cachedData)
            setNarrativesLoading(false)
            return
          } catch (e) {
            // Invalid cache, continue to fetch
          }
        }
      } else {
        // Clear cache when forcing refresh
        sessionStorage.removeItem(NARRATIVES_CACHE_KEY)
        // Also clear individual timeframe caches
        sessionStorage.removeItem('narratives_24h')
        sessionStorage.removeItem('narratives_7d')
        sessionStorage.removeItem('narratives_30d')
      }
      
      const timeframes: Array<{ key: '24h' | '7d' | '30d', label: string }> = [
        { key: '24h', label: '24H' },
        { key: '7d', label: '7D' },
        { key: '30d', label: '30D' },
      ]
      
      const usedNarrativeIds = new Set<string>()
      const usedNarrativeTitles = new Set<string>()
      const selectedNarratives: NarrativeWithTimeframe[] = []
      
      // Process timeframes sequentially to avoid duplicates
      for (const tf of timeframes) {
        let narratives: Narrative[] = []
        const cacheKey = `narratives_${tf.key}`
        
        // Check individual timeframe cache if not forcing refresh
        if (!forceRefresh) {
          const cached = sessionStorage.getItem(cacheKey)
          if (cached) {
            try {
              const cachedData = JSON.parse(cached)
              narratives = cachedData.map(transformNarrative)
            } catch (e) {
              // Invalid cache, continue to fetch
            }
          }
        }
        
        // If no cached data or forcing refresh, fetch from API
        if (narratives.length === 0) {
          try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), 30000)
            const apiNarratives = await fetchNarratives(tf.key, controller.signal)
            clearTimeout(timeoutId)
            narratives = apiNarratives.map(transformNarrative)
            
            // Cache the fetched data
            sessionStorage.setItem(cacheKey, JSON.stringify(narratives))
          } catch (fetchErr: any) {
            // Silently fail for preview, continue to next timeframe
            continue
          }
        }
        
        // Find the first narrative that hasn't been used yet
        // Check both by ID and by title to catch any edge cases
        for (const narrative of narratives) {
          const narrativeTitle = narrative.title?.toLowerCase().trim() || ''
          const isDuplicate = usedNarrativeIds.has(narrative.id) || 
                             (narrativeTitle && usedNarrativeTitles.has(narrativeTitle))
          
          if (!isDuplicate) {
            usedNarrativeIds.add(narrative.id)
            if (narrativeTitle) {
              usedNarrativeTitles.add(narrativeTitle)
            }
            selectedNarratives.push({ ...narrative, timeframeLabel: tf.label })
            break
          }
        }
      }
      
      setNarratives(selectedNarratives)
      // Cache the combined result
      sessionStorage.setItem(NARRATIVES_CACHE_KEY, JSON.stringify(selectedNarratives))
    } catch (err) {
      // Silently fail for preview
    } finally {
      setNarrativesLoading(false)
    }
  }

  useEffect(() => {
    loadNarratives()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-5xl font-bold mb-3 font-display text-ragard-textPrimary">
          Home
        </h1>
      </div>
      
      {/* Top Narratives Preview */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold font-display text-ragard-textPrimary">
            Top Narratives
          </h2>
          <button
            onClick={() => loadNarratives(true)}
            disabled={narrativesLoading}
            className="px-4 py-2 rounded-full text-sm font-medium text-ragard-textSecondary hover:text-ragard-textPrimary bg-ragard-surface border border-slate-800 hover:bg-ragard-surfaceAlt transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            title="Refresh narratives"
          >
            <svg
              className={`w-4 h-4 ${narrativesLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
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
        {narrativesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="flex items-center justify-center min-h-[200px]">
                <RadarLoader message="Loading narrative..." />
              </Card>
            ))}
          </div>
        ) : narratives.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {narratives.map((narrative) => (
              <Card key={`${narrative.id}-${narrative.timeframeLabel}`} className="hover:shadow-ragard-glow-sm transition-shadow">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium px-2 py-1 rounded-full bg-ragard-surfaceAlt border border-slate-800 text-ragard-textSecondary">
                    {narrative.timeframeLabel}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-ragard-textPrimary font-display mb-2">
                  {narrative.title}
                </h3>
                <p className="text-sm text-ragard-textSecondary mb-3 line-clamp-2">
                  {narrative.description}
                </p>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-ragard-textSecondary">
                    {narrative.tickers.length} ticker{narrative.tickers.length !== 1 ? 's' : ''}
                  </span>
                  <Link
                    href={`/narratives/${narrative.id}`}
                    className="text-xs text-ragard-accent hover:text-ragard-accent/80 transition-colors font-medium"
                  >
                    View narrative →
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        ) : null}
      </div>
      
      {/* Trending section */}
      <div>
        <TrendingTable />
      </div>
      
      {/* Watchlist section below */}
      <Watchlist />
    </div>
  )
}

