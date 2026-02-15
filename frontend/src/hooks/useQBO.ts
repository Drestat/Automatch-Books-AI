"use client";

import { useState, useEffect, useCallback } from 'react';
import { useUser } from '@/hooks/useUser'; // Use custom hook
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/context/ToastContext';

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';
import { track } from '@/lib/analytics';

/**
 * Maps technical backend error messages to user-friendly descriptions
 */
const formatApprovalError = (backendError: string): string => {
    const errorMappings: Record<string, string> = {
        'missing category': 'Please select a category before confirming',
        'Stale Object': 'Transaction was updated elsewhere. Please refresh and try again',
        'entity not found': 'Vendor or customer not found in QuickBooks',
        'insufficient tokens': 'Your token balance is too low. Please upgrade your plan',
        'Connection not found': 'QuickBooks connection lost. Please reconnect',
        'already approved': 'This transaction has already been approved',
        'not found': 'Transaction not found. It may have been deleted',
    };

    for (const [key, message] of Object.entries(errorMappings)) {
        if (backendError.toLowerCase().includes(key.toLowerCase())) {
            return message;
        }
    }

    // Return formatted error message if no mapping found
    return `Approval failed: ${backendError}`;
};

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
    description: string | null;
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
    account_id?: string;
    account_name?: string;
    payee?: string;
    suggested_payee?: string;
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

export interface Vendor {
    id: string;
    display_name: string;
}

export interface Category {
    id: string;
    name: string;
    type: string;
}

