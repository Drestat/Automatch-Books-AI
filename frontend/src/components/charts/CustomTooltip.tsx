"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface CustomTooltipProps {
    active?: boolean;
    payload?: any[];
    label?: string;
    valuePrefix?: string;
    valueSuffix?: string;
}

export const CustomTooltip = ({ active, payload, label, valuePrefix = '$', valueSuffix = '' }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel px-4 py-3 !rounded-xl border-brand/20 shadow-2xl backdrop-blur-3xl bg-[#030712]/80"
            >
                <p className="text-xs font-bold text-white/40 uppercase tracking-wider mb-1">{label}</p>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-brand animate-pulse" />
                    <p className="text-lg font-black text-white">
                        {valuePrefix}{payload[0].value.toLocaleString()}{valueSuffix}
                    </p>
                </div>
            </motion.div>
        );
    }
    return null;
};
