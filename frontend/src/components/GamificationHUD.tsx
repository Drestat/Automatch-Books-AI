import React from 'react';
import { motion } from 'framer-motion';
import { Flame, Star, Trophy, Zap } from 'lucide-react';
import { useGamification } from '@/hooks/useGamification';

const LEVEL_TITLES: { [key: number]: string } = {
    1: "Bookkeeper",
    10: "Controller",
    50: "CFO"
};

const getLevelTitle = (level: number) => {
    // Find the highest threshold met
    let title = "Bookkeeper"; // Default
    const thresholds = [1, 10, 50];
    for (const t of thresholds) {
        if (level >= t) title = LEVEL_TITLES[t];
    }
    return title;
};

const getNextLevelXP = (currentLevel: number) => {
    // Simple mapping based on backend logic
    const thresholds = {
        1: 100,
        2: 250,
        3: 500,
        4: 1000,
        5: 2500,
        10: 7500,
        25: 15000,
        50: 999999
    };
    // Find next threshold > currentLevel
    // Actually, backend calculates level based on Total XP.
    // Frontend needs to know progress within the level.
    // For MVP, just showing Total XP is safer to avoid desync math.
    return thresholds[currentLevel as keyof typeof thresholds] || 100;
};


export function GamificationHUD() {
    const { stats, loading } = useGamification();

    if (loading || !stats) return null;

    const isStreakActive = stats.current_streak > 0;
    const streakColor = stats.current_streak >= 7 ? "text-yellow-400" : stats.current_streak >= 3 ? "text-purple-400" : "text-blue-400";
    const streakBg = stats.current_streak >= 7 ? "bg-yellow-400/10" : stats.current_streak >= 3 ? "bg-purple-400/10" : "bg-blue-400/10";
    const streakBorder = stats.current_streak >= 7 ? "border-yellow-400/20" : stats.current_streak >= 3 ? "border-purple-400/20" : "border-blue-400/20";

    // Haptics on Level Up or Streak Increase
    React.useEffect(() => {
        if (loading || !stats) return;

        // We could store previous state in a ref to only trigger on *change*, 
        // but for now, let's just trigger on mount if they have a high streak to celebrate?
        // No, that's annoying. We need a ref for previous.
    }, [stats, loading]);

    const prevStatsRef = React.useRef(stats);
    React.useEffect(() => {
        if (!stats) return;
        const prev = prevStatsRef.current;

        if (prev) {
            // Level Up -> Medium Haptic
            if (stats.current_level > prev.current_level) {
                import('@/lib/haptics').then(({ triggerHapticFeedback }) => triggerHapticFeedback());
            }
            // Streak Increase -> Light Haptic (simulated by same function for now, or we can enhance haptics.ts later)
            // For now, just trigger event.
            if (stats.current_streak > prev.current_streak) {
                import('@/lib/haptics').then(({ triggerHapticFeedback }) => triggerHapticFeedback());
            }
        }
        prevStatsRef.current = stats;
    }, [stats]);

    return (
        <div className="flex items-center gap-3">
            {/* Streak Badge */}
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border ${streakBorder} ${streakBg} backdrop-blur-md`}
                title="Clarity Streak: Consecutive days categorizing transactions"
            >
                <div className="relative">
                    <Flame
                        size={16}
                        className={`${isStreakActive ? streakColor : "text-white/20"} ${isStreakActive ? "fill-current" : ""}`}
                    />
                    {isStreakActive && (
                        <motion.div
                            animate={{ opacity: [0.5, 1, 0.5], scale: [1, 1.2, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className={`absolute inset-0 blur-sm ${streakColor} opacity-50`}
                        />
                    )}
                </div>
                <div className="flex flex-col">
                    <span className={`text-[9px] font-black uppercase tracking-wider ${isStreakActive ? streakColor : "text-white/40"}`}>
                        Streak
                    </span>
                    <span className="font-mono font-bold text-xs leading-none">
                        {stats.current_streak} <span className="text-[9px] text-white/40 font-normal">days</span>
                    </span>
                </div>
            </motion.div>

            {/* Level / XP Badge */}
            <div className="flex items-center gap-3 px-3 py-1.5 rounded-xl border border-white/5 bg-white/[0.03] backdrop-blur-md">
                <div className="p-1.5 rounded-lg bg-pink-500/10 border border-pink-500/20">
                    <Trophy size={14} className="text-pink-400" />
                </div>
                <div className="flex flex-col">
                    <span className="text-[9px] uppercase text-pink-400/80 font-black tracking-wider leading-none mb-1">
                        Lvl {stats.current_level} • {getLevelTitle(stats.current_level)}
                    </span>
                    <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-white/90 leading-none text-xs">
                            {stats.total_xp.toLocaleString()} AP
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
