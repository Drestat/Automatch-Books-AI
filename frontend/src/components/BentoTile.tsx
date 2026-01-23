"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface BentoTileProps {
    children: React.ReactNode;
    className?: string;
    delay?: number;
}

export const BentoTile = ({ children, className, delay = 0 }: BentoTileProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
                duration: 0.5,
                delay,
                ease: [0.23, 1, 0.32, 1]
            }}
            whileHover={{
                y: -5,
                transition: { duration: 0.2 }
            }}
            className={cn(
                "glass-card p-6 flex flex-col",
                className
            )}
        >
            {children}
        </motion.div>
    );
};
