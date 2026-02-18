"use client";

import { useState, useCallback } from 'react';
import { useToast } from '@/context/ToastContext';
import { useUser } from '@/hooks/useUser';
import { API_BASE_URL } from '@/lib/api';
import { track } from '@/lib/analytics';
import type { Transaction } from '@/hooks/useTransactions';

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
    return `Approval failed: ${backendError}`;
};

export const useTransactionApproval = (
    realmId: string | null,
    transactions: Transaction[],
    setTransactions: React.Dispatch<React.SetStateAction<Transaction[]>>,
    setLoading: (loading: boolean) => void,
) => {
    const { user } = useUser();
    const { showToast } = useToast();
    const [pendingUndo, setPendingUndo] = useState<Record<string, { timer: NodeJS.Timeout; originalTx: Transaction }>>({});

    const undoApprove = useCallback((txId: string) => {
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
    }, [pendingUndo, setTransactions, showToast]);

    const approveMatch = useCallback(async (txId: string) => {
        if (!realmId) return;

        const originalTx = transactions.find(t => t.id === txId);
        if (!originalTx) return;

        // Optimistic update: remove from list
        setTransactions(prev => prev.filter(tx => tx.id !== txId));

        // Haptic feedback
        try {
            const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
            await Haptics.impact({ style: ImpactStyle.Medium });
        } catch { }

        // 10-second undo timer
        const timer = setTimeout(async () => {
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
                    setTransactions(prev => [...prev, originalTx]);
                } else {
                    track('match_approve', { txId, mode: 'live' }, user?.id);
                }
            } catch {
                showToast('Sync error. Transaction restored.', 'error');
                setTransactions(prev => [...prev, originalTx]);
            }
        }, 10000);

        setPendingUndo(prev => ({ ...prev, [txId]: { timer, originalTx } }));

        showToast('Approved! You have 10s to undo.', 'success', {
            label: 'Undo',
            onClick: () => undoApprove(txId)
        });

        return true;
    }, [realmId, transactions, setTransactions, showToast, user?.id, undoApprove]);

    const bulkApprove = useCallback(async (txIds: string[]) => {
        if (!realmId || txIds.length === 0) return false;
        setLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/transactions/bulk-approve?realm_id=${realmId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(txIds)
            });

            if (response.ok) {
                setTransactions(prev => prev.filter(tx => !txIds.includes(tx.id)));
                track('match_approve', { count: txIds.length, mode: 'live_bulk' }, user?.id);

                try {
                    const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
                    await Haptics.impact({ style: ImpactStyle.Heavy });
                } catch { }

                return true;
            }
            return false;
        } catch {
            return false;
        } finally {
            setLoading(false);
        }
    }, [realmId, setTransactions, setLoading, user?.id]);

    return { approveMatch, undoApprove, bulkApprove };
};
