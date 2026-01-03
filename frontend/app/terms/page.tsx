export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-6 text-ragard-textPrimary">Terms of Service</h1>
      
      <div className="prose prose-invert max-w-none">
        <p className="text-ragard-textSecondary mb-4">
          <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
        </p>
        
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Agreement to Terms</h2>
          <p className="text-ragard-textSecondary mb-4">
            By accessing or using Ragard, you agree to be bound by these Terms of Service and all applicable laws and regulations.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Use License</h2>
          <p className="text-ragard-textSecondary mb-4">
            Permission is granted to temporarily use Ragard for personal, non-commercial use only. This is the grant of a license, not a transfer of title.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Disclaimer</h2>
          <p className="text-ragard-textSecondary mb-4">
            The information provided by Ragard is for informational purposes only and does not constitute financial advice. Trading stocks involves risk, and you should consult with a qualified financial advisor before making investment decisions.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Limitations</h2>
          <p className="text-ragard-textSecondary mb-4">
            In no event shall Ragard or its suppliers be liable for any damages arising out of the use or inability to use the service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Account Responsibilities</h2>
          <ul className="list-disc pl-6 text-ragard-textSecondary space-y-2">
            <li>You are responsible for maintaining the confidentiality of your account</li>
            <li>You are responsible for all activities under your account</li>
            <li>You must notify us immediately of any unauthorized use</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">Contact Us</h2>
          <p className="text-ragard-textSecondary">
            If you have questions about these Terms, please contact us.
          </p>
        </section>

        <p className="text-sm text-ragard-textSecondary mt-8">
          <em>Note: This is a placeholder terms of service. Please review and customize it according to your specific needs and legal requirements.</em>
        </p>
      </div>
    </div>
  )
}

