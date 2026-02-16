import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';

export interface GamificationStats {
    current_level: number;
    total_xp: number;
    current_streak: number;
    longest_streak: number;
    last_activity_date: string | null;
    next_level_xp: number;
    progress_percent: number;
}

export interface LeaderboardEntry {
    user_id: string;
    name: string;
    level: number;
    xp: number;
    is_me: boolean;
}

export function useGamification() {
    const { getToken, userId } = useAuth();
    const [stats, setStats] = useState<GamificationStats | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        if (!userId) return;
        try {
            const token = await getToken();
            const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:8000'; // Default to local for dev

            const res = await fetch(`${baseUrl}/api/v1/gamification/stats`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'X-User-Id': userId
                }
            });

            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (error) {
            console.error("Failed to fetch gamification stats:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
    }, [userId]);

    return { stats, loading, refreshStats: fetchStats };
}

export function useLeaderboard() {
    const { getToken, userId } = useAuth();
    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchLeaderboard = async () => {
        if (!userId) return;
        try {
            const token = await getToken();
            const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:8000';

            const res = await fetch(`${baseUrl}/api/v1/gamification/leaderboard`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'X-User-Id': userId
                }
            });

            if (res.ok) {
                const data = await res.json();
                setLeaderboard(data);
            }
        } catch (error) {
            console.error("Failed to fetch leaderboard:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLeaderboard();
    }, [userId]);

    return { leaderboard, loading, refreshLeaderboard: fetchLeaderboard };
}
