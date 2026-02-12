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
 */
export async function getWatchlistItems(watchlistId: string): Promise<WatchlistItem[]> {
  return callRagardAPI(`/api/watchlists/${watchlistId}/items`, {
    method: 'GET',
  })
}

/**
 * Update a watchlist name.
 */
export async function updateWatchlist(
  watchlistId: string,
  name: string
): Promise<Watchlist> {
  return callRagardAPI(`/api/watchlists/${watchlistId}`, {
    method: 'PUT',
    body: JSON.stringify({ name }),
  })
}

/**
 * Check which watchlists contain a specific ticker.
 * Returns an object with ticker and array of watchlist IDs.
 */
export async function getTickerWatchlistStatus(
  ticker: string
): Promise<{ ticker: string; watchlist_ids: string[] }> {
  return callRagardAPI(`/api/watchlists/items/status?ticker=${encodeURIComponent(ticker)}`, {
    method: 'GET',
  })
}

