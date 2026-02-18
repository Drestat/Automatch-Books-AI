"use client";

import { useState, useCallback, useEffect, useMemo } from 'react';
import { useToast } from '@/context/ToastContext';
import { useUser } from '@/hooks/useUser';
import { API_BASE_URL } from '@/lib/api';
import { track } from '@/lib/analytics';
import type { Account } from '@/hooks/useQBOData';

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
    suggested_category_id?: string;
    suggested_category_name: string;
    category_id?: string;
    category_name?: string;
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

export const useTransactions = (
    realmId: string | null,
    accounts: Account[],
) => {
    const { user } = useUser();
    const { showToast } = useToast();
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(false);
    const [showTokenModal, setShowTokenModal] = useState(false);

    const fetchTransactions = useCallback(async (realm: string, accountIds?: string[]) => {
        setLoading(true);
        try {
            let url = `${API_BASE_URL}/transactions/?realm_id=${realm}`;
            if (accountIds && accountIds.length > 0) {
                url += `&account_ids=${accountIds.join(',')}`;
            }
            url += `&_t=${Date.now()}`;

            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                setTransactions(data);
            }
        } catch {
            // Transaction fetch failed silently
        } finally {
            setLoading(false);
        }
    }, []);

    const activeAccountIds = useMemo(
        () => accounts.filter(acc => acc.is_active).map(acc => acc.id),
        [accounts],
    );

    // Auto-filter transactions by active accounts
    useEffect(() => {
        if (realmId && accounts.length > 0) {
            if (activeAccountIds.length > 0) {
                fetchTransactions(realmId, activeAccountIds);
            } else {
                fetchTransactions(realmId);
            }
        }
    }, [accounts, realmId, fetchTransactions, activeAccountIds]);

    const sync = useCallback(async (overrideRealm?: string) => {
        const targetRealm = overrideRealm || realmId;
        if (!targetRealm) return;

        try {
            track('sync_start', { mode: 'live', realmId: targetRealm }, user?.id);
            await fetch(`${API_BASE_URL}/transactions/sync?realm_id=${targetRealm}`, { method: 'POST' });
            showToast('Syncing with QuickBooks...', 'info');

            setTimeout(() => {
                fetchTransactions(targetRealm);
                showToast('Transactions mirrored successfully', 'success');
            }, 2000);
        } catch {
            showToast('Sync failed. Please check your QBO connection.', 'error');
        }
    }, [realmId, user?.id, showToast, fetchTransactions]);

    const updateTransaction = useCallback(async (txId: string, updates: Partial<Transaction>) => {
        if (!realmId) return;

        setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, ...updates } : tx));

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
            } else {
                fetchTransactions(realmId);
            }
        } catch {
            fetchTransactions(realmId);
        }
    }, [realmId, fetchTransactions]);

    const reAnalyze = useCallback(async (txId: string, refreshProfile: () => void) => {
        if (!realmId) return;

        try {
            setTransactions(prev => prev.map(t => t.id === txId ? { ...t, status: 'unmatched' } : t));
            showToast('Starting AI re-analysis...', 'info');

            const response = await fetch(`${API_BASE_URL}/transactions/analyze?realm_id=${realmId}&tx_id=${txId}`, { method: 'POST' });

            if (response.status === 402) {
                setShowTokenModal(true);
                showToast('Insufficient tokens', 'error');
                await fetchTransactions(realmId);
                return;
            }

            if (response.ok) {
                showToast('AI analysis triggered', 'success');
                track('re_analyze_start', { txId, realmId }, user?.id);
                refreshProfile();

                const ids = activeAccountIds.length > 0 ? activeAccountIds : undefined;
                const poll = (delay: number) => setTimeout(() => fetchTransactions(realmId, ids), delay);
                poll(4000);
                poll(8000);
                poll(12000);
                poll(16000);
                poll(25000);
            } else {
                showToast('Failed to trigger re-analysis', 'error');
            }
        } catch {
            showToast('Communication error', 'error');
        }
    }, [realmId, user?.id, showToast, fetchTransactions, activeAccountIds]);

    const excludeTransaction = useCallback(async (txId: string) => {
        if (!realmId) return false;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/exclude?realm_id=${realmId}`, { method: 'POST' });
            if (response.ok) {
                setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, is_excluded: true } : tx));
                showToast('Transaction excluded', 'info');
                return true;
            }
        } catch {
            // Exclude failed silently
        }
        return false;
    }, [realmId, showToast]);

    const includeTransaction = useCallback(async (txId: string) => {
        if (!realmId) return false;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/include?realm_id=${realmId}`, { method: 'POST' });
            if (response.ok) {
                setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, is_excluded: false } : tx));
                showToast('Transaction included', 'success');
                return true;
            }
        } catch {
            // Include failed silently
        }
        return false;
    }, [realmId, showToast]);

    const splitTransaction = useCallback(async (txId: string, splits: TransactionSplit[]) => {
        if (!realmId) return false;
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}/split?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(splits)
            });
            if (response.ok) {
                showToast('Transaction split successfully', 'success');
                setTransactions(prev => prev.map(tx => tx.id === txId ? { ...tx, is_split: true, splits, status: 'pending_approval' } : tx));
                return true;
            } else {
                const data = await response.json();
                showToast(data.detail || 'Split failed', 'error');
            }
        } catch {
            showToast('Communication error during split', 'error');
        }
        return false;
    }, [realmId, showToast]);

    return {
        transactions, setTransactions,
        loading, setLoading,
        showTokenModal, setShowTokenModal,
        fetchTransactions, sync,
        updateTransaction, reAnalyze,
        excludeTransaction, includeTransaction, splitTransaction,
    };
};
