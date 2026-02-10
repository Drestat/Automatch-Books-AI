"use client";

import { useUser as useClerkUser } from "@clerk/nextjs";
import { useState, useEffect } from "react";

const API_BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

export interface UserProfile {
    id: string;
    email: string;
    subscription_tier: string;
    subscription_status: string;
    token_balance: number;
    monthly_token_allowance: number;
    auto_accept_enabled: boolean;
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
        } catch (e) {
            console.error("Failed to fetch user profile", e);
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
