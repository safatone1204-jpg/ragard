import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h2 className="text-4xl font-bold mb-4">404</h2>
      <p className="text-gray-400 mb-6">Ticker not found</p>
      <Link
        href="/"
        className="text-primary-400 hover:text-primary-300 font-medium"
      >
        ← Back to Trending
      </Link>
    </div>
  )
}