export const useQBO = () => {
    const { user, isLoaded, refreshProfile, profile } = useUser();
    const router = useRouter();
    const searchParams = useSearchParams();
    const { showToast } = useToast();

    const [realmId, setRealmId] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    // Removed isDemo state
    const [loading, setLoading] = useState(false);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [tags, setTags] = useState<Tag[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [vendors, setVendors] = useState<Vendor[]>([]);
    const [subscriptionStatus, setSubscriptionStatus] = useState<'active' | 'inactive' | 'free' | 'expired' | 'trial' | 'no_plan' | null>(null);
    const [daysRemaining, setDaysRemaining] = useState<number>(0);
    const [pendingUndo, setPendingUndo] = useState<Record<string, { timer: NodeJS.Timeout, originalTx: Transaction }>>({});

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

            // Add cache buster
            url += `&_t=${Date.now()}`;

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

    const fetchVendors = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/vendors?realm_id=${realm}`);
            if (response.ok) {
                setVendors(await response.json());
            }
        } catch (error) {
            console.error("Failed to fetch vendors", error);
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

        // Sync Realm ID from Profile (Backfill if LocalStorage empty)
        if (profile?.realm_id && !realmId) {
            console.log('Restoring QBO connection from user profile:', profile.realm_id);
            setRealmId(profile.realm_id);
            setIsConnected(true);
            localStorage.setItem('qbo_realm_id', profile.realm_id);

            // Trigger data fetches
            fetchAccounts(profile.realm_id);
            fetchTags(profile.realm_id);
            fetchCategories(profile.realm_id);
            fetchVendors(profile.realm_id);
        }

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
    }, [isLoaded, user, profile, realmId]); // Added profile and realmId dependency

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
            fetchVendors(storedRealm as string);
        }
    }, [fetchAccounts, fetchTags, fetchCategories, fetchVendors]);

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
            showToast('Please sign in to connect to QuickBooks.', 'error');
            return;
        }
        track('sync_start', { type: 'connect_flow' }, user.id);
        setLoading(true);

        try {
            // Add a timeout to catch cold starts
            // Cold starts can be slow (20s+). Set to 60s to be safe.
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

            // USE PROXY to bypass CORS
            const proxyUrl = `/api/qbo-proxy?endpoint=qbo/authorize&user_id=${user.id}`;

            const response = await fetch(proxyUrl, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Server returned ${response.status}: ${text}`);
            }

            const data = await response.json() as ConnectResponse;

            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                showToast('Failed to get authorization URL. Please try again.', 'error');
            }
        } catch (error: any) {
            console.error('Connect Error:', error);
            const errorMsg = error.message || 'Unknown Error';
            showToast(`Connection failed: ${errorMsg}`, 'error');
        } finally {
            setLoading(false);
        }
    };


    // Removed enableDemo and disableDemo functions

    const sync = async (overrideRealm?: string) => {
        const targetRealm = overrideRealm || realmId;
        if (!targetRealm) return;

        try {
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
        if (!realmId) return;

        const originalTx = transactions.find(t => t.id === txId);
        if (!originalTx) return;

        // Optimistic update: remove from list
        setTransactions(prev => prev.filter(tx => tx.id !== txId));

        // Trigger Haptic Feedback immediately
        try {
            const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
            await Haptics.impact({ style: ImpactStyle.Medium });
        } catch { }

        // Start 10-second undo timer
        const timer = setTimeout(async () => {
            // Remove from pending undo
            setPendingUndo(prev => {
                const updated = { ...prev };
                delete updated[txId];
                return updated;
            });

            try {
                const response = await fetch(`${API_BASE_URL}/transactions/${txId}/approve?realm_id=${realmId}`, { method: 'POST' });
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                    showToast(formatApprovalError(errorData.detail || 'Failed'), 'error');
                    // Put it back on failure
                    setTransactions(prev => [...prev, originalTx]);
                } else {
                    track('match_approve', { txId, mode: 'live' }, user?.id);
                }
            } catch (error) {
                console.error('Approve Error:', error);
                showToast('Sync error. Transaction restored.', 'error');
                setTransactions(prev => [...prev, originalTx]);
            }
        }, 10000); // 10 seconds buffer (Zen Mode)

        setPendingUndo(prev => ({ ...prev, [txId]: { timer, originalTx } }));

        showToast('Approved! You have 10s to undo.', 'success', {
            label: 'Undo',
            onClick: () => undoApprove(txId)
        });

        return true;
    };

    const undoApprove = (txId: string) => {
        const pending = pendingUndo[txId];
        if (pending) {
            clearTimeout(pending.timer);
            setTransactions(prev => [pending.originalTx, ...prev]);
            setPendingUndo(prev => {
                const updated = { ...prev };
                delete updated[txId];
                return updated;
            });
            showToast('Action reversed', 'info');
            return true;
        }
        return false;
    };

    const bulkApprove = async (txIds: string[]) => {
        if (!realmId || txIds.length === 0) return;
        setLoading(true);

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

            // OPTIMISTIC UPDATE: Update UI immediately to show receipt is being uploaded
            setTransactions(prev => prev.map(tx =>
                tx.id === txId
                    ? { ...tx, receipt_url: 'uploading' }  // Temporary placeholder
                    : tx
            ));

            const response = await fetch(`${API_BASE_URL}/transactions/upload-receipt?realm_id=${realmId}&tx_id=${txId}`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                showToast('Receipt uploaded and linked', 'success');

                // CONFIRMED UPDATE: Set actual receipt URL from backend response
                setTransactions(prev => prev.map(tx =>
                    tx.id === txId
                        ? { ...tx, receipt_url: data.receipt_url || '/tmp/uploaded' }
                        : tx
                ));

                return data;
            } else {
                // ROLLBACK on failure - remove receipt_url
                setTransactions(prev => prev.map(tx =>
                    tx.id === txId
                        ? { ...tx, receipt_url: undefined }
                        : tx
                ));

                console.error('Upload Failed Response:', data);
                showToast(data.detail || 'Upload failed', 'error');
            }
        } catch (error) {
            // ROLLBACK on error - remove receipt_url
            setTransactions(prev => prev.map(tx =>
                tx.id === txId
                    ? { ...tx, receipt_url: undefined }
                    : tx
            ));

            console.error('Upload Error:', error);
            showToast('Network error during upload', 'error');
        } finally {
            setLoading(false);
        }
    };

    const updateTransaction = async (txId: string, updates: any) => {
        if (!realmId) return;

        // Optimistic update
        setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, ...updates } : tx));

        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}?realm_id=${realmId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            if (response.ok) {
                const updatedTx = await response.json();
                // Merge final backend data just in case
                setTransactions(prev => prev.map(tx => tx.id === txId ? updatedTx : tx));
                return updatedTx;
            } else {
                // Revert if error
                console.error("Update failed on backend, refreshing...");
                fetchTransactions(realmId);
            }
        } catch (e) {
            console.error("Update Transaction Failed", e);
            fetchTransactions(realmId);
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
            // Optimistic update: Mark as re-analyzing but DO NOT reset confidence to 0.
            // Resetting to 0 causes the card to jump to the bottom if sorting by confidence.
            // We set it to a slightly neutralized value if it's already high, or keep it.
            setTransactions(prev => prev.map(t => t.id === txId ? { ...t, status: 'unmatched' } : t));
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
                const poll = (delay: number) => setTimeout(() => fetchTransactions(targetRealm, activeAccountIds.length > 0 ? activeAccountIds : undefined), delay);

                poll(4000);
                poll(8000);
                poll(12000); // Extended for cold starts
                poll(16000);
                poll(25000); // Final safety check
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
        if (!realmId) return;

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
            setRealmId(null);
            setIsConnected(false);
            setTransactions([]);
            setAccounts([]);
            showToast('Disconnected from QuickBooks', 'success');

            // Hard reload to ensure clean state
            window.location.reload();
        } catch (error) {
            console.error('Disconnect error:', error);

            // Even if backend fails, clear local state
            localStorage.removeItem('qbo_realm_id');
            setRealmId(null);
            setIsConnected(false);
            setTransactions([]);
            setAccounts([]);

        } finally {
            setLoading(false);
        }
    };

    const splitTransaction = async (txId: string, splits: TransactionSplit[]) => {
        if (!realmId) return;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/split?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(splits)
            });
            if (response.ok) {
                showToast('Transaction split successfully', 'success');
                // Optimistic update
                setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, is_split: true, splits, status: 'pending_approval' } : tx));
                return true;
            } else {
                const data = await response.json();
                showToast(data.detail || 'Split failed', 'error');
            }
        } catch (e) {
            console.error("Split failed", e);
            showToast('Communication error during split', 'error');
        }
        return false;
    };

    return {
        isConnected,
        loading,
        transactions,
        connect,
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
        vendors,
        fetchTransactions,
        updateTransaction,
        createTag,
        updateBankNickname,
        reAnalyze,
        excludeTransaction,
        includeTransaction,
        splitTransaction,
        undoApprove,
        disconnect,
        showTokenModal,
        setShowTokenModal,
        realmId,
        showToast
    };
};
