"use client";

import React from 'react';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { SpendTrendChart } from '@/components/charts/SpendTrendChart';
import { CategoryPieChart } from '@/components/charts/CategoryPieChart';
import { motion } from 'framer-motion';
import { TrendingUp, PieChart, Calendar, ArrowUpRight } from 'lucide-react';
import Link from 'next/link';
import { UserButton } from "@clerk/nextjs";
import { useAnalytics } from '@/hooks/useAnalytics';

export default function AnalyticsPage() {
    const { spendTrend, categoryData, kpi, loading } = useAnalytics();

    if (loading) return <div className="min-h-screen flex items-center justify-center text-white/40">Loading insights...</div>;

    return (
        <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto">
            {/* Header */}
            <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-8">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    <div className="flex items-center gap-2 mb-2 text-brand">
                        <Link href="/dashboard" className="flex items-center gap-2 text-sm font-bold tracking-widest uppercase hover:text-white transition-colors">
                            <ArrowUpRight className="rotate-180" size={16} /> Back to Dashboard
                        </Link>
                    </div>
                    <h1 className="text-[clamp(2rem,6vw,3.5rem)] font-black tracking-tight leading-[1.1]">
                        Financial Insights
                    </h1>
                    <p className="text-white/40 text-lg mt-2">Real-time analysis of your cash flow and spend.</p>
                </motion.div>

                <div className="flex items-center gap-4">
                    <button className="btn-glass px-4 py-2 text-sm flex items-center gap-2">
                        <Calendar size={16} />
                        Last 30 Days
                    </button>
                    <div className="ml-2">
                        <UserButton afterSignOutUrl="/" />
                    </div>
                </div>
            </header>

            {/* Main Grid */}
            <BentoGrid>
                {/* Main Trend Chart - Wide */}
                <BentoTile className="md:col-span-2 md:row-span-2 min-h-[400px]">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-xl bg-brand/10 text-brand flex items-center justify-center">
                            <TrendingUp size={20} />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold">Cash Flow Trend</h3>
                            <p className="text-xs text-white/40">Income vs Expenses (Daily)</p>
                        </div>
                    </div>
                    <SpendTrendChart data={spendTrend} />
                </BentoTile>

                {/* Category Breakdown - Tall */}
                <BentoTile className="md:col-span-1 md:row-span-2 min-h-[400px] bg-white/[0.02]">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-xl bg-brand-accent/10 text-brand-accent flex items-center justify-center">
                            <PieChart size={20} />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold">Spend by Category</h3>
                            <p className="text-xs text-white/40">Where your money goes</p>
                        </div>
                    </div>
                    <div className="flex-1 flex flex-col justify-center">
                        <CategoryPieChart data={categoryData} />
                    </div>
                    <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/5 mx-2">
                        <p className="text-xs text-white/40 mb-2">Insight</p>
                        <p className="text-sm font-medium leading-relaxed">
                            <span className="text-brand font-bold">{categoryData[0]?.name || 'Top Category'}</span> is your biggest expense driver this month, accounting for {(categoryData[0]?.value / kpi.totalSpend * 100 || 0).toFixed(1)}% of flow.
                        </p>
                    </div>
                </BentoTile>

                {/* KPI Cards */}
                <BentoTile delay={0.1}>
                    <p className="text-sm text-white/40 font-bold uppercase tracking-wider mb-2">Total Spend</p>
                    <h4 className="text-4xl font-black text-white mb-2">${kpi.totalSpend.toLocaleString()}</h4>
                    <div className="flex items-center gap-2 text-xs font-bold text-rose-400 bg-rose-400/10 px-2 py-1 rounded w-fit">
                        <TrendingUp size={12} /> +12.5% vs last month
                    </div>
                </BentoTile>

                <BentoTile delay={0.2} className="border-brand/20 bg-brand/5">
                    <p className="text-sm text-brand font-bold uppercase tracking-wider mb-2">Total Income</p>
                    <h4 className="text-4xl font-black text-white mb-2">${kpi.totalIncome.toLocaleString()}</h4>
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded w-fit">
                        <TrendingUp size={12} /> +5.2% vs last month
                    </div>
                </BentoTile>

                <BentoTile delay={0.3}>
                    <p className="text-sm text-white/40 font-bold uppercase tracking-wider mb-2">Net Cash Flow</p>
                    <h4 className="text-4xl font-black text-white mb-2">
                        {kpi.netFlow >= 0 ? '+' : ''}${kpi.netFlow.toLocaleString()}
                    </h4>
                    <p className="text-xs text-white/30 mt-2">
                        {kpi.netFlow >= 0 ? "Healthy margin maintained." : "Burn rate alert."}
                    </p>
                </BentoTile>

            </BentoGrid>
        </div>
    );
}
