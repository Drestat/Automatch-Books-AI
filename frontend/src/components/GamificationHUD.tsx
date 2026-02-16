import React from 'react';
import { motion } from 'framer-motion';
import { Flame, Star, Trophy, Zap } from 'lucide-react';
import { useGamification } from '@/hooks/useGamification';
import { LeaderboardModal } from '@/components/LeaderboardModal';




export function GamificationHUD() {
    const { stats, loading } = useGamification();

    const prevStatsRef = React.useRef(stats);

    // Haptics on Level Up or Streak Increase
    React.useEffect(() => {
        if (loading || !stats) return;
        const prev = prevStatsRef.current;

        if (prev) {
            // Level Up -> Medium Haptic
            if (stats.current_level > prev.current_level) {
                import('@/lib/haptics').then(({ triggerHapticFeedback }) => triggerHapticFeedback());
            }
            // Streak Increase -> Light Haptic
            if (stats.current_streak > prev.current_streak) {
                import('@/lib/haptics').then(({ triggerHapticFeedback }) => triggerHapticFeedback());
            }
        }
        prevStatsRef.current = stats;
    }, [stats, loading]);

    if (loading || !stats) return null;

    const isStreakActive = stats.current_streak > 0;
    const streakColor = stats.current_streak >= 7 ? "text-yellow-400" : stats.current_streak >= 3 ? "text-purple-400" : "text-blue-400";
    const streakBg = stats.current_streak >= 7 ? "bg-yellow-400/10" : stats.current_streak >= 3 ? "bg-purple-400/10" : "bg-blue-400/10";
    const streakBorder = stats.current_streak >= 7 ? "border-yellow-400/20" : stats.current_streak >= 3 ? "border-purple-400/20" : "border-blue-400/20";


    const [isLeaderboardOpen, setIsLeaderboardOpen] = React.useState(false);

    return (
        <div className="flex items-center gap-3">
            <LeaderboardModal
                isOpen={isLeaderboardOpen}
                onClose={() => setIsLeaderboardOpen(false)}
            />

            {/* Streak Badge */}
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border ${streakBorder} ${streakBg} backdrop-blur-md`}
                title="Clarity Streak: Consecutive weeks of activity"
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
                        {stats.current_streak} <span className="text-[9px] text-white/40 font-normal">wks</span>
                    </span>
                </div>
            </motion.div>

            {/* Level / XP Badge (Clickable for Leaderboard) */}
            <div
                onClick={() => setIsLeaderboardOpen(true)}
                className="flex items-center gap-3 px-3 py-1.5 rounded-xl border border-white/5 bg-white/[0.03] backdrop-blur-md min-w-[140px] cursor-pointer hover:bg-white/[0.08] hover:border-white/10 transition-all group"
                title="Click to view Leaderboard"
            >
                <div className="p-1.5 rounded-lg bg-pink-500/10 border border-pink-500/20 group-hover:bg-pink-500/20 transition-colors">
                    <Trophy size={14} className="text-pink-400" />
                </div>
                <div className="flex flex-col w-full">
                    <div className="flex justify-between items-end mb-1">
                        <span className="text-[9px] uppercase text-pink-400/80 font-black tracking-wider leading-none">
                            Lvl {stats.current_level}
                        </span>
                        <span className="text-[9px] text-white/40 font-mono">
                            {Math.round(stats.progress_percent)}%
                        </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden mb-1">
                        <motion.div
                            className="h-full bg-gradient-to-r from-pink-500 to-purple-500"
                            initial={{ width: 0 }}
                            animate={{ width: `${stats.progress_percent}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                        />
                    </div>

                    <span className="font-mono font-bold text-white/90 leading-none text-[10px]">
                        {stats.total_xp.toLocaleString('en-US')} <span className="text-white/40">XP</span>
                    </span>
                </div>
            </div>
        </div>
    );
}
