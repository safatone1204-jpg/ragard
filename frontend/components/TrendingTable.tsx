'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { fetchTrending } from '@/lib/api'
import RiskBadges from './RiskBadges'
import RagardScoreGauge from './RagardScoreGauge'
import RagardScoreBadge from './RagardScoreBadge'
import Card from './Card'
import RadarLoader from './RadarLoader'
import { TimeframeKey } from '@/types/narratives'

const TIMEFRAMES = [
  { key: '24h' as TimeframeKey, label: '24H' },
  { key: '7d' as TimeframeKey, label: '7D' },
  { key: '30d' as TimeframeKey, label: '30D' },
]

interface Ticker {
  symbol: string
  company_name: string
  price: number
  change_pct: number
  market_cap: number | null
  ragard_score: number | null  // Can be null if data is missing
  risk_level: string
}

// Cache key for sessionStorage
const getCacheKey = (timeframe: TimeframeKey) => `trending_tickers_${timeframe}`

// Tooltip component that positions itself to avoid clipping
function RegardScoreTooltip() {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const buttonRef = useRef<HTMLSpanElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const handleMouseEnter = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const tooltipWidth = 250
      const tooltipHeight = 120
      const spacing = 8
      
      // Position to the bottom-left of the button
      let left = rect.left
      let top = rect.bottom + spacing
      
      // Adjust if tooltip would go off screen to the right
      if (left + tooltipWidth > window.innerWidth - 20) {
        left = window.innerWidth - tooltipWidth - 20
      }
      
      // Adjust if tooltip would go off screen to the bottom
      if (top + tooltipHeight > window.innerHeight - 20) {
        top = rect.top - tooltipHeight - spacing
      }
      
      // Ensure it doesn't go off screen to the left
      if (left < 20) {
        left = 20
      }
      
      // Ensure it doesn't go off screen to the top
      if (top < 20) {
        top = 20
      }
      
      setPosition({ top, left })
      setIsVisible(true)
    }
  }

  const handleMouseLeave = () => {
    setIsVisible(false)
  }

  return (
    <div className="flex items-center justify-center gap-2">
      <span>Regard Score</span>
      <div className="relative">
        <span 
          ref={buttonRef}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className="w-5 h-5 rounded-full bg-ragard-surfaceAlt border border-slate-800 text-ragard-textSecondary text-xs cursor-help flex items-center justify-center hover:bg-ragard-surface hover:border-ragard-accent/30 transition-colors"
        >
          ?
        </span>
        {isVisible && (
          <div
            ref={tooltipRef}
            className="fixed z-[9999] pointer-events-none"
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
            }}
          >
            <div className="bg-ragard-surfaceAlt border border-slate-800 rounded-md p-2.5 shadow-xl text-[11px] leading-relaxed text-ragard-textPrimary whitespace-normal min-w-[200px] max-w-[250px]">
              Regard Score is a 0-100 degen meter for investing in this company right now. 0 = solid, boring, low-risk; 100 = full casino, hyper-speculative. Higher = more degen / more risk. Timeframe changes which stocks appear, not the score itself.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function TrendingTable() {
  const [selectedTimeframe, setSelectedTimeframe] = useState<TimeframeKey>('24h')
  const [tickers, setTickers] = useState<Ticker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load from cache or fetch when timeframe changes
  useEffect(() => {
    const cacheKey = getCacheKey(selectedTimeframe)
    const cached = sessionStorage.getItem(cacheKey)
    
    if (cached) {
      // Use cached data if available for this specific timeframe
      try {
        const cachedData = JSON.parse(cached)
        setTickers(cachedData)
        setLoading(false)
        return
      } catch (e) {
        // Invalid cache, continue to fetch
        console.warn('Invalid cache data, fetching fresh data')
      }
    }
    
    // No cache exists for this timeframe - fetch it
    loadTrendingData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTimeframe])

  const loadTrendingData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Add timeout to prevent hanging (increased for Regard Score calculations)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 second timeout
      
      try {
        const data = await fetchTrending(selectedTimeframe, controller.signal)
        clearTimeout(timeoutId)
        setTickers(data)
        
        // Cache the data for this timeframe
        const cacheKey = getCacheKey(selectedTimeframe)
        sessionStorage.setItem(cacheKey, JSON.stringify(data))
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
        : 'Failed to load trending tickers'
      setError(errorMessage)
      console.error('Error loading trending tickers:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    // Clear cache for current timeframe and reload
    const cacheKey = getCacheKey(selectedTimeframe)
    sessionStorage.removeItem(cacheKey)
    loadTrendingData()
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        {/* Trending Header */}
        <div>
          <div className="flex items-center justify-between gap-4 mb-2">
            <h2 className="text-2xl font-bold font-display text-ragard-textPrimary">
              Trending
            </h2>
          <div className="flex items-center gap-4">
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
            
            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-4 py-2 rounded-full text-sm font-medium transition-all bg-ragard-surface border border-slate-800 text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
            </div>
          </div>
          <p className="text-sm text-ragard-textSecondary">
            Stocks are ranked by Reddit mentions and price movement. Selected from tickers mentioned at least {selectedTimeframe === '24h' ? '1' : selectedTimeframe === '7d' ? '2' : '3'} time{selectedTimeframe === '24h' ? '' : 's'} in the selected timeframe.
          </p>
        </div>
        
        <RadarLoader message="Scanning Reddit for trending tickers..." />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        {/* Trending Header */}
        <div>
          <div className="flex items-center justify-between gap-4 mb-2">
            <h2 className="text-2xl font-bold font-display text-ragard-textPrimary">
              Trending
            </h2>
            <div className="flex items-center gap-4">
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
              
              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="px-4 py-2 rounded-full text-sm font-medium transition-all bg-ragard-surface border border-slate-800 text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Refresh
              </button>
            </div>
          </div>
          <p className="text-sm text-ragard-textSecondary">
            Stocks are ranked by Reddit mentions and price movement. Selected from tickers mentioned at least {selectedTimeframe === '24h' ? '1' : selectedTimeframe === '7d' ? '2' : '3'} time{selectedTimeframe === '24h' ? '' : 's'} in the selected timeframe.
          </p>
        </div>
        
        <div className="p-4 rounded-lg bg-ragard-danger/20 border border-ragard-danger/30 text-ragard-danger">
          <p className="font-medium">Error loading trending tickers</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 relative">
      {/* Trending Header */}
      <div>
        <div className="flex items-center justify-between gap-4 mb-2">
          <h2 className="text-2xl font-bold font-display text-ragard-textPrimary">
            Trending
          </h2>
          <div className="flex items-center gap-4">
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
            
            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-4 py-2 rounded-full text-sm font-medium transition-all bg-ragard-surface border border-slate-800 text-ragard-textSecondary hover:bg-ragard-surfaceAlt hover:text-ragard-textPrimary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
          </div>
        </div>
        <p className="text-sm text-ragard-textSecondary">
          Stocks are ranked by Reddit mentions and price movement. Selected from tickers mentioned at least {selectedTimeframe === '24h' ? '1' : selectedTimeframe === '7d' ? '2' : '3'} time{selectedTimeframe === '24h' ? '' : 's'} in the selected timeframe.
        </p>
      </div>

      {/* Table */}
      {tickers.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-ragard-textSecondary">No trending tickers found for this timeframe.</p>
          </div>
        </Card>
      ) : (
        <div className="relative">
          <Card className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
              <thead className="bg-ragard-surfaceAlt/50 border-b border-slate-800 relative">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    {selectedTimeframe.toUpperCase()} % Move
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    <RegardScoreTooltip />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {tickers.map((ticker) => {
                  const handleRowClick = () => {
                    // Cache ticker data for detail page consistency
                    sessionStorage.setItem(`ticker_${ticker.symbol}`, JSON.stringify(ticker))
                    window.location.href = `/stocks/${ticker.symbol}`
                  }
                  
                  return (
                    <tr
                      key={ticker.symbol}
                      onClick={handleRowClick}
                      className="hover:bg-ragard-surfaceAlt/30 transition-colors cursor-pointer"
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick()
                        }
                      }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-ragard-accent font-semibold">
                          {ticker.symbol}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-ragard-textPrimary">
                          {ticker.company_name}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-ragard-textPrimary">
                        ${Number(ticker.price).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`font-semibold ${
                            ticker.change_pct >= 0
                              ? 'text-ragard-success'
                              : 'text-ragard-danger'
                          }`}
                        >
                          {ticker.change_pct >= 0 ? '+' : ''}
                          {Number(ticker.change_pct).toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {ticker.ragard_score !== null && ticker.ragard_score !== undefined ? (
                          <div className="w-12 h-12 mx-auto">
                            <RagardScoreGauge score={ticker.ragard_score} size="sm" />
                          </div>
                        ) : (
                          <span className="text-ragard-textSecondary text-sm">N/A</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
