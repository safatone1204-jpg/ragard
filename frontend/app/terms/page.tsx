import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Terms of Service | Ragard',
  description: 'Terms of Service for Ragard - The legal agreement governing your use of the Ragard website, Chrome extension, and API.',
}

const effectiveDate = 'February 5, 2026'

export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-slate-800">
        <h1 className="text-5xl font-bold mb-4 font-display text-ragard-textPrimary">
          Terms of Service
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
          <li><a href="#agreement" className="text-ragard-accent hover:underline">1. Agreement to Terms</a></li>
          <li><a href="#eligibility" className="text-ragard-accent hover:underline">2. Eligibility</a></li>
          <li><a href="#services" className="text-ragard-accent hover:underline">3. Description of Services</a></li>
          <li><a href="#accounts" className="text-ragard-accent hover:underline">4. Accounts and Registration</a></li>
          <li><a href="#acceptable-use" className="text-ragard-accent hover:underline">5. Acceptable Use</a></li>
          <li><a href="#intellectual-property" className="text-ragard-accent hover:underline">6. Intellectual Property</a></li>
          <li><a href="#disclaimer" className="text-ragard-accent hover:underline">7. No Financial or Investment Advice</a></li>
          <li><a href="#disclaimers" className="text-ragard-accent hover:underline">8. Disclaimers</a></li>
          <li><a href="#limitation" className="text-ragard-accent hover:underline">9. Limitation of Liability</a></li>
          <li><a href="#indemnification" className="text-ragard-accent hover:underline">10. Indemnification</a></li>
          <li><a href="#termination" className="text-ragard-accent hover:underline">11. Termination</a></li>
          <li><a href="#governing-law" className="text-ragard-accent hover:underline">12. Governing Law and Disputes</a></li>
          <li><a href="#changes" className="text-ragard-accent hover:underline">13. Changes to Terms</a></li>
          <li><a href="#general" className="text-ragard-accent hover:underline">14. General Provisions</a></li>
          <li><a href="#contact" className="text-ragard-accent hover:underline">15. Contact</a></li>
        </ul>
      </nav>

      <div className="prose prose-invert max-w-none text-ragard-textSecondary space-y-8">
        <section id="agreement">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">1. Agreement to Terms</h2>
          <p className="leading-relaxed">
            These Terms of Service (&quot;Terms&quot;) constitute a legally binding agreement between you (&quot;you,&quot; &quot;your,&quot; or &quot;User&quot;) and Ragard AI governing your access to and use of the Ragard website at ragardai.com, the Ragard Chrome extension (Ragard Sidebar Extension), the Ragard API, and any related services, features, content, or applications (collectively, the &quot;Services&quot;). By accessing or using the Services, you agree that you have read, understood, and agree to be bound by these Terms. If you do not agree to these Terms, you may not access or use the Services.
          </p>
        </section>

        <section id="eligibility">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">2. Eligibility</h2>
          <p className="leading-relaxed mb-4">
            You must be at least 18 years of age (or the age of majority in your jurisdiction, if higher) to use the Services. By using the Services, you represent and warrant that you meet this age requirement and have the legal capacity to enter into these Terms. If you are using the Services on behalf of an organization, you represent that you have the authority to bind that organization to these Terms.
          </p>
          <p className="leading-relaxed">
            The Services are not intended for use in any jurisdiction where their provision or use would be prohibited or restricted. You are responsible for compliance with all applicable local laws.
          </p>
        </section>

        <section id="services">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">3. Description of Services</h2>
          <p className="leading-relaxed mb-4">
            Ragard provides tools and analytics related to stocks, market sentiment, and public discussion of securities. The Services may include, without limitation:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>The Ragard website, including stock profiles, narratives, trending data, watchlists, and saved analyses</li>
            <li>The Ragard Chrome extension, which allows you to request analysis of web content (e.g., social media posts or articles) and view summaries and scores within the extension</li>
            <li>APIs and data feeds used to power the website and extension</li>
            <li>Account features such as authentication, saved analyses, and watchlists when you register</li>
          </ul>
          <p className="leading-relaxed mt-4">
            We may modify, suspend, or discontinue any part of the Services at any time, with or without notice. We do not guarantee that the Services will be available at all times or that they will be error-free.
          </p>
        </section>

        <section id="accounts">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">4. Accounts and Registration</h2>
          <p className="leading-relaxed mb-4">
            Certain features may require you to create an account. You agree to provide accurate, current, and complete information during registration and to update such information as needed. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You must notify us promptly of any unauthorized access or use of your account.
          </p>
          <p className="leading-relaxed">
            We may suspend or terminate your account if we reasonably believe you have violated these Terms or engaged in conduct that is harmful to the Services or other users.
          </p>
        </section>

        <section id="acceptable-use">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">5. Acceptable Use</h2>
          <p className="leading-relaxed mb-4">
            You agree to use the Services only for lawful purposes and in accordance with these Terms. You agree not to:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Use the Services in any way that violates applicable law or regulation</li>
            <li>Attempt to gain unauthorized access to the Services, other accounts, or any systems or networks connected to the Services</li>
            <li>Use the Services to transmit any malware, viruses, or other harmful code</li>
            <li>Scrape, crawl, or use automated means to collect data from the Services in a manner that exceeds normal use or that we have not expressly permitted</li>
            <li>Resell, sublicense, or commercially exploit the Services or any data obtained through the Services without our prior written consent</li>
            <li>Use the Services to harass, abuse, or harm others, or to send spam or unsolicited communications</li>
            <li>Reverse engineer, decompile, or attempt to derive source code from the Services except to the extent permitted by applicable law</li>
          </ul>
          <p className="leading-relaxed mt-4">
            We reserve the right to investigate suspected violations and to cooperate with law enforcement. Failure to comply with this section may result in immediate termination of your access to the Services.
          </p>
        </section>

        <section id="intellectual-property">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">6. Intellectual Property</h2>
          <p className="leading-relaxed">
            The Services, including but not limited to the software, design, text, graphics, logos, and other content (excluding third-party content and data), are owned by Ragard or its licensors and are protected by copyright, trademark, and other intellectual property laws. You do not acquire any ownership rights by using the Services. You may not copy, modify, distribute, sell, or create derivative works from the Services or our intellectual property without our prior written consent. Trademarks, service marks, and logos used in connection with the Services are the property of Ragard or their respective owners.
          </p>
        </section>

        <section id="disclaimer">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">7. No Financial or Investment Advice</h2>
          <p className="leading-relaxed mb-4">
            <strong>The Services are for informational and educational purposes only.</strong> Nothing on the Services, including any scores, summaries, narratives, or analytics, constitutes financial, investment, legal, tax, or other professional advice. Ragard is not a registered investment adviser, broker-dealer, or financial planner. We do not recommend or endorse any particular security, transaction, or investment strategy.
          </p>
          <p className="leading-relaxed">
            All content and data are provided &quot;as is&quot; and may be incomplete, delayed, or inaccurate. You should conduct your own research and consult qualified professionals before making any investment or trading decisions. You are solely responsible for your investment decisions and any losses that may result. Past performance and sentiment indicators do not guarantee future results.
          </p>
        </section>

        <section id="disclaimers">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">8. Disclaimers</h2>
          <p className="leading-relaxed mb-4">
            TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, THE SERVICES ARE PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND ACCURACY. WE DO NOT WARRANT THAT THE SERVICES WILL BE UNINTERRUPTED, SECURE, OR ERROR-FREE, OR THAT DEFECTS WILL BE CORRECTED.
          </p>
          <p className="leading-relaxed">
            Data and content displayed through the Services may come from third-party sources. We do not guarantee the accuracy, completeness, or timeliness of such data. Use of the Services and reliance on any content is at your sole risk.
          </p>
        </section>

        <section id="limitation">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">9. Limitation of Liability</h2>
          <p className="leading-relaxed mb-4">
            TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL RAGARD, ITS AFFILIATES, OFFICERS, DIRECTORS, EMPLOYEES, AGENTS, OR LICENSORS BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES (INCLUDING WITHOUT LIMITATION LOSS OF PROFITS, DATA, USE, OR GOODWILL) ARISING OUT OF OR IN CONNECTION WITH YOUR USE OF OR INABILITY TO USE THE SERVICES, WHETHER BASED ON WARRANTY, CONTRACT, TORT (INCLUDING NEGLIGENCE), STRICT LIABILITY, OR ANY OTHER LEGAL THEORY, EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
          </p>
          <p className="leading-relaxed mb-4">
            IN NO EVENT SHALL OUR TOTAL AGGREGATE LIABILITY FOR ALL CLAIMS ARISING OUT OF OR RELATED TO THESE TERMS OR THE SERVICES EXCEED THE GREATER OF (A) THE AMOUNT YOU PAID US, IF ANY, IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM, OR (B) ONE HUNDRED U.S. DOLLARS ($100).
          </p>
          <p className="leading-relaxed">
            Some jurisdictions do not allow the exclusion or limitation of certain damages. In such jurisdictions, our liability shall be limited to the maximum extent permitted by law.
          </p>
        </section>

        <section id="indemnification">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">10. Indemnification</h2>
          <p className="leading-relaxed">
            You agree to indemnify, defend, and hold harmless Ragard and its affiliates, officers, directors, employees, agents, and licensors from and against any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys&apos; fees) arising out of or related to (a) your use of the Services, (b) your violation of these Terms, (c) your violation of any third-party right, including intellectual property or privacy rights, (d) any content or data you submit or transmit through the Services, or (e) any investment or trading decisions you make based on the Services. We reserve the right to assume the exclusive defense and control of any matter subject to indemnification by you, at your expense.
          </p>
        </section>

        <section id="termination">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">11. Termination</h2>
          <p className="leading-relaxed mb-4">
            You may stop using the Services at any time. We may suspend or terminate your access to the Services, or any part thereof, at any time, with or without cause or notice, including for violation of these Terms. Upon termination, your right to use the Services will immediately cease.
          </p>
          <p className="leading-relaxed">
            Sections that by their nature should survive termination (including without limitation Sections 6, 7, 8, 9, 10, 12, 14, and 15) shall survive.
          </p>
        </section>

        <section id="governing-law">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">12. Governing Law and Disputes</h2>
          <p className="leading-relaxed mb-4">
            These Terms and any dispute or claim arising out of or related to them or the Services shall be governed by and construed in accordance with the laws of the State of Delaware, United States, without regard to its conflict of law provisions. You agree that any legal action or proceeding shall be brought exclusively in the state or federal courts located in Delaware, and you consent to the personal jurisdiction of such courts.
          </p>
          <p className="leading-relaxed">
            To the extent permitted by law, you agree that any dispute resolution proceedings will be conducted only on an individual basis and not in a class, consolidated, or representative action.
          </p>
        </section>

        <section id="changes">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">13. Changes to Terms</h2>
          <p className="leading-relaxed">
            We may update these Terms from time to time. We will notify you of material changes by posting the updated Terms on the Services and updating the &quot;Effective Date&quot; at the top of this page, or by sending you an email or other notice where we have your contact information. Your continued use of the Services after the effective date of any changes constitutes your acceptance of the revised Terms. If you do not agree to the new Terms, you must stop using the Services. We encourage you to review these Terms periodically.
          </p>
        </section>

        <section id="general">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">14. General Provisions</h2>
          <p className="leading-relaxed mb-4">
            <strong>Entire Agreement.</strong> These Terms, together with our Privacy Policy and any other policies or guidelines we publish on the Services, constitute the entire agreement between you and Ragard regarding the Services and supersede any prior agreements.
          </p>
          <p className="leading-relaxed mb-4">
            <strong>Severability.</strong> If any provision of these Terms is held to be invalid or unenforceable, the remaining provisions will remain in full force and effect.
          </p>
          <p className="leading-relaxed mb-4">
            <strong>Waiver.</strong> Our failure to enforce any right or provision of these Terms will not be deemed a waiver of such right or provision.
          </p>
          <p className="leading-relaxed">
            <strong>Assignment.</strong> You may not assign or transfer these Terms or your rights hereunder without our prior written consent. We may assign our rights and obligations without restriction.
          </p>
        </section>

        <section id="contact">
          <h2 className="text-2xl font-semibold mb-4 text-ragard-textPrimary">15. Contact</h2>
          <p className="leading-relaxed">
            If you have questions about these Terms of Service, please contact us at{' '}
            <a
              href="mailto:ragard.owner@gmail.com"
              className="text-ragard-accent hover:text-ragard-accent/80 hover:underline transition-colors"
            >
              ragard.owner@gmail.com
            </a>.
          </p>
        </section>
      </div>

      <div className="mt-12 pt-6 border-t border-slate-800">
        <Link
          href="/"
          className="text-ragard-accent hover:text-ragard-accent/80 hover:underline text-sm"
        >
          ← Back to Home
        </Link>
      </div>
    </div>
  )
}
