"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Lock, Sparkles, Clock, AlertCircle, ArrowRight } from 'lucide-react';

interface SubscriptionGuardProps {
    status: 'active' | 'inactive' | 'free' | 'expired' | 'trial' | 'no_plan' | null;
    daysRemaining: number;
    children: React.ReactNode;
}

export const SubscriptionGuard: React.FC<SubscriptionGuardProps> = ({ status, daysRemaining, children }) => {
    const router = useRouter();

    if (!status) {
        // Loading state - maybe a skeleton or just null
        // Loading state
        return (
            <div className="min-h-screen bg-black flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin" />
                <span className="ml-3 text-white/50 font-mono text-sm">Loading Profile...</span>
            </div>
        );
    }

    // BLOCKING STATES

    if (status === 'no_plan' || status === 'inactive') {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.02] -z-10" />

                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-xl p-8 rounded-3xl text-center shadow-2xl"
                >
                    <div className="w-16 h-16 bg-brand/10 rounded-2xl flex items-center justify-center mx-auto mb-6 ring-1 ring-brand/20">
                        <Sparkles size={32} className="text-brand" />
                    </div>
                    <h2 className="text-3xl font-black mb-4">Welcome to AutoMatch</h2>
                    <p className="text-white/50 mb-8 leading-relaxed">
                        To activate your AI bookkeeper, please select a plan. Start your 7-day free trial today.
                    </p>

                    <button
                        onClick={() => router.push('/pricing')}
                        className="w-full btn-primary py-4 rounded-xl font-bold flex items-center justify-center gap-2 group"
                    >
                        Choose Your Plan <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                    </button>

                    <p className="mt-4 text-xs text-white/20">No credit card required for trial.</p>
                </motion.div>
            </div>
        );
    }

    if (status === 'expired') {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.02] -z-10" />
                <div className="absolute inset-0 bg-rose-500/5 backdrop-blur-sm z-0" />

                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="w-full max-w-md bg-[#0a0a0a] border border-rose-500/20 p-8 rounded-3xl text-center shadow-[0_0_50px_rgba(244,63,94,0.1)] relative z-10"
                >
                    <div className="w-16 h-16 bg-rose-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 ring-1 ring-rose-500/20">
                        <Lock size={32} className="text-rose-500" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Trial Expired</h2>
                    <p className="text-white/50 mb-8 text-sm">
                        Your 7-day trial has ended. To continue matching transactions and syncing to QuickBooks, please upgrade your plan.
                    </p>

                    <button
                        onClick={() => router.push('/pricing')}
                        className="w-full py-4 rounded-xl font-bold bg-rose-600 hover:bg-rose-500 text-white transition-colors shadow-lg shadow-rose-900/20"
                    >
                        Restore Access
                    </button>
                </motion.div>
            </div>
        );
    }

    // NON-BLOCKING STATES (Active / Trial)

    return (
        <div className="relative">
            {status === 'trial' && (
                <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 border-b border-white/5 backdrop-blur-md sticky top-0 z-50">
                    <div className="max-w-[1400px] mx-auto px-6 h-10 flex items-center justify-center gap-2 text-xs font-medium text-white/80">
                        <Clock size={14} className="text-brand-accent" />
                        <span>
                            <span className="text-brand-accent font-bold">{daysRemaining} days</span> remaining in your free trial.
                        </span>
                        <button
                            onClick={() => router.push('/pricing')}
                            className="ml-2 underline hover:text-white transition-colors"
                        >
                            Upgrade Now
                        </button>
                    </div>
                </div>
            )}

            {/* Render Dashboard Content */}
            {children}
        </div>
    );
};
