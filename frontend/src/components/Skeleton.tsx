"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface SkeletonProps {
    className?: string;
    width?: string | number;
    height?: string | number;
    circle?: boolean;
}

export default function Skeleton({ className = "", width, height, circle = false }: SkeletonProps) {
    return (
        <div
            className={`relative overflow-hidden bg-white/5 rounded-lg ${className}`}
            style={{
                width: width || '100%',
                height: height || '1rem',
                borderRadius: circle ? '50%' : undefined
            }}
        >
            <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent"
                animate={{
                    x: ['-100%', '100%']
                }}
                transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
            />
        </div>
    );
}
