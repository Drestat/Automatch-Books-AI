import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const TARGET_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run') + '/api/v1';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const endpoint = searchParams.get('endpoint');

    if (!endpoint) {
        return NextResponse.json({ error: 'Endpoint required' }, { status: 400 });
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
    console.log(`[Proxy] Forwarding to: ${url}`);

    try {
        const response = await fetch(url, {
            headers: {
                'X-User-Id': userId,
            },
        });
        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error: any) {
        console.error('[Proxy] Error:', error);
        return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
    }
}
