"use client";

import React, { useState, useEffect } from 'react';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { Users, BarChart3, Database, RefreshCw, Trophy, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

interface UserUsage {
    realmId: string;
    lastActive: string | null;
    totalSyncs: number;
    totalItems: number;
    totalTransactions: number;
}

export default function AdminDashboard() {
    const [usageData, setUsageData] = useState<UserUsage[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchUsage = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/analytics/admin/usage`);
            const data = await res.json();
            if (Array.isArray(data)) {
                setUsageData(data);
            }
        } catch (e) {
            console.error("Failed to fetch usage data", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsage();
    }, []);

    const totalUsers = usageData.length;
    const totalItemsProcessed = usageData.reduce((acc, curr) => acc + curr.totalItems, 0);
    const totalTxProcessed = usageData.reduce((acc, curr) => acc + curr.totalTransactions, 0);

    return (
        <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto">
            <header className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white">
                            <Database size={16} />
                        </div>
                        <span className="text-sm font-bold tracking-[0.3em] uppercase text-brand">System Administration</span>
                    </div>
                    <h1 className="text-5xl font-black tracking-tight mb-4">
                        Network <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Usage</span>
                    </h1>
                    <p className="text-white/40 text-lg max-w-md">
                        Compare account activity and monitor global data synchronization healthy.
                    </p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex gap-4"
                >
                    <button
                        onClick={fetchUsage}
                        disabled={loading}
                        className="btn-glass px-6 py-4 flex items-center gap-3 transition-all hover:bg-white/10"
                    >
                        <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
                        <span className="font-bold">{loading ? 'Refreshing...' : 'Refresh Stats'}</span>
                    </button>
                </motion.div>
            </header>

            <main>
                <BentoGrid>
                    {/* Global KPIs */}
                    <BentoTile className="md:col-span-1 bg-gradient-to-br from-brand/10 to-transparent border-brand/20">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 rounded-xl bg-brand/20 text-brand">
                                <Users size={24} />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-white/30 uppercase tracking-widest">Total Accounts</span>
                                <h3 className="text-3xl font-black leading-none">{totalUsers}</h3>
                            </div>
                        </div>
                        <p className="text-sm text-white/40">Unique QuickBooks Realms currently connected & active.</p>
                    </BentoTile>

                    <BentoTile className="md:col-span-1 border-white/5">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 rounded-xl bg-brand-secondary/20 text-brand-secondary">
                                <BarChart3 size={24} />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-white/30 uppercase tracking-widest">Global Items</span>
                                <h3 className="text-3xl font-black leading-none">{totalItemsProcessed.toLocaleString()}</h3>
                            </div>
                        </div>
                        <p className="text-sm text-white/40">Historical volume of categories and customers mirrored.</p>
                    </BentoTile>

                    <BentoTile className="md:col-span-1 border-white/5 bg-white/[0.01]">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 rounded-xl bg-emerald-500/20 text-emerald-400">
                                <Activity size={24} />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-white/30 uppercase tracking-widest">Live TX Core</span>
                                <h3 className="text-3xl font-black leading-none">{totalTxProcessed.toLocaleString()}</h3>
                            </div>
                        </div>
                        <p className="text-sm text-white/40">Total transactions managed across the entire network.</p>
                    </BentoTile>

                    {/* Leaderboard Table */}
                    <BentoTile className="md:col-span-3 mt-8 border-brand/10 shadow-2xl shadow-brand/5 overflow-hidden">
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-3">
                                <Trophy size={20} className="text-brand" />
                                <h2 className="text-xl font-bold">Usage Leaderboard</h2>
                            </div>
                            <div className="text-xs font-bold text-white/20 uppercase tracking-widest">Ranked by Transaction Volume</div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="text-[10px] uppercase tracking-[0.2em] font-bold text-white/20 border-b border-white/5">
                                    <tr>
                                        <th className="pb-4 pl-4">Account Realm ID</th>
                                        <th className="pb-4">Last Sync</th>
                                        <th className="pb-4 text-center">Syncs</th>
                                        <th className="pb-4 text-center">Entity Vol</th>
                                        <th className="pb-4 text-right pr-4">Transactions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {usageData.length > 0 ? (
                                        usageData.sort((a, b) => b.totalTransactions - a.totalTransactions).map((user, idx) => (
                                            <motion.tr
                                                key={user.realmId}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: idx * 0.05 }}
                                                className="group hover:bg-white/[0.02] transition-colors"
                                            >
                                                <td className="py-6 pl-4 font-mono text-sm">
                                                    <span className="text-brand mr-2">#{(idx + 1).toString().padStart(2, '0')}</span>
                                                    <span className="text-white/80 group-hover:text-white transition-colors">{user.realmId}</span>
                                                </td>
                                                <td className="py-6 text-xs text-white/40">
                                                    {user.lastActive ? new Date(user.lastActive).toLocaleString() : 'Never'}
                                                </td>
                                                <td className="py-6 text-center font-bold text-brand-secondary">
                                                    {user.totalSyncs}
                                                </td>
                                                <td className="py-6 text-center text-white/60">
                                                    {user.totalItems}
                                                </td>
                                                <td className="py-6 text-right pr-4">
                                                    <div className="inline-flex items-center gap-2 bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-black">
                                                        {user.totalTransactions}
                                                        <div className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
                                                    </div>
                                                </td>
                                            </motion.tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={5} className="py-20 text-center">
                                                <div className="flex flex-col items-center gap-4 text-white/20">
                                                    <Database size={48} className="opacity-10" />
                                                    <p className="font-bold italic">No user data currently synthesized. Awaiting first QBO synchronization...</p>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </BentoTile>
                </BentoGrid>
            </main>

            <footer className="mt-24 border-t border-white/5 pt-12 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-white/10">
                <div>Network Node: Primary-Alpha-01</div>
                <div>Built for Internal Ops • &copy; 2026</div>
            </footer>
        </div>
    );
}
