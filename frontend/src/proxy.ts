import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isProtectedRoute = createRouteMatcher(['/dashboard(.*)', '/analytics(.*)']);

export const proxy = clerkMiddleware(async (auth, req) => {
    // Protect dashboard routes
    if (isProtectedRoute(req)) {
        await auth.protect();

        const { sessionClaims } = await auth();
        const status = sessionClaims?.metadata?.subscription_status;

        // Allow access if status is missing (new user) or if active/trialing
        if (status && status !== 'active' && status !== 'trialing') {
            return NextResponse.redirect(new URL('/pricing', req.url));
        }
    }
});

export const config = {
    matcher: [
        // Skip Next.js internals and all static files, unless found in search params
        '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
        // Always run for API routes
        '/(api|trpc)(.*)',
    ],
};
