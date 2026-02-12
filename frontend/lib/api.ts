/**
 * API integration layer.
 * This is the only place in the frontend that knows about the backend URL.
 * All UI components must call these functions, not directly fetch from the API.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

/**
 * Central API helper that automatically includes auth token if available.
 * Use this for all authenticated API calls.
 */
export async function callRagardAPI(
  path: string,
  options: RequestInit = {}
): Promise<any> {
  const { getAccessToken } = await import('./authStorage')
  const token = await getAccessToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  // Handle 401 - unauthorized
  if (response.status === 401) {
    const { clearAccessToken } = await import('./authStorage')
    await clearAccessToken()
    // Dispatch event to notify auth context
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    throw new Error('Unauthorized - please log in again')
  }

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`)
  }

  return response.json()
}

export interface Ticker {
  symbol: string
  company_name: string
  price: number
  change_pct: number
  market_cap: number | null
  ragard_score: number | null  // Can be null if data is missing
  risk_level: string
  regard_data_completeness?: string | null  // "full" | "partial" | "unknown"
  regard_missing_factors?: string[] | null  // List of missing data fields
}

export interface TickerMetrics extends Ticker {
  volume: number | null
  float_shares: number | null
  exit_liquidity_rating: string
  hype_vs_price_text: string
  ragard_label: string | null
}

export async function fetchTrending(
  timeframe: '24h' | '7d' | '30d' = '24h',
  signal?: AbortSignal
): Promise<Ticker[]> {
  const response = await fetch(`${API_BASE_URL}/api/trending?timeframe=${timeframe}`, {
    cache: 'no-store', // Always fetch fresh data for trending
    signal: signal, // Pass the AbortSignal for timeout/cancellation
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch trending tickers: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchTicker(symbol: string): Promise<TickerMetrics | null> {
  const response = await fetch(`${API_BASE_URL}/api/tickers/${symbol}`, {
    cache: 'no-store', // Always fetch fresh data
  })

  if (!response.ok) {
    if (response.status === 404) {
      return null
    }
    throw new Error(`Failed to fetch ticker details: ${response.statusText}`)
  }

  return response.json()
}

export interface NarrativeMetrics {
  avg_move_pct: number
  up_count: number
  down_count: number
  heat_score: number
  social_buzz_score?: number | null
}

export interface Narrative {
  id: string
  name: string
  description: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  tickers: string[]
  metrics: {
    '24h': NarrativeMetrics
    '7d': NarrativeMetrics
    '30d': NarrativeMetrics
  }
  ai_title?: string | null
  ai_summary?: string | null
  ai_sentiment?: 'bullish' | 'bearish' | 'mixed' | 'neutral' | null
}

export async function fetchNarratives(
  timeframe: '24h' | '7d' | '30d' = '24h',
  signal?: AbortSignal
): Promise<Narrative[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/narratives?timeframe=${timeframe}`, {
      cache: 'no-store', // Always fetch fresh data
      signal: signal, // Pass the AbortSignal for timeout/cancellation
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch narratives: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`)
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your backend server.')
    }
    throw error
  }
}

export interface FilingSummary {
  form_type: string
  filed_at: string
  description: string | null
  edgar_url: string
}

export interface ValuationSnapshot {
  market_cap: number | null
  pe_ttm: number | null
  forward_pe: number | null
  price_to_sales: number | null
  ev_to_ebitda: number | null
  beta: number | null
  sector_pe_vs_market: number | null
  valuation_label: string | null
}

export interface FinancialHealth {
  revenue_ttm: number | null
  revenue_yoy_growth_pct: number | null
  net_income_ttm: number | null
  net_margin_pct: number | null
  debt_to_equity: number | null
  free_cash_flow_ttm: number | null
}

export interface RedditStatsForTicker {
  mention_count_24h: number
  mention_count_7d: number
  mention_count_30d: number
  top_subreddits: string[]
  top_keywords: string[]
}

export interface RagardScoreBreakdown {
  hype: number | null
  volatility: number | null
  liquidity: number | null
  risk: number | null
  hype_score: number | null
  volatility_score: number | null
  liquidity_score: number | null
  risk_score: number | null
}

export interface StockAIOverview {
  headline: string
  summary_bullets: string[]
  risk_label?: 'low' | 'medium' | 'high'
  timeframe_hint?: string | null
  regard_score_explanation?: string | null
  recent_catalysts?: string | null
  market_context?: string | null
  financial_snapshot?: string | null
  trading_context?: string | null
}

export interface CompanyProfile {
  symbol: string
  company_name: string | null
  cik: string | null
  sector: string | null
  industry: string | null
  country: string | null
  website: string | null
  description: string | null
  price: number | null
  change_pct: number | null
  valuation: ValuationSnapshot | null
  financials: FinancialHealth | null
  filings: FilingSummary[]
  reddit_stats: RedditStatsForTicker | null
  narratives: string[]
  ragard_score: number | null
  risk_level: string | null
  ragard_breakdown: RagardScoreBreakdown | null
  ai_overview?: StockAIOverview | null
  regard_data_completeness?: string | null  // "full" | "partial" | "unknown"
  regard_missing_factors?: string[] | null  // List of missing data fields
}

export interface BasicStockInfo {
  symbol: string
  company_name: string | null
  price: number | null
  change_pct: number | null
}

/**
 * Fetch basic stock information quickly (price, name, change).
 * This is a lightweight endpoint that returns fast without calculating regard scores.
 */
export async function fetchStockBasicInfo(
  symbol: string,
  signal?: AbortSignal
): Promise<BasicStockInfo> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stocks/${symbol.toUpperCase()}/basic`, {
      cache: 'no-store',
      signal: signal,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Stock not found for ${symbol}`)
      }
      throw new Error(`Failed to fetch basic stock info: ${response.status} ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`)
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your backend server.')
    }
    throw error
  }
}

export async function fetchStockProfile(
  symbol: string,
  signal?: AbortSignal
): Promise<CompanyProfile> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stocks/${symbol.toUpperCase()}`, {
      cache: 'no-store', // Always fetch fresh data
      signal: signal,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Stock profile not found for ${symbol}`)
      }
      throw new Error(`Failed to fetch stock profile: ${response.status} ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`)
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your backend server.')
    }
    throw error
  }
}

export interface AuthorAnalysis {
  author: string | null
  author_regard_score: number | null
  trust_level: 'low' | 'medium' | 'high' | null
  summary: string | null
}

export async function fetchAuthorAnalysis(
  author: string,
  signal?: AbortSignal
): Promise<AuthorAnalysis> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/reddit/author-analysis?author=${encodeURIComponent(author)}`, {
      cache: 'no-store',
      signal: signal,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch author analysis: ${response.status} ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`)
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your backend server.')
    }
    throw error
  }
}

export interface RegardHistoryEntry {
  timestamp_utc: string
  score_raw: number | null
  score_rounded: number | null
  scoring_mode: string
  ai_success: boolean
  total_posts: number
  price_at_snapshot: number | null
  change_24h_pct: number | null
  volume_24h: number | null
  market_cap: number | null
  model_version: string | null
  scoring_version: string
}

export async function fetchRegardHistory(
  ticker: string,
  days: number = 7,
  signal?: AbortSignal
): Promise<RegardHistoryEntry[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/regard-history?ticker=${encodeURIComponent(ticker)}&days=${days}`, {
      cache: 'no-store',
      signal: signal,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch Regard history: ${response.status} ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`)
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your backend server.')
    }
    throw error
  }
}

// User Account APIs
export interface UserRegardResponse {
  regardScore: number | null
  wins: number
  losses: number
  winRate: number | null
  sampleSize: number
  lastUpdated: string | null
}

export async function fetchUserRegard(): Promise<UserRegardResponse> {
  return callRagardAPI('/api/user-regard', {
    method: 'GET',
  })
}

export interface UploadProgress {
  user_id: string
  current_step: number
  total_steps: number
  percentage: number
  status: string
  message: string
  error?: string | null
  created_at: string
  updated_at: string
}

export async function getUploadProgress(): Promise<UploadProgress> {
  return callRagardAPI('/api/trade-history/progress', { method: 'GET' })
}

export async function downloadUserReport(): Promise<Blob> {
  const { getAccessToken } = await import('./authStorage')
  const token = await getAccessToken()

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/user-regard/report`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    if (response.status === 400) {
      const error = await response.json()
      throw new Error(error.detail || 'Not enough trade history to generate a report')
    }
    throw new Error(`Failed to generate report: ${response.status} ${response.statusText}`)
  }

  return response.blob()
}

export async function uploadTradeHistory(file: File): Promise<{ success: boolean; message?: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('format', 'csv')

  const { getAccessToken } = await import('./authStorage')
  const token = await getAccessToken()

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  // Don't set Content-Type - let browser set it with boundary for multipart/form-data

  const url = `${API_BASE_URL}/api/trade-history/upload`
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (response.status === 401) {
      const { clearAccessToken } = await import('./authStorage')
      await clearAccessToken()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
      throw new Error('Unauthorized - please log in again')
    }

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to upload trade history: ${response.status} ${response.statusText} - ${errorText}`)
    }

    return response.json()
  } catch (error: any) {
    // Enhanced error logging
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      console.error('Network error:', {
        url,
        apiBaseUrl: API_BASE_URL,
        error: error.message,
        stack: error.stack
      })
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running? Error: ${error.message}`)
    }
    throw error
  }
}

export interface SavedAnalysis {
  id: string
  user_id: string
  ticker: string
  snapshot: Record<string, any>
  tags: string[]
  note: string | null
  created_at: string
  // Extracted from snapshot for convenience
  url?: string
  title?: string
  hostname?: string
  score?: number
  summaryText?: string
  contentType?: string
}

export async function fetchSavedAnalyses(limit?: number): Promise<SavedAnalysis[]> {
  const url = limit ? `/api/saved-analyses?limit=${limit}` : '/api/saved-analyses'
  return callRagardAPI(url, {
    method: 'GET',
  })
}

export async function deleteSavedAnalysis(id: string): Promise<void> {
  return callRagardAPI(`/api/saved-analyses/${id}`, {
    method: 'DELETE',
  })
}
