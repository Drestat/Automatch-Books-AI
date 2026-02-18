"use client";

import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '@/lib/api';
import { useToast } from '@/context/ToastContext';

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

export const useQBOData = (realmId: string | null) => {
    const { showToast } = useToast();
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [tags, setTags] = useState<Tag[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [vendors, setVendors] = useState<Vendor[]>([]);

    const fetchAccounts = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/qbo/accounts?realm_id=${realm}`);
            if (response.ok) {
                const data = await response.json();
                setAccounts(data.accounts);
                return data.accounts;
            }
        } catch {
            return [];
        }
        return [];
    }, []);

    const fetchTags = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/tags?realm_id=${realm}`);
            if (response.ok) {
                setTags(await response.json());
            }
        } catch {
            // Tags fetch failed silently
        }
    }, []);

    const fetchCategories = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/categories?realm_id=${realm}`);
            if (response.ok) {
                setCategories(await response.json());
            }
        } catch {
            // Categories fetch failed silently
        }
    }, []);

    const fetchVendors = useCallback(async (realm: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/vendors?realm_id=${realm}`);
            if (response.ok) {
                setVendors(await response.json());
            }
        } catch {
            // Vendors fetch failed silently
        }
    }, []);

    const createTag = useCallback(async (name: string) => {
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
        } catch {
            // Tag creation failed silently
        }
    }, [realmId]);

    const updateBankNickname = useCallback(async (accountId: string, nickname: string) => {
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
        } catch {
            // Nickname update failed silently
        }
    }, [realmId, showToast]);

    // Initial data fetch when realm is available
    useEffect(() => {
        if (realmId) {
            fetchAccounts(realmId);
            fetchTags(realmId);
            fetchCategories(realmId);
            fetchVendors(realmId);
        }
    }, [realmId, fetchAccounts, fetchTags, fetchCategories, fetchVendors]);

    return {
        accounts, setAccounts,
        tags, setTags,
        categories, setCategories,
        vendors, setVendors,
        fetchAccounts, fetchTags, fetchCategories, fetchVendors,
        createTag, updateBankNickname,
    };
};
