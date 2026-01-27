"use client";

import { useState, useEffect, useCallback } from 'react';
import { useUser } from '@clerk/nextjs';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/context/ToastContext';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') + '/api/v1';
import { track } from '@/lib/analytics';

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
    vendor_reasoning?: string;
    category_reasoning?: string;
    note_reasoning?: string;
    confidence: number;
    is_split?: boolean;
    splits?: TransactionSplit[];
    receipt_url?: string;
    is_exported?: boolean;
}

export interface Account {
    id: string;
    name: string;
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
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [subscriptionStatus, setSubscriptionStatus] = useState<'active' | 'inactive' | 'free' | 'expired' | 'trial' | 'no_plan' | null>(null);
    const [daysRemaining, setDaysRemaining] = useState<number>(0);

    useEffect(() => {
        // Check for Demo Mode flag on mount
        const demoFlag = localStorage.getItem('is_demo_mode');
        if (demoFlag === 'true') {
            setIsDemo(true);
        }
    }, []);

    const handleCallback = useCallback(async (code: string, state: string, realm: string) => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/callback?code=${code}&state=${state}&realmId=${realm}`);
            const data = await response.json() as QBOCallbackResponse;

            if (response.ok) {
                localStorage.setItem('qbo_realm_id', realm);
                setRealmId(realm);
                setIsConnected(true);
                fetchAccounts(realm); // Fetch accounts after successful connection
                fetchTransactions(realm); // Fetch transactions after successful connection
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
        if (!isLoaded || !user) return;

        // Fetch User Subscription Status
        const fetchUserStatus = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/users/${user.id}`);
                if (res.ok) {
                    const userData = await res.json();
                    setSubscriptionStatus(userData.subscription_status);
                    if (userData.days_remaining) {
                        setDaysRemaining(userData.days_remaining);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch user status", e);
            }
        };
        fetchUserStatus();

        // Check for saved Realm ID
        const storedRealm = localStorage.getItem('qbo_realm_id');
        if (storedRealm) {
            setRealmId(storedRealm);
            setIsConnected(true);
            fetchAccounts(storedRealm); // Fetch accounts on initial load if connected
            fetchTransactions(storedRealm);
        }

        // Handle OAuth Callback
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const realm = searchParams.get('realmId');

        if (code && realm && state) {
            handleCallback(code, state, realm);
        }
    }, [isLoaded, user, searchParams, handleCallback]);

    const connect = async () => {
        if (!user) return;
        track('sync_start', { type: 'connect_flow' }, user.id);
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
        localStorage.setItem('is_demo_mode', 'true');
        track('demo_start', {}, user?.id);
        setTransactions([
            {
                id: 'demo1',
                date: '2023-10-25',
                description: 'STARBUCKS STORE 192',
                amount: -6.45,
                currency: 'USD',
                status: 'unmatched',
                suggested_category_name: 'Meals & Entertainment',
                reasoning: 'Coffee shop patterns detected',
                vendor_reasoning: 'Identified "STARBUCKS" as a known coffee chain.',
                category_reasoning: 'Transactions under $15 at coffee shops are classified as Meals & Entertainment.',
                note_reasoning: 'Frequent vendor match found.',
                confidence: 0.95,
                is_exported: true
            },
            {
                id: 'demo2',
                date: '2023-10-26',
                description: 'APPLECARD GOOGLE PAYMENT',
                amount: -12.99,
                currency: 'USD',
                status: 'unmatched',
                suggested_category_name: 'Software & Subscriptions',
                reasoning: 'Recurring tech subscription',
                vendor_reasoning: 'Identified "GOOGLE PAYMENT" via Apple Card.',
                category_reasoning: 'Amount matches standard monthly G-Suite / Cloud storage pricing.',
                note_reasoning: 'Recurring monthly charge detected.',
                confidence: 0.88
            },
            {
                id: 'demo3',
                date: '2023-10-27',
                description: 'UBER TRIP 8485',
                amount: -24.30,
                currency: 'USD',
                status: 'unmatched',
                suggested_category_name: 'Travel',
                reasoning: 'Rideshare service',
                vendor_reasoning: 'Recognized "UBER" as transport provider.',
                category_reasoning: 'Classified as Travel/Ground Transportation.',
                note_reasoning: 'Trip ID 8485 extracted.',
                confidence: 0.92
            },
            {
                id: 'demo4',
                date: '2023-10-28',
                description: 'OFFICE DEPOT 112',
                amount: -145.20,
                currency: 'USD',
                status: 'unmatched',
                suggested_category_name: 'Office Supplies',
                reasoning: 'Office supply vendor',
                vendor_reasoning: 'Explicit match for "OFFICE DEPOT".',
                category_reasoning: 'Merchant Category Code (MCC) maps to Office Supplies.',
                note_reasoning: 'High confidence vendor match.',
                confidence: 0.98
            },
            {
                id: 'demo5',
                date: '2023-10-29',
                description: 'SHELL OIL 5235235',
                amount: -45.00,
                currency: 'USD',
                status: 'unmatched',
                suggested_category_name: 'Fuel',
                reasoning: 'Gas station',
                vendor_reasoning: 'Identified "SHELL OIL" as fuel provider.',
                category_reasoning: 'Fuel/Auto category applied.',
                note_reasoning: 'Consistent with previous fuel purchases.',
                confidence: 0.91
            },
            {
                id: 'demo6',
                date: '2023-10-30',
                description: 'AMAZON.COM RETAIL',
                amount: -125.50,
                currency: 'USD',
                status: 'unmatched',
                suggested_category_name: 'Mixed - Split',
                reasoning: 'Multi-item purchase detected via Amazon integration.',
                vendor_reasoning: 'Verified Amazon retail purchase.',
                category_reasoning: 'Identified multiple items requiring split classification.',
                confidence: 0.94,
                is_split: true,
                splits: [
                    { category_name: 'Office Supplies', amount: 75.50, description: 'Office Chair' },
                    { category_name: 'Software', amount: 50.00, description: 'Adobe Subscription' }
                ]
            }
        ]);
        showToast('Demo Mode Activated', 'success');
    };

    const fetchAccounts = async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/?realm_id=${realm}`);
            if (response.ok) {
                const data = await response.json();
                setAccounts(data);
            }
        } catch (error) {
            console.error("Failed to fetch accounts", error);
        }
    };

    const fetchTransactions = async (realm: string, accountIds?: string[]) => {
        setLoading(true);
        try {
            let url = `${API_BASE_URL}/transactions/?realm_id=${realm}`;
            if (accountIds && accountIds.length > 0) {
                url += `&account_ids=${accountIds.join(',')}`;
            }

            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                setTransactions(data);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const sync = async () => {
        if (!realmId && !isDemo) return;
        try {
            if (isDemo) {
                setLoading(true);
                track('sync_start', { mode: 'demo' }, user?.id);
                setTimeout(() => {
                    setLoading(false);
                    showToast('Demo Sync Complete', 'success');
                }, 1500);
                return;
            }
            track('sync_start', { mode: 'live', realmId }, user?.id);
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
                track('match_approve', { txId, mode: 'demo' }, user?.id);
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
                track('match_approve', { txId, mode: 'live' }, user?.id);
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
                track('match_approve', { count: txIds.length, mode: 'demo_bulk' }, user?.id);
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
                track('match_approve', { count: txIds.length, mode: 'live_bulk' }, user?.id);

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
        isLoaded,
        subscriptionStatus,
        daysRemaining,
        accounts,
        fetchTransactions
    };
};
