"use client";

import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, AreaChart, Area, Legend
} from 'recharts';
import {
    TrendingUp, Users, Briefcase, DollarSign, ArrowLeft
} from 'lucide-react';
import Link from 'next/link';

// Mock Data for Analytics
const PROJECT_SPEND = [
    { name: 'Jan', labor: 4000, material: 2400, overhead: 2400 },
    { name: 'Feb', labor: 3000, material: 1398, overhead: 2210 },
    { name: 'Mar', labor: 2000, material: 9800, overhead: 2290 },
    { name: 'Apr', labor: 2780, material: 3908, overhead: 2000 },
    { name: 'May', labor: 1890, material: 4800, overhead: 2181 },
    { name: 'Jun', labor: 2390, material: 3800, overhead: 2500 },
];

const SUBCONTRACTOR_DATA = [
    { name: 'Alpha Builders', value: 45000, color: '#6366f1' },
    { name: 'Prime Electrical', value: 32000, color: '#a855f7' },
    { name: 'Urban Plumbing', value: 28000, color: '#ec4899' },
    { name: 'Skyline HVAC', value: 15000, color: '#3b82f6' },
];

const CATEGORY_DISTRIBUTION = [
    { name: 'Materials', value: 40 },
    { name: 'Labor', value: 35 },
    { name: 'Taxes', value: 15 },
    { name: 'Misc', value: 10 },
];

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#3b82f6'];

export default function AnalyticsPage() {
    return (
        <div className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
                <div>
                    <Link href="/" className="flex items-center text-brand mb-4 hover:underline transition-all">
                        <ArrowLeft size={16} className="mr-2" />
                        Back to Dashboard
                    </Link>
                    <h1 className="text-5xl font-extrabold tracking-tighter">Financial Insights</h1>
                    <p className="text-white/50 mt-2 text-lg">Meticulous tracking of your project capital</p>
                </div>

                <div className="flex gap-4">
                    <div className="glass-panel px-6 py-4 flex items-center gap-4">
                        <div className="bg-brand/20 p-3 rounded-2xl text-brand">
                            <DollarSign size={24} />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-widest text-white/40">Total Spend</p>
                            <p className="text-2xl font-bold">$124,500</p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Grid */}
            <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Project Cost Tracking - Large Area Chart */}
                <section className="lg:col-span-2 glass-panel p-8" aria-label="Project Cost Trajectory">
                    <div className="flex justify-between items-center mb-8">
                        <h3 className="text-xl font-semibold flex items-center gap-2">
                            <TrendingUp size={20} className="text-brand" />
                            Project Cost Trajectory
                        </h3>
                        <div className="flex gap-2">
                            <span className="flex items-center gap-1 text-[10px] text-white/40 uppercase">
                                <div className="w-2 h-2 rounded-full bg-brand" /> Labor
                            </span>
                            <span className="flex items-center gap-1 text-[10px] text-white/40 uppercase">
                                <div className="w-2 h-2 rounded-full bg-purple-500" /> Material
                            </span>
                        </div>
                    </div>

                    <div className="h-[350px] w-full" role="img" aria-label="Area chart showing labor and material costs over time">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={PROJECT_SPEND}>
                                <defs>
                                    <linearGradient id="colorLabor" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="labor" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorLabor)" />
                                <Area type="monotone" dataKey="material" stroke="#a855f7" strokeWidth={3} fill="none" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                {/* Category Breakdown - Pie Chart */}
                <section className="glass-panel p-8" aria-label="Capital Distribution">
                    <h3 className="text-xl font-semibold mb-8 flex items-center gap-2">
                        <Briefcase size={20} className="text-brand" />
                        Capital Distribution
                    </h3>
                    <div className="h-[250px] w-full relative" role="img" aria-label="Pie chart showing distribution of capital among labor, materials, taxes, and misc">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={CATEGORY_DISTRIBUTION}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={8}
                                    dataKey="value"
                                >
                                    {CATEGORY_DISTRIBUTION.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                            <p className="text-xs text-white/40 uppercase">Top Exp</p>
                            <p className="text-xl font-bold">Labor</p>
                        </div>
                    </div>
                    <div className="mt-8 space-y-3">
                        {CATEGORY_DISTRIBUTION.map((item, i) => (
                            <div key={item.name} className="flex justify-between items-center text-sm">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                                    <span className="text-white/60">{item.name}</span>
                                </div>
                                <span className="font-medium">{item.value}%</span>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Subcontractor Spend - Bar Chart */}
                <section className="lg:col-span-3 glass-panel p-8 mt-4" aria-label="Subcontractor Engagement">
                    <h3 className="text-xl font-semibold mb-8 flex items-center gap-2">
                        <Users size={20} className="text-brand" />
                        Subcontractor Engagement
                    </h3>
                    <div className="h-[300px] w-full" role="img" aria-label="Bar chart showing spending per subcontractor">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart layout="vertical" data={SUBCONTRACTOR_DATA} margin={{ left: 40 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                                <XAxis type="number" hide />
                                <YAxis
                                    type="category"
                                    dataKey="name"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: 'rgba(255,255,255,0.8)', fontSize: 13, fontWeight: 500 }}
                                />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                    contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px' }}
                                />
                                <Bar
                                    dataKey="value"
                                    radius={[0, 10, 10, 0]}
                                    barSize={32}
                                >
                                    {SUBCONTRACTOR_DATA.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>

            </main>

            <footer className="mt-20 text-center pb-12">
                <p className="text-white/20 text-xs tracking-widest uppercase">Precision Financial Intelligence v3.0</p>
            </footer>
        </div>
    );
}
