"use client";

import React from 'react';
import Footer from '@/components/Footer';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white">
            <main className="py-24 px-6 max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-16"
                >
                    <div className="w-12 h-12 rounded-2xl bg-brand/10 text-brand flex items-center justify-center mb-6">
                        <Shield size={24} />
                    </div>
                    <h1 className="text-5xl font-black tracking-tight mb-4">Privacy Policy</h1>
                    <p className="text-white/40 text-lg">Last Updated: January 2026</p>
                </motion.div>

                <div className="glass-card p-8 md:p-12 border-white/5 space-y-12 text-white/70 leading-relaxed">
                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">1. Data Sovereignty</h2>
                        <p>
                            At AutoMatch Books AI, we believe your financial data is yours alone. We use read-only access to your QuickBooks Online account to mirror transactions locally for AI analysis. We never modify your original bank records without your explicit &quot;Approval&quot; action.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">2. AI Processing</h2>
                        <p>
                            Transaction data is processed using Google Gemini 3 Flash. Data sent to the AI is stripped of sensitive personally identifiable information (PII) where possible. Google does not use data submitted to Gemini via the API to train their global models for other users.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">3. Security</h2>
                        <p>
                            We utilize bank-grade encryption (AES-256) for all data at rest and TLS 1.3 for data in transit. Your QuickBooks credentials are never stored on our servers; we use secure OAuth 2.0 tokens managed by Intuit.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">4. Cookies</h2>
                        <p>
                            We use essential cookies to maintain your session and security via Clerk. We do not use third-party tracking or advertising cookies.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">5. Google API Services Compliance</h2>
                        <p>
                            AutoMatch Books AI's use and transfer to any other app of information received from Google APIs will adhere to <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer" className="text-brand hover:underline">Google API Services User Data Policy</a>, including the Limited Use requirements. We do not use Google user data for developing, improving, or training generalized/non-personalized AI and/or ML models.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">6. Intuit Data Compliance</h2>
                        <p>
                            We strictly adhere to the <a href="https://developer.intuit.com/app/developer/qbo/docs/go-live/publish-app/legal-agreements" target="_blank" rel="noopener noreferrer" className="text-brand hover:underline">Intuit Developer Terms</a>. We do not sell, rent, or trade your QuickBooks Online data to any third parties. Your financial data is used solely for the purpose of categorizing transactions within your account.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">7. Data Retention & Deletion</h2>
                        <p>
                            We retain your data only as long as your account is active. Upon subscription cancellation or explicit request, all synced financial data is permanently deleted from our servers within 30 days. You may request immediate data deletion by contacting support.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">8. Third-Party Sharing</h2>
                        <p>
                            We share data only with essential service providers necessary to operate the service:
                            <ul className="list-disc pl-5 mt-2 space-y-1">
                                <li><strong>Clerk:</strong> For authentication and user management.</li>
                                <li><strong>Stripe:</strong> For payment processing (we do not store credit card details).</li>
                                <li><strong>Google Gemini:</strong> For AI processing (anonymized data snippets only).</li>
                                <li><strong>Neon/AWS:</strong> for encrypted database hosting.</li>
                            </ul>
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">9. Contact</h2>
                        <p>
                            Questions about your privacy? Reach <a href="mailto:support@automatchbooksai.com" className="text-brand hover:underline">
                                support@automatchbooksai.com
                            </a>.
                        </p>
                    </section>
                </div>
            </main>
            <Footer />
        </div>
    );
}
