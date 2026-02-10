"use client";

import React, { Suspense } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, User, Zap, LogOut, Settings, Shield, ChevronRight, Cloud, HelpCircle, ToggleLeft, ToggleRight, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useClerk } from "@clerk/nextjs";
import { useQBO } from '@/hooks/useQBO';
import { useUser } from '@/hooks/useUser';
import Footer from '@/components/Footer';
import dynamicLoader from 'next/dynamic';

const ClerkParameters = dynamicLoader(() => import('@/components/ClerkParameters'), { ssr: false });

export const dynamic = 'force-dynamic';

function ProfileContent() {
    const { sync, disconnect, loading: qboLoading, isConnected } = useQBO();
    const { profile, refreshProfile } = useUser();
    const { signOut, user } = useClerk();
    const [updatingPrefs, setUpdatingPrefs] = React.useState(false);

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

    const [isMounted, setIsMounted] = React.useState(false);

    React.useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted) {
        return null;
    }

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
                                    disabled={qboLoading}
                                    className="w-full btn-primary py-4 rounded-xl flex items-center justify-center gap-3 font-bold text-sm hover:translate-y-[-2px] active:translate-y-[1px] transition-all shadow-lg shadow-brand/10"
                                >
                                    <Zap size={18} className={qboLoading ? 'animate-spin' : ''} />
                                    {qboLoading ? 'SYNCING DATA...' : 'SYNC NOW'}
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
                                    <span className="text-[10px] text-white/60 font-bold">v3.61.0</span>
                                </div>
                            </div>
                        </motion.div>

                        {/* Autonomous Engine Control */}
                        <motion.div variants={itemVariants} className="glass-panel p-8 border-white/5 bg-white/[0.01] backdrop-blur-2xl relative overflow-hidden group">
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-4">
                                    <div className="p-3.5 rounded-2xl bg-brand/10 text-brand border border-brand/20">
                                        <Zap size={22} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg tracking-tight">Autonomous Engine</h3>
                                        <p className="text-[10px] uppercase tracking-widest text-white/30 font-bold">Background Worker</p>
                                    </div>
                                </div>
                                {!(profile?.subscription_tier === 'founder' || profile?.subscription_tier === 'empire') && (
                                    <div className="group/tooltip relative">
                                        <HelpCircle size={16} className="text-white/20 hover:text-white/40 transition-colors cursor-help" />
                                        <div className="absolute bottom-full right-0 mb-2 w-48 p-3 rounded-xl bg-black border border-white/10 text-[10px] leading-relaxed text-white/60 font-medium opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 shadow-2xl backdrop-blur-xl">
                                            This feature is reserved for our <span className="text-brand">Founder</span> and <span className="text-brand">Empire</span> partners.
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className={`p-4 rounded-2xl border transition-all ${(profile?.subscription_tier === 'founder' || profile?.subscription_tier === 'empire')
                                ? 'bg-white/[0.02] border-white/5'
                                : 'bg-black/40 border-white/5 opacity-40 grayscale pointer-events-none'
                                }`}>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-bold text-sm text-white/80">Auto-Accept</p>
                                        <p className="text-[10px] text-white/30 font-medium max-w-[180px] mt-1">Automatically approve matches with 95%+ AI confidence.</p>
                                    </div>
                                    <button
                                        disabled={updatingPrefs}
                                        onClick={async () => {
                                            if (!profile || !user?.id) return;
                                            setUpdatingPrefs(true);
                                            try {
                                                const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run'}/api/v1/users/${user.id}/preferences`, {
                                                    method: 'PATCH',
                                                    headers: { 'Content-Type': 'application/json' },
                                                    body: JSON.stringify({ auto_accept_enabled: !profile.auto_accept_enabled })
                                                });
                                                if (res.ok) await refreshProfile();
                                            } finally {
                                                setUpdatingPrefs(false);
                                            }
                                        }}
                                        className="text-brand transition-all hover:scale-110 active:scale-95 disabled:opacity-50"
                                    >
                                        {updatingPrefs ? <Loader2 size={24} className="animate-spin" /> : (profile?.auto_accept_enabled ? <ToggleRight size={32} /> : <ToggleLeft size={32} className="text-white/20" />)}
                                    </button>
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
                                <ClerkParameters />
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

export default function ProfilePage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-[#020405] text-white flex items-center justify-center">Loading Profile...</div>}>
            <ProfileContent />
        </Suspense>
    );
}
