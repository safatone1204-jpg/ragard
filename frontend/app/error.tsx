'use client'

import { useEffect } from 'react'
import Link from 'next/link'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Application error:', error)
    }
    // In production, you could send this to an error tracking service
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-ragard-background">
      <div className="max-w-md w-full mx-4">
        <div className="bg-ragard-surface border border-slate-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-ragard-textPrimary mb-4">
            Something went wrong
          </h2>
          <p className="text-ragard-textSecondary mb-4">
            We encountered an unexpected error. Please try again.
          </p>
          <div className="flex gap-4">
            <button
              onClick={reset}
              className="px-4 py-2 bg-ragard-accent text-white rounded-lg hover:bg-ragard-accent/80 transition-colors"
            >
              Try Again
            </button>
            <Link
              href="/"
              className="px-4 py-2 bg-ragard-surfaceAlt border border-slate-800 text-ragard-textPrimary rounded-lg hover:bg-ragard-surface transition-colors"
            >
              Go Home
            </Link>
          </div>
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4">
              <summary className="text-sm text-ragard-textSecondary cursor-pointer">
                Error Details (Development Only)
              </summary>
              <pre className="mt-2 text-xs bg-slate-900 p-3 rounded overflow-auto">
                {error.toString()}
                {error.stack}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}

