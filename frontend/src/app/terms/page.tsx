"use client";

import React from 'react';
import Footer from '@/components/Footer';
import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';

export default function TermsPage() {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white">
            <main className="py-24 px-6 max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-16"
                >
                    <div className="w-12 h-12 rounded-2xl bg-brand/10 text-brand flex items-center justify-center mb-6">
                        <FileText size={24} />
                    </div>
                    <h1 className="text-5xl font-black tracking-tight mb-4">Terms of Service</h1>
                    <p className="text-white/40 text-lg">Effective Date: January 2026</p>
                </motion.div>

                <div className="glass-card p-8 md:p-12 border-white/5 space-y-12 text-white/70 leading-relaxed">
                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
                        <p>
                            By accessing or using AutoMatch Books AI, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">2. Description of Service</h2>
                        <p>
                            AutoMatch Books AI is an AI-powered automation tool for QuickBooks Online. We provide transaction mirroring, AI-driven categorization suggestions, and sync capabilities. We are not a replacement for a certified professional accountant (CPA).
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">3. Subscription & Payments</h2>
                        <p>
                            We offer several subscription tiers. Payments are processed via Stripe. You may cancel your subscription at any time; however, we do not offer pro-rated refunds for partial months. Free trials automatically transition to paid subscriptions unless canceled.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">4. Limitation of Liability</h2>
                        <p>
                            While our AI strives for high accuracy (94%+), all final transactions must be reviewed and approved by you. We are not responsible for errors in financial reporting, tax filings, or QuickBooks data resulting from the use of our automated suggestions.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-bold text-white mb-4">5. Intellectual Property</h2>
                        <p>
                            All software, designs, and AI prompts used in AutoMatch Books AI are the intellectual property of AutoMatch Books AI Engine. You are granted a limited, non-exclusive license to use the service for your business purposes.
                        </p>
                    </section>
                </div>
            </main>
            <Footer />
        </div>
    );
}
