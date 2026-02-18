"use client";

import { useCallback } from 'react';
import { useToast } from '@/context/ToastContext';
import { API_BASE_URL } from '@/lib/api';
import type { Transaction } from '@/hooks/useTransactions';

export const useReceiptUpload = (
    realmId: string | null,
    setTransactions: React.Dispatch<React.SetStateAction<Transaction[]>>,
    setLoading: (loading: boolean) => void,
) => {
    const { showToast } = useToast();

    const uploadReceipt = useCallback(async (txId: string, file: File) => {
        if (!realmId) return;
        const formData = new FormData();
        formData.append('file', file);

        try {
            setLoading(true);

            // Optimistic: show uploading state
            setTransactions(prev => prev.map(tx =>
                tx.id === txId ? { ...tx, receipt_url: 'uploading' } : tx
            ));

            const response = await fetch(`${API_BASE_URL}/transactions/upload-receipt?realm_id=${realmId}&tx_id=${txId}`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                showToast('Receipt uploaded and linked', 'success');
                setTransactions(prev => prev.map(tx =>
                    tx.id === txId ? { ...tx, receipt_url: data.receipt_url || '/tmp/uploaded' } : tx
                ));
                return data;
            } else {
                // Rollback
                setTransactions(prev => prev.map(tx =>
                    tx.id === txId ? { ...tx, receipt_url: undefined } : tx
                ));
                showToast(data.detail || 'Upload failed', 'error');
            }
        } catch {
            // Rollback
            setTransactions(prev => prev.map(tx =>
                tx.id === txId ? { ...tx, receipt_url: undefined } : tx
            ));
            showToast('Network error during upload', 'error');
        } finally {
            setLoading(false);
        }
    }, [realmId, setTransactions, setLoading, showToast]);

    return { uploadReceipt };
};
