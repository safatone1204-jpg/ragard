import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | Ragard',
  description: 'Privacy Policy for Ragard - Learn how we collect, use, and protect your data when using the Ragard website, Chrome extension, and API.',
}

// Effective date - update this when the policy changes
const effectiveDate = 'January 18, 2026'

export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-slate-800">
        <h1 className="text-5xl font-bold mb-4 font-display text-ragard-textPrimary">
          Privacy Policy
        </h1>
        <p className="text-sm text-ragard-textSecondary mb-2">
          <strong>Effective Date:</strong> {effectiveDate}
        </p>
        <p className="text-sm text-ragard-textSecondary mb-4">
          <strong>Company:</strong> Ragard AI (&quot;Ragard,&quot; &quot;we,&quot; &quot;us,&quot; &quot;our&quot;)
        </p>
        <p className="text-sm text-ragard-textSecondary">
          <strong>Contact:</strong>{' '}
          <a 
            href="mailto:ragard.owner@gmail.com" 
            className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors"
          >
            ragard.owner@gmail.com
          </a>
        </p>
      </div>

      {/* Table of Contents */}
      <nav className="mb-12 p-6 bg-ragard-surface border border-slate-800 rounded-lg">
        <h2 className="text-xl font-semibold mb-4 text-ragard-textPrimary">Table of Contents</h2>
        <ul className="space-y-2 text-sm">
          <li>
            <a href="#introduction" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              1. What Ragard does
            </a>
          </li>
          <li>
            <a href="#data-we-collect" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              2. Data we collect
            </a>
          </li>
          <li>
            <a href="#what-we-store" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              3. What we store (and what we don&apos;t)
            </a>
          </li>
          <li>
            <a href="#how-we-use" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              4. How we use information
            </a>
          </li>
          <li>
            <a href="#sharing-third-parties" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              5. Sharing and third parties
            </a>
          </li>
          <li>
            <a href="#data-retention" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              6. Data retention
            </a>
          </li>
          <li>
            <a href="#your-choices" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              7. Your choices and controls
            </a>
          </li>
          <li>
            <a href="#security" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              8. Security
            </a>
          </li>
          <li>
            <a href="#children-privacy" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              9. Children&apos;s privacy
            </a>
          </li>
          <li>
            <a href="#international-users" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              10. International users
            </a>
          </li>
          <li>
            <a href="#payments" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              11. Payments (future)
            </a>
          </li>
          <li>
            <a href="#policy-changes" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              12. Changes to this policy
            </a>
          </li>
          <li>
            <a href="#contact" className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors">
              13. Contact
            </a>
          </li>
        </ul>
      </nav>

      {/* Introduction */}
      <div className="mb-8">
        <p className="text-ragard-textSecondary mb-6 leading-relaxed">
          This Privacy Policy explains how Ragard collects, uses, and shares information when you use:
        </p>
        <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 mb-8">
          <li>The Ragard website (ragardai.com)</li>
          <li>The Ragard Sidebar Extension (Chrome extension)</li>
          <li>The Ragard API (api.ragardai.com)</li>
        </ul>
      </div>

      {/* Section 1 */}
      <section id="introduction" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            1. What Ragard does
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          Ragard is a real-time stock analysis tool that analyzes public web content (e.g., posts and financial articles) when you request it, and produces derived insights such as detected tickers, summaries, and scoring.
        </p>
      </section>

      {/* Section 2 */}
      <section id="data-we-collect" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            2. Data we collect
          </h2>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-xl font-semibold mb-3 text-ragard-textPrimary">A. Information you provide</h3>
            <p className="text-ragard-textSecondary mb-4 leading-relaxed">
              <strong>Account information (website/app):</strong>
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 mb-4">
              <li>Email address (required for accounts)</li>
              <li>Name (optional)</li>
              <li>Authentication data (handled by Supabase Auth, including OAuth or email/password; passwords are hashed by Supabase)</li>
            </ul>
            <p className="text-ragard-textSecondary mb-4 leading-relaxed">
              <strong>Saved items (if logged in):</strong>
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
              <li>Watchlists and related account data you save in Ragard</li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-semibold mb-3 text-ragard-textPrimary">B. Information the extension collects (only when you click &quot;Analyze Page&quot;)</h3>
            <p className="text-ragard-textSecondary mb-4 leading-relaxed">
              The extension accesses and sends limited information to the Ragard API only when you explicitly request analysis:
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 mb-4">
              <li>URL of the page being analyzed</li>
              <li>Page title</li>
              <li>Content snippet from the page (typically up to ~4,000–12,000 characters, depending on the page and feature)</li>
            </ul>
            <p className="text-ragard-textSecondary mb-4 leading-relaxed">
              <strong>The extension does not collect:</strong>
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
              <li>Your keystrokes or form inputs</li>
              <li>Your browsing history in the background</li>
              <li>Your search queries</li>
              <li>&quot;Click tracking&quot; or behavioral analytics</li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-semibold mb-3 text-ragard-textPrimary">C. Derived analysis data</h3>
            <p className="text-ragard-textSecondary mb-4 leading-relaxed">
              Ragard generates analysis outputs such as:
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
              <li>Detected tickers (derived)</li>
              <li>Scores/ratings, summaries, and related metadata (derived)</li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-semibold mb-3 text-ragard-textPrimary">D. Settings and local storage</h3>
            <p className="text-ragard-textSecondary leading-relaxed">
              The extension may store certain preferences locally in your browser/extension storage, such as:
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
              <li>API URL configuration (production/development)</li>
              <li>User preferences (where applicable)</li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-semibold mb-3 text-ragard-textPrimary">E. Server and technical data</h3>
            <p className="text-ragard-textSecondary mb-4 leading-relaxed">
              When you use the website or API, standard web requests may include:
            </p>
            <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 mb-4">
              <li>IP address</li>
              <li>Device/browser and request metadata (e.g., timestamps, headers)</li>
            </ul>
            <p className="text-ragard-textSecondary leading-relaxed">
              We may keep this information in standard server logs for security and reliability. We do not store IP addresses in our database as part of your profile.
            </p>
          </div>
        </div>
      </section>

      {/* Section 3 */}
      <section id="what-we-store" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            3. What we store (and what we don&apos;t)
          </h2>
        </div>
        <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 leading-relaxed">
          <li>We do not store full page text from analyzed pages in our database.</li>
          <li>We store analysis results (e.g., tickers detected, scores, summaries) needed to provide features and (if applicable) show results to logged-in users.</li>
          <li>We store watchlists and account-related data if you choose to use those features.</li>
        </ul>
      </section>

      {/* Section 4 */}
      <section id="how-we-use" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            4. How we use information
          </h2>
        </div>
        <p className="text-ragard-textSecondary mb-4 leading-relaxed">
          We use information to:
        </p>
        <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
          <li>Provide and operate Ragard features (analysis, scoring, watchlists)</li>
          <li>Authenticate users and manage accounts</li>
          <li>Improve performance and reliability (debugging, error monitoring)</li>
          <li>Protect against abuse, fraud, and security risks</li>
          <li>Communicate important service updates (e.g., changes to the product or policy)</li>
        </ul>
      </section>

      {/* Section 5 */}
      <section id="sharing-third-parties" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            5. Sharing and third parties
          </h2>
        </div>
        <p className="text-ragard-textSecondary mb-6 leading-relaxed">
          We do not sell your personal information and we do not share your data with advertisers.
        </p>
        <p className="text-ragard-textSecondary mb-4 leading-relaxed">
          We may share data with service providers only as needed to run Ragard:
        </p>

        <div className="space-y-4">
          <div className="p-4 bg-ragard-surface border border-slate-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 text-ragard-textPrimary">Supabase (Database + Auth)</h3>
            <p className="text-ragard-textSecondary leading-relaxed">
              We use Supabase to store account data and watchlists and to handle authentication.
            </p>
          </div>

          <div className="p-4 bg-ragard-surface border border-slate-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 text-ragard-textPrimary">Sentry (Optional error monitoring)</h3>
            <p className="text-ragard-textSecondary leading-relaxed">
              If we enable Sentry (only when configured), error data may include technical context needed to diagnose problems. Configure this to avoid collecting unnecessary personal data.
            </p>
          </div>

          <div className="p-4 bg-ragard-surface border border-slate-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 text-ragard-textPrimary">OpenAI (Optional AI features)</h3>
            <p className="text-ragard-textSecondary leading-relaxed">
              If AI features are enabled, limited page snippets and/or derived context may be sent to OpenAI to generate analysis outputs. This only occurs when you request analysis (e.g., clicking &quot;Analyze Page&quot;).
            </p>
          </div>

          <div className="p-4 bg-ragard-surface border border-slate-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 text-ragard-textPrimary">Reddit API (Optional)</h3>
            <p className="text-ragard-textSecondary leading-relaxed">
              If enabled, Ragard may fetch Reddit content via the Reddit API to support analysis. This depends on feature configuration.
            </p>
          </div>

          <div className="p-4 bg-ragard-surface border border-slate-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 text-ragard-textPrimary">Market data</h3>
            <p className="text-ragard-textSecondary leading-relaxed">
              We may use tools like yfinance to fetch market data related to detected tickers.
            </p>
          </div>
        </div>

        <p className="text-ragard-textSecondary mt-6 leading-relaxed">
          We may also share information if required by law, to enforce our terms, or to protect safety and security.
        </p>
      </section>

      {/* Section 6 */}
      <section id="data-retention" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            6. Data retention
          </h2>
        </div>
        <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 leading-relaxed">
          <li><strong>Account data:</strong> kept until you delete your account.</li>
          <li><strong>Watchlists:</strong> kept until you delete them or delete your account.</li>
          <li><strong>Analysis results:</strong> not stored long-term as full page text; derived results may be retained to support product features.</li>
          <li><strong>Browser cache:</strong> analysis results may be cached locally in your browser for performance (e.g., ~10 minutes TTL).</li>
          <li><strong>Logs:</strong> standard server logs are typically retained for 30–90 days.</li>
          <li><strong>Sentry data:</strong> retention depends on Sentry settings.</li>
        </ul>
      </section>

      {/* Section 7 */}
      <section id="your-choices" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            7. Your choices and controls
          </h2>
        </div>
        <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2 leading-relaxed">
          <li><strong>Account deletion:</strong> You can delete your account via Supabase-supported account controls (which should remove associated user data from Ragard systems, subject to legal/security retention needs).</li>
          <li><strong>Extension data:</strong> You can remove local extension storage by removing the extension or clearing extension data via Chrome settings.</li>
          <li><strong>Opting out of analysis:</strong> If you don&apos;t click &quot;Analyze Page,&quot; the extension does not send page data to Ragard.</li>
        </ul>
      </section>

      {/* Section 8 */}
      <section id="security" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            8. Security
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          We take reasonable measures to protect information, including access controls and secure transport (HTTPS for production). No system is 100% secure, but we work to minimize risk.
        </p>
      </section>

      {/* Section 9 */}
      <section id="children-privacy" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            9. Children&apos;s privacy
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          Ragard is not directed to children under 13, and we do not knowingly collect personal information from children under 13. If you believe a child has provided personal information, contact us at{' '}
          <a 
            href="mailto:ragard.owner@gmail.com" 
            className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors"
          >
            ragard.owner@gmail.com
          </a>.
        </p>
      </section>

      {/* Section 10 */}
      <section id="international-users" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            10. International users
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          If you access Ragard from outside the United States, your information may be processed in countries where our providers operate. By using Ragard, you understand your information may be transferred and processed across borders.
        </p>
      </section>

      {/* Section 11 */}
      <section id="payments" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            11. Payments (future)
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          Ragard currently does not process payments. If we introduce paid plans in the future, we will update this policy to describe payment processing (typically via a third-party processor such as Stripe) and what data is collected for billing.
        </p>
      </section>

      {/* Section 12 */}
      <section id="policy-changes" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            12. Changes to this policy
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          We may update this Privacy Policy from time to time. We will post the updated version on this page and update the &quot;Effective date&quot; above.
        </p>
      </section>

      {/* Section 13 */}
      <section id="contact" className="mb-12 scroll-mt-8">
        <div className="mb-6 pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-semibold text-ragard-textPrimary font-display">
            13. Contact
          </h2>
        </div>
        <p className="text-ragard-textSecondary leading-relaxed">
          For privacy questions or requests, contact:{' '}
          <a 
            href="mailto:ragard.owner@gmail.com" 
            className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors"
          >
            ragard.owner@gmail.com
          </a>
        </p>
      </section>

      {/* Footer note */}
      <div className="mt-12 pt-8 border-t border-slate-800">
        <p className="text-sm text-ragard-textMuted text-center">
          Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>
    </div>
  )
}
