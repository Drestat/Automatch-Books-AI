"use client";

import React from 'react';
import { Check, Edit2, Info, ArrowUpRight, FilePlus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Split {
    category_name: string;
    amount: number;
    description: string;
}

interface Transaction {
    id: string;
    date: string;
    description: string;
    amount: number;
    currency: string;
    suggested_category_name: string;
    reasoning: string;
    confidence: number;
    is_split?: boolean;
    splits?: Split[];
    receipt_url?: string;
}

interface TransactionCardProps {
    tx: Transaction;
    onAccept: (id: string) => void;
    onReceiptUpload?: (id: string, file: File) => void;
}

export default function TransactionCard({ tx, onAccept, onReceiptUpload }: TransactionCardProps) {
    const isExpense = tx.amount < 0;
    const [showReasoning, setShowReasoning] = React.useState(false);
    const [isUploading, setIsUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleAccept = async () => {
        const { triggerHapticFeedback } = await import('@/lib/haptics');
        triggerHapticFeedback();
        onAccept(tx.id);
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && onReceiptUpload) {
            setIsUploading(true);
            await onReceiptUpload(tx.id, file);
            setIsUploading(false);
        }
    };

    return (
        <div className="glass-card overflow-hidden group">
            <div className="p-6">
                <div className="flex justify-between items-start mb-6">
                    <div className="flex gap-4">
                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${isExpense ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'
                            } border border-white/5`}>
                            {isExpense ? <ArrowUpRight className="rotate-180" size={24} /> : <ArrowUpRight size={24} />}
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="text-lg font-bold tracking-tight text-white group-hover:text-brand transition-colors">
                                    {tx.description}
                                </h3>
                                {tx.is_split && (
                                    <span className="px-1.5 py-0.5 rounded-md bg-brand/20 border border-brand/30 text-[8px] font-black uppercase tracking-widest text-brand">Split</span>
                                )}
                            </div>
                            <p className="text-sm text-white/40">{tx.date}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className={`text-xl font-black ${isExpense ? 'text-white' : 'text-emerald-400'}`}>
                            {isExpense ? '' : '+'}{tx.amount.toLocaleString('en-US', { style: 'currency', currency: tx.currency })}
                        </p>
                    </div>
                </div>

                <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-4 mb-6 relative overflow-hidden">
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-[10px] uppercase tracking-[0.2em] font-bold text-brand">{tx.is_split ? 'Suggested Splits' : 'Suggested Category'}</span>
                        <div className="h-[1px] flex-1 bg-white/5" />
                        <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border ${tx.confidence > 0.9 ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                            tx.confidence > 0.7 ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                                'bg-rose-500/10 border-rose-500/20 text-rose-400'
                            }`}>
                            <div className={`w-1 h-1 rounded-full animate-pulse ${tx.confidence > 0.9 ? 'bg-emerald-500' :
                                tx.confidence > 0.7 ? 'bg-amber-500' :
                                    'bg-rose-500'
                                }`} />
                            <span className="text-[10px] font-bold">{Math.round(tx.confidence * 100)}% Match</span>
                        </div>
                    </div>
                    <div className="flex justify-between items-start">
                        <div className="flex-1">
                            {tx.is_split && tx.splits && tx.splits.length > 0 ? (
                                <div className="space-y-3">
                                    {tx.splits.map((split, i) => (
                                        <div key={i} className="flex justify-between items-center text-sm border-b border-white/5 pb-2 last:border-0 last:pb-0">
                                            <div>
                                                <p className="font-bold text-white/90">{split.category_name}</p>
                                                <p className="text-[10px] text-white/40">{split.description}</p>
                                            </div>
                                            <p className="font-black text-white/80">${split.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-lg font-medium text-white/90">{tx.suggested_category_name}</p>
                            )}
                        </div>
                        <button
                            onClick={() => setShowReasoning(!showReasoning)}
                            className="p-1 hover:bg-white/5 rounded-lg transition-colors text-white/20 hover:text-white/40 ml-4"
                            title="Toggle AI Reasoning"
                        >
                            <Info size={16} />
                        </button>
                    </div>

                    <AnimatePresence>
                        {showReasoning && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3, ease: 'easeInOut' }}
                                className="overflow-hidden"
                            >
                                <div className="mt-3 pt-3 border-t border-white/5 flex gap-2 items-start">
                                    <p className="text-xs text-white/40 leading-relaxed italic">{tx.reasoning}</p>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div className="flex gap-3">
                    <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={handleAccept}
                        className="flex-1 bg-brand hover:bg-brand/90 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-brand/20 transition-all border border-white/10"
                    >
                        <Check size={18} />
                        Confirm Match
                    </motion.button>

                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="hidden"
                        accept="image/*"
                    />

                    <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className={`w-12 h-12 ${tx.receipt_url ? 'bg-brand/20 text-brand border-brand/30' : 'bg-white/5 text-white/60 hover:text-white'} border border-white/10 rounded-xl flex items-center justify-center transition-all`}
                        title="Mirror Receipt"
                    >
                        {isUploading ? (
                            <div className="w-4 h-4 border-2 border-brand border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <FilePlus size={18} />
                        )}
                    </motion.button>

                    <motion.button
                        whileTap={{ scale: 0.95 }}
                        className="w-12 h-12 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl flex items-center justify-center text-white/60 hover:text-white transition-all"
                    >
                        <Edit2 size={18} />
                    </motion.button>
                </div>
            </div>
            <div className="h-1 w-full bg-gradient-to-r from-transparent via-brand/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
    );
}
