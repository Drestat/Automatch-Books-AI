"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
    Check,
    Sparkles,
    Shield,
    Zap,
    Crown,
    ArrowRight
} from 'lucide-react';
import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Pricing | AutoMatch Books AI",
    description: "Flexible pricing tiers for businesses of all sizes. Start your 14-day free trial of AI-powered QuickBooks automation today.",
    alternates: {
        canonical: '/pricing',
    }
};

const TIERS = [
    {
        name: "Freelancer",
        price: "$9",
        period: "/mo",
        description: "Perfect for side hustles and solo operators.",
        icon: Zap,
        features: [
            "1 Connected Bank Account",
            "Manual Sync (On Demand)",
            "Basic AI Categorization",
            "30-Day History",
            "Email Support"
        ],
        cta: "Start Free Trial",
        highlight: false
    },
    {
        name: "Founder",
        price: "$29",
        period: "/mo",
        description: "The growth engine for modern startups.",
        icon: Sparkles,
        features: [
            "Unlimited Connected Accounts",
            "Auto-Sync (Midnight Run)",
            "High-Confidence Auto-Approve",
            "Reasoning Narratives",
            "Unlimited History",
            "Priority Support"
        ],
        cta: "Start Free Trial",
        highlight: true,
        badge: "Most Popular"
    },
    {
        name: "Empire",
        price: "$79",
        period: "/mo",
        description: "For scaling teams and heavy transaction volume.",
        icon: Crown,
        features: [
            "Multi-User Access (5 Seats)",
            "Concierge Onboarding",
            "Custom AI Rules Engine",
            "Advanced Anomaly Detection",
            "Dedicated Account Manager",
            "API Access"
        ],
        cta: "Contact Sales",
        highlight: false
    }
];

export default function PricingPage() {
    const [loading, setLoading] = React.useState<string | null>(null);

    const handleCheckout = async (tierName: string, priceId: string) => {
        setLoading(tierName);
        try {
            const res = await fetch('/api/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ priceId, tierName }),
            });
            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (error) {
            console.error('Checkout error:', error);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white py-24 px-6 relative overflow-hidden">
            {/* Background Gradients */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-brand/10 rounded-full blur-[120px] -z-10 opacity-40" />

            <div className="max-w-7xl mx-auto relative z-10">
                <div className="text-center mb-20 max-w-2xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <h1 className="text-4xl md:text-6xl font-black tracking-tight mb-6">
                            Invest in <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Sanity</span>.
                        </h1>
                        <p className="text-xl text-white/40 leading-relaxed">
                            Stop paying with your time. Upgrade to the magical mirror and let AI handle the books.
                        </p>
                    </motion.div>
                </div>

                <div className="grid md:grid-cols-3 gap-8 items-start">
                    {TIERS.map((tier, index) => (
                        <motion.div
                            key={tier.name}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.1 * index }}
                            className={`relative glass-card p-8 rounded-3xl border transition-all duration-300 ${tier.highlight
                                ? 'border-brand/40 bg-brand/5 scale-105 shadow-2xl shadow-brand/20 z-10'
                                : 'border-white/5 hover:border-white/10'
                                }`}
                        >
                            {tier.highlight && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-brand text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-lg">
                                    {tier.badge}
                                </div>
                            )}

                            <div className="mb-8">
                                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${tier.highlight ? 'bg-brand text-white' : 'bg-white/5 text-white/60'
                                    }`}>
                                    <tier.icon size={24} />
                                </div>
                                <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
                                <p className="text-white/40 text-sm min-h-[40px]">{tier.description}</p>
                            </div>

                            <div className="flex items-baseline gap-1 mb-8">
                                <span className="text-4xl font-black tracking-tight">{tier.price}</span>
                                <span className="text-white/40 font-bold">{tier.period}</span>
                            </div>

                            <ul className="space-y-4 mb-8">
                                {tier.features.map((feature) => (
                                    <li key={feature} className="flex items-start gap-3 text-sm">
                                        <Check size={16} className={`mt-0.5 ${tier.highlight ? 'text-brand' : 'text-white/40'
                                            }`} />
                                        <span className="text-white/80">{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={() => handleCheckout(tier.name, tier.name === 'Freelancer' ? 'price_HB1_free' : tier.name === 'Founder' ? 'price_HB1_pro' : 'price_HB1_ent')}
                                className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all group ${tier.highlight
                                    ? 'bg-brand text-white hover:bg-brand-secondary hover:scale-[1.02]'
                                    : 'bg-white/5 text-white hover:bg-white/10'
                                    }`}
                            >
                                {tier.cta}
                                {tier.highlight && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
                            </button>

                            {tier.highlight && (
                                <p className="text-center text-xs text-white/30 mt-4 font-medium">
                                    7-Day Free Trial • Cancel Anytime
                                </p>
                            )}
                        </motion.div>
                    ))}
                </div>

                <div className="mt-24 text-center border-t border-white/5 pt-12">
                    <h4 className="text-lg font-bold mb-4">Enterprise Customization</h4>
                    <p className="text-white/40 max-w-2xl mx-auto mb-8">
                        Need on-premise deployment, custom Data Retention policies, or SSO?
                        We offer bespoke engineering solutions for heavy-compliance industries.
                    </p>
                    <a href="mailto:sales@easymirror.app" className="text-brand font-bold hover:underline">
                        Contact Enterprise Sales
                    </a>
                </div>
            </div>
        </div>
    );
}
