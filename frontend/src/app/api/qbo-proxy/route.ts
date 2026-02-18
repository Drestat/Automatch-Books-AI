import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const TARGET_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

// Allowlist of permitted backend endpoint prefixes.
// Only endpoints the frontend legitimately needs are included.
// Admin, stripe, and webhook endpoints are excluded.
const ALLOWED_ENDPOINT_PREFIXES = [
    'qbo/',
    'transactions/',
    'accounts/',
    'users/',
    'analytics/',
    'rules/',
    'aliases/',
    'gamification/',
];

function isAllowedEndpoint(endpoint: string): boolean {
    // Reject path traversal and encoding tricks
    const decoded = decodeURIComponent(endpoint);
    if (decoded.includes('..') || decoded.includes('//') || decoded.startsWith('/')) {
        return false;
    }
    return ALLOWED_ENDPOINT_PREFIXES.some(prefix => decoded.startsWith(prefix));
}

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const endpoint = searchParams.get('endpoint');

    if (!endpoint) {
        return NextResponse.json({ error: 'Endpoint required' }, { status: 400 });
    }

    if (!isAllowedEndpoint(endpoint)) {
        return NextResponse.json({ error: 'Endpoint not allowed' }, { status: 403 });
    }

    // Get the authenticated user's ID from Clerk
    const { userId } = await auth();
    if (!userId) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Forward all params except 'endpoint'
    const forwardParams = new URLSearchParams();
    searchParams.forEach((value, key) => {
        if (key !== 'endpoint') {
            forwardParams.append(key, value);
        }
    });

    const url = `${TARGET_URL}/${endpoint}?${forwardParams.toString()}`;

    try {
        const response = await fetch(url, {
            headers: {
                'X-User-Id': userId,
            },
        });
        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error: unknown) {
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
