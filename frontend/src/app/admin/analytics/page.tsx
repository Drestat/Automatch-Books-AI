"use client";

import React, { useState, useEffect } from 'react';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { track } from '@/lib/analytics';
import { Bot, RefreshCw, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';

export const dynamic = 'force-dynamic';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

interface AnalyticsEvent {
    id: string;
    user_id: string;
    event_name: string;
    properties?: Record<string, any>;
    timestamp: string;
}

interface AIInsights {
    patterns: string[];
    suggestions: string[];
    anomalies: string[];
    error?: string;
}

export default function AdminAnalyticsPage() {
    const [events, setEvents] = useState<AnalyticsEvent[]>([]);
    const [insights, setInsights] = useState<AIInsights | null>(null);
    const [loading, setLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);

    const fetchEvents = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/analytics/events?limit=50`);
            const data = await res.json();
            if (Array.isArray(data)) {
                setEvents(data);
            }
        } catch (e) {
            console.error("Failed to fetch events", e);
        } finally {
            setLoading(false);
        }
    };

    const generateInsights = async () => {
        setAiLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/analytics/insights`, {
                method: 'POST'
            });
            const data = await res.json();
            if (data.error) {
                console.error(data.error);
            } else {
                setInsights(data);
            }
        } catch (e) {
            console.error("Failed to generate insights", e);
        } finally {
            setAiLoading(false);
        }
    };

    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        fetchEvents();
    }, []);

    if (!isMounted) {
        return null; // Prevent server-side rendering of Clerk components during build
    }

    return (
        <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto selection:bg-brand selection:text-white pb-32">
            <header className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8 header-glow">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    <div className="flex items-center gap-2.5 mb-3 text-xs sm:text-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand animate-pulse shadow-[0_0_12px_rgba(0,223,216,0.6)]" />
                        <span className="text-[10px] font-black tracking-[0.3em] text-brand uppercase">
                            Data Intelligence
                        </span>
                    </div>
                    <h1 className="text-5xl sm:text-7xl font-black tracking-tighter mb-3 leading-none heading-shimmer">
                        Analytics
                    </h1>
                    <p className="text-white/30 text-sm sm:text-base font-medium max-w-sm">
                        Internal Data Lake & Strategic AI Analysis
                    </p>
                </motion.div>
                <div className="flex gap-4">
                    <a
                        href={`https://analytics.google.com/analytics/web/`}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-glass px-5 py-3 flex items-center gap-2.5 text-xs font-black uppercase tracking-widest text-white/60 hover:text-white transition-all tactile-item"
                    >
                        <ExternalLink size={16} className="text-brand" /> GA4 Portal
                    </a>
                    <button
                        onClick={fetchEvents}
                        disabled={loading}
                        className="btn-glass px-5 py-3 flex items-center gap-2.5 text-xs font-black uppercase tracking-widest transition-all tactile-item bg-white/[0.03]"
                    >
                        <RefreshCw size={16} className={`${loading ? 'animate-spin' : ''} text-brand`} /> Refresh
                    </button>
                </div>
            </header>

            <BentoGrid>
                {/* AI Analyst Panel */}
                <BentoTile className="md:col-span-3 min-h-[300px]">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-brand/20 text-brand flex items-center justify-center">
                                <Bot size={24} />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold">Gemini 2.5 Flash Analyst</h3>
                                <p className="text-xs text-white/40">Strategic Insights on Usage Data</p>
                            </div>
                        </div>
                        <button
                            onClick={generateInsights}
                            disabled={aiLoading}
                            className="bg-brand hover:bg-brand/90 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg shadow-brand/20 transition-all disabled:opacity-50 flex items-center gap-2"
                        >
                            {aiLoading ? (
                                <>
                                    <RefreshCw size={14} className="animate-spin" /> Analyzing...
                                </>
                            ) : (
                                "Generate Usage Report"
                            )}
                        </button>
                    </div>

                    {insights ? (
                        <div className="grid md:grid-cols-3 gap-6">
                            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                                <h4 className="text-brand font-bold uppercase tracking-wider text-xs mb-3">Key Patterns</h4>
                                <ul className="space-y-2">
                                    {insights.patterns.map((p, i) => (
                                        <li key={i} className="text-sm text-white/80 border-l-2 border-brand/50 pl-2">{p}</li>
                                    ))}
                                </ul>
                            </div>
                            <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                                <h4 className="text-emerald-400 font-bold uppercase tracking-wider text-xs mb-3">Suggestions</h4>
                                <ul className="space-y-2">
                                    {insights.suggestions.map((s, i) => (
                                        <li key={i} className="text-sm text-white/80 border-l-2 border-emerald-500/50 pl-2">{s}</li>
                                    ))}
                                </ul>
                            </div>
                            <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/10">
                                <h4 className="text-rose-400 font-bold uppercase tracking-wider text-xs mb-3">Anomalies</h4>
                                <ul className="space-y-2">
                                    {insights.anomalies.map((a, i) => (
                                        <li key={i} className="text-sm text-white/80 border-l-2 border-rose-500/50 pl-2">{a}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-[200px] text-white/20 border-2 border-dashed border-white/5 rounded-xl">
                            <Bot size={48} className="mb-4 opacity-50" />
                            <p>No report generated yet. Click "Generate Usage Report" to analyze recent data.</p>
                        </div>
                    )}
                </BentoTile>

                {/* Live Event Stream */}
                <BentoTile className="md:col-span-3 min-h-[500px] overflow-hidden">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-1.5 h-6 bg-brand rounded-full" />
                        <h3 className="text-xl font-black tracking-tight uppercase">Live Activity Stream</h3>
                    </div>
                    <div className="overflow-x-auto -mx-2">
                        <table className="w-full text-left text-sm border-separate border-spacing-y-2">
                            <thead className="text-[10px] uppercase font-black tracking-[0.2em] text-white/20">
                                <tr>
                                    <th className="pb-4 pl-4">Time (UTC)</th>
                                    <th className="pb-4">Event Signature</th>
                                    <th className="pb-4">Identity</th>
                                    <th className="pb-4 text-right pr-4">Payload</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.map((e) => (
                                    <tr key={e.id} className="group transition-all hover:bg-white/[0.02]">
                                        <td className="py-4 pl-4 text-white/40 text-[10px] font-mono data-field border-t border-white/5 first:rounded-l-2xl">
                                            {new Date(e.timestamp).toLocaleTimeString()}
                                        </td>
                                        <td className="py-4 font-black text-brand tracking-tight border-t border-white/5 uppercase text-xs">
                                            {e.event_name.replace(/_/g, ' ')}
                                        </td>
                                        <td className="py-4 text-white/60 text-[10px] font-mono data-field border-t border-white/5">
                                            {e.user_id.substring(0, 12)}...
                                        </td>
                                        <td className="py-4 text-white/30 text-[10px] font-mono data-field border-t border-white/5 text-right pr-4 last:rounded-r-2xl">
                                            <div className="max-w-[300px] ml-auto overflow-hidden text-ellipsis whitespace-nowrap">
                                                {JSON.stringify(e.properties)}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {events.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="py-20 text-center">
                                            <div className="flex flex-col items-center gap-3 opacity-20">
                                                <RefreshCw size={32} className="animate-spin-slow" />
                                                <p className="text-[10px] uppercase font-black tracking-widest">Awaiting Data Stream...</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </BentoTile>
            </BentoGrid>
        </div>
    );
}
