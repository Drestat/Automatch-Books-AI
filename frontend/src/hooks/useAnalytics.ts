"use client";

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';

interface SpendTrendItem {
    name: string;
    income: number;
    expense: number;
}

interface CategoryDataItem {
    name: string;
    value: number;
    color: string;
}

interface KPI {
    totalSpend: number;
    totalIncome: number;
    netFlow: number;
}

export const useAnalytics = () => {
    const [loading, setLoading] = useState(true);
    const [spendTrend, setSpendTrend] = useState<SpendTrendItem[]>([]);
    const [categoryData, setCategoryData] = useState<CategoryDataItem[]>([]);
    const [kpi, setKpi] = useState<KPI>({
        totalSpend: 0,
        totalIncome: 0,
        netFlow: 0
    });

    const { user, isLoaded } = useUser();
    const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

    useEffect(() => {
        const fetchAnalytics = async () => {
            if (!isLoaded || !user) return;

            try {
                // In a real app we'd pass an auth token, but for now we rely on the backend finding the connection via user_id
                const headers = { 'X-User-Id': user.id };
                const res = await fetch(`${API_BASE_URL}/analytics`, { headers });

                if (res.ok) {
                    const data = await res.json();
                    if (data.error) {
                        console.error('Analytics Error:', data.error);
                        return;
                    }
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
    }, [isLoaded, user]);

    return {
        spendTrend,
        categoryData,
        kpi,
        loading
    };
};
