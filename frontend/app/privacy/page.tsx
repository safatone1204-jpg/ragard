export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-6 text-ragard-textPrimary">Privacy Policy</h1>
      
      <div className="prose prose-invert max-w-none">
        <p className="text-ragard-textSecondary mb-4">
          <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
        </p>
        
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Introduction</h2>
          <p className="text-ragard-textSecondary mb-4">
            This Privacy Policy describes how Ragard ("we", "our", or "us") collects, uses, and protects your personal information when you use our service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Information We Collect</h2>
          <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
            <li>Account information (email, name)</li>
            <li>Trade history data (if uploaded)</li>
            <li>Usage data and analytics</li>
            <li>Cookies and similar tracking technologies</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">How We Use Your Information</h2>
          <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
            <li>To provide and maintain our service</li>
            <li>To process your trade history and generate reports</li>
            <li>To improve our service</li>
            <li>To communicate with you</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Data Security</h2>
          <p className="text-ragard-textSecondary mb-4">
            We implement appropriate security measures to protect your personal information. However, no method of transmission over the Internet is 100% secure.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Contact Us</h2>
          <p className="text-ragard-textSecondary">
            If you have questions about this Privacy Policy, please contact us.
          </p>
        </section>

        <p className="text-sm text-ragard-textSecondary mt-8">
          <em>Note: This is a placeholder privacy policy. Please review and customize it according to your specific needs and legal requirements.</em>
        </p>
      </div>
    </div>
  )
}

