import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';

export interface GamificationStats {
    user_id: string;
    current_streak: number;
    longest_streak: number;
    total_xp: number;
    current_level: number;
    last_activity_date: string | null;
}

export function useGamification() {
    const { getToken } = useAuth();
    const [stats, setStats] = useState<GamificationStats | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        try {
            const token = await getToken();
            if (!token) return;

            const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run';
            const res = await fetch(`${baseUrl}/api/v1/gamification/stats`, {
                headers: {
                    Authorization: `Bearer ${token}`
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
    }, []);

    return { stats, loading, refreshStats: fetchStats };
}
