"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { CustomTooltip } from './CustomTooltip';

const COLORS = ['#00dfd8', '#008f7a', '#005f56', '#2dd4bf', '#10b981'];

interface CategoryPieChartProps {
    data: {
        name: string;
        value: number;
        color?: string;
    }[];
}

export const CategoryPieChart = ({ data }: CategoryPieChartProps) => {
    return (
        <div className="h-[300px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={70}
                        outerRadius={90}
                        paddingAngle={8}
                        dataKey="value"
                        stroke="none"
                        animationBegin={200}
                        animationDuration={1200}
                    >
                        {data.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={COLORS[index % COLORS.length]}
                                className="hover:opacity-80 transition-opacity cursor-pointer"
                            />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                </PieChart>
            </ResponsiveContainer>
            {/* Center Label */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                <p className="text-[10px] text-white/30 font-black uppercase tracking-widest">Expenses</p>
                <p className="text-lg font-black text-white">Top 5</p>
            </div>
        </div>
    );
};
