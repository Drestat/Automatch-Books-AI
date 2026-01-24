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
                        <h2 className="text-2xl font-bold text-white mb-4">5. Contact</h2>
                        <p>
                            Questions about your privacy? Reach out to us at <a href="mailto:privacy@automatchbooks.ai" className="text-brand hover:underline">privacy@automatchbooks.ai</a>.
                        </p>
                    </section>
                </div>
            </main>
            <Footer />
        </div>
    );
}
