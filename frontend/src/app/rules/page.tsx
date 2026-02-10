"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ShieldCheck,
    Plus,
    Trash2,
    Search,
    ChevronRight,
    Activity,
    Settings2,
    Zap,
    ArrowLeft,
    Sparkles,
    Tag,
    Building2,
    DollarSign,
    Info,
    CheckCircle2,
    X,
    Filter
} from 'lucide-react';
import Link from 'next/link';
import { useQBO } from '@/hooks/useQBO';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

interface Rule {
    id: string;
    name: string;
    priority: number;
    conditions: {
        description_contains?: string;
        amount_min?: number;
        amount_max?: number;
    };
    action: {
        category?: string;
        tag?: string;
    };
}

interface Alias {
    id: string;
    alias: string;
    vendor_id: string;
    vendor_name: string;
}

export default function RulesPage() {
    const { realmId, categories, vendors, showToast } = useQBO();
    const [activeTab, setActiveTab] = useState<'rules' | 'aliases'>('rules');
    const [rules, setRules] = useState<Rule[]>([]);
    const [aliases, setAliases] = useState<Alias[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Form State
    const [newRule, setNewRule] = useState<Partial<Rule>>({
        name: '',
        priority: 10,
        conditions: { description_contains: '' },
        action: { category: '' }
    });
    const [newAlias, setNewAlias] = useState<{ alias: string, vendor_id: string }>({
        alias: '',
        vendor_id: ''
    });

    const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

    useEffect(() => {
        if (realmId) {
            fetchData();
        }
    }, [realmId]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [rulesRes, aliasesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/rules?realm_id=${realmId}`),
                fetch(`${API_BASE_URL}/aliases?realm_id=${realmId}`)
            ]);

            if (rulesRes.ok) setRules(await rulesRes.json());
            if (aliasesRes.ok) setAliases(await aliasesRes.json());
        } catch (error) {
            console.error("Fetch Data Error:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateRule = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_BASE_URL}/rules?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newRule)
            });
            if (res.ok) {
                showToast("Rule created successfully", "success");
                setShowCreateModal(false);
                fetchData();
            }
        } catch (error) {
            showToast("Failed to create rule", "error");
        }
    };

    const handleCreateAlias = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_BASE_URL}/aliases?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newAlias)
            });
            if (res.ok) {
                showToast("Alias created successfully", "success");
                setShowCreateModal(false);
                fetchData();
            }
        } catch (error) {
            showToast("Failed to create alias", "error");
        }
    };

    const handleDeleteRule = async (id: string) => {
        if (!confirm("Are you sure you want to delete this rule?")) return;
        try {
            const res = await fetch(`${API_BASE_URL}/rules/${id}?realm_id=${realmId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                showToast("Rule deleted", "info");
                fetchData();
            }
        } catch (error) {
            showToast("Failed to delete rule", "error");
        }
    };

    const handleDeleteAlias = async (id: string) => {
        if (!confirm("Are you sure you want to delete this alias?")) return;
        try {
            const res = await fetch(`${API_BASE_URL}/aliases/${id}?realm_id=${realmId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                showToast("Alias deleted", "info");
                fetchData();
            }
        } catch (error) {
            showToast("Failed to delete alias", "error");
        }
    };

    return (
        <main className="min-h-screen bg-[#020617] text-white selection:bg-brand/30">
            <Navbar />

            {/* Ambient Background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand/10 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-brand-accent/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }} />
            </div>

            <div className="relative z-10 max-w-7xl mx-auto px-4 pt-24 pb-20">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                    >
                        <Link href="/dashboard" className="flex items-center gap-2 text-white/40 hover:text-white transition-colors text-[10px] uppercase tracking-widest font-bold mb-4 group">
                            <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Back to Dashboard
                        </Link>
                        <h1 className="text-4xl md:text-5xl font-black tracking-tighter mb-2">
                            Autonomous <span className="text-brand">Engine</span>
                        </h1>
                        <p className="text-white/40 font-medium max-w-xl">
                            Configure deterministic logic to override AI suggestions. Rules and Aliases ensure 100% accuracy for recurring patterns.
                        </p>
                    </motion.div>

                    <motion.button
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-2 px-6 py-3 bg-brand rounded-2xl font-black text-xs uppercase tracking-widest hover:brightness-110 shadow-xl shadow-brand/20 border border-white/10"
                    >
                        <Plus size={18} /> New {activeTab === 'rules' ? 'Rule' : 'Alias'}
                    </motion.button>
                </div>

                {/* Tab Switcher */}
                <div className="flex gap-4 mb-8 border-b border-white/5 pb-1">
                    <button
                        onClick={() => setActiveTab('rules')}
                        className={`px-4 py-2 text-[10px] uppercase tracking-widest font-black transition-all relative ${activeTab === 'rules' ? 'text-brand' : 'text-white/30 hover:text-white/60'}`}
                    >
                        Classification Rules
                        {activeTab === 'rules' && <motion.div layoutId="tab-active" className="absolute bottom-[-1px] left-0 right-0 h-0.5 bg-brand" />}
                    </button>
                    <button
                        onClick={() => setActiveTab('aliases')}
                        className={`px-4 py-2 text-[10px] uppercase tracking-widest font-black transition-all relative ${activeTab === 'aliases' ? 'text-brand' : 'text-white/30 hover:text-white/60'}`}
                    >
                        Vendor Normalization
                        {activeTab === 'aliases' && <motion.div layoutId="tab-active" className="absolute bottom-[-1px] left-0 right-0 h-0.5 bg-brand" />}
                    </button>
                </div>

                {/* Content Area */}
                <AnimatePresence mode="wait">
                    {loading ? (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col items-center justify-center py-20"
                        >
                            <div className="w-12 h-12 border-4 border-brand/20 border-t-brand rounded-full animate-spin mb-4" />
                            <p className="text-[10px] uppercase tracking-[0.2em] font-black text-white/20">Syncing Logic...</p>
                        </motion.div>
                    ) : activeTab === 'rules' ? (
                        <motion.div
                            key="rules-list"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                        >
                            {rules.length === 0 ? (
                                <div className="col-span-full py-20 text-center glass-panel border-dashed border-white/10">
                                    <ShieldCheck size={48} className="mx-auto text-white/5 mb-4" />
                                    <p className="text-white/30 font-medium">No active classification rules yet.</p>
                                </div>
                            ) : rules.map((rule) => (
                                <div key={rule.id} className="glass-panel group hover:border-brand/30 transition-all p-6">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-2 rounded-xl bg-brand/10 text-brand">
                                            <ShieldCheck size={20} />
                                        </div>
                                        <button
                                            onClick={() => handleDeleteRule(rule.id)}
                                            className="p-2 rounded-lg hover:bg-rose-500/10 text-white/20 hover:text-rose-400 transition-all"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                    <h3 className="text-lg font-black tracking-tight mb-4">{rule.name}</h3>

                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <p className="text-[9px] uppercase tracking-widest font-bold text-white/20">Conditions</p>
                                            {rule.conditions.description_contains && (
                                                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/5">
                                                    <Search size={12} className="text-white/30" />
                                                    <span className="text-[11px] font-medium text-white/70">Contains: <span className="text-white">"{rule.conditions.description_contains}"</span></span>
                                                </div>
                                            )}
                                        </div>

                                        <div className="space-y-2">
                                            <p className="text-[9px] uppercase tracking-widest font-bold text-white/20">Action</p>
                                            {rule.action.category && (
                                                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-accent/5 border border-brand-accent/10">
                                                    <Tag size={12} className="text-brand-accent/60" />
                                                    <span className="text-[11px] font-medium text-white/70">Assign: <span className="text-brand-accent font-black uppercase tracking-wider">{rule.action.category}</span></span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="aliases-list"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                        >
                            <div className="glass-panel overflow-hidden border-white/5">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-white/[0.02] border-b border-white/5">
                                            <th className="px-6 py-4 text-[10px] uppercase tracking-[0.2em] font-black text-white/30">Bank Description Pattern</th>
                                            <th className="px-6 py-4 text-[10px] uppercase tracking-[0.2em] font-black text-white/30">Canonical Merchant</th>
                                            <th className="px-6 py-4 text-[10px] uppercase tracking-[0.2em] font-black text-white/30">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {aliases.length === 0 ? (
                                            <tr>
                                                <td colSpan={3} className="px-6 py-20 text-center">
                                                    <Activity size={48} className="mx-auto text-white/5 mb-4" />
                                                    <p className="text-white/30 font-medium">No vendor normalization rules yet.</p>
                                                </td>
                                            </tr>
                                        ) : aliases.map((alias) => (
                                            <tr key={alias.id} className="group hover:bg-white/[0.01] transition-colors">
                                                <td className="px-6 py-5">
                                                    <code className="text-xs bg-white/5 px-2 py-1 rounded text-white/70">*{alias.alias.toLowerCase()}*</code>
                                                </td>
                                                <td className="px-6 py-5">
                                                    <div className="flex items-center gap-2 font-bold text-sm">
                                                        <Building2 size={14} className="text-brand" />
                                                        {alias.vendor_name}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-5">
                                                    <button
                                                        onClick={() => handleDeleteAlias(alias.id)}
                                                        className="p-2 rounded-lg hover:bg-rose-500/10 text-white/10 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-all"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Create Modal */}
                <AnimatePresence>
                    {showCreateModal && (
                        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setShowCreateModal(false)}
                                className="absolute inset-0 bg-black/60 backdrop-blur-md"
                            />
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                                className="relative w-full max-w-xl glass-panel border-white/10 p-8 shadow-2xl"
                            >
                                <div className="flex justify-between items-center mb-8">
                                    <h2 className="text-2xl font-black tracking-tight uppercase">New {activeTab === 'rules' ? 'Rule' : 'Alias'}</h2>
                                    <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-white/5 rounded-full text-white/40 hover:text-white transition-all">
                                        <X size={20} />
                                    </button>
                                </div>

                                {activeTab === 'rules' ? (
                                    <form onSubmit={handleCreateRule} className="space-y-6">
                                        <div>
                                            <label className="block text-[10px] uppercase tracking-widest font-black text-white/40 mb-2">Rule Name</label>
                                            <input
                                                type="text"
                                                required
                                                placeholder="e.g., Starbucks Auto-Categorize"
                                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-brand/40 transition-all outline-none"
                                                value={newRule.name}
                                                onChange={e => setNewRule({ ...newRule, name: e.target.value })}
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-[10px] uppercase tracking-widest font-black text-white/40 mb-2">Condition: Match Path</label>
                                                <input
                                                    type="text"
                                                    placeholder="STARBUCKS"
                                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-brand/40 transition-all outline-none"
                                                    value={newRule.conditions?.description_contains}
                                                    onChange={e => setNewRule({ ...newRule, conditions: { ...newRule.conditions, description_contains: e.target.value } })}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-[10px] uppercase tracking-widest font-black text-white/40 mb-2">Priority (0-100)</label>
                                                <input
                                                    type="number"
                                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-brand/40 transition-all outline-none"
                                                    value={newRule.priority}
                                                    onChange={e => setNewRule({ ...newRule, priority: parseInt(e.target.value) })}
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <label className="block text-[10px] uppercase tracking-widest font-black text-white/40 mb-2">Action: Assign Category</label>
                                            <select
                                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-brand/40 transition-all outline-none appearance-none"
                                                value={newRule.action?.category}
                                                onChange={e => setNewRule({ ...newRule, action: { ...newRule.action, category: e.target.value } })}
                                            >
                                                <option value="">Select Category</option>
                                                {categories.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                                            </select>
                                        </div>

                                        <button className="w-full py-4 bg-brand rounded-2xl font-black text-xs uppercase tracking-widest hover:brightness-110 shadow-xl shadow-brand/20 border border-white/10 transition-all active:scale-[0.98]">
                                            Activate Rule
                                        </button>
                                    </form>
                                ) : (
                                    <form onSubmit={handleCreateAlias} className="space-y-6">
                                        <div>
                                            <label className="block text-[10px] uppercase tracking-widest font-black text-white/40 mb-2">Description Snippet</label>
                                            <input
                                                type="text"
                                                placeholder="e.g., ADOBE *PHOTOG"
                                                required
                                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-brand/40 transition-all outline-none"
                                                value={newAlias.alias}
                                                onChange={e => setNewAlias({ ...newAlias, alias: e.target.value })}
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-[10px] uppercase tracking-widest font-black text-white/40 mb-2">Map to Merchant</label>
                                            <select
                                                required
                                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-brand/40 transition-all outline-none appearance-none"
                                                value={newAlias.vendor_id}
                                                onChange={e => setNewAlias({ ...newAlias, vendor_id: e.target.value })}
                                            >
                                                <option value="">Select Official Vendor</option>
                                                {vendors.map(v => <option key={v.id} value={v.id}>{v.display_name}</option>)}
                                            </select>
                                        </div>

                                        <button className="w-full py-4 bg-brand-accent/80 text-black rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-brand-accent shadow-xl border border-white/10 transition-all active:scale-[0.98]">
                                            Create Mapping
                                        </button>
                                    </form>
                                )}
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>
            </div>

            <Footer />
        </main>
    );
}

