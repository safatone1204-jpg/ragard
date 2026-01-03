'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { fetchStockProfile } from '@/lib/api'
import {
  fetchWatchlists,
  createWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
  type Watchlist,
  type WatchlistItem,
} from '@/lib/watchlistAPI'
import Card from './Card'
import RagardScoreGauge from './RagardScoreGauge'
import RagardScoreBadge from './RagardScoreBadge'
import RiskBadges from './RiskBadges'
import RadarLoader from './RadarLoader'

interface WatchlistItemWithData {
  item: WatchlistItem
  symbol: string
  company_name: string | null
  price: number | null
  change_pct: number | null
  ragard_score: number | null
  risk_level: string | null
}

export default function Watchlist() {
  const { isLoggedIn, loading: authLoading } = useAuth()
  const router = useRouter()
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [currentWatchlist, setCurrentWatchlist] = useState<Watchlist | null>(null)
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItemWithData[]>([])
  const [loading, setLoading] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Load watchlists when logged in
  useEffect(() => {
    if (!isLoggedIn || authLoading) {
      setWatchlists([])
      setCurrentWatchlist(null)
      setWatchlistItems([])
      return
    }

    async function loadWatchlists() {
      try {
        setLoading(true)
        const fetchedWatchlists = await fetchWatchlists()

        if (fetchedWatchlists.length === 0) {
          // Create default watchlist if none exist
          const defaultWatchlist = await createWatchlist('My Watchlist')
          setWatchlists([defaultWatchlist])
          setCurrentWatchlist(defaultWatchlist)
        } else {
          setWatchlists(fetchedWatchlists)
          setCurrentWatchlist(fetchedWatchlists[0]) // Use first watchlist
        }
      } catch (err: any) {
        console.error('Error loading watchlists:', err)
        setError('Failed to load watchlists')
      } finally {
        setLoading(false)
      }
    }

    loadWatchlists()
  }, [isLoggedIn, authLoading])

  // Load items for current watchlist
  useEffect(() => {
    if (!isLoggedIn || !currentWatchlist) {
      setWatchlistItems([])
      return
    }

    // TODO: Backend needs GET /api/watchlists/:id/items endpoint
    // For now, items added during this session will be shown
    // Existing items from previous sessions won't load until endpoint is added
    async function loadItems() {
      if (!currentWatchlist) return
      
      try {
        const { getWatchlistItems } = await import('@/lib/watchlistAPI')
        const items = await getWatchlistItems(currentWatchlist.id)
        
        // Fetch data for each item
        const itemsWithData = await Promise.all(
          items.map(async (item) => {
            try {
              const profile = await fetchStockProfile(item.ticker)
              return {
                item,
                symbol: item.ticker,
                company_name: profile.company_name,
                price: profile.price,
                change_pct: profile.change_pct,
                ragard_score: profile.ragard_score,
                risk_level: profile.risk_level,
              }
            } catch {
              return {
                item,
                symbol: item.ticker,
                company_name: null,
                price: null,
                change_pct: null,
                ragard_score: null,
                risk_level: null,
              }
            }
          })
        )
        setWatchlistItems(itemsWithData)
      } catch (error) {
        // Endpoint may not exist yet - that's okay, items will be empty
        console.log('Could not load watchlist items:', error)
      }
    }

    loadItems()
  }, [currentWatchlist, isLoggedIn])

  const addToWatchlist = async (symbol: string) => {
    if (!isLoggedIn) {
      setError('You must be logged in to save watchlists')
      router.push('/account')
      return
    }

    if (!currentWatchlist) {
      setError('No watchlist available')
      return
    }

    const upperSymbol = symbol.toUpperCase().trim()

    if (!upperSymbol) {
      setError('Please enter a valid symbol')
      return
    }

    // Check if already in watchlist
    if (watchlistItems.some((item) => item.item.ticker === upperSymbol)) {
      setError(`${upperSymbol} is already in your watchlist`)
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Verify the symbol exists
      await fetchStockProfile(upperSymbol)

      // Add to watchlist via API
      const newItem = await addWatchlistItem(currentWatchlist.id, upperSymbol)

      // Fetch updated stock data
      const profile = await fetchStockProfile(upperSymbol)
      const itemWithData: WatchlistItemWithData = {
        item: newItem,
        symbol: upperSymbol,
        company_name: profile.company_name,
        price: profile.price,
        change_pct: profile.change_pct,
        ragard_score: profile.ragard_score,
        risk_level: profile.risk_level,
      }

      setWatchlistItems([...watchlistItems, itemWithData])
      setNewSymbol('')
      setError(null)
    } catch (err: any) {
      const errorMsg = err?.message || `Symbol ${upperSymbol} not found or invalid`
      setError(errorMsg)
      console.error('Error adding to watchlist:', err)
    } finally {
      setLoading(false)
    }
  }

  const removeFromWatchlist = async (item: WatchlistItemWithData) => {
    if (!currentWatchlist) return

    try {
      setLoading(true)
      await removeWatchlistItem(currentWatchlist.id, item.item.id)
      setWatchlistItems(watchlistItems.filter((i) => i.item.id !== item.item.id))
    } catch (err: any) {
      setError('Failed to remove item from watchlist')
      console.error('Error removing from watchlist:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    addToWatchlist(newSymbol)
  }

  // Not logged in state
  if (!isLoggedIn && !authLoading) {
    return (
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold mb-2 font-display text-ragard-textPrimary">
            Watchlist
          </h2>
          <p className="text-sm text-ragard-textSecondary">
            Track your favorite stocks
          </p>
        </div>

        <Card>
          <div className="text-center py-8 space-y-4">
            <p className="text-ragard-textSecondary">
              Log in to use personalized watchlists.
            </p>
            <p className="text-sm text-ragard-textSecondary">
              Watchlists are only available when you're signed in.
            </p>
            <button
              onClick={() => router.push('/account')}
              className="px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium"
            >
              Go to Account to log in
            </button>
          </div>
        </Card>
      </div>
    )
  }

  // Loading or logged in state
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold mb-2 font-display text-ragard-textPrimary">
          Watchlist
        </h2>
        <p className="text-sm text-ragard-textSecondary">
          Track your favorite stocks
        </p>
      </div>

      {/* Add symbol form */}
      <Card>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => {
              setNewSymbol(e.target.value)
              setError(null)
            }}
            placeholder="Add symbol (e.g., TSLA)"
            className="flex-1 px-4 py-2 bg-ragard-surface border border-slate-700 rounded-md text-ragard-textPrimary placeholder-ragard-textSecondary focus:outline-none focus:ring-2 focus:ring-ragard-accent focus:border-transparent"
            maxLength={10}
            disabled={loading || !isLoggedIn}
          />
          <button
            type="submit"
            disabled={loading || !newSymbol.trim() || !isLoggedIn}
            className="px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Adding...' : 'Add'}
          </button>
        </form>
        {error && (
          <p className="mt-2 text-sm text-ragard-danger">{error}</p>
        )}
      </Card>

      {/* Watchlist items */}
      {loading && watchlistItems.length === 0 ? (
        <Card>
          <div className="flex justify-center py-8">
            <RadarLoader message="Loading watchlist..." />
          </div>
        </Card>
      ) : watchlistItems.length === 0 ? (
        <Card>
          <p className="text-center py-8 text-ragard-textSecondary">
            Your watchlist is empty. Add symbols above to get started.
          </p>
        </Card>
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-ragard-surfaceAlt/50 border-b border-slate-800">
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
                    Change
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    Regard Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ragard-textSecondary uppercase tracking-wider">
                    
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {watchlistItems.map((item) => (
                  <tr
                    key={item.item.id}
                    className="hover:bg-ragard-surfaceAlt/30 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/stocks/${item.symbol}`}
                        className="text-ragard-accent font-semibold hover:text-ragard-accent/80 transition-colors"
                      >
                        {item.symbol}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/stocks/${item.symbol}`}
                        className="text-ragard-textPrimary hover:text-ragard-accent transition-colors"
                      >
                        {item.company_name || 'N/A'}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-ragard-textPrimary">
                      {item.price !== null ? `$${item.price.toFixed(2)}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.change_pct !== null ? (
                        <span
                          className={`font-semibold ${
                            item.change_pct >= 0
                              ? 'text-ragard-success'
                              : 'text-ragard-danger'
                          }`}
                        >
                          {item.change_pct >= 0 ? '+' : ''}
                          {item.change_pct.toFixed(2)}%
                        </span>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.ragard_score !== null ? (
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12">
                            <RagardScoreGauge score={item.ragard_score} size="sm" />
                          </div>
                          <RagardScoreBadge score={item.ragard_score} showLabel={false} />
                        </div>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => removeFromWatchlist(item)}
                        className="text-ragard-danger hover:text-ragard-danger/80 transition-colors text-sm font-medium"
                        disabled={loading}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
