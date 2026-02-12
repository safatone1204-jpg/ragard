'use client'
/* eslint-disable react/no-unescaped-entities */

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { fetchStockProfile, fetchStockBasicInfo } from '@/lib/api'
import {
  fetchWatchlists,
  createWatchlist,
  updateWatchlist,
  deleteWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
  getWatchlistItems,
  type Watchlist,
  type WatchlistItem,
} from '@/lib/watchlistAPI'
import Card from './Card'
import RagardScoreGauge from './RagardScoreGauge'
import RagardScoreBadge from './RagardScoreBadge'
import RadarLoader from './RadarLoader'

interface WatchlistItemWithData {
  item: WatchlistItem
  symbol: string
  company_name: string | null
  price: number | null
  change_pct: number | null
  ragard_score: number | null
  risk_level: string | null
  loadingScore?: boolean
}

export default function Watchlist() {
  const { isLoggedIn, loading: authLoading } = useAuth()
  const router = useRouter()
  
  // State
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [currentWatchlistId, setCurrentWatchlistId] = useState<string | null>(null)
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItemWithData[]>([])
  const [loading, setLoading] = useState(false)
  const [itemsLoading, setItemsLoading] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  // Watchlist management
  const [showCreateWatchlist, setShowCreateWatchlist] = useState(false)
  const [newWatchlistName, setNewWatchlistName] = useState('')
  const [editingWatchlistId, setEditingWatchlistId] = useState<string | null>(null)
  const [editingWatchlistName, setEditingWatchlistName] = useState('')
  
  // Prevent race conditions
  const operationInProgress = useRef(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Load watchlists when logged in
  useEffect(() => {
    if (!isLoggedIn || authLoading) {
      setWatchlists([])
      setCurrentWatchlistId(null)
      setWatchlistItems([])
      return
    }

    async function loadWatchlists() {
      try {
        setLoading(true)
        setError(null)
        const fetchedWatchlists = await fetchWatchlists()

        if (fetchedWatchlists.length === 0) {
          // Don't auto-create - let user create their first watchlist
          setWatchlists([])
          setCurrentWatchlistId(null)
        } else {
          setWatchlists(fetchedWatchlists)
          // Use first watchlist or previously selected one
          const savedWatchlistId = typeof window !== 'undefined' 
            ? localStorage.getItem('ragard_selected_watchlist_id')
            : null
          const watchlistToSelect = savedWatchlistId && fetchedWatchlists.find(w => w.id === savedWatchlistId)
            ? savedWatchlistId
            : fetchedWatchlists[0].id
          setCurrentWatchlistId(watchlistToSelect)
        }
      } catch (err: any) {
        console.error('Error loading watchlists:', err)
        setError('Failed to load watchlists. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    loadWatchlists()
  }, [isLoggedIn, authLoading])

  // Save selected watchlist to localStorage
  useEffect(() => {
    if (currentWatchlistId && typeof window !== 'undefined') {
      localStorage.setItem('ragard_selected_watchlist_id', currentWatchlistId)
    }
  }, [currentWatchlistId])

  // Load items for current watchlist
  useEffect(() => {
    if (!isLoggedIn || !currentWatchlistId) {
      setWatchlistItems([])
      return
    }

    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    async function loadItems() {
      try {
        setItemsLoading(true)
        setError(null)
        
        const items = await getWatchlistItems(currentWatchlistId)
        
        if (abortControllerRef.current?.signal.aborted) return
        
        // Show items immediately with just symbol, mark all as loading
        const initialItems: WatchlistItemWithData[] = items.map(item => ({
          item,
          symbol: item.ticker,
          company_name: null,
          price: null,
          change_pct: null,
          ragard_score: null,
          risk_level: null,
          loadingScore: true,
        }))
        
        if (!abortControllerRef.current?.signal.aborted) {
          setWatchlistItems(initialItems)
          setItemsLoading(false) // Items are now visible, stop showing full loader
        }
        
        // Now fetch basic info first (fast), then regard scores separately
        items.forEach(async (item) => {
          if (abortControllerRef.current?.signal.aborted) return
          
          // Fetch basic info first (fast)
          try {
            const basicInfo = await fetchStockBasicInfo(item.ticker, abortControllerRef.current?.signal)
            
            if (!abortControllerRef.current?.signal.aborted) {
              // Update with basic info immediately
              setWatchlistItems(prev => 
                prev.map(prevItem => 
                  prevItem.item.id === item.id
                    ? {
                        ...prevItem,
                        company_name: basicInfo.company_name,
                        price: basicInfo.price,
                        change_pct: basicInfo.change_pct,
                        // Keep loadingScore true, will update when regard score loads
                      }
                    : prevItem
                )
              )
            }
          } catch (error) {
            // If basic info fetch fails, continue anyway
            console.warn(`Failed to fetch basic info for ${item.ticker}:`, error)
          }
          
          // Now fetch full profile for regard score (slower)
          if (abortControllerRef.current?.signal.aborted) return
          
          try {
            const profile = await fetchStockProfile(item.ticker, abortControllerRef.current?.signal)
            
            if (!abortControllerRef.current?.signal.aborted) {
              // Update with regard score
              setWatchlistItems(prev => 
                prev.map(prevItem => 
                  prevItem.item.id === item.id
                    ? {
                        ...prevItem,
                        ragard_score: profile.ragard_score,
                        risk_level: profile.risk_level,
                        loadingScore: false,
                      }
                    : prevItem
                )
              )
            }
          } catch (error) {
            // If regard score fetch fails, just mark as not loading
            if (!abortControllerRef.current?.signal.aborted) {
              setWatchlistItems(prev => 
                prev.map(prevItem => 
                  prevItem.item.id === item.id
                    ? {
                        ...prevItem,
                        loadingScore: false,
                      }
                    : prevItem
                )
              )
            }
          }
        })
      } catch (error: any) {
        if (error.name === 'AbortError') {
          return // Request was cancelled
        }
        console.error('Error loading watchlist items:', error)
        setError('Failed to load watchlist items. Please try again.')
        setItemsLoading(false)
      }
    }

    loadItems()

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [currentWatchlistId, isLoggedIn])

  const currentWatchlist = watchlists.find(w => w.id === currentWatchlistId)

  const addToWatchlist = useCallback(async (symbol: string) => {
    if (operationInProgress.current) return
    
    if (!isLoggedIn) {
      setError('You must be logged in to save watchlists')
      router.push('/account')
      return
    }

    if (!currentWatchlistId) {
      setError('Please select or create a watchlist first')
      return
    }

    const upperSymbol = symbol.toUpperCase().trim()

    if (!upperSymbol) {
      setError('Please enter a valid symbol')
      return
    }

    // Check if already in watchlist (client-side check)
    if (watchlistItems.some((item) => item.item.ticker === upperSymbol)) {
      setError(`${upperSymbol} is already in this watchlist`)
      return
    }

    operationInProgress.current = true
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // Add to watchlist via API first (backend will validate the symbol)
      const newItem = await addWatchlistItem(currentWatchlistId, upperSymbol)

      // Show item immediately with just symbol, mark as loading
      const immediateItem: WatchlistItemWithData = {
        item: newItem,
        symbol: upperSymbol,
        company_name: null,
        price: null,
        change_pct: null,
        ragard_score: null,
        risk_level: null,
        loadingScore: true,
      }

      setWatchlistItems([...watchlistItems, immediateItem])
      setNewSymbol('')
      setSuccess(`${upperSymbol} added to watchlist`)
      setError(null)
      setLoading(false)
      operationInProgress.current = false

      // Fetch basic info first (fast)
      fetchStockBasicInfo(upperSymbol)
        .then((basicInfo) => {
          setWatchlistItems(prev => 
            prev.map(item => 
              item.item.id === newItem.id
                ? {
                    ...item,
                    company_name: basicInfo.company_name,
                    price: basicInfo.price,
                    change_pct: basicInfo.change_pct,
                    // Keep loadingScore true for regard score
                  }
                : item
            )
          )
        })
        .catch((err) => {
          console.warn('Error fetching basic info for added item:', err)
        })

      // Then fetch full profile for regard score (slower)
      fetchStockProfile(upperSymbol)
        .then((profile) => {
          setWatchlistItems(prev => 
            prev.map(item => 
              item.item.id === newItem.id
                ? {
                    ...item,
                    ragard_score: profile.ragard_score,
                    risk_level: profile.risk_level,
                    loadingScore: false,
                  }
                : item
            )
          )
        })
        .catch((err) => {
          console.error('Error fetching regard score for added item:', err)
          // Update to remove loading state even if fetch fails
          setWatchlistItems(prev => 
            prev.map(item => 
              item.item.id === newItem.id
                ? {
                    ...item,
                    loadingScore: false,
                  }
                : item
            )
          )
        })
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || `Symbol ${upperSymbol} not found or invalid`
      if (errorMsg.includes('already') || errorMsg.includes('duplicate') || errorMsg.includes('409')) {
        setError(`${upperSymbol} is already in this watchlist`)
      } else {
        setError(errorMsg)
      }
      console.error('Error adding to watchlist:', err)
      setLoading(false)
      operationInProgress.current = false
    }
  }, [currentWatchlistId, isLoggedIn, watchlistItems, router])

  const removeFromWatchlist = useCallback(async (item: WatchlistItemWithData) => {
    if (operationInProgress.current || !currentWatchlistId) return

    try {
      operationInProgress.current = true
      setLoading(true)
      await removeWatchlistItem(currentWatchlistId, item.item.id)
      setWatchlistItems(watchlistItems.filter((i) => i.item.id !== item.item.id))
      setSuccess(`${item.symbol} removed from watchlist`)
    } catch (err: any) {
      setError('Failed to remove item from watchlist')
      console.error('Error removing from watchlist:', err)
    } finally {
      setLoading(false)
      operationInProgress.current = false
    }
  }, [currentWatchlistId, watchlistItems])

  const handleCreateWatchlist = useCallback(async () => {
    if (!newWatchlistName.trim()) {
      setError('Watchlist name cannot be empty')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const newWatchlist = await createWatchlist(newWatchlistName.trim())
      setWatchlists([...watchlists, newWatchlist])
      setCurrentWatchlistId(newWatchlist.id)
      setNewWatchlistName('')
      setShowCreateWatchlist(false)
      setSuccess(`Watchlist "${newWatchlist.name}" created`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create watchlist')
      console.error('Error creating watchlist:', err)
    } finally {
      setLoading(false)
    }
  }, [newWatchlistName, watchlists])

  const handleUpdateWatchlist = useCallback(async (watchlistId: string) => {
    if (!editingWatchlistName.trim()) {
      setError('Watchlist name cannot be empty')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const updated = await updateWatchlist(watchlistId, editingWatchlistName.trim())
      setWatchlists(watchlists.map(w => w.id === watchlistId ? updated : w))
      setEditingWatchlistId(null)
      setEditingWatchlistName('')
      setSuccess(`Watchlist renamed to "${updated.name}"`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update watchlist')
      console.error('Error updating watchlist:', err)
    } finally {
      setLoading(false)
    }
  }, [editingWatchlistName, watchlists])

  const handleDeleteWatchlist = useCallback(async (watchlistId: string) => {
    if (!confirm('Are you sure you want to delete this watchlist? All items will be removed.')) {
      return
    }

    try {
      setLoading(true)
      setError(null)
      await deleteWatchlist(watchlistId)
      const remaining = watchlists.filter(w => w.id !== watchlistId)
      setWatchlists(remaining)
      
      if (remaining.length > 0) {
        setCurrentWatchlistId(remaining[0].id)
      } else {
        setCurrentWatchlistId(null)
        setWatchlistItems([])
      }
      setSuccess('Watchlist deleted')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to delete watchlist')
      console.error('Error deleting watchlist:', err)
    } finally {
      setLoading(false)
    }
  }, [watchlists])

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
            Watchlists
          </h2>
          <p className="text-sm text-ragard-textSecondary">
            Track your favorite stocks across multiple watchlists
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
          Watchlists
        </h2>
        <p className="text-sm text-ragard-textSecondary">
          Track your favorite stocks across multiple watchlists
        </p>
      </div>

      {/* Success/Error messages */}
      {success && (
        <div className="p-3 bg-ragard-success/20 border border-ragard-success/30 rounded-md text-ragard-success text-sm">
          {success}
        </div>
      )}
      {error && (
        <div className="p-3 bg-ragard-danger/20 border border-ragard-danger/30 rounded-md text-ragard-danger text-sm">
          {error}
        </div>
      )}

      {/* Watchlist selector */}
      {loading && watchlists.length === 0 ? (
        <Card>
          <div className="flex justify-center py-8">
            <RadarLoader message="Loading watchlists..." />
          </div>
        </Card>
      ) : (
        <Card>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-ragard-textSecondary">Watchlist:</span>
            {watchlists.length === 0 ? (
              <span className="text-sm text-ragard-textSecondary">No watchlists yet</span>
            ) : (
              <>
                {watchlists.map((wl) => (
                  <div key={wl.id} className="flex items-center gap-1">
                    {editingWatchlistId === wl.id ? (
                      <form
                        onSubmit={(e) => {
                          e.preventDefault()
                          handleUpdateWatchlist(wl.id)
                        }}
                        className="flex items-center gap-1"
                      >
                        <input
                          type="text"
                          value={editingWatchlistName}
                          onChange={(e) => setEditingWatchlistName(e.target.value)}
                          className="px-2 py-1 text-sm bg-ragard-surface border border-slate-700 rounded text-ragard-textPrimary focus:outline-none focus:ring-2 focus:ring-ragard-accent"
                          autoFocus
                          onBlur={() => {
                            setEditingWatchlistId(null)
                            setEditingWatchlistName('')
                          }}
                        />
                        <button
                          type="submit"
                          className="px-2 py-1 text-xs bg-ragard-accent text-white rounded hover:bg-ragard-accent/80"
                        >
                          ✓
                        </button>
                      </form>
                    ) : (
                      <>
                        <button
                          onClick={() => setCurrentWatchlistId(wl.id)}
                          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                            currentWatchlistId === wl.id
                              ? 'bg-ragard-accent text-white'
                              : 'bg-ragard-surfaceAlt text-ragard-textPrimary hover:bg-ragard-surfaceAlt/80'
                          }`}
                        >
                          {wl.name}
                        </button>
                        <button
                          onClick={() => {
                            setEditingWatchlistId(wl.id)
                            setEditingWatchlistName(wl.name)
                          }}
                          className="text-ragard-textSecondary hover:text-ragard-textPrimary text-xs"
                          title="Rename watchlist"
                        >
                          ✎
                        </button>
                        {watchlists.length > 1 && (
                          <button
                            onClick={() => handleDeleteWatchlist(wl.id)}
                            className="text-ragard-danger hover:text-ragard-danger/80 text-xs"
                            title="Delete watchlist"
                          >
                            ×
                          </button>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </>
            )}
            {showCreateWatchlist ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleCreateWatchlist()
                }}
                className="flex items-center gap-1"
              >
                <input
                  type="text"
                  value={newWatchlistName}
                  onChange={(e) => setNewWatchlistName(e.target.value)}
                  placeholder="Watchlist name"
                  className="px-2 py-1 text-sm bg-ragard-surface border border-slate-700 rounded text-ragard-textPrimary focus:outline-none focus:ring-2 focus:ring-ragard-accent"
                  autoFocus
                  maxLength={50}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-2 py-1 text-xs bg-ragard-accent text-white rounded hover:bg-ragard-accent/80 disabled:opacity-50"
                >
                  ✓
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateWatchlist(false)
                    setNewWatchlistName('')
                  }}
                  className="px-2 py-1 text-xs bg-ragard-surfaceAlt text-ragard-textSecondary rounded hover:bg-ragard-surfaceAlt/80"
                >
                  ×
                </button>
              </form>
            ) : (
              <button
                onClick={() => setShowCreateWatchlist(true)}
                className="px-3 py-1.5 text-sm bg-ragard-surfaceAlt text-ragard-textSecondary rounded-md hover:bg-ragard-surfaceAlt/80 transition-colors"
              >
                + New Watchlist
              </button>
            )}
          </div>
        </Card>
      )}

      {/* Add symbol form */}
      {currentWatchlistId && (
        <Card>
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => {
                setNewSymbol(e.target.value.toUpperCase())
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
        </Card>
      )}

      {/* Watchlist items */}
      {!currentWatchlistId ? (
        <Card>
          <p className="text-center py-8 text-ragard-textSecondary">
            {watchlists.length === 0
              ? 'Create your first watchlist to get started.'
              : 'Select a watchlist to view its items.'}
          </p>
        </Card>
      ) : itemsLoading && watchlistItems.length === 0 ? (
        <Card>
          <div className="flex justify-center py-8">
            <RadarLoader message="Loading watchlist..." />
          </div>
        </Card>
      ) : watchlistItems.length === 0 ? (
        <Card>
          <p className="text-center py-8 text-ragard-textSecondary">
            This watchlist is empty. Add symbols above to get started.
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
                      {item.loadingScore ? (
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 flex items-center justify-center">
                            <div className="w-8 h-8 border-2 border-ragard-accent/30 border-t-ragard-accent rounded-full animate-spin"></div>
                          </div>
                          <div className="w-16 h-5 bg-ragard-surfaceAlt/50 rounded animate-pulse"></div>
                        </div>
                      ) : item.ragard_score !== null ? (
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12">
                            <RagardScoreGauge score={item.ragard_score} size="sm" />
                          </div>
                          <RagardScoreBadge score={item.ragard_score} showLabel={false} />
                        </div>
                      ) : (
                        <span className="text-ragard-textSecondary text-sm">N/A</span>
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
