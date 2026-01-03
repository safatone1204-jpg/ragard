/**
 * Watchlist API functions that use the authenticated API helper.
 */

import { callRagardAPI } from './api'

export interface Watchlist {
  id: string
  user_id: string
  name: string
  created_at: string
}

export interface WatchlistItem {
  id: string
  watchlist_id: string
  ticker: string
  created_at: string
}

/**
 * Get all watchlists for the current user.
 */
export async function fetchWatchlists(): Promise<Watchlist[]> {
  return callRagardAPI('/api/watchlists', {
    method: 'GET',
  })
}

/**
 * Create a new watchlist.
 */
export async function createWatchlist(name: string): Promise<Watchlist> {
  return callRagardAPI('/api/watchlists', {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

/**
 * Delete a watchlist.
 */
export async function deleteWatchlist(watchlistId: string): Promise<void> {
  return callRagardAPI(`/api/watchlists/${watchlistId}`, {
    method: 'DELETE',
  })
}

/**
 * Add a ticker to a watchlist.
 */
export async function addWatchlistItem(
  watchlistId: string,
  ticker: string
): Promise<WatchlistItem> {
  return callRagardAPI(`/api/watchlists/${watchlistId}/items`, {
    method: 'POST',
    body: JSON.stringify({ ticker }),
  })
}

/**
 * Remove a ticker from a watchlist.
 */
export async function removeWatchlistItem(
  watchlistId: string,
  itemId: string
): Promise<void> {
  return callRagardAPI(`/api/watchlists/${watchlistId}/items/${itemId}`, {
    method: 'DELETE',
  })
}

/**
 * Get all items for a watchlist.
 * Note: This requires a backend endpoint GET /api/watchlists/:id/items
 * For now, items are managed locally after being added.
 */
export async function getWatchlistItems(watchlistId: string): Promise<WatchlistItem[]> {
  try {
    return callRagardAPI(`/api/watchlists/${watchlistId}/items`, {
      method: 'GET',
    })
  } catch (error) {
    // If endpoint doesn't exist yet, return empty array
    console.warn('Watchlist items endpoint not available:', error)
    return []
  }
}

