"use client";

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { useRouter, useSearchParams } from 'next/navigation';

const API_BASE_URL = 'http://localhost:8000/api/v1'; // Local backend

export interface Transaction {
    id: string;
    date: string;
    description: string;
    amount: number;
    currency: string;
    status: string;
    suggested_category_name: string;
    reasoning: string;
    confidence: number;
}

export const useQBO = () => {
    const { user, isLoaded } = useUser();
    const router = useRouter();
    const searchParams = useSearchParams();

    const [realmId, setRealmId] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [loading, setLoading] = useState(false);
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    // Initialize state from local storage or URL params
    useEffect(() => {
        if (!isLoaded) return;

        // Check for saved Realm ID
        const storedRealm = localStorage.getItem('qbo_realm_id');
        if (storedRealm) {
            setRealmId(storedRealm);
            setIsConnected(true);
            fetchTransactions(storedRealm);
        }

        // Handle OAuth Callback
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const realm = searchParams.get('realmId');

        if (code && realm && state) {
            handleCallback(code, state, realm);
        }
    }, [isLoaded, searchParams]);

    const handleCallback = async (code: string, state: string, realm: string) => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/callback?code=${code}&state=${state}&realmId=${realm}`);
            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('qbo_realm_id', realm);
                setRealmId(realm);
                setIsConnected(true);
                // Clear URL params
                router.replace('/dashboard');
            } else {
                console.error('QBO Callback Failed:', data);
            }
        } catch (error) {
            console.error('QBO Callback Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const connect = async () => {
        if (!user) return;
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/authorize?user_id=${user.id}`);
            const data = await response.json();
            if (data.auth_url) {
                window.location.href = data.auth_url;
            }
        } catch (error) {
            console.error('Connect Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchTransactions = async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/?realm_id=${realm}`);
            const data = await response.json();
            if (Array.isArray(data)) {
                setTransactions(data);
            }
        } catch (error) {
            console.error('Fetch Transactions Error:', error);
        }
    };

    const sync = async () => {
        if (!realmId) return;
        try {
            await fetch(`${API_BASE_URL}/transactions/sync?realm_id=${realmId}`, { method: 'POST' });
            // Poll or re-fetch transactions
            setTimeout(() => fetchTransactions(realmId), 2000);
        } catch (error) {
            console.error('Sync Error:', error);
        }
    };

    const approveMatch = async (txId: string) => {
        if (!realmId) return;
        try {
            await fetch(`${API_BASE_URL}/transactions/${txId}/approve?realm_id=${realmId}`, { method: 'POST' });
            // Optimistic update
            setTransactions(prev => prev.filter(tx => tx.id !== txId));
            return true;
        } catch (error) {
            console.error('Approve Error:', error);
            return false;
        }
    };

    return {
        isConnected,
        loading,
        transactions,
        connect,
        sync,
        approveMatch,
        user
    };
};
