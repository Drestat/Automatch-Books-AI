export type AnalyticsEvent =
    | 'match_approve'
    | 'match_reject'
    | 'sync_start'
    | 'demo_start'
    | 'nav_analytics';

declare global {
    interface Window {
        gtag?: (command: string, ...args: any[]) => void;
    }
}

export const track = async (event: AnalyticsEvent, properties?: Record<string, unknown>, userId?: string) => {
    const timestamp = new Date().toISOString();

    // 1. Console Log (Dev)
    console.log(`[Analytics] ${timestamp} | ${event}`, properties || '');

    // 2. Google Analytics (GA4)
    if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('event', event, {
            ...properties,
            user_id: userId
        });
    }

    // 3. Backend (Permanent Data Lake)
    // We only track to backend if we have a userId to attribute it to
    if (userId) {
        try {
            await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/v1/analytics/track`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_name: event,
                    properties: properties,
                    user_id: userId
                })
            });
        } catch (error) {
            console.error('[Analytics] Backend sync failed:', error);
        }
    }
};

export const identify = (userId: string) => {
    if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('config', process.env.NEXT_PUBLIC_GA_ID || '', {
            user_id: userId
        });
    }
};
