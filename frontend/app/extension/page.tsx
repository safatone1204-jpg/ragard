'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import Card from '@/components/Card'

// TODO: Replace with actual Chrome Web Store URL when extension is published
const CHROME_EXTENSION_URL = "https://chromewebstore.google.com/detail/ragard-extension-placeholder"

// Extension Demo Component
function ExtensionDemo() {
  const [stage, setStage] = useState<'idle' | 'clicking' | 'analyzing' | 'showing'>('idle')
  const [isCursorAnimating, setIsCursorAnimating] = useState(false)
  const stageRef = useRef(stage)
  
  // Keep ref in sync with state
  useEffect(() => {
    stageRef.current = stage
  }, [stage])

  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = []
    
    const runSequence = () => {
      setStage('idle')
      setIsCursorAnimating(false)
      timeouts.push(setTimeout(() => {
        setStage('clicking')
        setIsCursorAnimating(true)
        // Change to analyzing stage exactly when click happens (594ms)
        // The click scale animation happens at 33% of the 1.8s animation
        timeouts.push(setTimeout(() => {
          // Force immediate state update when click happens
          setStage('analyzing') // Show loading dots immediately when click happens
          // Keep animation running until it completes (1.8s total)
          timeouts.push(setTimeout(() => {
            setIsCursorAnimating(false)
            timeouts.push(setTimeout(() => {
              setStage('showing') // Show analysis results
              timeouts.push(setTimeout(() => {
                runSequence()
              }, 6000))
            }, 0))
          }, 1206)) // Remaining time after click (1.8s - 0.594s = 1.206s)
        }, 594)) // Start analyzing exactly when click happens (33% of 1.8s = 0.594s)
      }, 2000))
    }

    runSequence()
    return () => {
      timeouts.forEach(timeout => clearTimeout(timeout))
    }
  }, [])

  return (
    <div className="w-full h-full bg-slate-950 relative overflow-hidden pointer-events-none">
      {/* Browser Window Frame */}
      <div className="absolute inset-0 flex flex-col">
        {/* Browser Header */}
        <div className="h-10 bg-slate-900 border-b border-slate-800 flex items-center gap-2 px-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-slate-700"></div>
            <div className="w-3 h-3 rounded-full bg-slate-700"></div>
            <div className="w-3 h-3 rounded-full bg-slate-700"></div>
          </div>
          <div className="flex-1 h-6 bg-slate-800 rounded mx-4 flex items-center px-3">
            <span className="text-[10px] text-slate-500">reddit.com/r/example/post</span>
          </div>
        </div>

        {/* Reddit Post Content */}
        <div className="flex-1 p-6 bg-slate-900 overflow-hidden">
          <div className="max-w-2xl mx-auto space-y-4 h-full">
            {/* Post Header */}
            <div className="flex items-start gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center overflow-hidden p-1">
                <img 
                  src="https://www.redditstatic.com/desktop2x/img/id-cards/snoo-avatar.svg" 
                  alt="Reddit Snoo" 
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    // Fallback if image doesn't load
                    const target = e.target as HTMLImageElement
                    target.style.display = 'none'
                    const parent = target.parentElement
                    if (parent) {
                      parent.innerHTML = `
                        <div class="w-full h-full bg-white rounded-full flex items-center justify-center">
                          <div class="w-4 h-4 bg-orange-500 rounded-full"></div>
                        </div>
                      `
                    }
                  }}
                />
              </div>
              <div className="flex-1">
                <div className="text-xs font-medium text-slate-300 mb-0.5">r/stocks</div>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="text-slate-300 hover:text-slate-200">u/stocktrader123</span>
                  <span>•</span>
                  <span>2 hours ago</span>
                </div>
              </div>
            </div>
            
            {/* Post Title */}
            <h2 className="text-lg font-semibold text-slate-200 mb-3 leading-tight">
              What are your thoughts on TSLA's recent earnings?
            </h2>
            
            {/* Post Body */}
            <div className="space-y-2.5 mb-4">
              <div className="h-3.5 bg-slate-700/70 rounded w-full"></div>
              <div className="h-3.5 bg-slate-700/70 rounded w-5/6"></div>
              <div className="h-3.5 bg-slate-700/70 rounded w-4/5"></div>
              <div className="h-3.5 bg-slate-700/70 rounded w-full"></div>
            </div>
            
            {/* Post Actions */}
            <div className="flex items-center gap-4 pt-2 border-t border-slate-800">
              <div className="h-4 w-16 bg-slate-700/50 rounded"></div>
              <div className="h-4 w-16 bg-slate-700/50 rounded"></div>
              <div className="h-4 w-16 bg-slate-700/50 rounded"></div>
            </div>

            {/* Post Actions */}
            <div className="flex items-center gap-4 pt-2">
              <div className="h-4 w-16 bg-slate-700/50 rounded"></div>
              <div className="h-4 w-16 bg-slate-700/50 rounded"></div>
              <div className="h-4 w-16 bg-slate-700/50 rounded"></div>
            </div>

            {/* Comments Section */}
            <div className="pt-2 border-t border-slate-800 space-y-3">
              <div className="h-4 w-32 bg-slate-700/50 rounded"></div>
              
              {/* Comment 1 */}
              <div className="space-y-1.5 pl-4 border-l-2 border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-slate-700"></div>
                  <div className="h-2.5 w-20 bg-slate-700/50 rounded"></div>
                </div>
                <div className="space-y-1">
                  <div className="h-3 bg-slate-700/60 rounded w-full"></div>
                  <div className="h-3 bg-slate-700/60 rounded w-5/6"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Extension Popup */}
      <div className={`absolute top-12 right-4 transition-all duration-500 ease-out pointer-events-none ${
        stage === 'idle' || stage === 'clicking' || stage === 'analyzing' || stage === 'showing'
          ? 'opacity-100 translate-y-0'
          : 'opacity-0 -translate-y-2'
      }`}>
        <div className="bg-ragard-surface border border-slate-800 rounded-lg shadow-2xl overflow-hidden w-52">
          {/* Header */}
          <div className="flex items-center justify-between px-2.5 py-1.5 border-b border-slate-800 bg-ragard-surfaceAlt/30">
            <div className="flex items-center gap-1">
              <span className="text-[10px] font-semibold text-ragard-textPrimary">Ragard AI</span>
              <span className="px-1 py-0.5 bg-ragard-success text-ragard-background text-[7px] font-bold rounded">BETA</span>
            </div>
            <div className="w-2.5 h-2.5 text-pink-400">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                <path d="M16,12V4H17V2H7V4H8V12L6,14V16H11.2V22H12.8V16H18V14L16,12Z" />
              </svg>
            </div>
          </div>

          {/* Content */}
          <div className="p-2.5">
            {stage === 'idle' ? (
              <div className="space-y-2.5 text-center py-0.5">
                <p className="text-[9px] text-ragard-textSecondary leading-relaxed">
                  Click the button below to analyze this Reddit post.
                </p>
                <div className="w-full px-2.5 py-1.5 bg-ragard-success text-ragard-background rounded-lg font-semibold text-[10px] shadow-lg">
                  Analyze Post
                </div>
              </div>
            ) : stage === 'clicking' ? (
              <div className="space-y-2.5 text-center py-0.5">
                <p className="text-[9px] text-ragard-textSecondary leading-relaxed">
                  Click the button below to analyze this Reddit post.
                </p>
                <div className="w-full px-2.5 py-1.5 bg-ragard-success text-ragard-background rounded-lg font-semibold text-[10px] shadow-lg">
                  Analyze Post
                </div>
              </div>
            ) : stage === 'analyzing' ? (
              <div className="flex items-center gap-2 py-4">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-ragard-accent animate-pulse"></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-ragard-accent animate-pulse" style={{ animationDelay: '0.15s' }}></div>
                  <div className="w-1.5 h-1.5 rounded-full bg-ragard-accent animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                </div>
                <span className="text-[9px] text-ragard-textSecondary">Analyzing...</span>
              </div>
            ) : stage === 'showing' ? (
              <div className="space-y-2.5 animate-fadeIn py-1">
                {/* Post Info */}
                <div className="space-y-0.5 pb-1.5 border-b border-slate-800">
                  <div className="text-[8px] text-ragard-textSecondary">
                    <span className="text-ragard-textPrimary font-medium">/r/stocks</span>
                  </div>
                  <div className="text-[8px] text-ragard-textSecondary line-clamp-1">
                    What are your thoughts on TSLA's recent earnings?
                  </div>
                </div>

                {/* Author Score */}
                <div className="flex items-center gap-1.5 pb-1.5 border-b border-slate-800">
                  <div className="text-[8px] text-ragard-textSecondary">Author:</div>
                  <div className="w-6 h-6 relative">
                    <svg className="w-6 h-6 transform -rotate-90" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(34, 211, 238, 0.15)" strokeWidth="2" />
                      <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(251, 191, 36, 1)" strokeWidth="2" strokeDasharray={`${(70 / 100) * 2 * Math.PI * 13}, ${2 * Math.PI * 13}`} strokeLinecap="round" />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-[7px] font-bold text-yellow-400">70</span>
                  </div>
                  <span className="text-[8px] px-1 py-0.5 bg-ragard-danger/20 text-ragard-danger rounded border border-ragard-danger/30">Low Trust</span>
                </div>

                {/* Ticker */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-ragard-textPrimary">TSLA</span>
                    <div className="w-7 h-7 relative">
                      <svg className="w-7 h-7 transform -rotate-90" viewBox="0 0 36 36">
                        <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(34, 211, 238, 0.15)" strokeWidth="2" />
                        <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(251, 191, 36, 1)" strokeWidth="2" strokeDasharray={`${(62 / 100) * 2 * Math.PI * 13}, ${2 * Math.PI * 13}`} strokeLinecap="round" />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-[7px] font-bold text-yellow-400">62</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[8px]">
                    <span className="text-ragard-textSecondary">$245.30</span>
                    <span className="text-ragard-success font-semibold">+2.45%</span>
                  </div>
                </div>

                {/* AI Summary */}
                <div className="space-y-1 pt-1.5 border-t border-slate-800">
                  <div className="text-[8px] font-semibold text-ragard-textSecondary uppercase">AI Take</div>
                  <p className="text-[8px] text-ragard-textSecondary leading-relaxed line-clamp-3">
                    Discussion focuses on earnings performance and market outlook for the stock. Analysis indicates positive sentiment around recent developments.
                  </p>
                  <span className="inline-block px-1 py-0.5 bg-ragard-success/20 text-ragard-success text-[7px] font-semibold rounded border border-ragard-success/30 mt-1">
                    Bullish
                  </span>
                </div>

                {/* Action Button */}
                <div className="w-full mt-2 px-2.5 py-1.5 bg-ragard-success text-ragard-background rounded text-[9px] font-semibold text-center">
                  Full Analysis in Ragard
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Cursor Animation */}
      <div className="absolute pointer-events-none z-50"
      style={{
        top: '140px',
        right: '250px',
        opacity: 1,
        animation: isCursorAnimating ? 'cursorMoveAndClick 1.8s cubic-bezier(0.4, 0, 0.2, 1) forwards' : 'none'
      }}>
        <svg 
          width="24" 
          height="24" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-lg"
          style={{
            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))'
          }}
        >
          <path 
            d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z" 
            fill="white" 
            stroke="black" 
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  )
}

