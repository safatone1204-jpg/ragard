'use client'
/* eslint-disable react/no-unescaped-entities */

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import Card from '@/components/Card'

const CHROME_EXTENSION_URL = "https://chromewebstore.google.com/detail/ragard-sidebar-extension/mlenmeikgmnlonpbflbbhpicjdkddigo"

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

        {/* Main Content Area - Split View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Reddit Post Content - Left Side */}
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

          {/* Sidebar Panel - Right Side */}
          <div className="w-52 bg-[#020617] border-l border-slate-800 flex flex-col">
            {/* Sidebar Header */}
            <div className="h-10 flex items-center justify-between px-3 border-b border-slate-800/50 bg-[#0f172a]/50 flex-shrink-0">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-xs text-ragard-textPrimary">Ragard AI</span>
                <span className="text-[9px] px-1 py-0.5 bg-ragard-accent/20 rounded text-ragard-accent">BETA</span>
              </div>
              <button className="text-ragard-textSecondary text-xs w-5 h-5 flex items-center justify-center hover:text-ragard-textPrimary transition-colors">
                ⚙️
              </button>
            </div>

            {/* Sidebar Content */}
            <div className="flex-1 overflow-hidden p-3">
              {stage === 'idle' ? (
                <div className="text-center py-6">
                  <p className="text-[11px] text-ragard-textSecondary mb-3 leading-relaxed">
                    Click the button below to analyze this page.
                  </p>
                  <button 
                    id="demo-analyze-btn"
                    className="w-full px-3 py-2.5 rounded-full border-none bg-ragard-accent text-ragard-background font-semibold text-xs cursor-pointer shadow-lg transition-all hover:bg-ragard-accent/90"
                    style={{ boxShadow: '0 2px 8px rgba(34, 211, 238, 0.3)' }}
                  >
                    Analyze Page
                  </button>
                </div>
              ) : stage === 'clicking' ? (
                <div className="text-center py-6">
                  <p className="text-[11px] text-ragard-textSecondary mb-3 leading-relaxed">
                    Click the button below to analyze this page.
                  </p>
                  <button 
                    id="demo-analyze-btn"
                    className="w-full px-3 py-2.5 rounded-full border-none bg-ragard-accent text-ragard-background font-semibold text-xs cursor-pointer shadow-lg transition-all"
                    style={{ 
                      boxShadow: '0 2px 8px rgba(34, 211, 238, 0.3)',
                      transform: 'scale(0.95)'
                    }}
                  >
                    Analyze Page
                  </button>
                </div>
              ) : stage === 'analyzing' ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="flex gap-1.5 mb-2.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-ragard-accent animate-pulse"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-ragard-accent animate-pulse" style={{ animationDelay: '0.15s' }}></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-ragard-accent animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                  </div>
                  <span className="text-[11px] text-ragard-textSecondary">Analyzing...</span>
                </div>
              ) : stage === 'showing' ? (
                <div className="space-y-3 animate-fadeIn h-full flex flex-col">
                  {/* Post Info */}
                  <div className="pb-2.5 border-b border-slate-800/50">
                    <div className="text-[9px] text-ragard-textSecondary mb-0.5">
                      <span className="text-ragard-textPrimary font-medium">/r/stocks</span>
                    </div>
                    <div className="text-[11px] text-ragard-textSecondary line-clamp-2">
                      What are your thoughts on TSLA's recent earnings?
                    </div>
                  </div>

                  {/* Author Score */}
                  <div className="pb-2.5 border-b border-slate-800/50">
                    <div className="text-[9px] text-ragard-textSecondary mb-1.5">Author</div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-8 h-8 relative flex-shrink-0">
                        <svg className="w-8 h-8 transform -rotate-90" viewBox="0 0 36 36">
                          <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(34, 211, 238, 0.15)" strokeWidth="2" />
                          <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(251, 191, 36, 1)" strokeWidth="2" strokeDasharray={`${(70 / 100) * 2 * Math.PI * 13}, ${2 * Math.PI * 13}`} strokeLinecap="round" />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-[8px] font-bold text-yellow-400">70</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] font-medium text-ragard-textPrimary mb-0.5 truncate">u/stocktrader123</div>
                        <span className="inline-block px-1.5 py-0.5 bg-ragard-danger/20 text-ragard-danger text-[9px] font-semibold rounded border border-ragard-danger/30">Low Trust</span>
                      </div>
                    </div>
                  </div>

                  {/* Ticker */}
                  <div className="pb-2.5 border-b border-slate-800/50">
                    <div className="text-[9px] text-ragard-textSecondary mb-1.5 uppercase tracking-wide">Tickers</div>
                    <div className="bg-[#0b1120]/60 border border-slate-800/50 rounded-lg p-2">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-bold text-ragard-textPrimary">TSLA</span>
                        <div className="w-7 h-7 relative flex-shrink-0">
                          <svg className="w-7 h-7 transform -rotate-90" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(34, 211, 238, 0.15)" strokeWidth="2" />
                            <circle cx="18" cy="18" r="13" fill="none" stroke="rgba(251, 191, 36, 1)" strokeWidth="2" strokeDasharray={`${(62 / 100) * 2 * Math.PI * 13}, ${2 * Math.PI * 13}`} strokeLinecap="round" />
                          </svg>
                          <span className="absolute inset-0 flex items-center justify-center text-[7px] font-bold text-yellow-400">62</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-ragard-textSecondary">$245.30</span>
                        <span className="text-ragard-success font-semibold">+2.45%</span>
                      </div>
                    </div>
                  </div>

                  {/* AI Summary */}
                  <div className="pb-2.5 flex-1 min-h-0">
                    <div className="text-[9px] text-ragard-textSecondary mb-1.5 uppercase tracking-wide">AI Take</div>
                    <p className="text-[10px] text-ragard-textSecondary leading-relaxed mb-1.5 line-clamp-3">
                      Discussion focuses on earnings performance and market outlook for the stock. Analysis indicates positive sentiment around recent developments.
                    </p>
                    <span className="inline-block px-1.5 py-0.5 bg-ragard-success/20 text-ragard-success text-[9px] font-semibold rounded border border-ragard-success/30">
                      Bullish
                    </span>
                  </div>

                  {/* Action Button */}
                  <div className="pt-2 border-t border-slate-800/50 mt-auto">
                    <button className="w-full px-3 py-2.5 rounded-full border-none bg-ragard-accent text-ragard-background font-semibold text-xs cursor-pointer shadow-lg transition-all hover:bg-ragard-accent/90">
                      Full Analysis in Ragard
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {/* Cursor Animation */}
      <div className="absolute pointer-events-none z-50"
      style={{
        top: '172px',
        right: '98px',
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

