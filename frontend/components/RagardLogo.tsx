'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface RagardLogoProps {
  className?: string
  showText?: boolean
}

export default function RagardLogo({ className = '', showText = true }: RagardLogoProps) {
  const router = useRouter()

  const handleLogoClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    router.push('/')
    // Force navigation as fallback - always go to trending
    setTimeout(() => {
      if (window.location.pathname !== '/') {
        window.location.href = '/'
      } else {
        // If already on homepage, refresh to ensure we're on trending
        router.refresh()
      }
    }, 50)
  }

  return (
    <Link 
      href="/" 
      onClick={handleLogoClick}
      className={`flex items-center space-x-3 ${className}`}
      style={{ pointerEvents: 'auto', zIndex: 100, position: 'relative' }}
    >
      {/* Radar icon - more realistic radar display */}
      <div className="relative w-10 h-10 flex items-center justify-center pointer-events-none">
        {/* Outer circle - radar screen border */}
        <div className="absolute inset-0 rounded-full bg-ragard-surface border border-ragard-accent/30"></div>
        
        {/* Concentric circles - radar range rings */}
        <div className="absolute inset-1 rounded-full border border-ragard-accent/20"></div>
        <div className="absolute inset-2 rounded-full border border-ragard-accent/15"></div>
        <div className="absolute inset-3 rounded-full border border-ragard-accent/10"></div>
        
        {/* Crosshairs - center lines */}
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Horizontal line */}
          <div className="absolute w-full h-px bg-ragard-accent/20"></div>
          {/* Vertical line */}
          <div className="absolute h-full w-px bg-ragard-accent/20"></div>
        </div>
        
        {/* Sweep line - rotating radar sweep */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div 
            className="absolute h-0.5 bg-gradient-to-r from-ragard-accent/80 to-transparent"
            style={{ 
              width: '50%',
              left: '50%',
              top: '50%',
              transform: 'translate(0, -50%) rotate(45deg)',
              transformOrigin: '0 center',
              boxShadow: '0 0 4px rgba(34, 211, 238, 0.5)'
            }}
          ></div>
        </div>
        
        {/* Center dot - radar origin */}
        <div className="absolute w-1.5 h-1.5 rounded-full bg-ragard-accent z-10"></div>
      </div>
      
      {showText && (
        <span className="font-display text-xl font-bold tracking-tight">
          <span className="text-ragard-textPrimary">Ra</span>
          <span className="text-ragard-accent">gard</span>
        </span>
      )}
    </Link>
  )
}

