"use client";

import { useState, useEffect, useCallback } from 'react';
import { useUser } from '@clerk/nextjs';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/context/ToastContext';

const API_BASE_URL = 'http://localhost:8000/api/v1'; // Local backend

interface QBOCallbackResponse {
    message?: string;
    realmId?: string;
    // Add other fields from backend response if necessary
}

interface ConnectResponse {
    auth_url: string;
}

interface ReceiptResponse {
    message: string;
    extracted: Record<string, unknown>; // Ideally we define this too, but for now 'any' might be unavoidable for complex receipt data unless we know the shape. 
    // But lint rule hates 'any'. Let's use 'Record<string, unknown>' or 'object'.
    // Or just keep it 'any' and suppress if needed, but better to use 'unknown' if possible. 
    // Let's use specific type if we can recall what backend sends.
    // Backend sends: "extracted": result.get('extracted')
    // SyncService logic suggests it's a dict.
    // Let's use 'Record<string, unknown>'.
    match_id?: string;
}

export interface TransactionSplit {
    category_name: string;
    amount: number;
    description: string;
    category_id?: string;
}

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
    is_split?: boolean;
    splits?: TransactionSplit[];
    receipt_url?: string;
}

export const useQBO = () => {
    const { user, isLoaded } = useUser();
    const router = useRouter();
    const searchParams = useSearchParams();
    const { showToast } = useToast();

    const [realmId, setRealmId] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isDemo, setIsDemo] = useState(false);
    const [loading, setLoading] = useState(false);
    const [transactions, setTransactions] = useState<Transaction[]>([]);

    const handleCallback = useCallback(async (code: string, state: string, realm: string) => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/callback?code=${code}&state=${state}&realmId=${realm}`);
            const data = await response.json() as QBOCallbackResponse;

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
    }, [router]);

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
    }, [isLoaded, searchParams, handleCallback]);

    const connect = async () => {
        if (!user) return;
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/authorize?user_id=${user.id}`);
            const data = await response.json() as ConnectResponse;
            if (data.auth_url) {
                window.location.href = data.auth_url;
            }
        } catch (error) {
            console.error('Connect Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const enableDemo = () => {
        setIsDemo(true);
        setTransactions([
            { id: 'demo1', date: '2023-10-25', description: 'STARBUCKS STORE 192', amount: -6.45, currency: 'USD', status: 'unmatched', suggested_category_name: 'Meals & Entertainment', reasoning: 'Frequent coffee shop vendor', confidence: 0.95 },
            { id: 'demo2', date: '2023-10-26', description: 'APPLECARD GOOGLE PAYMENT', amount: -12.99, currency: 'USD', status: 'unmatched', suggested_category_name: 'Software & Subscriptions', reasoning: 'Matches known software subscription pattern', confidence: 0.88 },
            { id: 'demo3', date: '2023-10-27', description: 'UBER TRIP 8485', amount: -24.30, currency: 'USD', status: 'unmatched', suggested_category_name: 'Travel', reasoning: 'Rideshare service detected', confidence: 0.92 },
            { id: 'demo4', date: '2023-10-28', description: 'OFFICE DEPOT 112', amount: -145.20, currency: 'USD', status: 'unmatched', suggested_category_name: 'Office Supplies', reasoning: 'Office supply store match', confidence: 0.98 },
            { id: 'demo5', date: '2023-10-29', description: 'SHELL OIL 5235235', amount: -45.00, currency: 'USD', status: 'unmatched', suggested_category_name: 'Fuel', reasoning: 'Gas station vendor', confidence: 0.91 }
        ]);
        showToast('Demo Mode Activated', 'success');
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
        if (!realmId && !isDemo) return;
        try {
            if (isDemo) {
                setLoading(true);
                setTimeout(() => {
                    setLoading(false);
                    showToast('Demo Sync Complete', 'success');
                }, 1500);
                return;
            }
            await fetch(`${API_BASE_URL}/transactions/sync?realm_id=${realmId}`, { method: 'POST' });
            showToast('Syncing with QuickBooks...', 'info');
            // Poll or re-fetch transactions
            setTimeout(() => {
                if (realmId) fetchTransactions(realmId);
                showToast('Transactions mirrored successfully', 'success');
            }, 2000);
        } catch (error) {
            console.error('Sync Error:', error);
            showToast('Sync failed. Please check your QBO connection.', 'error');
        }
    };

    const approveMatch = async (txId: string) => {
        if (!realmId && !isDemo) return;
        try {
            if (isDemo) {
                setTransactions(prev => prev.filter(tx => tx.id !== txId));
                showToast('Demo: Transaction Approved', 'success');
                return true;
            }
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/approve?realm_id=${realmId}`, { method: 'POST' });

            if (response.ok) {
                // Trigger Haptic Feedback for mobile users
                try {
                    const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
                    await Haptics.impact({ style: ImpactStyle.Medium });
                } catch {
                    // Ignore if not in a capacitor environment
                }

                // Optimistic update
                setTransactions(prev => prev.filter(tx => tx.id !== txId));
                showToast('Reconciled successfully', 'success');
                return true;
            }
            showToast('Failed to approve match', 'error');
            return false;
        } catch (error) {
            console.error('Approve Error:', error);
            showToast('Communication error with backend', 'error');
            return false;
        }
    };

    const bulkApprove = async (txIds: string[]) => {
        if ((!realmId && !isDemo) || txIds.length === 0) return;
        setLoading(true);
        if (isDemo) {
            setTimeout(() => {
                setTransactions(prev => prev.filter(tx => !txIds.includes(tx.id)));
                setLoading(false);
                showToast('Demo: Bulk Approved', 'success');
            }, 1000);
            return true;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/bulk-approve?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(txIds)
            });

            if (response.ok) {
                // Optimistic update
                setTransactions(prev => prev.filter(tx => !txIds.includes(tx.id)));

                // Trigger success haptic
                try {
                    const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
                    await Haptics.impact({ style: ImpactStyle.Heavy });
                } catch { }

                return true;
            }
            return false;
        } catch (error) {
            console.error('Bulk Approve Error:', error);
            return false;
        } finally {
            setLoading(false);
        }
    };

    const uploadReceipt = async (txId: string, file: File) => {
        if (!realmId) return;
        const formData = new FormData();
        formData.append('file', file);

        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/transactions/upload-receipt?realm_id=${realmId}`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json() as ReceiptResponse;

            if (response.ok) {
                // Refresh transactions to show the receipt link/badge
                await fetchTransactions(realmId);
                return data;
            }
        } catch (error) {
            console.error('Upload Error:', error);
        } finally {
            setLoading(false);
        }
    };

    return {
        isConnected,
        loading,
        transactions,
        isDemo,
        connect,
        enableDemo,
        sync,
        approveMatch,
        bulkApprove,
        uploadReceipt,
        user,
        isLoaded
    };
};
