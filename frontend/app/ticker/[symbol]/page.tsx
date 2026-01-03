'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import TickerDetail from '@/components/TickerDetail'
import { fetchTicker, TickerMetrics } from '@/lib/api'
import RadarLoader from '@/components/RadarLoader'

export default function TickerPage() {
  const params = useParams()
  const symbol = params.symbol as string
  const [ticker, setTicker] = useState<TickerMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadTicker() {
      try {
        setLoading(true)
        setError(null)

        // First, check if we have cached data from trending list
        const cacheKey = `ticker_${symbol}`
        const cached = sessionStorage.getItem(cacheKey)
        
        if (cached) {
          try {
            const cachedTicker = JSON.parse(cached)
            // Use cached score, but fetch fresh data for other details
            const freshTicker = await fetchTicker(symbol)
            if (freshTicker) {
              // Use cached score to ensure consistency
              freshTicker.ragard_score = cachedTicker.ragard_score
              setTicker(freshTicker)
              setLoading(false)
              return
            }
          } catch (e) {
            // Invalid cache, continue to fetch
          }
        }

        // No cache, fetch normally
        const data = await fetchTicker(symbol)
        if (data) {
          setTicker(data)
        } else {
          setError('Ticker not found')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load ticker')
        console.error('Error loading ticker:', err)
      } finally {
        setLoading(false)
      }
    }

    if (symbol) {
      loadTicker()
    }
  }, [symbol])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <RadarLoader message="Loading ticker details..." />
      </div>
    )
  }

  if (error || !ticker) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="p-4 rounded-lg bg-ragard-danger/20 border border-ragard-danger/30 text-ragard-danger">
          <p className="font-medium">Error loading ticker</p>
          <p className="text-sm mt-1">{error || 'Ticker not found'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <TickerDetail ticker={ticker} />
    </div>
  )
}

