'use client'

import Link from 'next/link'
import { TickerMetrics } from '@/lib/api'
import RagardScoreGauge from './RagardScoreGauge'
import RagardScoreBadge from './RagardScoreBadge'
import RiskBadges from './RiskBadges'
import Card from './Card'

interface TickerDetailProps {
  ticker: TickerMetrics
}

export default function TickerDetail({ ticker }: TickerDetailProps) {
  const marketCapFormatted = ticker.market_cap
    ? `$${(Number(ticker.market_cap) / 1e9).toFixed(2)}B`
    : 'N/A'

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
        <div className="flex-1">
          <Link
            href="/"
            className="text-ragard-accent hover:text-ragard-accent/80 text-sm mb-4 inline-block transition-colors"
          >
            ← Back to Trending
          </Link>
          <h1 className="text-5xl font-bold mb-3 font-display text-ragard-textPrimary">
            {ticker.symbol}
            <span className="text-2xl text-ragard-textSecondary font-normal ml-3">
              {ticker.company_name}
            </span>
          </h1>
          <div className="flex flex-wrap items-center gap-6 text-ragard-textSecondary">
            <span className="text-3xl font-semibold text-ragard-textPrimary">
              ${Number(ticker.price).toFixed(2)}
            </span>
            <span
              className={`text-2xl font-semibold ${
                ticker.change_pct >= 0 ? 'text-ragard-success' : 'text-ragard-danger'
              }`}
            >
              {ticker.change_pct >= 0 ? '+' : ''}
              {Number(ticker.change_pct).toFixed(2)}%
            </span>
            <span>Market Cap: {marketCapFormatted}</span>
          </div>
        </div>
        <div className="flex flex-col items-center md:items-end">
          <div className="w-48 h-48 mb-4">
            <RagardScoreGauge score={ticker.ragard_score} size="lg" />
          </div>
          <RagardScoreBadge score={ticker.ragard_score} />
          {ticker.ragard_label && (
            <p className="text-ragard-textSecondary text-sm mt-2">
              {ticker.ragard_label}
            </p>
          )}
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Exit Liquidity Card */}
        <Card>
          <h3 className="text-lg font-semibold mb-3 text-ragard-textPrimary font-display">
            Exit Liquidity
          </h3>
          <div className="mb-4">
            <RiskBadges riskLevel={ticker.risk_level} />
          </div>
          <p className="text-ragard-textSecondary text-sm leading-relaxed">
            {ticker.exit_liquidity_rating}
          </p>
        </Card>

        {/* Hype vs Price Card */}
        <Card>
          <h3 className="text-lg font-semibold mb-3 text-ragard-textPrimary font-display">
            Hype vs Price
          </h3>
          <p className="text-ragard-textSecondary text-sm leading-relaxed">
            {ticker.hype_vs_price_text}
          </p>
        </Card>

        {/* Quick Stats Card */}
        <Card>
          <h3 className="text-lg font-semibold mb-3 text-ragard-textPrimary font-display">
            Quick Stats
          </h3>
          <div className="space-y-2 text-sm">
            {ticker.volume && (
              <div className="flex justify-between">
                <span className="text-ragard-textSecondary">Volume:</span>
                <span className="text-ragard-textPrimary">
                  {(ticker.volume / 1e6).toFixed(2)}M
                </span>
              </div>
            )}
            {ticker.float_shares && (
              <div className="flex justify-between">
                <span className="text-ragard-textSecondary">Float:</span>
                <span className="text-ragard-textPrimary">
                  {(ticker.float_shares / 1e6).toFixed(2)}M
                </span>
              </div>
            )}
            {ticker.market_cap && (
              <div className="flex justify-between">
                <span className="text-ragard-textSecondary">Market Cap:</span>
                <span className="text-ragard-textPrimary">{marketCapFormatted}</span>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

