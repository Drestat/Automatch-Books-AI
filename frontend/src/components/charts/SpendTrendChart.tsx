"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CustomTooltip } from './CustomTooltip';

interface SpendTrendChartProps {
    data: {
        name: string;
        income: number;
        expense: number;
    }[];
}

export const SpendTrendChart = ({ data }: SpendTrendChartProps) => {
    return (
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                    data={data}
                    margin={{
                        top: 10,
                        right: 10,
                        left: 0,
                        bottom: 0,
                    }}
                >
                    <defs>
                        <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#00dfd8" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#00dfd8" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#005f56" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#005f56" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                    <XAxis
                        dataKey="name"
                        stroke="rgba(255,255,255,0.1)"
                        fontSize={9}
                        tickLine={false}
                        axisLine={false}
                        tick={{ fill: 'rgba(255,255,255,0.2)', fontWeight: 800 }}
                        minTickGap={30}
                        dy={10}
                    />
                    <YAxis
                        stroke="rgba(255,255,255,0.1)"
                        fontSize={9}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `$${value}`}
                        tick={{ fill: 'rgba(255,255,255,0.2)', fontWeight: 800 }}
                        dx={-10}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(0,223,216,0.2)', strokeWidth: 1 }} />

                    <Area
                        name="Income"
                        type="monotone"
                        dataKey="income"
                        stroke="#00dfd8"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorIncome)"
                        animationDuration={1500}
                        className="drop-shadow-[0_0_8px_rgba(0,223,216,0.3)]"
                    />
                    <Area
                        name="Expense"
                        type="monotone"
                        dataKey="expense"
                        stroke="#005f56"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorExpense)"
                        animationDuration={1500}
                        className="drop-shadow-[0_0_8px_rgba(0,95,86,0.3)]"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};
