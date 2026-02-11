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
import Footer from '@/components/Footer';

export const dynamic = 'force-dynamic';

import Skeleton from '@/components/Skeleton';

const COLORS = ['#00dfd8', '#008f7a', '#005f56', '#2dd4bf', '#10b981'];


export default function AnalyticsPage() {
    const { spendTrend, categoryData, kpi, loading } = useAnalytics();

    const [isMounted, setIsMounted] = React.useState(false);

    React.useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted) {
        return null;
    }

    if (loading) return (
        <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto">
            <header className="mb-12 flex justify-between items-end">
                <div className="space-y-4">
                    <Skeleton width="200px" height="20px" />
                    <Skeleton width="400px" height="60px" />
                    <Skeleton width="300px" height="30px" />
                </div>
            </header>
            <BentoGrid>
                <BentoTile className="md:col-span-2 md:row-span-2 min-h-[400px]">
                    <Skeleton height="100%" />
                </BentoTile>
                <BentoTile className="md:col-span-1 md:row-span-2 min-h-[400px]">
                    <Skeleton height="100%" />
                </BentoTile>
                <BentoTile><Skeleton height="100px" /></BentoTile>
                <BentoTile><Skeleton height="100px" /></BentoTile>
                <BentoTile><Skeleton height="100px" /></BentoTile>
            </BentoGrid>
        </div>
    );

    return (
        <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto selection:bg-brand selection:text-white pb-32">
            {/* Header */}
            <header className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8 header-glow">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    <div className="flex items-center gap-2.5 mb-3 text-xs sm:text-sm">
                        <Link href="/dashboard" className="flex items-center gap-2 text-brand hover:text-white transition-all group">
                            <ArrowUpRight className="rotate-180 group-hover:-translate-x-1" size={16} />
                            <span className="text-[10px] font-black tracking-[0.3em] uppercase">Back to Hub</span>
                        </Link>
                    </div>
                    <h1 className="text-5xl sm:text-7xl font-black tracking-tighter mb-3 leading-none heading-shimmer">
                        Financials
                    </h1>
                    <p className="text-white/30 text-sm sm:text-base font-medium max-w-sm">
                        Real-time intelligence on cash flow and spend velocity.
                    </p>
                </motion.div>

                <div className="flex items-center gap-4">
                    <button className="btn-glass px-5 py-3 text-xs font-black uppercase tracking-widest flex items-center gap-2.5 transition-all tactile-item">
                        <Calendar size={16} className="text-brand" />
                        Last 30 Days
                    </button>
                    <div className="ml-2 ring-2 ring-white/5 rounded-full p-1 bg-white/5">
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
                            <h3 className="text-xl font-bold">Spend Sources</h3>
                            <p className="text-xs text-white/40">Category Distribution</p>
                        </div>
                    </div>
                    <div className="flex-1 flex flex-col justify-center">
                        <CategoryPieChart data={categoryData} />
                    </div>
                    <div className="mt-8 space-y-2.5">
                        {categoryData.slice(0, 3).map((cat, i) => (
                            <div key={i} className="flex items-center justify-between p-3.5 rounded-2xl bg-white/[0.03] border border-white/5 mx-2 glass-card tactile-item">
                                <div className="flex items-center gap-2.5">
                                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">{cat.name}</span>
                                </div>
                                <span className="text-xs font-mono font-bold text-white data-field">${cat.value.toLocaleString('en-US')}</span>
                            </div>
                        ))}
                    </div>
                </BentoTile>

                {/* KPI Cards */}
                <BentoTile delay={0.1} className="tactile-item border-white/5">
                    <p className="text-[10px] text-white/20 font-black uppercase tracking-[0.2em] mb-4">Gross Outflow</p>
                    <h4 className="text-4xl font-black text-white tracking-tighter mb-4">${kpi.totalSpend.toLocaleString('en-US')}</h4>
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-rose-400 bg-rose-400/10 px-2.5 py-1.5 rounded-xl w-fit">
                        <TrendingUp size={12} /> +12.5% vs Prev
                    </div>
                </BentoTile>

                <BentoTile delay={0.2} className="border-brand/20 bg-brand/5 tactile-item">
                    <p className="text-[10px] text-brand/60 font-black uppercase tracking-[0.2em] mb-4">Total Inflow</p>
                    <h4 className="text-4xl font-black text-white tracking-tighter mb-4">${kpi.totalIncome.toLocaleString('en-US')}</h4>
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-emerald-400 bg-emerald-400/10 px-2.5 py-1.5 rounded-xl w-fit">
                        <TrendingUp size={12} /> +5.2% vs Prev
                    </div>
                </BentoTile>

                <BentoTile delay={0.3} className="tactile-item border-white/5">
                    <p className="text-[10px] text-white/20 font-black uppercase tracking-[0.2em] mb-4">Net Liquidity</p>
                    <h4 className="text-4xl font-black text-white tracking-tighter mb-4 font-mono">
                        {kpi.netFlow >= 0 ? '+' : ''}${kpi.netFlow.toLocaleString('en-US')}
                    </h4>
                    <p className="text-[10px] font-black uppercase tracking-widest text-white/20 mt-2">
                        {kpi.netFlow >= 0 ? "Margin Optimized" : "Burn Accelerated"}
                    </p>
                </BentoTile>

            </BentoGrid>
            <Footer />
        </div>
    );
}
