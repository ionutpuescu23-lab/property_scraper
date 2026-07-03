'use client';

import React from 'react';
import Link from 'next/link';

export default function PrivacyPolicyPage() {
  return (
    <div 
      className="min-h-screen text-slate-100 font-sans p-6 md:p-12 bg-cover bg-center bg-no-repeat bg-fixed"
      style={{ 
        backgroundImage: `linear-gradient(to bottom, rgba(11, 23, 27, 0.96), rgba(13, 148, 136, 0.1), rgba(15, 23,  slate-950, 0.98)), url('https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1920&q=85')` 
      }}
    >
      <div className="max-w-3xl mx-auto bg-slate-900/60 border border-slate-800/80 p-8 md:p-12 rounded-2xl shadow-2xl backdrop-blur-md">
        
        {/* Back Navigation */}
        <Link 
          href="/" 
          className="inline-flex items-center text-xs font-bold text-teal-400 hover:text-teal-300 transition gap-1.5 mb-8 group"
        >
          <span className="transform group-hover:-translate-x-1 transition-transform">←</span> Return to Live Pipeline
        </Link>

        {/* Title Block */}
        <header className="border-b border-slate-800/60 pb-6 mb-8">
          <h1 className="text-3xl font-black tracking-tight text-white">Privacy Policy</h1>
          <p className="text-sm text-slate-400 font-medium mt-2">AlphaDeals Ltd</p>
          <p className="text-xs text-slate-500 font-mono mt-1">Last updated: July 2026</p>
        </header>

        {/* Content Body */}
        <div className="space-y-6 text-sm text-slate-300 leading-relaxed">
          
          <section>
            <h2 className="text-base font-bold text-white mb-2">1. Introduction</h2>
            <p>AlphaDeals Ltd ("we", "our", "us", or "AlphaDeals") operates the AlphaDeals platform. This Privacy Policy explains how we collect, use, and protect your personal data when you use our service.</p>
            <p className="mt-2">We are committed to protecting your privacy and being transparent about what data we collect and how we use it. This policy complies with UK data protection law, including the UK General Data Protection Regulation (GDPR) and the Data Protection Act 2018.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">2. What Data We Collect</h2>
            <p>We collect the following personal data:</p>
            <ul className="list-disc list-inside pl-2 mt-2 space-y-1 text-slate-400">
              <li><strong className="text-slate-300">Email address</strong> — to create and manage your account</li>
              <li><strong className="text-slate-300">Password</strong> — to secure your account (stored encrypted)</li>
              <li><strong className="text-slate-300">Payment information</strong> — name, address, and transaction details (processed by Stripe, our payment processor)</li>
              <li><strong className="text-slate-300">Membership tier information</strong> — to track your deal access permissions</li>
            </ul>
            <p className="mt-2 text-amber-400/90 bg-amber-500/5 border border-amber-500/10 p-3 rounded-xl text-xs">
              💡 We do not collect or retain behavioral data (e.g., which deals you view or how long you spend on the platform).
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">3. Why We Collect This Data</h2>
            <p>We collect personal data to:</p>
            <ul className="list-disc list-inside pl-2 mt-1 space-y-1 text-slate-400">
              <li>Create and authenticate your account</li>
              <li>Process one-off payments for deal access</li>
              <li>Provide you with property listings and deal information</li>
              <li>Communicate with you about your account and service updates</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">4. Property Listing Data</h2>
            <p>AlphaDeals sources property listings from publicly available sources including Rightmove. Once you access deal information on our platform, how you use that information is your own decision. We do not track your actions after accessing the data.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">5. How Long We Keep Your Data</h2>
            <p>We retain your personal data for as long as you maintain an account with us. If you request account deletion, we will delete all personal data within 30 days, except where we are required to retain it by law (e.g., for tax or accounting purposes).</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">6. Your Data Rights</h2>
            <p>Under UK GDPR, you have the right to access your personal data, request correction of inaccurate data, request deletion, restrict processing, receive a copy in a portable format, or lodge a complaint with the UK Information Commissioner's Office (ICO).</p>
            <p className="mt-2">To exercise any of these rights, contact us at <span className="text-teal-400">info@alphadeals.co.uk</span> with "Data Subject Request" in the subject line. We will respond within 30 days.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">7. Who We Share Your Data With</h2>
            <p>We use the following third parties to process your data:</p>
            <ul className="list-disc list-inside pl-2 mt-1 space-y-1 text-slate-400">
              <li><strong className="text-slate-300">Supabase (database provider)</strong> — stores your account and payment information</li>
              <li><strong className="text-slate-300">Stripe (payment processor)</strong> — processes one-off payments securely</li>
            </ul>
            <p className="mt-2">These third parties are bound by data protection agreements and may only use your data to provide their services to us. We do not sell or rent your personal data to any third party.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">8. Security</h2>
            <p>We implement industry-standard security measures to protect your data, including encryption in transit and at rest. However, no method of transmission over the internet is 100% secure, and we cannot guarantee absolute security.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">9. Legal Basis for Processing</h2>
            <p>We process your personal data on the following legal bases: Contract (to provide you with access to AlphaDeals), Consent (for marketing communications, which you can withdraw anytime), and Legal obligation (to comply with UK tax and accounting requirements).</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">10. Children</h2>
            <p>AlphaDeals is not intended for users under 18. We do not knowingly collect personal data from children. If we become aware that a child has provided us with personal data, we will delete it immediately.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-white mb-2">11. Changes to This Privacy Policy</h2>
            <p>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on our website and updating the "Last updated" date. Your continued use of AlphaDeals after changes constitute your acceptance of the updated policy.</p>
          </section>

          <section className="border-t border-slate-800/60 pt-6 mt-8">
            <h2 className="text-base font-bold text-white mb-2">12. Contact Us</h2>
            <p>If you have questions about this Privacy Policy or want to exercise your data rights, contact us at:</p>
            <div className="bg-slate-950/40 border border-slate-800/60 p-4 rounded-xl mt-3 font-mono text-xs space-y-1 text-slate-400">
              <p>Email: <span className="text-teal-400">info@alphadeals.co.uk</span></p>
              <p>Company: AlphaDeals Ltd</p>
            </div>
            <p className="mt-4 text-xs text-slate-400">
              If you are not satisfied with our response, you can lodge a complaint with the Information Commissioner's Office (ICO) at <a href="https://www.ico.org.uk" target="_blank" rel="noopener noreferrer" className="text-teal-400 hover:underline">www.ico.org.uk</a>.
            </p>
          </section>

        </div>

        <footer className="text-center text-[10px] text-slate-500 border-t border-slate-800/40 mt-12 pt-4">
          © AlphaDeals Ltd 2026. All rights reserved.
        </footer>

      </div>
    </div>
  );
}