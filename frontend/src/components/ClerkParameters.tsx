'use client';

import React, { useState, useEffect } from 'react';
import { UserProfile } from "@clerk/nextjs";
import { dark } from "@clerk/themes";

const clerkAppearance = {
    baseTheme: dark,
    variables: {
        colorPrimary: '#00DFD8',
        colorBackground: 'transparent',
        colorText: '#ffffff',
        colorTextSecondary: 'rgba(255, 255, 255, 0.45)',
        colorInputBackground: 'rgba(255, 255, 255, 0.03)',
        colorInputText: '#ffffff',
        borderRadius: '1rem',
        fontFamily: 'inherit',
    },
    elements: {
        card: 'bg-transparent shadow-none border-none p-0',
        navbar: 'hidden',
        header: 'hidden',
        profileSectionTitleText: 'text-brand font-bold uppercase tracking-[0.15em] text-[11px] mb-6',
        scrollBox: 'bg-transparent overflow-visible',
        userPreviewMainIdentifier: 'text-white font-semibold text-base',
        userPreviewSecondaryIdentifier: 'text-white/40 font-medium text-sm',
        accordionTriggerButton: 'hover:bg-white/5 transition-all duration-200 rounded-xl px-4',
        profilePage: 'p-0',
        userButtonPopoverCard: 'hidden',
        breadcrumbs: 'hidden',
        formButtonPrimary: 'btn-primary font-bold py-2.5 px-6 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all',
        formFieldInput: 'bg-white/5 border-white/10 focus:border-brand/40 transition-all rounded-xl py-3 px-4',
        activeDeviceIcon: 'text-brand',
    }
};

export default function ClerkParameters() {
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted) {
        return null;
    }

    return (
        <UserProfile appearance={clerkAppearance} />
    );
}
