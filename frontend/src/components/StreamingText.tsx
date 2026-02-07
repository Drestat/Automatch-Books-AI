"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface StreamingTextProps {
    text: string;
    speed?: number;
    className?: string;
    startDelay?: number;
}

export default function StreamingText({ text, speed = 20, className = "", startDelay = 0 }: StreamingTextProps) {
    const [displayedText, setDisplayedText] = useState("");
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        let timeout: NodeJS.Timeout;

        if (startDelay > 0) {
            timeout = setTimeout(() => {
                startStreaming();
            }, startDelay);
        } else {
            startStreaming();
        }

        function startStreaming() {
            let i = 0;
            const interval = setInterval(() => {
                setDisplayedText(text.slice(0, i + 1));
                i++;
                if (i >= text.length) {
                    clearInterval(interval);
                    setIsComplete(true);
                }
            }, speed);
            return () => clearInterval(interval);
        }

        return () => clearTimeout(timeout);
    }, [text, speed, startDelay]);

    return (
        <span className={className}>
            {displayedText}
            {!isComplete && (
                <motion.span
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className="inline-block w-1 h-3 bg-brand-accent ml-0.5"
                />
            )}
        </span>
    );
}
