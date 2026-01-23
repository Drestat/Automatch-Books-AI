"use client";

import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { CustomTooltip } from './CustomTooltip';

const data = [
    { name: 'Software', value: 4500, color: '#6366f1' },  // Brand
    { name: 'Office', value: 1200, color: '#ec4899' },    // Pink
    { name: 'Travel', value: 3400, color: '#a855f7' },    // Purple
    { name: 'Meals', value: 800, color: '#10b981' },      // Emerald
];

export const CategoryPieChart = () => {
    return (
        <div className="h-[300px] w-full">
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
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        verticalAlign="middle"
                        layout="vertical"
                        align="right"
                        iconType="circle"
                        iconSize={8}
                        formatter={(value, entry: any) => (
                            <span className="text-white/60 text-xs font-bold ml-2">{value}</span>
                        )}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
};
