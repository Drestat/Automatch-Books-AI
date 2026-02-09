"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, User, Zap, LogOut, Settings, Shield, ChevronRight, Cloud } from 'lucide-react';
import Link from 'next/link';
import { UserProfile, useClerk } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { useQBO } from '@/hooks/useQBO';
import Footer from '@/components/Footer';

export default function ProfilePage() {
    const { sync, disconnect, loading, isConnected } = useQBO();
    const { signOut } = useClerk();

    const clerkAppearance = {
        baseTheme: dark,
        variables: {
            colorPrimary: '#00DFD8',
            colorBackground: 'transparent',
            colorText: '#ffffff',
            colorTextSecondary: 'rgba(255, 255, 255, 0.45)',
            colorInputBackground: 'rgba(255, 255, 255, 0.03)',
            colorInputText: '#ffffff',
            borderRadius: '1rem',
            fontFamily: 'inherit',
        },
        elements: {
            card: 'bg-transparent shadow-none border-none p-0',
            navbar: 'hidden',
            header: 'hidden',
            profileSectionTitleText: 'text-brand font-bold uppercase tracking-[0.15em] text-[11px] mb-6',
            scrollBox: 'bg-transparent overflow-visible',
            userPreviewMainIdentifier: 'text-white font-semibold text-base',
            userPreviewSecondaryIdentifier: 'text-white/40 font-medium text-sm',
            accordionTriggerButton: 'hover:bg-white/5 transition-all duration-200 rounded-xl px-4',
            profilePage: 'p-0',
            userButtonPopoverCard: 'hidden',
            breadcrumbs: 'hidden',
            formButtonPrimary: 'btn-primary font-bold py-2.5 px-6 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all',
            formFieldInput: 'bg-white/5 border-white/10 focus:border-brand/40 transition-all rounded-xl py-3 px-4',
            activeDeviceIcon: 'text-brand',
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.08,
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
    };

    return (
        <div className="min-h-screen pb-24 md:pb-12 bg-[#020405] text-white selection:bg-brand/30">
            {/* Minimal Background Polish */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 right-0 w-[50vw] h-[50vw] bg-brand/5 blur-[120px] opacity-40" />
                <div className="absolute bottom-0 left-0 w-[40vw] h-[40vw] bg-brand-accent/5 blur-[120px] opacity-30" />
            </div>

            <div className="max-w-7xl mx-auto px-6 pt-12 relative z-10">
                {/* Header Section - Refined & Professional */}
                <header className="mb-12">
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                        className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-white/5"
                    >
                        <div>
                            <div className="flex items-center gap-3 text-white/40 text-[10px] uppercase tracking-[0.2em] font-bold mb-4">
                                <Link href="/dashboard" className="hover:text-brand transition-colors font-bold">TERMINAL</Link>
                                <ChevronRight size={10} />
                                <span className="text-white/80 font-bold">ACCOUNT SETTINGS</span>
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-2">
                                Settings
                            </h1>
                            <p className="text-white/40 text-base md:text-lg max-w-xl font-medium">
                                Manage your personal information, security, and QuickBooks integration.
                            </p>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className={`px-4 py-2 rounded-xl flex items-center gap-2.5 border backdrop-blur-md transition-all ${isConnected ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-white/5 border-white/10'}`}>
                                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)] animate-pulse' : 'bg-white/20'}`} />
                                <span className={`text-[10px] font-black uppercase tracking-widest ${isConnected ? 'text-emerald-400' : 'text-white/40'}`}>
                                    {isConnected ? 'Sync Status: Active' : 'Status: Offline'}
                                </span>
                            </div>
                        </div>
                    </motion.div>
                </header>

                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="grid grid-cols-1 lg:grid-cols-12 gap-8"
                >
                    {/* Left Column: Vertical Control Center */}
                    <div className="lg:col-span-4 space-y-8">
                        {/* QuickBooks Connection HUB - Simplified Professional */}
                        <motion.div variants={itemVariants} className="glass-panel p-8 border-white/5 bg-white/[0.01] backdrop-blur-2xl relative group overflow-hidden">
                            <div className="flex items-center gap-4 mb-8">
                                <div className="p-3.5 rounded-2xl bg-brand/10 text-brand border border-brand/20">
                                    <Cloud size={22} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg tracking-tight">QuickBooks Online</h3>
                                    <p className="text-[10px] uppercase tracking-widest text-white/30 font-bold">System Integration</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <button
                                    onClick={() => sync()}
                                    disabled={loading}
                                    className="w-full btn-primary py-4 rounded-xl flex items-center justify-center gap-3 font-bold text-sm hover:translate-y-[-2px] active:translate-y-[1px] transition-all shadow-lg shadow-brand/10"
                                >
                                    <Zap size={18} className={loading ? 'animate-spin' : ''} />
                                    {loading ? 'SYNCING DATA...' : 'SYNC NOW'}
                                </button>

                                <button
                                    onClick={() => disconnect()}
                                    className="w-full px-6 py-4 text-white/40 hover:text-rose-400 transition-all rounded-xl hover:bg-rose-500/5 border border-white/5 hover:border-rose-500/20 flex items-center justify-center gap-3 text-xs font-bold tracking-widest"
                                >
                                    <LogOut size={16} />
                                    DISCONNECT SYSTEM
                                </button>
                            </div>

                            <div className="mt-8 pt-6 border-t border-white/5">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-[10px] text-white/30 font-bold uppercase tracking-widest">Environment</span>
                                    <span className="text-[10px] text-white/60 font-bold">Production</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] text-white/30 font-bold uppercase tracking-widest">Version</span>
                                    <span className="text-[10px] text-white/60 font-bold">v3.32.0</span>
                                </div>
                            </div>
                        </motion.div>

                        {/* Session Control */}
                        <motion.div variants={itemVariants} className="glass-panel border-white/5 p-6 bg-white/[0.01] backdrop-blur-2xl">
                            <button
                                onClick={() => signOut()}
                                className="w-full flex items-center gap-4 py-3 px-4 rounded-xl hover:bg-white/5 transition-all group"
                            >
                                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-white/40 group-hover:bg-rose-500/10 group-hover:text-rose-400 transition-all">
                                    <LogOut size={18} />
                                </div>
                                <div className="text-left flex-1">
                                    <span className="block text-sm font-bold tracking-tight mb-0.5" style={{ color: '#ffffff' }}>Logout</span>
                                    <span className="text-[10px] uppercase tracking-widest font-bold text-white/20">End current session</span>
                                </div>
                                <ChevronRight size={14} className="text-white/10 group-hover:text-white/40 transition-colors" />
                            </button>
                        </motion.div>
                    </div>

                    {/* Right Column: Clerk Integration Area */}
                    <motion.div
                        variants={itemVariants}
                        className="lg:col-span-8"
                    >
                        <div className="glass-panel border-white/10 bg-white/[0.01] backdrop-blur-3xl overflow-hidden p-6 md:p-12 relative flex flex-col min-h-[600px]">
                            {/* Professional Framing */}
                            <div className="mb-10 flex items-center gap-4">
                                <div className="h-4 w-1 bg-brand rounded-full" />
                                <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-white/60">Profile Configuration</h2>
                            </div>

                            <div className="flex-1 w-full max-w-full clerk-professional-skin">
                                <UserProfile appearance={clerkAppearance} />
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            </div>

            <Footer />

            <style jsx global>{`
                .clerk-professional-skin .cl-userProfile-root {
                    width: 100% !important;
                    max-width: 100% !important;
                }
                .clerk-professional-skin .cl-profileSection {
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    padding: 2rem 0;
                }
                .clerk-professional-skin .cl-profileSection:last-child {
                    border-bottom: none;
                }
                .clerk-professional-skin .cl-profileSectionHeader {
                    margin-bottom: 2rem;
                }
                .clerk-professional-skin .cl-userPreviewAvatarContainer {
                    width: 72px;
                    height: 72px;
                    border-radius: 1.25rem;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 4px;
                    background: rgba(255, 255, 255, 0.03);
                }
                .clerk-professional-skin .cl-userPreviewAvatarImage {
                    border-radius: 1rem;
                }
                .clerk-professional-skin .cl-navbar {
                    display: none !important;
                }
                .clerk-professional-skin .cl-scrollBox {
                    box-shadow: none !important;
                }
                .clerk-professional-skin .cl-card {
                    margin: 0 !important;
                    padding: 0 !important;
                }
            `}</style>
        </div>
    );
}
