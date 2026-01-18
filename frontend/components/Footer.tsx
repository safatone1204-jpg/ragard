import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-800 bg-ragard-surfaceAlt">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-sm text-ragard-textSecondary">
            © {new Date().getFullYear()} Ragard AI. All rights reserved.
          </div>
          <div className="flex items-center gap-6">
            <Link
              href="/privacy"
              className="text-sm text-ragard-textSecondary hover:text-ragard-accent hover:underline transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              href="/terms"
              className="text-sm text-ragard-textSecondary hover:text-ragard-accent hover:underline transition-colors"
            >
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
