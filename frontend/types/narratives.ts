// Types for Narratives feature
// TODO: Replace with backend API types when wiring real data

export type TimeframeKey = '24h' | '7d' | '30d'

export interface NarrativeMetrics {
  avgMovePct: number // average % move for that narrative's tickers
  upCount: number // # of tickers up
  downCount: number // # of tickers down
  heatScore: number // 0–100 heat
}

export interface Narrative {
  id: string
  title: string
  description: string
  sentiment: 'bullish' | 'bearish' | 'neutral' | 'mixed'
  tickers: string[]
  createdAt: string
  metrics: {
    [K in TimeframeKey]: NarrativeMetrics
  }
  ai_title?: string | null
  ai_summary?: string | null
  ai_sentiment?: 'bullish' | 'bearish' | 'mixed' | 'neutral' | null
}

