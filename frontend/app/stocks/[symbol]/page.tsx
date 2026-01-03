'use client'

import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { fetchStockProfile, fetchAuthorAnalysis, fetchRegardHistory, CompanyProfile, AuthorAnalysis, RegardHistoryEntry } from '@/lib/api'
import RadarLoader from '@/components/RadarLoader'
import Card from '@/components/Card'
import RagardScoreGauge from '@/components/RagardScoreGauge'
import RagardScoreBadge from '@/components/RagardScoreBadge'
import RiskBadges from '@/components/RiskBadges'
import RegardScoreBreakdownStrip from '@/components/RegardScoreBreakdownStrip'
import RegardHistoryChart from '@/components/RegardHistoryChart'
import RegardHistoryTable from '@/components/RegardHistoryTable'

export default function StockProfilePage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const symbol = params.symbol as string
  const author = searchParams?.get('author') || null
  const [profile, setProfile] = useState<CompanyProfile | null>(null)
  const [authorAnalysis, setAuthorAnalysis] = useState<AuthorAnalysis | null>(null)
  const [authorLoading, setAuthorLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [descriptionExpanded, setDescriptionExpanded] = useState(false)
  const [regardHistory, setRegardHistory] = useState<RegardHistoryEntry[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyDays, setHistoryDays] = useState(7)

  useEffect(() => {
    let isMounted = true
    const controller = new AbortController()

    async function loadProfile() {
      if (!symbol) return

      try {
        setLoading(true)
        setError(null)

        // Timeout set to 60 seconds (1 minute) to allow for slow backend responses
        const timeoutId = setTimeout(() => {
          if (isMounted) {
            controller.abort()
          }
        }, 60000)

        try {
          const data = await fetchStockProfile(symbol, controller.signal)
          clearTimeout(timeoutId)
          
          if (isMounted) {
            // Use the ragard_score and ragard_breakdown directly from the backend
            // The backend is the single source of truth
            setProfile(data)
            setLoading(false)
          }
        } catch (fetchErr: any) {
          clearTimeout(timeoutId)
          if (isMounted) {
            if (fetchErr.name === 'AbortError' || fetchErr.message?.includes('timeout')) {
              setError('Request timed out. The backend may be slow or unavailable. Please try refreshing.')
            } else if (fetchErr.message?.includes('Cannot connect')) {
              setError('Cannot connect to backend server. Make sure it is running on port 8000.')
            } else {
              setError(fetchErr.message || 'Failed to load stock profile')
            }
            setLoading(false)
            console.error('Error loading stock profile:', fetchErr)
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load stock profile')
          setLoading(false)
          console.error('Error loading stock profile:', err)
        }
      }
    }

    loadProfile()

    // Cleanup function
    return () => {
      isMounted = false
      controller.abort()
    }
  }, [symbol])

  // Load author analysis if author param is present
  useEffect(() => {
    let isMounted = true

    async function loadAuthorAnalysis() {
      if (!author || author.trim() === '') {
        setAuthorAnalysis(null)
        return
      }

      try {
        setAuthorLoading(true)
        const analysis = await fetchAuthorAnalysis(author)
        if (isMounted) {
          setAuthorAnalysis(analysis)
          setAuthorLoading(false)
        }
      } catch (err) {
        if (isMounted) {
          console.error('Error loading author analysis:', err)
          setAuthorAnalysis(null)
          setAuthorLoading(false)
        }
      }
    }

    loadAuthorAnalysis()

    return () => {
      isMounted = false
    }
  }, [author])

  // Load Regard history
  useEffect(() => {
    let isMounted = true

    async function loadHistory() {
      if (!symbol) return

      try {
        setHistoryLoading(true)
        const history = await fetchRegardHistory(symbol, historyDays)
        if (isMounted) {
          setRegardHistory(history)
          setHistoryLoading(false)
        }
      } catch (err) {
        if (isMounted) {
          console.error('Error loading Regard history:', err)
          setRegardHistory([])
          setHistoryLoading(false)
        }
      }
    }

    loadHistory()

    return () => {
      isMounted = false
    }
  }, [symbol, historyDays])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <RadarLoader message="Scanning this stock's profile..." />
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="p-4 rounded-lg bg-ragard-danger/20 border border-ragard-danger/30 text-ragard-danger">
          <p className="font-medium">Error loading stock profile</p>
          <p className="text-sm mt-1">{error || 'Stock profile not found'}</p>
        </div>
      </div>
    )
  }

  const marketCapFormatted = profile.valuation?.market_cap
    ? `$${(profile.valuation.market_cap / 1e9).toFixed(2)}B`
    : 'N/A'

  const descriptionPreview = profile.description
    ? profile.description.substring(0, 200)
    : null
  const descriptionFull = profile.description || null
  const showReadMore = descriptionFull && descriptionFull.length > 200

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Radar Overview Card */}
      <Card className="p-6">
        <Link
          href="/"
          className="text-ragard-accent hover:text-ragard-accent/80 text-sm mb-6 inline-block transition-colors"
        >
          ← Back to Trending
        </Link>

        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
          <div className="flex-1">
            <h1 className="text-5xl font-bold mb-3 font-display text-ragard-textPrimary">
              {profile.symbol}
              {profile.company_name && (
                <span className="text-2xl text-ragard-textSecondary font-normal ml-3">
                  {profile.company_name}
                </span>
              )}
            </h1>
            <div className="flex flex-wrap items-center gap-6 text-ragard-textSecondary">
              {profile.price !== null && (
                <span className="text-3xl font-semibold text-ragard-textPrimary">
                  ${profile.price.toFixed(2)}
                </span>
              )}
              {profile.change_pct !== null && (
                <span
                  className={`text-2xl font-semibold ${
                    profile.change_pct >= 0 ? 'text-ragard-success' : 'text-ragard-danger'
                  }`}
                >
                  {profile.change_pct >= 0 ? '+' : ''}
                  {profile.change_pct.toFixed(2)}%
                </span>
              )}
              {profile.valuation?.market_cap && (
                <span>Market Cap: {marketCapFormatted}</span>
              )}
              {profile.sector && <span>Sector: {profile.sector}</span>}
              {profile.industry && <span>Industry: {profile.industry}</span>}
              {profile.ragard_score !== null && (
                <div className="flex items-center gap-2">
                  <RagardScoreBadge score={profile.ragard_score} />
                  <span 
                    className="text-ragard-textSecondary text-xs cursor-help"
                    title="Regard Score is a 0-100 degen meter for investing in this company right now. 0 = solid, boring, low-risk; 100 = full casino, hyper-speculative. Higher = more degen / more risk."
                  >
                    ⓘ
                  </span>
                </div>
              )}
              {profile.regard_data_completeness && profile.regard_data_completeness !== 'full' && (
                <div className="text-xs text-ragard-textSecondary italic">
                  ⚠ Regard score may be less accurate: missing data for {profile.regard_missing_factors?.join(', ') || 'some factors'}.
                </div>
              )}
              {profile.risk_level && (
                <RiskBadges riskLevel={profile.risk_level} />
              )}
            </div>
          </div>
          <div className="flex flex-col items-center md:items-end">
            {profile.ragard_score !== null && (
              <div className="w-48 h-48">
                <RagardScoreGauge score={profile.ragard_score} size="lg" />
              </div>
            )}
          </div>
        </div>

        {/* Regard Score Breakdown - Degen Meter */}
        {profile.ragard_breakdown && (
          <div className="mt-6">
            <RegardScoreBreakdownStrip
              score={profile.ragard_score}
              breakdown={profile.ragard_breakdown}
            />
          </div>
        )}

        {/* AI Overview */}
        {profile.ai_overview && (
          <div className="mt-6 pt-6 border-t border-slate-800">
            <div className="mb-3">
              <h3 className="text-lg font-semibold text-ragard-textPrimary font-display">
                AI Overview
              </h3>
              <p className="text-xs text-ragard-textSecondary mt-1">
                Generated by Ragard AI – not financial advice.
              </p>
            </div>
            <div className="space-y-4">
              <p className="text-ragard-textPrimary font-medium leading-relaxed">
                {profile.ai_overview.headline}
              </p>
              <ul className="space-y-2">
                {profile.ai_overview.summary_bullets.map((bullet, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-ragard-textSecondary">
                    <span className="text-ragard-accent">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap items-center justify-center gap-3">
                {profile.ai_overview.risk_label && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      profile.ai_overview.risk_label === 'high'
                        ? 'bg-ragard-danger/20 text-ragard-danger border border-ragard-danger/30'
                        : profile.ai_overview.risk_label === 'medium'
                        ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'
                        : 'bg-ragard-success/20 text-ragard-success border border-ragard-success/30'
                    }`}
                  >
                    {profile.ai_overview.risk_label.charAt(0).toUpperCase() + profile.ai_overview.risk_label.slice(1)} Risk
                  </span>
                )}
                {profile.ai_overview.timeframe_hint && (
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-ragard-surface border border-slate-800 text-ragard-textSecondary">
                    Recommended timeframe: {profile.ai_overview.timeframe_hint}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Narratives */}
        {profile.narratives.length > 0 && (
          <div className="mt-6 pt-6 border-t border-slate-800">
            <h3 className="text-sm font-medium text-ragard-textSecondary mb-3">Narratives</h3>
            <div className="flex flex-wrap gap-2">
              {profile.narratives.map((narrative) => (
                <Link
                  key={narrative}
                  href="/narratives"
                  className="px-3 py-1 rounded-full text-xs font-medium bg-ragard-surface border border-slate-800 text-ragard-accent hover:bg-ragard-surfaceAlt transition-colors"
                >
                  {narrative}
                </Link>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Reddit Author Analysis Card */}
      {author && (
        <Card className="p-6">
          <h2 className="text-2xl font-bold mb-4 font-display text-ragard-textPrimary">
            Reddit Author Analysis
          </h2>
          {authorLoading ? (
            <div className="flex items-center justify-center py-8">
              <RadarLoader message="Analyzing author..." />
            </div>
          ) : authorAnalysis && authorAnalysis.author_regard_score !== null ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span className="text-lg font-semibold text-ragard-textPrimary">
                  {authorAnalysis.author || `u/${author}`}
                </span>
                <div className="flex items-center gap-3">
                  <RagardScoreGauge score={authorAnalysis.author_regard_score} size="sm" />
                  {authorAnalysis.trust_level && (
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        authorAnalysis.trust_level === 'high'
                          ? 'bg-ragard-success/20 text-ragard-success border border-ragard-success/30'
                          : authorAnalysis.trust_level === 'medium'
                          ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'
                          : 'bg-ragard-danger/20 text-ragard-danger border border-ragard-danger/30'
                      }`}
                    >
                      {authorAnalysis.trust_level.charAt(0).toUpperCase() + authorAnalysis.trust_level.slice(1)} Trust
                    </span>
                  )}
                </div>
              </div>
              {authorAnalysis.summary && (
                <p className="text-sm text-ragard-textSecondary leading-relaxed">
                  {authorAnalysis.summary}
                </p>
              )}
            </div>
          ) : (
            <div className="text-sm text-ragard-textSecondary italic">
              Author analysis not available.
            </div>
          )}
        </Card>
      )}

      {/* Company Profile Card */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4 font-display text-ragard-textPrimary">
          Company Profile
        </h2>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {profile.sector && (
              <div>
                <span className="text-ragard-textSecondary">Sector:</span>
                <span className="text-ragard-textPrimary ml-2">{profile.sector}</span>
              </div>
            )}
            {profile.industry && (
              <div>
                <span className="text-ragard-textSecondary">Industry:</span>
                <span className="text-ragard-textPrimary ml-2">{profile.industry}</span>
              </div>
            )}
            {profile.country && (
              <div>
                <span className="text-ragard-textSecondary">Country:</span>
                <span className="text-ragard-textPrimary ml-2">{profile.country}</span>
              </div>
            )}
            {profile.website && (
              <div>
                <span className="text-ragard-textSecondary">Website:</span>
                <a
                  href={profile.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-ragard-accent hover:text-ragard-accent/80 ml-2 transition-colors"
                >
                  {profile.website.replace(/^https?:\/\//, '')}
                </a>
              </div>
            )}
          </div>

          {profile.description && (
            <div className="mt-4">
              <p className="text-ragard-textSecondary text-sm leading-relaxed">
                {descriptionExpanded ? descriptionFull : descriptionPreview}
                {showReadMore && !descriptionExpanded && '...'}
              </p>
              {showReadMore && (
                <button
                  onClick={() => setDescriptionExpanded(!descriptionExpanded)}
                  className="text-ragard-accent hover:text-ragard-accent/80 text-sm font-medium mt-2 transition-colors"
                >
                  {descriptionExpanded ? 'Read less' : 'Read more'}
                </button>
              )}
            </div>
          )}

          {profile.cik && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <a
                href={`https://www.sec.gov/cgi-bin/browse-edgar?CIK=${profile.cik.padStart(10, '0')}&action=getcompany`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-ragard-accent hover:text-ragard-accent/80 text-sm font-medium transition-colors inline-flex items-center gap-2"
              >
                View on EDGAR →
              </a>
            </div>
          )}
        </div>
      </Card>

      {/* Valuation & Financial Health - Side by Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Valuation Snapshot */}
        <Card className="p-6">
          <h2 className="text-2xl font-bold mb-4 font-display text-ragard-textPrimary">
            Valuation Snapshot
          </h2>
          {profile.valuation ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {profile.valuation.pe_ttm !== null && (
                  <div>
                    <span className="text-ragard-textSecondary">P/E (TTM):</span>
                    <span className="text-ragard-textPrimary ml-2 font-medium">
                      {profile.valuation.pe_ttm.toFixed(2)}
                    </span>
                  </div>
                )}
                {profile.valuation.forward_pe !== null && (
                  <div>
                    <span className="text-ragard-textSecondary">Forward P/E:</span>
                    <span className="text-ragard-textPrimary ml-2 font-medium">
                      {profile.valuation.forward_pe.toFixed(2)}
                    </span>
                  </div>
                )}
                {profile.valuation.price_to_sales !== null && (
                  <div>
                    <span className="text-ragard-textSecondary">P/S:</span>
                    <span className="text-ragard-textPrimary ml-2 font-medium">
                      {profile.valuation.price_to_sales.toFixed(2)}
                    </span>
                  </div>
                )}
                {profile.valuation.ev_to_ebitda !== null && (
                  <div>
                    <span className="text-ragard-textSecondary">EV/EBITDA:</span>
                    <span className="text-ragard-textPrimary ml-2 font-medium">
                      {profile.valuation.ev_to_ebitda.toFixed(2)}
                    </span>
                  </div>
                )}
                {profile.valuation.beta !== null && (
                  <div>
                    <span className="text-ragard-textSecondary">Beta:</span>
                    <span className="text-ragard-textPrimary ml-2 font-medium">
                      {profile.valuation.beta.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
              {profile.valuation.valuation_label && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-ragard-surface border border-slate-800 text-ragard-textPrimary">
                    {profile.valuation.valuation_label}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-ragard-textSecondary text-sm">Valuation data not available</p>
          )}
        </Card>

        {/* Financial Health */}
        <Card className="p-6">
          <h2 className="text-2xl font-bold mb-4 font-display text-ragard-textPrimary">
            Financial Health
          </h2>
          {profile.financials ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              {profile.financials.revenue_ttm !== null && (
                <div>
                  <span className="text-ragard-textSecondary">Revenue (TTM):</span>
                  <span className="text-ragard-textPrimary ml-2 font-medium">
                    ${(profile.financials.revenue_ttm / 1e9).toFixed(2)}B
                  </span>
                </div>
              )}
              {profile.financials.revenue_yoy_growth_pct !== null && (
                <div>
                  <span className="text-ragard-textSecondary">Revenue Growth (YoY):</span>
                  <span
                    className={`ml-2 font-medium ${
                      profile.financials.revenue_yoy_growth_pct >= 0
                        ? 'text-ragard-success'
                        : 'text-ragard-danger'
                    }`}
                  >
                    {profile.financials.revenue_yoy_growth_pct >= 0 ? '+' : ''}
                    {profile.financials.revenue_yoy_growth_pct.toFixed(2)}%
                  </span>
                </div>
              )}
              {profile.financials.net_income_ttm !== null && (
                <div>
                  <span className="text-ragard-textSecondary">Net Income (TTM):</span>
                  <span className="text-ragard-textPrimary ml-2 font-medium">
                    ${(profile.financials.net_income_ttm / 1e9).toFixed(2)}B
                  </span>
                </div>
              )}
              {profile.financials.net_margin_pct !== null && (
                <div>
                  <span className="text-ragard-textSecondary">Net Margin:</span>
                  <span className="text-ragard-textPrimary ml-2 font-medium">
                    {profile.financials.net_margin_pct.toFixed(2)}%
                  </span>
                </div>
              )}
              {profile.financials.debt_to_equity !== null && (
                <div>
                  <span className="text-ragard-textSecondary">Debt/Equity:</span>
                  <span className="text-ragard-textPrimary ml-2 font-medium">
                    {profile.financials.debt_to_equity.toFixed(2)}
                  </span>
                </div>
              )}
              {profile.financials.free_cash_flow_ttm !== null && (
                <div>
                  <span className="text-ragard-textSecondary">FCF (TTM):</span>
                  <span className="text-ragard-textPrimary ml-2 font-medium">
                    ${(profile.financials.free_cash_flow_ttm / 1e9).toFixed(2)}B
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-ragard-textSecondary text-sm">Financial data not available</p>
          )}
        </Card>
      </div>

      {/* SEC Filings - Compact */}
      {profile.filings.length > 0 && (
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-3 font-display text-ragard-textPrimary">
            Recent SEC Filings
          </h2>
          <div className="space-y-2">
            {profile.filings.slice(0, 3).map((filing, index) => (
              <div
                key={index}
                className="flex items-center justify-between gap-3 py-2 border-b border-slate-800 last:border-0"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-ragard-surfaceAlt text-ragard-accent whitespace-nowrap">
                    {filing.form_type}
                  </span>
                  <span className="text-ragard-textSecondary text-xs">
                    {new Date(filing.filed_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </span>
                </div>
                <a
                  href={filing.edgar_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-ragard-accent hover:text-ragard-accent/80 text-xs transition-colors whitespace-nowrap"
                >
                  View →
                </a>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Reddit / Narrative Lens */}
      {profile.reddit_stats && (
        <Card className="p-6">
          <h2 className="text-2xl font-bold mb-4 font-display text-ragard-textPrimary">
            Reddit Activity
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 rounded-lg bg-ragard-surfaceAlt border border-slate-800">
                <div className="text-2xl font-bold text-ragard-textPrimary">
                  {profile.reddit_stats.mention_count_24h}
                </div>
                <div className="text-sm text-ragard-textSecondary mt-1">24H Mentions</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-ragard-surfaceAlt border border-slate-800">
                <div className="text-2xl font-bold text-ragard-textPrimary">
                  {profile.reddit_stats.mention_count_7d}
                </div>
                <div className="text-sm text-ragard-textSecondary mt-1">7D Mentions</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-ragard-surfaceAlt border border-slate-800">
                <div className="text-2xl font-bold text-ragard-textPrimary">
                  {profile.reddit_stats.mention_count_30d}
                </div>
                <div className="text-sm text-ragard-textSecondary mt-1">30D Mentions</div>
              </div>
            </div>

            {profile.reddit_stats.top_subreddits.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-ragard-textSecondary mb-2">
                  Top Subreddits
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profile.reddit_stats.top_subreddits.map((subreddit) => (
                    <span
                      key={subreddit}
                      className="px-3 py-1 rounded-full text-xs font-medium bg-ragard-surface border border-slate-800 text-ragard-textPrimary"
                    >
                      r/{subreddit}
                    </span>
                  ))}
                </div>
              </div>
            )}

          </div>
        </Card>
      )}

      {/* Regard Score History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold font-display text-ragard-textPrimary">
            Regard Score History
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-ragard-textSecondary">Days:</span>
            <select
              value={historyDays}
              onChange={(e) => setHistoryDays(Number(e.target.value))}
              className="bg-ragard-surface border border-slate-800 rounded px-3 py-1 text-sm text-ragard-textPrimary focus:outline-none focus:ring-2 focus:ring-ragard-accent"
            >
              <option value={7}>7</option>
              <option value={14}>14</option>
              <option value={30}>30</option>
              <option value={60}>60</option>
              <option value={90}>90</option>
            </select>
          </div>
        </div>
        <p className="text-xs text-ragard-textSecondary mb-6">
          Historical snapshots of Regard scores over time. Each point represents a score calculation with market context.
        </p>

        {historyLoading ? (
          <div className="flex items-center justify-center py-8">
            <RadarLoader message="Loading history..." />
          </div>
        ) : regardHistory.length > 0 ? (
          <div className="space-y-6">
            {/* Chart */}
            <div>
              <h3 className="text-sm font-medium text-ragard-textSecondary mb-3">Score Trend</h3>
              <RegardHistoryChart history={regardHistory} />
            </div>

            {/* Table */}
            <div>
              <h3 className="text-sm font-medium text-ragard-textSecondary mb-3">Detailed History</h3>
              <RegardHistoryTable history={regardHistory} />
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-ragard-textSecondary">
            <p>No historical data available for this ticker yet.</p>
            <p className="text-xs mt-2">History will appear as scores are calculated.</p>
          </div>
        )}
      </Card>
    </div>
  )
}

