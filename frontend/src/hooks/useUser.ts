"use client";

import { useUser as useClerkUser } from "@clerk/nextjs";
import { useState, useEffect } from "react";
import { API_BASE_URL } from '@/lib/api';

export interface UserProfile {
    id: string;
    email: string;
    subscription_tier: string;
    subscription_status: string;
    token_balance: number;
    monthly_token_allowance: number;
    auto_accept_enabled: boolean;
    realm_id: string | null;
}

export const useUser = () => {
    const { user: clerkUser, isLoaded } = useClerkUser();
    const [profile, setProfile] = useState<UserProfile | null>(null);

    const fetchProfile = async () => {
        try {
            // Assuming we have an endpoint GET /users/me
            const res = await fetch(`${API_BASE_URL}/users/me?user_id=${clerkUser?.id}`);
            const data = await res.json();
            if (res.ok) {
                setProfile(data);
            }
        } catch {
            // Profile fetch failed — will retry on next mount
        }
    };

    useEffect(() => {
        if (!isLoaded || !clerkUser) return;
        fetchProfile();
    }, [isLoaded, clerkUser]);

    return {
        user: clerkUser,
        profile,
        isLoaded,
        refreshProfile: fetchProfile
    };
};
