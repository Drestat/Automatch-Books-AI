"use client";

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/context/ToastContext';
import { useUser } from '@/hooks/useUser';
import { API_BASE_URL } from '@/lib/api';
import { track } from '@/lib/analytics';

interface ConnectResponse {
    auth_url: string;
}

export const useQBOConnection = () => {
    const { user, isLoaded, profile } = useUser();
    const router = useRouter();
    const searchParams = useSearchParams();
    const { showToast } = useToast();

    const [realmId, setRealmId] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [loading, setLoading] = useState(false);

    // Handle QBO OAuth callback redirect
    const handleSuccessRedirect = useCallback((realm: string) => {
        setLoading(true);
        try {
            localStorage.setItem('qbo_realm_id', realm);
            localStorage.setItem('is_new_connection', 'true');
            setRealmId(realm);
            setIsConnected(true);
            router.replace('/dashboard');
        } catch {
            // State update failed silently
        } finally {
            setLoading(false);
        }
    }, [router]);

    // Effect: Handle URL params (QBO OAuth callback)
    useEffect(() => {
        const code = searchParams.get('code');
        const realm = searchParams.get('realmId');
        if (code && realm) {
            handleSuccessRedirect(realm);
        }
    }, [searchParams, handleSuccessRedirect]);

    // Effect: Backfill realm from user profile
    useEffect(() => {
        if (!isLoaded || !user) return;
        if (profile?.realm_id && !realmId) {
            setRealmId(profile.realm_id);
            setIsConnected(true);
            localStorage.setItem('qbo_realm_id', profile.realm_id);
        }
    }, [isLoaded, user, profile, realmId]);

    // Effect: Restore session from localStorage
    useEffect(() => {
        const storedRealm = localStorage.getItem('qbo_realm_id');
        if (storedRealm) {
            setRealmId(storedRealm);
            setIsConnected(true);
        }
    }, []);

    const connect = async () => {
        if (!user) {
            showToast('Please sign in to connect to QuickBooks.', 'error');
            return;
        }
        track('sync_start', { type: 'connect_flow' }, user.id);
        setLoading(true);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            const proxyUrl = `/api/qbo-proxy?endpoint=qbo/authorize&user_id=${user.id}`;
            const response = await fetch(proxyUrl, { signal: controller.signal });
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
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : 'Unknown Error';
            showToast(`Connection failed: ${message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    const disconnect = async () => {
        if (!realmId) return;
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/qbo/disconnect?realm_id=${realmId}`, {
                method: 'DELETE'
            });
            if (!response.ok && response.status !== 404) {
                throw new Error('Failed to disconnect from backend');
            }
        } catch {
            // Even if backend fails, clear local state below
        } finally {
            localStorage.removeItem('qbo_realm_id');
            setRealmId(null);
            setIsConnected(false);
            setLoading(false);
            window.location.reload();
        }
    };

    return { realmId, isConnected, loading, setLoading, connect, disconnect };
};
