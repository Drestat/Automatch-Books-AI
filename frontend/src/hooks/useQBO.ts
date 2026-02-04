"use client";

import { useState, useEffect, useCallback } from 'react';
import { useUser } from '@/hooks/useUser'; // Use custom hook
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/context/ToastContext';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';
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
    is_qbo_matched?: boolean;
    is_excluded?: boolean;
    is_bank_feed_import?: boolean;
    forced_review?: boolean;
    tags?: string[];
    suggested_tags?: string[];
    transaction_type?: string;
    note?: string;
}

export interface Account {
    id: string;
    name: string;
    nickname?: string;
    balance?: number;
    currency?: string;
    is_active?: boolean;
    is_connected?: boolean;
}

export interface Tag {
    id: string;
    name: string;
}

export interface Category {
    id: string;
    name: string;
    type: string;
}

export const useQBO = () => {
    const { user, isLoaded, refreshProfile } = useUser();
    const router = useRouter();
    const searchParams = useSearchParams();
    const { showToast } = useToast();

    const [realmId, setRealmId] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isDemo, setIsDemo] = useState(false);
    const [loading, setLoading] = useState(false);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [tags, setTags] = useState<Tag[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [subscriptionStatus, setSubscriptionStatus] = useState<'active' | 'inactive' | 'free' | 'expired' | 'trial' | 'no_plan' | null>(null);
    const [daysRemaining, setDaysRemaining] = useState<number>(0);

    useEffect(() => {
        // Check for Demo Mode flag on mount
        const demoFlag = localStorage.getItem('is_demo_mode');
        if (demoFlag === 'true') {
            setIsDemo(true);
        }
    }, []);

    // Simplified: Backend now handles the full token exchange and redirects to dashboard on success.
    // We just need to capture the realmId and update state.
    const handleSuccessRedirect = useCallback((realm: string) => {
        setLoading(true);
        try {
            console.log('Processing QBO Success Redirect with Realm:', realm);
            localStorage.setItem('qbo_realm_id', realm);
            localStorage.setItem('is_new_connection', 'true');
            setRealmId(realm);
            setIsConnected(true);

            // Immediate data fetch
            fetchAccounts(realm);
            fetchTransactions(realm);

            // Auto-trigger Sync to ensure DB is populated
            sync(realm);

            // Clean URL
            router.replace('/dashboard');
        } catch (error) {
            console.error('State Update Error:', error);
        } finally {
            setLoading(false);
        }
    }, [router]);


    // Helper: Fetch Accounts
    const fetchAccounts = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/accounts?realm_id=${realm}`);
            if (response.ok) {
                const data = await response.json();
                setAccounts(data.accounts); // Extract accounts array from response
                return data.accounts; // Return for chaining
            }
        } catch (error) {
            console.error("Failed to fetch accounts", error);
            return [];
        }
        return [];
    }, []);

    // Helper: Fetch Transactions
    const fetchTransactions = useCallback(async (realm: string, accountIds?: string[]) => {
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
    }, []);

    const fetchTags = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/tags?realm_id=${realm}`);
            if (response.ok) {
                setTags(await response.json());
            }
        } catch (error) {
            console.error("Failed to fetch tags", error);
        }
    }, []);

    const fetchCategories = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/categories?realm_id=${realm}`);
            if (response.ok) {
                setCategories(await response.json());
            }
        } catch (error) {
            console.error("Failed to fetch categories", error);
        }
    }, []);

    // Effect 1: Handle URL Params (QBO Connections) - INDEPENDENT of User Loading
    // This ensures that even if Clerk is slow, we act on the redirect immediately.
    useEffect(() => {
        const code = searchParams.get('code');
        const realm = searchParams.get('realmId');

        if (code && realm) {
            handleSuccessRedirect(realm);
        }
    }, [searchParams, handleSuccessRedirect]);

    // Effect 2: User-Dependent Data (Subscription, etc.)
    useEffect(() => {
        if (!isLoaded || !user) return;

        // ... rest of user fetch logic ...
        const safetyTimer = setTimeout(() => {
            setSubscriptionStatus(prev => prev || 'trial');
        }, 3000);

        // Fetch User Subscription Status
        const fetchUserStatus = async () => {
            // ... existing fetch logic ...
            try {
                const res = await fetch(`${API_BASE_URL}/users/${user.id}`);
                if (res.ok) {
                    const userData = await res.json();
                    setSubscriptionStatus(userData.subscription_status || 'trial');
                    if (userData.days_remaining) setDaysRemaining(userData.days_remaining);
                } else {
                    setSubscriptionStatus('trial');
                }
            } catch (e) {
                console.error("Fetch failed", e);
                setSubscriptionStatus('trial');
            } finally {
                clearTimeout(safetyTimer);
            }
        };
        fetchUserStatus();

        return () => clearTimeout(safetyTimer);
    }, [isLoaded, user]);

    // Effect 3: Restore Session from LocalStorage
    useEffect(() => {
        const storedRealm = localStorage.getItem('qbo_realm_id');
        if (storedRealm) {
            setRealmId(storedRealm);
            setIsConnected(true);
            // Fetch accounts first, then transactions will be auto-filtered by active accounts
            fetchAccounts(storedRealm as string);
            // Don't fetch transactions here - will be triggered by accounts effect below
            fetchTags(storedRealm as string);
            fetchCategories(storedRealm as string);
        }
    }, [fetchAccounts, fetchTags, fetchCategories]);

    // Effect 4: Auto-filter transactions by active accounts
    useEffect(() => {
        if (realmId && accounts.length > 0) {
            const activeAccountIds = accounts
                .filter(acc => acc.is_active)
                .map(acc => acc.id);

            if (activeAccountIds.length > 0) {
                console.log('Auto-filtering transactions by active accounts:', activeAccountIds);
                fetchTransactions(realmId, activeAccountIds);
            } else {
                // No active accounts - fetch all or show empty
                console.log('No active accounts found, fetching all transactions');
                fetchTransactions(realmId);
            }
        }
    }, [accounts, realmId, fetchTransactions]);

    const connect = async () => {
        // DEBUG: Check user existence immediately
        if (!user) {
            alert('Connect Aborted: NO USER FOUND. You appear to be logged out or Clerk failed to load.');
            return;
        }
        track('sync_start', { type: 'connect_flow' }, user.id);
        setLoading(true);
        // DEBUG: Alert user to connection attempt
        alert(`Requesting Auth URL from: ${API_BASE_URL}/qbo/authorize?user_id=${user.id}`);

        try {
            // Add a timeout to catch cold starts
            // Cold starts can be slow (20s+). Set to 60s to be safe.
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

            // USE PROXY to bypass CORS
            // Was: ${API_BASE_URL}/qbo/authorize?user_id=${user.id}
            const proxyUrl = `/api/qbo-proxy?endpoint=qbo/authorize&user_id=${user.id}`;

            const response = await fetch(proxyUrl, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            alert(`Response Status: ${response.status}`);

            if (!response.ok) {
                const text = await response.text();
                alert(`Error Body: ${text}`);
                throw new Error(`Server returned ${response.status}: ${text}`);
            }

            const data = await response.json() as ConnectResponse;
            alert(`Received Auth URL: ${data.auth_url || 'MISSING'}`);

            if (data.auth_url) {
                window.location.href = data.auth_url;
            }
        } catch (error: any) {
            console.error('Connect Error:', error);
            // DEBUG: Extract explicit error details because JSON.stringify(Error) returns {}
            const errorMsg = error.message || 'Unknown Error';
            const errorName = error.name || 'Error';
            alert(`Network/Code Error: ${errorName} - ${errorMsg}`);
            showToast('Connection failed. Please check network/console.', 'error');
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


    const sync = async (overrideRealm?: string) => {
        const targetRealm = overrideRealm || realmId;
        if (!targetRealm && !isDemo) return;

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

            track('sync_start', { mode: 'live', realmId: targetRealm }, user?.id);
            await fetch(`${API_BASE_URL}/transactions/sync?realm_id=${targetRealm}`, { method: 'POST' });
            showToast('Syncing with QuickBooks...', 'info');

            // Poll or re-fetch transactions AND accounts
            setTimeout(() => {
                if (targetRealm) {
                    fetchTransactions(targetRealm);
                    fetchAccounts(targetRealm);
                }
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

    const updateTransaction = async (txId: string, updates: any) => {
        if (!realmId) return;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}?realm_id=${realmId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            if (response.ok) {
                const updatedTx = await response.json();
                setTransactions(prev => prev.map(tx => tx.id === txId ? updatedTx : tx));
                return updatedTx;
            }
        } catch (e) {
            console.error("Update Transaction Failed", e);
        }
    };

    const createTag = async (name: string) => {
        if (!realmId) return;
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/tags?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            if (response.ok) {
                const newTag = await response.json();
                setTags(prev => [...prev, newTag]);
                return newTag;
            }
        } catch (e) {
            console.error("Create Tag Failed", e);
        }
    };

    const updateBankNickname = async (accountId: string, nickname: string) => {
        if (!realmId) return;
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/accounts/${accountId}?realm_id=${realmId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nickname })
            });
            if (response.ok) {
                setAccounts(prev => prev.map(a => a.id === accountId ? { ...a, nickname } : a));
                showToast('Nickname updated', 'success');
            }
        } catch (e) {
            console.error("Update Nickname Failed", e);
        }
    };

    const [showTokenModal, setShowTokenModal] = useState(false);


    // ... (rest of hook) ...

    const reAnalyze = async (txId: string) => {
        const targetRealm = realmId;
        if (!targetRealm) return;

        try {
            // Optimistic update: set status back to unmatched
            setTransactions(prev => prev.map(t => t.id === txId ? { ...t, status: 'unmatched', confidence: 0 } : t));
            showToast('Starting AI re-analysis...', 'info');

            const response = await fetch(`${API_BASE_URL}/transactions/analyze?realm_id=${targetRealm}&tx_id=${txId}`, { method: 'POST' });

            if (response.status === 402) {
                setShowTokenModal(true);
                showToast('Insufficient tokens', 'error');
                // Revert optimistic update
                await fetchTransactions(targetRealm);
                return;
            }

            if (response.ok) {
                showToast('AI analysis triggered', 'success');
                track('re_analyze_start', { txId, realmId: targetRealm }, user?.id);

                // Refresh tokens immediately
                refreshProfile();

                // Get active account IDs to preserve filter when refreshing
                const activeAccountIds = accounts
                    .filter(acc => acc.is_active)
                    .map(acc => acc.id);

                // Fetch fresh data with backoff polling to ensure background job finishes
                // Preserve active account filter
                // 1st attempt: 4s
                setTimeout(() => fetchTransactions(targetRealm, activeAccountIds.length > 0 ? activeAccountIds : undefined), 4000);
                // 2nd attempt: 8s
                setTimeout(() => fetchTransactions(targetRealm, activeAccountIds.length > 0 ? activeAccountIds : undefined), 8000);
            } else {
                showToast('Failed to trigger re-analysis', 'error');
            }
        } catch (error) {
            console.error('Re-analyze error:', error);
            showToast('Communication error', 'error');
        }
    };

    const excludeTransaction = async (txId: string) => {
        if (!realmId) return;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/exclude?realm_id=${realmId}`, { method: 'POST' });
            if (response.ok) {
                setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, is_excluded: true } : tx));
                showToast('Transaction excluded', 'info');
                return true;
            }
        } catch (e) {
            console.error("Exclude failed", e);
        }
        return false;
    };

    const includeTransaction = async (txId: string) => {
        if (!realmId) return;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/include?realm_id=${realmId}`, { method: 'POST' });
            if (response.ok) {
                setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, is_excluded: false } : tx));
                showToast('Transaction included', 'success');
                return true;
            }
        } catch (e) {
            console.error("Include failed", e);
        }
        return false;
    };

    const disconnect = async () => {
        if (!realmId && !isDemo) {
            // Just clear demo mode
            localStorage.removeItem('is_demo_mode');
            setIsDemo(false);
            showToast('Demo mode cleared', 'info');
            window.location.reload();
            return;
        }

        try {
            setLoading(true);

            // Call backend to delete connection and data
            if (realmId) {
                const response = await fetch(`${API_BASE_URL}/qbo/disconnect?realm_id=${realmId}`, {
                    method: 'DELETE'
                });

                // 404 means connection already deleted - treat as success
                if (!response.ok && response.status !== 404) {
                    throw new Error('Failed to disconnect from backend');
                }
            }

            // Clear local state
            localStorage.removeItem('qbo_realm_id');
            localStorage.removeItem('is_demo_mode');
            setRealmId(null);
            setIsConnected(false);
            setIsDemo(false);
            setTransactions([]);
            setAccounts([]);
            showToast('Disconnected from QuickBooks', 'success');

            // Hard reload to ensure clean state
            window.location.reload();
        } catch (error) {
            console.error('Disconnect error:', error);

            // Even if backend fails, clear local state
            localStorage.removeItem('qbo_realm_id');
            localStorage.removeItem('is_demo_mode');
            setRealmId(null);
            setIsConnected(false);
            setIsDemo(false);
            setTransactions([]);
            setAccounts([]);

            showToast('Disconnected locally (backend error)', 'info');
            window.location.reload();
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
        tags,
        categories,
        fetchTransactions,
        updateTransaction,
        createTag,
        updateBankNickname,
        reAnalyze,
        excludeTransaction,
        includeTransaction,
        disconnect,
        showTokenModal,
        setShowTokenModal
    };
};
