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
    const API_BASE_URL = 'http://localhost:8000/api/v1';

    useEffect(() => {
        const fetchAnalytics = async () => {
            if (!isLoaded || !user) return;

            // DEMO MODE CHECK
            if (localStorage.getItem('is_demo_mode') === 'true') {
                setSpendTrend([
                    { name: 'Oct 01', income: 4500, expense: 3200 },
                    { name: 'Oct 05', income: 1200, expense: 800 },
                    { name: 'Oct 10', income: 5600, expense: 3400 },
                    { name: 'Oct 15', income: 2800, expense: 1200 },
                    { name: 'Oct 20', income: 3900, expense: 2100 },
                    { name: 'Oct 25', income: 6200, expense: 4100 },
                    { name: 'Oct 30', income: 4800, expense: 2900 },
                ]);
                setCategoryData([
                    { name: 'Software', value: 2400, color: '#0070f3' },
                    { name: 'Office', value: 1200, color: '#7928ca' },
                    { name: 'Travel', value: 850, color: '#f5a623' },
                    { name: 'Meals', value: 450, color: '#ff0080' },
                ]);
                setKpi({
                    totalSpend: 15300,
                    totalIncome: 28900,
                    netFlow: 13600
                });
                setLoading(false);
                return;
            }

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
