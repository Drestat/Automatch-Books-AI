"use client";

import React, { useState, useEffect } from 'react';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { track } from '@/lib/analytics';
import { Bot, RefreshCw, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';

const API_BASE_URL = 'http://localhost:8000/api/v1';

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

    useEffect(() => {
        fetchEvents();
    }, []);

    return (
        <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto">
            <header className="mb-12 flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-black mb-2">Admin Analytics</h1>
                    <p className="text-white/40">Internal Data Lake & AI Analysis</p>
                </div>
                <div className="flex gap-4">
                    <a
                        href={`https://analytics.google.com/analytics/web/`}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-glass px-4 py-2 flex items-center gap-2 text-sm text-white/60 hover:text-white"
                    >
                        <ExternalLink size={16} /> Open Google Analytics
                    </a>
                    <button
                        onClick={fetchEvents}
                        disabled={loading}
                        className="btn-glass px-4 py-2 flex items-center gap-2 text-sm"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh Stream
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
                <BentoTile className="md:col-span-3 md:row-span-2">
                    <h3 className="text-xl font-bold mb-4">Live Event Stream</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="text-white/40 border-b border-white/10">
                                <tr>
                                    <th className="pb-3 pl-2">Timestamp</th>
                                    <th className="pb-3">Event</th>
                                    <th className="pb-3">User</th>
                                    <th className="pb-3">Properties</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {events.map((e) => (
                                    <tr key={e.id} className="hover:bg-white/5 transition-colors">
                                        <td className="py-3 pl-2 text-white/60 text-xs font-mono">
                                            {new Date(e.timestamp).toLocaleString()}
                                        </td>
                                        <td className="py-3 font-bold text-brand">
                                            {e.event_name}
                                        </td>
                                        <td className="py-3 text-white/60 text-xs font-mono">
                                            {e.user_id}
                                        </td>
                                        <td className="py-3 text-white/40 text-xs font-mono">
                                            {JSON.stringify(e.properties)}
                                        </td>
                                    </tr>
                                ))}
                                {events.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="py-8 text-center text-white/20">No events found. Start using the app to generate data.</td>
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
