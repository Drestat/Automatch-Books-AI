"use client";

import React, { useState, useEffect } from 'react';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { Users, BarChart3, Database, RefreshCw, Trophy, Activity, Globe, DollarSign, PieChart as PieChartIcon, Map } from 'lucide-react';
import { motion } from 'framer-motion';
import { TierDistributionChart, LocationBarChart } from '@/components/admin/AdminCharts';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

interface AdminStats {
    kpi: {
        mrr: number;
        totalVolume: number;
        activeUsers: number;
        avgRevenuePerUser: number;
    };
    distributions: {
        tiers: { name: string; value: number }[];
        locations: { currency: string; region: string; count: number }[];
    };
    leaderboard: {
        realmId: string;
        email: string;
        tier: string;
        lastActive: string | null;
        totalSyncs: number;
        totalItems: number;
        totalTransactions: number;
    }[];
}

export default function AdminDashboard() {
    const [data, setData] = useState<AdminStats | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchUsage = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/analytics/admin/usage`);
            const json = await res.json();
            if (json.kpi) {
                setData(json);
            }
        } catch (e) {
            console.error("Failed to fetch usage data", e);
        } finally {
            setLoading(false);
        }
    };

    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        fetchUsage();
    }, []);

    if (!isMounted) {
        return null;
    }

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
                        <span className="text-sm font-bold tracking-[0.3em] uppercase text-brand">Mission Control</span>
                    </div>
                    <h1 className="text-5xl font-black tracking-tight mb-4">
                        Global <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Intelligence</span>
                    </h1>
                    <p className="text-white/40 text-lg max-w-md">
                        Real-time telemetry, revenue metrics, and fleet status associated with the AutoMatch Books AI network.
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
                        <span className="font-bold">{loading ? 'Refreshing...' : 'Refresh Uplink'}</span>
                    </button>
                </motion.div>
            </header>

            <main>
                <BentoGrid>
                    {/* KPI: MRR */}
                    <BentoTile className="md:col-span-1 bg-gradient-to-br from-emerald-500/10 to-transparent border-emerald-500/20">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 rounded-xl bg-emerald-500/20 text-emerald-400">
                                <DollarSign size={24} />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-white/30 uppercase tracking-widest">Monthly Recurring Revenue</span>
                                <h3 className="text-3xl font-black leading-none">${data?.kpi.mrr.toFixed(2) || '0.00'}</h3>
                            </div>
                        </div>
                        <p className="text-sm text-white/40">Current run rate based on active subscriptions.</p>
                    </BentoTile>

                    {/* KPI: Total Volume */}
                    <BentoTile className="md:col-span-1 border-white/5 bg-white/[0.01]">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 rounded-xl bg-blue-500/20 text-blue-400">
                                <Activity size={24} />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-white/30 uppercase tracking-widest">Total Processed Volume</span>
                                <h3 className="text-3xl font-black leading-none">${(data?.kpi.totalVolume || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</h3>
                            </div>
                        </div>
                        <p className="text-sm text-white/40">Aggregate financial value managed by the platform.</p>
                    </BentoTile>

                    {/* KPI: Users */}
                    <BentoTile className="md:col-span-1 border-white/5">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 rounded-xl bg-purple-500/20 text-purple-400">
                                <Users size={24} />
                            </div>
                            <div>
                                <span className="text-xs font-bold text-white/30 uppercase tracking-widest">Active Fleet</span>
                                <h3 className="text-3xl font-black leading-none">{data?.kpi.activeUsers || 0}</h3>
                            </div>
                        </div>
                        <p className="text-sm text-white/40">Total registered users across all tiers.</p>
                    </BentoTile>

                    {/* Chart: Tier Distribution */}
                    <BentoTile className="md:col-span-1 border-white/5 flex flex-col">
                        <div className="flex items-center gap-3 mb-4">
                            <PieChartIcon size={16} className="text-white/40" />
                            <h3 className="font-bold text-sm uppercase tracking-wider text-white/60">Tier Distribution</h3>
                        </div>
                        <div className="flex-1 min-h-[200px]">
                            {data && <TierDistributionChart data={data.distributions.tiers} />}
                        </div>
                    </BentoTile>

                    {/* Chart: Locations */}
                    <BentoTile className="md:col-span-2 border-white/5 flex flex-col">
                        <div className="flex items-center gap-3 mb-4">
                            <Globe size={16} className="text-white/40" />
                            <h3 className="font-bold text-sm uppercase tracking-wider text-white/60">Global Presence (Currency Derived)</h3>
                        </div>
                        <div className="flex-1 min-h-[200px]">
                            {data && <LocationBarChart data={data.distributions.locations} />}
                        </div>
                    </BentoTile>

                    {/* God Mode Control Panel */}
                    <BentoTile className="md:col-span-3 border-brand-secondary/20 bg-brand-secondary/5 mt-8 mb-8">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 rounded-lg bg-brand-secondary text-white">
                                <Trophy size={20} />
                            </div>
                            <h2 className="text-xl font-black text-white">GOD MODE: Subscription Override</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            {['free', 'personal', 'business', 'corporate', 'expired'].map((tier) => (
                                <button
                                    key={tier}
                                    onClick={async () => {
                                        try {
                                            const res = await fetch(`${API_BASE_URL}/admin/set-tier`, {
                                                method: 'POST',
                                                headers: {
                                                    'Content-Type': 'application/json',
                                                    // Since this is admin page, we assume Clerk middleware adds auth, 
                                                    // but we might need to manually pass the active user ID if not automatically handled by proxy
                                                    // For now, let's rely on the user being logged in via ClerkProvider
                                                },
                                                body: JSON.stringify({
                                                    target_user_id: "me",
                                                    tier: tier,
                                                    token_balance: tier === 'corporate' ? 1000 : 100
                                                })
                                            });
                                            if (res.ok) {
                                                alert(`Successfully switched to ${tier.toUpperCase()} tier!`);
                                                window.location.reload();
                                            } else {
                                                const err = await res.json();
                                                alert(`Failed: ${err.detail || 'Unknown error'}`);
                                            }
                                        } catch (e) {
                                            alert("Network error executing God Mode.");
                                        }
                                    }}
                                    className="btn-glass py-3 px-4 font-bold uppercase text-xs tracking-wider hover:bg-white/10"
                                >
                                    Set to {tier}
                                </button>
                            ))}
                        </div>
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
                                        <th className="pb-4">Tier</th>
                                        <th className="pb-4">Last Sync</th>
                                        <th className="pb-4 text-center">Syncs</th>
                                        <th className="pb-4 text-center">Entity Vol</th>
                                        <th className="pb-4 text-right pr-4">Transactions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {data?.leaderboard && data.leaderboard.length > 0 ? (
                                        data.leaderboard.sort((a, b) => b.totalTransactions - a.totalTransactions).map((user, idx) => (
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
                                                    <div className="text-[10px] text-white/30 truncate max-w-[150px]">{user.email}</div>
                                                </td>
                                                <td className="py-6 text-xs font-bold uppercase tracking-wider text-white/60">
                                                    {user.tier || 'Free'}
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
                                            <td colSpan={6} className="py-20 text-center">
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
