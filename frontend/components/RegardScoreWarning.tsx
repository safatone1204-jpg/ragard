'use client'

import { useState, useRef, useEffect } from 'react'

interface RegardScoreWarningProps {
  dataCompleteness?: string | null
  missingFactors?: string[] | null
}

export default function RegardScoreWarning({ 
  dataCompleteness, 
  missingFactors 
}: RegardScoreWarningProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const iconRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  // Don't show warning if data is complete
  if (dataCompleteness === 'full' || !dataCompleteness) {
    return null
  }

  const handleMouseEnter = () => {
    if (iconRef.current) {
      const rect = iconRef.current.getBoundingClientRect()
      const tooltipWidth = 280
      const tooltipHeight = 150
      const spacing = 8
      
      // Position to the bottom-right of the icon
      let left = rect.right + spacing
      let top = rect.top
      
      // Adjust if tooltip would go off screen to the right
      if (left + tooltipWidth > window.innerWidth - 20) {
        left = rect.left - tooltipWidth - spacing
      }
      
      // Adjust if tooltip would go off screen to the bottom
      if (top + tooltipHeight > window.innerHeight - 20) {
        top = window.innerHeight - tooltipHeight - 20
      }
      
      // Ensure it doesn't go off screen to the left
      if (left < 20) {
        left = 20
      }
      
      // Ensure it doesn't go off screen to the top
      if (top < 20) {
        top = rect.bottom + spacing
      }
      
      setPosition({ top, left })
      setIsVisible(true)
    }
  }

  const handleMouseLeave = () => {
    setIsVisible(false)
  }

  // Format missing factors for display
  const formatMissingFactors = (factors: string[] | null | undefined): string => {
    if (!factors || factors.length === 0) {
      return 'some factors'
    }
    
    // Map technical names to user-friendly names
    const factorNames: Record<string, string> = {
      'market_cap': 'Market Cap',
      'profit_margins': 'Profit Margins',
      'beta': 'Beta (Volatility)',
      'avg_volume': 'Average Volume',
      'short_ratio': 'Short Ratio',
    }
    
    return factors.map(factor => factorNames[factor] || factor).join(', ')
  }

  const missingFactorsText = formatMissingFactors(missingFactors)

  return (
    <div className="relative inline-flex items-center">
      <div
        ref={iconRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="w-4 h-4 rounded-full bg-yellow-500/20 border border-yellow-500/40 text-yellow-500 text-xs cursor-help flex items-center justify-center hover:bg-yellow-500/30 hover:border-yellow-500/60 transition-colors flex-shrink-0"
      >
        ⚠
      </div>
      {isVisible && (
        <div
          ref={tooltipRef}
          className="fixed z-[9999] pointer-events-none"
          style={{
            top: `${position.top}px`,
            left: `${position.left}px`,
          }}
        >
          <div className="bg-ragard-surfaceAlt border border-slate-800 rounded-lg p-3 shadow-xl text-xs leading-relaxed text-ragard-textPrimary whitespace-normal min-w-[240px] max-w-[280px]">
            <div className="font-semibold text-yellow-500 mb-2 flex items-center gap-2">
              <span>⚠</span>
              <span>Score Accuracy Warning</span>
            </div>
            <p className="text-ragard-textSecondary mb-2">
              This Regard Score may be less accurate due to missing information.
            </p>
            <div className="mt-2 pt-2 border-t border-slate-800">
              <p className="text-ragard-textSecondary text-[11px]">
                <span className="font-medium text-ragard-textPrimary">Missing data:</span>{' '}
                {missingFactorsText}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
