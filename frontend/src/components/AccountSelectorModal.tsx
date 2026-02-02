"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Building2, Crown, Check, X, Sparkles } from 'lucide-react';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

interface Account {
    id: string;
    name: string;
    balance: number;
    currency: string;
    is_active: boolean;
}

interface AccountSelectorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    realmId: string;
}

export function AccountSelectorModal({ isOpen, onClose, onSuccess, realmId }: AccountSelectorModalProps) {
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [selectedIds, setSelectedIds] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [limit, setLimit] = useState(1);
    const [tier, setTier] = useState("free");

    // Preview State
    const [step, setStep] = useState<'select' | 'preview'>('select');
    const [previewLoading, setPreviewLoading] = useState(false);
    const [previewStats, setPreviewStats] = useState<{ total_transactions: number, already_matched: number, to_analyze: number } | null>(null);

    useEffect(() => {
        if (isOpen && realmId) {
            fetchAccounts();
        }
    }, [isOpen, realmId]);

    const fetchAccounts = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/qbo/accounts?realm_id=${realmId}`);
            if (!res.ok) throw new Error('Failed to fetch accounts');
            const data = await res.json();
            setAccounts(data.accounts);
            setLimit(data.limit);
            setTier(data.tier);
            setSelectedIds(data.accounts.filter((a: Account) => a.is_active).map((a: Account) => a.id));
        } catch (error) {
            console.error("Error fetching accounts:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleToggle = (id: string, checked: boolean) => {
        if (checked) {
            if (selectedIds.length >= limit) {
                return; // Limit reached
            }
            setSelectedIds([...selectedIds, id]);
        } else {
            setSelectedIds(selectedIds.filter(sid => sid !== id));
        }
    };

    const handlePreview = async () => {
        setPreviewLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/qbo/accounts/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ realm_id: realmId, active_account_ids: selectedIds })
            });
            const data = await res.json();
            setPreviewStats(data);
            setStep('preview');
        } catch (error) {
            console.error("Preview error:", error);
            alert("Failed to generating preview.");
        } finally {
            setPreviewLoading(false);
        }
    };

    const handleSave = async () => {
        setSubmitting(true);
        try {
            const res = await fetch(`${API_BASE_URL}/qbo/accounts/select`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ realm_id: realmId, active_account_ids: selectedIds })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to save');
            }
            onSuccess();
            onClose();
        } catch (error) {
            console.error("Save error:", error);
            alert("Failed to save selection. Please try again.");
        } finally {
            setSubmitting(false);
        }
    };

    const isLimitReached = selectedIds.length >= limit;

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-md bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
                    >
                        <div className="p-6 space-y-6">
                            <div className="flex items-center justify-between">
                                <div className="space-y-1">
                                    <h2 className="text-xl font-bold flex items-center gap-2 text-white">
                                        <Building2 size={24} className="text-brand" />
                                        Select Accounts
                                    </h2>
                                    <p className="text-sm text-white/60">
                                        Choose which bank accounts to track. Your plan allows for <span className="text-brand font-bold">{limit}</span> connected account{limit > 1 ? 's' : ''}.
                                    </p>
                                </div>
                                <button onClick={onClose} className="p-2 text-white/20 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            {loading ? (
                                <div className="py-16 flex flex-col items-center justify-center gap-4">
                                    <Loader2 className="animate-spin text-brand" size={40} />
                                    <p className="text-sm text-white/40">Loading your accounts...</p>
                                </div>
                            ) : step === 'select' && (
                                <div className="space-y-4 max-h-[50vh] overflow-y-auto">
                                    <div className="flex items-center justify-between text-xs text-white/50 px-2 pb-2 border-b border-white/5">
                                        <span>Available Accounts</span>
                                        <span className={isLimitReached ? "text-amber-400 font-bold" : ""}>
                                            {selectedIds.length} / {limit} Selected
                                        </span>
                                    </div>

                                    {accounts.map(account => {
                                        const isSelected = selectedIds.includes(account.id);
                                        const isDisabled = !isSelected && isLimitReached;

                                        return (
                                            <div key={account.id}
                                                className={`flex items-center space-x-3 p-3 rounded-xl border transition-all duration-200 cursor-pointer
                                                ${isSelected
                                                        ? 'bg-brand/10 border-brand/40'
                                                        : 'bg-white/5 border-white/5 hover:border-white/20'
                                                    }
                                                ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                                                `}
                                                onClick={() => !isDisabled && handleToggle(account.id, !isSelected)}
                                            >
                                                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${isSelected ? 'bg-brand border-brand text-black' : 'border-white/20 bg-transparent'}`}>
                                                    {isSelected && <Check size={14} strokeWidth={3} />}
                                                </div>

                                                <div className="flex-1">
                                                    <div className="font-bold text-sm text-white">{account.name}</div>
                                                    <div className="text-xs text-white/50 font-mono">
                                                        {new Intl.NumberFormat('en-US', { style: 'currency', currency: account.currency }).format(account.balance)}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}

                                    {accounts.length === 0 && !loading && (
                                        <div className="py-8 text-center space-y-2">
                                            <Building2 size={40} className="mx-auto text-white/20" />
                                            <p className="text-white/60 text-sm">No bank accounts found</p>
                                            <p className="text-white/40 text-xs">Make sure your QuickBooks has bank or credit card accounts.</p>
                                        </div>
                                    )}

                                    {isLimitReached && (
                                        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200 flex items-start gap-3">
                                            <Crown className="h-5 w-5 shrink-0 mt-0.5" />
                                            <div className="text-xs leading-relaxed">
                                                You've reached your plan limit. <a href="https://billing.stripe.com/p/login/test_..." target="_blank" className="underline font-bold hover:text-white">Upgrade to Pro</a> to connect more accounts.
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {step === 'preview' && previewStats && (
                            <div className="absolute inset-0 bg-[#0a0a0a] z-10 flex flex-col p-6 animate-in slide-in-from-right-4">
                                <h3 className="text-xl font-bold text-white mb-6">Import Summary</h3>

                                <div className="space-y-4 flex-1">
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-1">
                                        <p className="text-sm text-white/50">Total Transactions Found</p>
                                        <p className="text-3xl font-mono font-bold text-white">{previewStats.total_transactions}</p>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-1">
                                            <p className="text-xs text-emerald-400 font-bold uppercase tracking-wider">Matched</p>
                                            <p className="text-2xl font-mono font-bold text-white">{previewStats.already_matched}</p>
                                            <p className="text-[10px] text-white/40">Already categorized</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-brand/10 border border-brand/20 space-y-1">
                                            <p className="text-xs text-brand font-bold uppercase tracking-wider">To Analyze</p>
                                            <p className="text-2xl font-mono font-bold text-white">{previewStats.to_analyze}</p>
                                            <p className="text-[10px] text-white/40">Needs AI review</p>
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-start gap-3">
                                        <Sparkles className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
                                        <div>
                                            <p className="text-sm font-bold text-blue-200 mb-1">AI Analysis Available</p>
                                            <p className="text-xs text-blue-200 leading-relaxed">
                                                Importing is free. You can later use the <strong>AI Sparkles</strong> on individual transactions to analyze them (1 token each).
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end gap-3 mt-auto pt-6 border-t border-white/5">
                                    <button
                                        onClick={() => setStep('select')}
                                        className="px-4 py-2 text-sm font-medium text-white/50 hover:text-white transition-colors"
                                    >
                                        Back
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        disabled={submitting}
                                        className="px-6 py-2 rounded-lg bg-brand hover:bg-brand/90 text-black font-bold text-sm flex items-center gap-2 disabled:opacity-50 transition-colors"
                                    >
                                        {submitting ? <Loader2 className="animate-spin h-4 w-4" /> : null}
                                        {submitting ? 'Importing...' : 'Confirm Import'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {previewLoading && (
                            <div className="absolute inset-0 bg-[#0a0a0a] z-20 flex flex-col items-center justify-center gap-4">
                                <Loader2 className="animate-spin text-brand" size={40} />
                                <p className="text-sm text-white/40">Analyzing transactions...</p>
                            </div>
                        )}

                        {step === 'select' && (
                            <div className="p-4 bg-white/5 flex justify-end gap-3 border-t border-white/5">
                                <button
                                    onClick={onClose}
                                    disabled={previewLoading}
                                    className="px-4 py-2 text-sm font-medium text-white/50 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handlePreview}
                                    disabled={loading || previewLoading || selectedIds.length === 0}
                                    className="px-6 py-2 rounded-lg bg-brand hover:bg-brand/90 text-black font-bold text-sm flex items-center gap-2 disabled:opacity-50 transition-colors"
                                >
                                    {previewLoading ? <Loader2 className="animate-spin h-4 w-4" /> : null}
                                    {previewLoading ? 'Analyzing...' : 'Review Import'}
                                </button>
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
