"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Sparkles, ShieldCheck, Zap, ArrowRight, CheckCircle } from 'lucide-react';
import { SignedIn, SignedOut } from '@clerk/nextjs';
import Footer from '@/components/Footer';

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white">
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{
                    __html: JSON.stringify({
                        "@context": "https://schema.org",
                        "@graph": [
                            {
                                "@type": "Organization",
                                "@id": "https://automatchbooks.ai/#organization",
                                "name": "AutoMatch Books AI",
                                "url": "https://automatchbooks.ai",
                                "logo": {
                                    "@type": "ImageObject",
                                    "url": "https://automatchbooks.ai/logo.png"
                                }
                            },
                            {
                                "@type": "SoftwareApplication",
                                "@id": "https://automatchbooks.ai/#application",
                                "name": "AutoMatch Books AI",
                                "operatingSystem": "Web",
                                "applicationCategory": "FinanceApplication",
                                "description": "AI-powered transaction matching for QuickBooks Online.",
                                "publisher": { "@id": "https://automatchbooks.ai/#organization" },
                                "offers": {
                                    "@type": "Offer",
                                    "price": "0",
                                    "priceCurrency": "USD"
                                }
                            }
                        ]
                    })
                }}
            />
            {/* Navigation */}
            <nav className="fixed top-0 w-full z-50 bg-black/50 backdrop-blur-xl border-b border-white/5">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center shrink-0">
                            <Sparkles className="text-white" size={16} />
                        </div>
                        <span className="font-bold tracking-tight text-base sm:text-lg whitespace-nowrap">AutoMatch Books AI</span>
                        <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-white/40 font-mono">f3.10.2</span>
                    </div>
                    <div className="flex items-center gap-3 sm:gap-6">
                        <SignedOut>
                            <Link href="/dashboard" className="text-xs sm:text-sm font-bold text-white/60 hover:text-white transition-colors">
                                Log In
                            </Link>
                            <Link href="/sign-up" className="btn-primary px-4 sm:px-6 py-2 sm:py-2.5 text-xs sm:text-sm">
                                Try Free
                            </Link>
                        </SignedOut>
                        <SignedIn>
                            <Link href="/dashboard" className="text-xs sm:text-sm font-bold text-brand hover:text-brand/80 transition-colors">
                                Go to Dashboard
                            </Link>
                        </SignedIn>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 px-6 overflow-hidden">
                <div className="max-w-7xl mx-auto text-center relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-8">
                            <span className="w-2 h-2 rounded-full bg-brand animate-pulse" />
                            <span className="text-xs font-bold tracking-wider uppercase text-brand">AI-Powered Accountability</span>
                        </div>
                        <h1 className="text-[clamp(3rem,8vw,6rem)] font-black tracking-tight leading-[1.1] mb-6">
                            Your Books, on <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Smart Autopilot.</span>
                        </h1>
                        <p className="text-lg md:text-xl text-white/40 max-w-2xl mx-auto mb-10 leading-relaxed">
                            Stop categorizing transactions manually. AutoMatch is the **human-in-the-loop** financial layer that business owners desperately need. Auditable intelligence, not just automation.
                        </p>
                        <div className="flex flex-col md:flex-row items-center justify-center gap-4">
                            <Link href="/sign-up" className="btn-primary px-8 py-4 text-lg w-full md:w-auto flex items-center justify-center gap-3 group">
                                Start Syncing Now
                                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                            </Link>
                            <Link href="#how-it-works" className="px-8 py-4 text-lg font-bold text-white/60 hover:text-white transition-colors flex items-center gap-2">
                                See How It Works
                            </Link>
                        </div>
                    </motion.div>
                </div>

                {/* Background Gradients */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-brand/20 rounded-full blur-[120px] -z-10 opacity-50" />
            </section>

            {/* Feature Grid */}
            <section id="how-it-works" className="py-24 px-6 border-t border-white/5 bg-white/[0.02]">
                <div className="max-w-7xl mx-auto">
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="glass-panel p-8">
                            <Zap className="text-brand mb-6" size={40} />
                            <h3 className="text-xl font-bold mb-3">Zero-Lag Sync</h3>
                            <p className="text-white/40 leading-relaxed">
                                We mirror your QuickBooks data locally so you can categorize instantly. No loading spinners, no waiting.
                            </p>
                        </div>
                        <div className="glass-panel p-8">
                            <ShieldCheck className="text-emerald-400 mb-6" size={40} />
                            <h3 className="text-xl font-bold mb-3">Traffic Light Confidence</h3>
                            <p className="text-white/40 leading-relaxed">
                                Our AI assigns a confidence score to every match. Green means go, Amber means review.
                            </p>
                        </div>
                        <div className="glass-panel p-8">
                            <Sparkles className="text-brand-secondary mb-6" size={40} />
                            <h3 className="text-xl font-bold mb-3">Auditable Intelligence</h3>
                            <p className="text-white/40 leading-relaxed text-sm">
                                Most AI tools are &quot;black boxes.&quot; Our AI explains every transaction before you click **&quot;Agree.&quot;** You are the final boss who validates the logic.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing CTA */}
            <section className="py-32 px-6 text-center">
                <div className="max-w-3xl mx-auto glass-card p-12 border-brand/20 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand via-brand-secondary to-brand" />
                    <h2 className="text-4xl font-black tracking-tight mb-6">Ready for Clarity?</h2>
                    <p className="text-white/50 mb-10 text-lg">
                        Join 500+ businesses automating their bookkeeping today.
                    </p>
                    <ul className="flex flex-wrap justify-center gap-6 mb-10 text-sm font-bold text-white/80">
                        <li className="flex items-center gap-2"><CheckCircle size={16} className="text-brand" /> 14-Day Free Trial</li>
                        <li className="flex items-center gap-2"><CheckCircle size={16} className="text-brand" /> No Credit Card Required</li>
                        <li className="flex items-center gap-2"><CheckCircle size={16} className="text-brand" /> Cancel Anytime</li>
                    </ul>
                    <Link href="/sign-up" className="btn-primary px-10 py-5 text-xl inline-flex items-center gap-3">
                        Get Started Free
                    </Link>
                </div>
            </section>

            <Footer />
        </div>
    );
}
