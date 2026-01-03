'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { fetchSavedAnalyses, deleteSavedAnalysis, SavedAnalysis } from '@/lib/api'
import Card from '@/components/Card'
import RadarLoader from '@/components/RadarLoader'
import RagardScoreGauge from '@/components/RagardScoreGauge'

export default function SavedAnalysesPage() {
  const router = useRouter()
  const { isLoggedIn, loading: authLoading } = useAuth()
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading) {
      if (!isLoggedIn) {
        router.push('/account')
        return
      }
      loadSavedAnalyses()
    }
  }, [isLoggedIn, authLoading, router])

  const loadSavedAnalyses = async () => {
    try {
      setLoading(true)
      setError(null)
      const analyses = await fetchSavedAnalyses()
      setSavedAnalyses(analyses)
    } catch (err) {
      console.error('Error loading saved analyses:', err)
      setError('Failed to load saved analyses')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this saved analysis?')) {
      return
    }

    try {
      setDeletingId(id)
      await deleteSavedAnalysis(id)
      setSavedAnalyses(savedAnalyses.filter(a => a.id !== id))
    } catch (err) {
      console.error('Error deleting saved analysis:', err)
      alert('Failed to delete saved analysis')
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-ragard-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <RadarLoader message="Loading saved analyses..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-ragard-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <div className="p-6">
              <div className="text-ragard-danger mb-4">
                <h2 className="text-xl font-semibold mb-2">Error</h2>
                <p>{error}</p>
              </div>
              <button
                onClick={loadSavedAnalyses}
                className="px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors"
              >
                Retry
              </button>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-ragard-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <button
            onClick={() => router.push('/account')}
            className="text-ragard-textSecondary hover:text-ragard-textPrimary mb-4 flex items-center gap-2 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Account
          </button>
          <h1 className="text-4xl font-bold font-display text-ragard-textPrimary mb-2">
            Saved Analyses
          </h1>
          <p className="text-ragard-textSecondary">
            {savedAnalyses.length} saved analysis{savedAnalyses.length !== 1 ? 'es' : ''}
          </p>
        </div>

        {savedAnalyses.length === 0 ? (
          <Card>
            <div className="p-12 text-center">
              <p className="text-ragard-textSecondary text-lg mb-4">
                No saved analyses yet.
              </p>
              <p className="text-ragard-textSecondary text-sm mb-6">
                Save analyses from the Ragard browser extension to see them here.
              </p>
              <Link
                href="/account"
                className="inline-block px-4 py-2 bg-ragard-accent text-white rounded-md hover:bg-ragard-accent/80 transition-colors"
              >
                Back to Account
              </Link>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {savedAnalyses.map((analysis) => {
              // Extract metadata from snapshot
              const snapshot = analysis.snapshot || {}
              const pageTitle = snapshot.title || analysis.title || 'Untitled'
              const pageUrl = snapshot.url || analysis.url || null
              const hostname = snapshot.hostname || analysis.hostname || (pageUrl ? new URL(pageUrl).hostname : null)
              const score = snapshot.score || analysis.score || null
              const summaryText = snapshot.summaryText || analysis.summaryText || null
              const contentType = snapshot.contentType || analysis.contentType || 'unknown'
              const tickers = snapshot.tickers || [analysis.ticker]
              const aiSentiment = snapshot.ai_sentiment || snapshot.sentiment || null
              const aiNarrative = snapshot.ai_narrative || snapshot.summary || null

              return (
                <Card key={analysis.id} className="hover:shadow-ragard-glow-sm transition-shadow">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-xl font-bold text-ragard-accent">
                            {analysis.ticker}
                          </span>
                          {score !== null && (
                            <div className="flex items-center gap-2">
                              <div className="w-10 h-10">
                                <RagardScoreGauge score={score} size="sm" />
                              </div>
                            </div>
                          )}
                          {contentType && contentType !== 'unknown' && (
                            <span className="text-xs px-2 py-1 rounded-full bg-ragard-surfaceAlt text-ragard-textSecondary border border-slate-800 capitalize">
                              {contentType}
                            </span>
                          )}
                        </div>
                        {pageTitle && (
                          <h3 className="text-lg font-semibold text-ragard-textPrimary mb-2">
                            {pageTitle}
                          </h3>
                        )}
                        {pageUrl && (
                          <a
                            href={pageUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-ragard-accent hover:text-ragard-accent/80 transition-colors mb-2 block"
                          >
                            {hostname || pageUrl}
                          </a>
                        )}
                      </div>
                      <button
                        onClick={() => handleDelete(analysis.id)}
                        disabled={deletingId === analysis.id}
                        className="ml-4 px-3 py-1.5 text-sm text-ragard-textSecondary hover:text-ragard-danger transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete saved analysis"
                      >
                        {deletingId === analysis.id ? (
                          <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>

                    {summaryText && (
                      <p className="text-sm text-ragard-textSecondary mb-3 line-clamp-3">
                        {summaryText}
                      </p>
                    )}

                    {aiNarrative && !summaryText && (
                      <p className="text-sm text-ragard-textSecondary mb-3 line-clamp-3">
                        {aiNarrative}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-xs text-ragard-textSecondary mb-3">
                      <span>Saved {formatDate(analysis.created_at)}</span>
                      {tickers.length > 1 && (
                        <span>{tickers.length} tickers</span>
                      )}
                      {aiSentiment && (
                        <span className="capitalize">{aiSentiment}</span>
                      )}
                    </div>

                    {analysis.tags && analysis.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {analysis.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="text-xs px-2 py-1 rounded-full bg-ragard-surfaceAlt text-ragard-textSecondary border border-slate-800"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {analysis.note && (
                      <div className="mt-3 pt-3 border-t border-slate-800">
                        <p className="text-sm text-ragard-textSecondary">
                          <span className="font-medium text-ragard-textPrimary">Note:</span> {analysis.note}
                        </p>
                      </div>
                    )}

                    <div className="mt-4 pt-4 border-t border-slate-800">
                      <Link
                        href={`/stocks/${analysis.ticker}`}
                        className="text-sm text-ragard-accent hover:text-ragard-accent/80 transition-colors font-medium"
                      >
                        View {analysis.ticker} profile →
                      </Link>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

