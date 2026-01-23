import { useState, useEffect } from 'react';

export function useAnalytics() {
    const [spendTrend, setSpendTrend] = useState<any[]>([]);
    const [categoryData, setCategoryData] = useState<any[]>([]);
    const [kpi, setKpi] = useState({
        totalSpend: 0,
        totalIncome: 0,
        netFlow: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                // In a real app, get token from AuthContext
                const userId = localStorage.getItem('user_id');
                const headers: any = {};
                if (userId) headers['X-User-Id'] = userId;

                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analytics`, {
                    headers
                });

                if (res.ok) {
                    const data = await res.json();
                    setSpendTrend(data.trend || []);
                    setCategoryData(data.categories || []);
                    setKpi(data.kpi || { totalSpend: 0, totalIncome: 0, netFlow: 0 });
                }
            } catch (error) {
                console.error("Failed to fetch analytics:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, []);

    return { spendTrend, categoryData, kpi, loading };
}
