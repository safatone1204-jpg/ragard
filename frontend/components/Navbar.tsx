'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import RagardLogo from './RagardLogo'

export default function Navbar() {
  const pathname = usePathname()
  const router = useRouter()

  const navItems = [
    { href: '/', label: 'Home' },
    { href: '/narratives', label: 'Narratives' },
  ]

  const handleNavClick = (href: string, e: React.MouseEvent<HTMLAnchorElement>) => {
    // Force navigation to Home page, especially if already on it
    if (href === '/') {
      e.preventDefault()
      router.push('/')
      // Fallback to ensure navigation happens
      setTimeout(() => {
        if (window.location.pathname !== '/') {
          window.location.href = '/'
        } else {
          // Force a refresh if already on the page
          router.refresh()
        }
      }, 50)
    }
    // For other routes, let Link handle it normally
  }

  return (
    <nav className="sticky top-0 z-50 bg-ragard-surfaceAlt border-b border-slate-800 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div style={{ pointerEvents: 'auto', zIndex: 51 }}>
            <RagardLogo />
          </div>
          
          <div className="flex items-center space-x-1" style={{ pointerEvents: 'auto', zIndex: 51 }}>
            {navItems.map((item) => {
              const isActive =
                item.href === '/'
                  ? pathname === '/'
                  : pathname?.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={(e) => handleNavClick(item.href, e)}
                  className={`
                    px-4 py-2 rounded-md text-sm font-medium transition-colors
                    relative z-10 cursor-pointer
                    ${
                      isActive
                        ? 'text-ragard-textPrimary'
                        : 'text-ragard-textSecondary hover:text-ragard-textPrimary'
                    }
                    hover:underline
                  `}
                  style={{ pointerEvents: 'auto' }}
                >
                  {item.label}
                </Link>
              )
            })}
            
            {/* Account Link */}
            <Link
              href="/account"
              onClick={(e) => handleNavClick('/account', e)}
              className={`
                px-4 py-2 rounded-md text-sm font-medium transition-colors
                relative z-10 cursor-pointer
                ${
                  pathname?.startsWith('/account')
                    ? 'text-ragard-textPrimary'
                    : 'text-ragard-textSecondary hover:text-ragard-textPrimary'
                }
                hover:underline
              `}
              style={{ pointerEvents: 'auto' }}
            >
              Account
            </Link>
            
            {/* Chrome Extension Badge */}
            <Link
              href="/extension"
              className="
                px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                relative z-10 cursor-pointer
                bg-ragard-surface border border-slate-800 text-ragard-textSecondary
                hover:text-ragard-textPrimary hover:bg-ragard-surfaceAlt
                overflow-hidden
              "
              style={{ pointerEvents: 'auto' }}
              title="Analyze Reddit posts with the Ragard Chrome extension."
              role="button"
              tabIndex={0}
            >
              <span className="relative z-10">Chrome Extension</span>
              <span className="absolute inset-0 glint-animation"></span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}


