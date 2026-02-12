"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const COLORS = ['#00dfd8', '#008f7a', '#005f56', '#2dd4bf', '#10b981', '#f59e0b', '#ef4444'];

interface ChartData {
    name: string;
    value: number; // For Pie
    count?: number; // For Bar (mapped to value)
    currency?: string;
    region?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-black/80 backdrop-blur-xl border border-white/10 p-3 rounded-lg shadow-2xl">
                <p className="text-brand font-bold uppercase text-[10px] tracking-widest mb-1">{payload[0].name}</p>
                <p className="text-white font-black text-lg">
                    {payload[0].value}
                </p>
            </div>
        );
    }
    return null;
};

export const TierDistributionChart = ({ data }: { data: ChartData[] }) => {
    return (
        <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                </PieChart>
            </ResponsiveContainer>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                <p className="text-[10px] text-white/20 font-black uppercase tracking-widest">Tiers</p>
            </div>
        </div>
    );
};

export const LocationBarChart = ({ data }: { data: any[] }) => {
    // Map data to match BarChart expectations
    const chartData = data.map(d => ({
        name: d.region,
        count: d.count,
        currency: d.currency
    }));

    return (
        <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" hide />
                    <YAxis
                        dataKey="name"
                        type="category"
                        stroke="rgba(255,255,255,0.3)"
                        fontSize={10}
                        fontWeight={700}
                        width={100}
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} content={<CustomTooltip />} />
                    <Bar dataKey="count" fill="#00dfd8" radius={[0, 4, 4, 0]} barSize={20}>
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};
