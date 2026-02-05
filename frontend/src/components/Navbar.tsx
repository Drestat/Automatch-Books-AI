"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Sparkles, Menu, X } from 'lucide-react';
import { SignedIn, SignedOut } from '@clerk/nextjs';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navbar() {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const toggleMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

    return (
        <nav className="fixed top-0 w-full z-50 bg-black/50 backdrop-blur-xl border-b border-white/5">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 h-20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                        <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center shrink-0">
                            <Sparkles className="text-white" size={16} aria-hidden="true" />
                        </div>
                        <span className="font-bold tracking-tight text-base sm:text-lg whitespace-nowrap text-white">AutoMatch Books AI</span>
                    </Link>
                </div>

                <div className="flex items-center gap-8">
                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-6">
                        <Link href="/features" className="text-sm font-medium text-white/60 hover:text-white transition-colors">
                            Features
                        </Link>
                        <Link href="/pricing" className="text-sm font-medium text-white/60 hover:text-white transition-colors">
                            Pricing
                        </Link>
                    </div>

                    <div className="hidden md:flex items-center gap-3 sm:gap-6">
                        <SignedOut>
                            <Link href="/dashboard" className="text-xs sm:text-sm font-bold text-white/60 hover:text-white transition-colors">
                                Log In
                            </Link>
                            <Link href="/sign-up" className="btn-primary px-4 sm:px-6 py-2 sm:py-2.5 text-xs sm:text-sm">
                                Try Free
                            </Link>
                        </SignedOut>
                        <SignedIn>
                            <Link href="/dashboard" className="text-xs sm:text-sm font-bold text-brand hover:text-brand/80 transition-colors">
                                Go to Dashboard
                            </Link>
                        </SignedIn>
                    </div>

                    {/* Mobile Menu Toggle */}
                    <button
                        onClick={toggleMenu}
                        className="md:hidden p-2 text-white/60 hover:text-white transition-colors"
                        aria-label="Toggle menu"
                    >
                        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </div>
            </div>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="md:hidden bg-black/90 backdrop-blur-xl border-b border-white/5 overflow-hidden"
                    >
                        <div className="flex flex-col p-6 gap-6">
                            <Link
                                href="/features"
                                className="text-lg font-medium text-white/80 hover:text-white"
                                onClick={() => setIsMobileMenuOpen(false)}
                            >
                                Features
                            </Link>
                            <Link
                                href="/pricing"
                                className="text-lg font-medium text-white/80 hover:text-white"
                                onClick={() => setIsMobileMenuOpen(false)}
                            >
                                Pricing
                            </Link>
                            <div className="h-px bg-white/10 my-2" />
                            <SignedOut>
                                <Link
                                    href="/dashboard"
                                    className="text-lg font-bold text-white/60 hover:text-white"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    Log In
                                </Link>
                                <Link
                                    href="/sign-up"
                                    className="btn-primary py-3 text-center justify-center flex"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    Try Free
                                </Link>
                            </SignedOut>
                            <SignedIn>
                                <Link
                                    href="/dashboard"
                                    className="text-lg font-bold text-brand hover:text-brand/80"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    Go to Dashboard
                                </Link>
                            </SignedIn>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
}