export default function ExtensionPage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div className="space-y-6">
          <h1 className="text-5xl font-bold font-display text-ragard-textPrimary">
            Ragard Chrome Extension
          </h1>
          <p className="text-xl text-ragard-textSecondary">
            Get instant Regard Scores and AI analysis for any Reddit post.
          </p>
          <div className="space-y-3">
            <a
              href={CHROME_EXTENSION_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="
                inline-block px-6 py-3 rounded-lg
                bg-ragard-accent text-ragard-background
                font-semibold text-base
                hover:bg-ragard-accent/90 transition-colors
                shadow-lg hover:shadow-ragard-glow-sm
              "
            >
              Add to Chrome
            </a>
            <p className="text-xs text-ragard-textSecondary">
              Works on Chrome, Brave, Edge, and other Chromium browsers.
            </p>
          </div>
        </div>
        <div className="relative">
          <div className="aspect-[4/3] bg-ragard-surfaceAlt border border-slate-800 rounded-lg overflow-hidden relative">
            <ExtensionDemo />
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="space-y-6">
        <h2 className="text-3xl font-bold font-display text-ragard-textPrimary">
          How it works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-ragard-accent text-ragard-background flex items-center justify-center font-bold text-sm">
                1
              </div>
              <h3 className="text-lg font-semibold text-ragard-textPrimary">
                Install the extension
              </h3>
            </div>
            <p className="text-sm text-ragard-textSecondary">
              Add the Ragard extension from the Chrome Web Store.
            </p>
          </Card>

          <Card className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-ragard-accent text-ragard-background flex items-center justify-center font-bold text-sm">
                2
              </div>
              <h3 className="text-lg font-semibold text-ragard-textPrimary">
                Visit a Reddit post
              </h3>
            </div>
            <p className="text-sm text-ragard-textSecondary">
              Navigate to any Reddit post. The extension automatically scans the post for ticker symbols.
            </p>
          </Card>

          <Card className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-ragard-accent text-ragard-background flex items-center justify-center font-bold text-sm">
                3
              </div>
              <h3 className="text-lg font-semibold text-ragard-textPrimary">
                Get the verdict instantly
              </h3>
            </div>
            <p className="text-sm text-ragard-textSecondary">
              See its Regard Score, price action snapshot, and key narratives. Click through to the full page in Ragard.
            </p>
          </Card>
        </div>
      </div>

      {/* What It Does Section */}
      <div className="space-y-6">
        <h2 className="text-3xl font-bold font-display text-ragard-textPrimary">
          What the extension does for you
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="space-y-2">
            <h3 className="text-lg font-semibold text-ragard-textPrimary">
              Instant analysis on Reddit posts
            </h3>
            <p className="text-sm text-ragard-textSecondary">
              No more tab-hopping. Get ticker context and AI insights directly on any Reddit post.
            </p>
          </Card>

          <Card className="space-y-2">
            <h3 className="text-lg font-semibold text-ragard-textPrimary">
              Same Regard Score, new surface
            </h3>
            <p className="text-sm text-ragard-textSecondary">
              See the same scoring logic you trust in the app, directly in your browsing flow.
            </p>
          </Card>

          <Card className="space-y-2">
              <h3 className="text-lg font-semibold text-ragard-textPrimary">
                Works on Reddit
              </h3>
            <p className="text-sm text-ragard-textSecondary">
              Automatically analyzes any Reddit post you're viewing. No manual selection needed—just click "Analyze Post."
            </p>
          </Card>

          <Card className="space-y-2">
            <h3 className="text-lg font-semibold text-ragard-textPrimary">
              One-click deep dive
            </h3>
            <p className="text-sm text-ragard-textSecondary">
              Jump from the popup straight into the full Ragard view for that ticker.
            </p>
          </Card>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="space-y-6">
        <h2 className="text-3xl font-bold font-display text-ragard-textPrimary">
          FAQ
        </h2>
        <div className="space-y-4">
          <Card className="space-y-2">
            <h3 className="text-lg font-semibold text-ragard-textPrimary">
              Is the extension free?
            </h3>
            <p className="text-sm text-ragard-textSecondary">
              Yes. The extension is free to install and use. Some advanced features may require a Ragard account, but you can see basic information without paying.
            </p>
          </Card>

          <Card className="space-y-2">
            <h3 className="text-lg font-semibold text-ragard-textPrimary">
              What data does the extension read?
            </h3>
            <p className="text-sm text-ragard-textSecondary">
              The extension only reads the current Reddit post to detect ticker symbols and analyze the content. It does not access passwords, your Reddit account, or any sensitive data.
            </p>
          </Card>

          <Card className="space-y-2">
            <h3 className="text-lg font-semibold text-ragard-textPrimary">
              Which browsers are supported?
            </h3>
            <p className="text-sm text-ragard-textSecondary">
              Any Chromium-based browser that supports Chrome extensions, including Chrome, Brave, and Edge.
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}

