"use client";

import { useState, useEffect } from 'react';
import { useUser } from '@/hooks/useUser';
import { useToast } from '@/context/ToastContext';
import { API_BASE_URL } from '@/lib/api';
import { useQBOConnection } from '@/hooks/useQBOConnection';
import { useQBOData } from '@/hooks/useQBOData';
import { useTransactions } from '@/hooks/useTransactions';
import { useTransactionApproval } from '@/hooks/useTransactionApproval';
import { useReceiptUpload } from '@/hooks/useReceiptUpload';

// Re-export types so existing imports from '@/hooks/useQBO' continue to work
export type { Transaction, TransactionSplit } from '@/hooks/useTransactions';
export type { Account, Tag, Vendor, Category } from '@/hooks/useQBOData';

export const useQBO = () => {
    const { user, isLoaded, refreshProfile } = useUser();
    const { showToast } = useToast();

    // Connection state
    const { realmId, isConnected, loading: connectionLoading, connect, disconnect } = useQBOConnection();

    // QBO reference data (accounts, tags, categories, vendors)
    const qboData = useQBOData(realmId);

    // Transactions
    const txns = useTransactions(realmId, qboData.accounts);

    // Approvals
    const { approveMatch, undoApprove, bulkApprove } = useTransactionApproval(
        realmId, txns.transactions, txns.setTransactions, txns.setLoading,
    );

    // Receipt upload
    const { uploadReceipt } = useReceiptUpload(realmId, txns.setTransactions, txns.setLoading);

    // Subscription status (user-dependent)
    const [subscriptionStatus, setSubscriptionStatus] = useState<'active' | 'inactive' | 'free' | 'expired' | 'trial' | 'no_plan' | null>(null);
    const [daysRemaining, setDaysRemaining] = useState<number>(0);

    useEffect(() => {
        if (!isLoaded || !user) return;

        const safetyTimer = setTimeout(() => {
            setSubscriptionStatus(prev => prev || 'trial');
        }, 3000);

        const fetchUserStatus = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/users/${user.id}`);
                if (res.ok) {
                    const userData = await res.json();
                    setSubscriptionStatus(userData.subscription_status || 'trial');
                    if (userData.days_remaining) setDaysRemaining(userData.days_remaining);
                } else {
                    setSubscriptionStatus('trial');
                }
            } catch {
                setSubscriptionStatus('trial');
            } finally {
                clearTimeout(safetyTimer);
            }
        };
        fetchUserStatus();

        return () => clearTimeout(safetyTimer);
    }, [isLoaded, user]);

    // Wrap reAnalyze to inject refreshProfile
    const reAnalyze = async (txId: string) => {
        return txns.reAnalyze(txId, refreshProfile);
    };

    // Merge loading states
    const loading = connectionLoading || txns.loading;

    return {
        isConnected,
        loading,
        transactions: txns.transactions,
        connect,
        sync: txns.sync,
        approveMatch,
        bulkApprove,
        uploadReceipt,
        user,
        isLoaded,
        subscriptionStatus,
        daysRemaining,
        accounts: qboData.accounts,
        tags: qboData.tags,
        categories: qboData.categories,
        vendors: qboData.vendors,
        fetchTransactions: txns.fetchTransactions,
        updateTransaction: txns.updateTransaction,
        createTag: qboData.createTag,
        updateBankNickname: qboData.updateBankNickname,
        reAnalyze,
        excludeTransaction: txns.excludeTransaction,
        includeTransaction: txns.includeTransaction,
        splitTransaction: txns.splitTransaction,
        undoApprove,
        disconnect,
        showTokenModal: txns.showTokenModal,
        setShowTokenModal: txns.setShowTokenModal,
        realmId,
        showToast
    };
};
