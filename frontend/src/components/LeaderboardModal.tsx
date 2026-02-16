"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, X, Medal, User } from 'lucide-react';
import { useLeaderboard } from '@/hooks/useGamification';

interface LeaderboardModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function LeaderboardModal({ isOpen, onClose }: LeaderboardModalProps) {
    const { leaderboard, loading } = useLeaderboard();

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-md bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                    <Trophy size={20} className="text-yellow-500" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Leaderboard</h2>
                                    <p className="text-xs text-white/40">Top performing bookkeepers</p>
                                </div>
                            </div>
                            <button onClick={onClose} className="p-2 text-white/20 hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* List */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-2">
                            {loading ? (
                                <div className="text-center py-8 text-white/30 text-sm">Loading rankings...</div>
                            ) : leaderboard.length === 0 ? (
                                <div className="text-center py-8 text-white/30 text-sm">No data available</div>
                            ) : (
                                leaderboard.map((entry, index) => {
                                    const rank = index + 1;
                                    const isTop3 = rank <= 3;
                                    let rankIcon = <span className="text-white/40 font-mono font-bold w-6 text-center">{rank}</span>;

                                    if (rank === 1) rankIcon = <Medal size={20} className="text-yellow-400 fill-yellow-400/20" />;
                                    if (rank === 2) rankIcon = <Medal size={20} className="text-zinc-400 fill-zinc-400/20" />;
                                    if (rank === 3) rankIcon = <Medal size={20} className="text-amber-700 fill-amber-700/20" />;

                                    return (
                                        <div
                                            key={entry.user_id}
                                            className={`flex items-center gap-4 p-3 rounded-xl border transition-all
                                                ${entry.is_me
                                                    ? 'bg-brand/10 border-brand/30'
                                                    : 'bg-white/5 border-white/5'
                                                }
                                            `}
                                        >
                                            <div className="flex-shrink-0 w-8 flex justify-center">
                                                {rankIcon}
                                            </div>

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className={`font-bold text-sm truncate ${entry.is_me ? 'text-white' : 'text-white/80'}`}>
                                                        {entry.name}
                                                    </span>
                                                    {entry.is_me && <span className="text-[9px] bg-brand text-black px-1.5 rounded font-bold uppercase">You</span>}
                                                </div>
                                                <div className="text-xs text-white/40 font-mono">
                                                    Lvl {entry.level}
                                                </div>
                                            </div>

                                            <div className="text-right">
                                                <div className="font-mono font-bold text-white text-sm">
                                                    {entry.xp.toLocaleString()} <span className="text-[10px] text-white/30">XP</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>

                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
