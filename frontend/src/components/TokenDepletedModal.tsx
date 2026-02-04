
"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, X, ShieldCheck, Crown } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface TokenDepletedModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const TokenDepletedModal: React.FC<TokenDepletedModalProps> = ({ isOpen, onClose }) => {
    const router = useRouter();

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                    onClick={onClose}
                />

                <motion.div
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="relative bg-[#0a0a0a] border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl shadow-brand/20 overflow-hidden"
                >
                    {/* Background Gradient */}
                    <div className="absolute top-0 left-0 w-full h-[200px] bg-gradient-to-b from-brand/10 to-transparent -z-10" />

                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/5 text-white/40 hover:text-white transition-colors"
                    >
                        <X size={20} />
                    </button>

                    <div className="flex flex-col items-center text-center space-y-6">
                        <div className="w-20 h-20 rounded-full bg-brand/10 flex items-center justify-center mb-2 animate-pulse ring-4 ring-brand/5">
                            <Zap size={40} className="text-brand" />
                        </div>

                        <div>
                            <h2 className="text-2xl font-black text-white mb-2">Out of Knowledge Tokens</h2>
                            <p className="text-white/60 leading-relaxed text-sm">
                                You've used all your AI tokens for this month. Upgrade your plan to continue using Gemini 3 Flash for instant categorization.
                            </p>
                        </div>

                        <div className="w-full bg-white/5 rounded-xl p-4 border border-white/5 text-left space-y-3">
                            <div className="flex items-center gap-3">
                                <ShieldCheck className="text-emerald-400" size={18} />
                                <span className="text-sm text-white/80">Unlimited AI Analysis</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <ShieldCheck className="text-emerald-400" size={18} />
                                <span className="text-sm text-white/80">Bulk Approval Actions</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <ShieldCheck className="text-emerald-400" size={18} />
                                <span className="text-sm text-white/80">Priority Support</span>
                            </div>
                        </div>

                        <button
                            onClick={() => router.push('/pricing')}
                            className="w-full py-4 btn-primary rounded-xl font-bold flex items-center justify-center gap-2 group"
                        >
                            <Crown size={20} className="text-yellow-900 group-hover:text-white transition-colors" />
                            Upgrade to Pro
                        </button>

                        <button
                            onClick={onClose}
                            className="text-white/30 text-xs font-medium hover:text-white transition-colors"
                        >
                            Maybe Later
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
