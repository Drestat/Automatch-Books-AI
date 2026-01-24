import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';
import { clerkClient } from '@clerk/nextjs/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2025-12-15.clover',
});

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(req: Request) {
    const body = await req.text();
    const signature = (await headers()).get('stripe-signature') as string;

    let event: Stripe.Event;

    try {
        event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (err: unknown) {
        console.error(`Webhook signature verification failed: ${(err as Error).message}`);
        return NextResponse.json({ error: (err as Error).message }, { status: 400 });
    }

    const session = event.data.object as Stripe.Checkout.Session;

    // Handle specific events
    if (event.type === 'checkout.session.completed') {
        const clerkId = session.metadata?.clerkId;
        if (!clerkId) {
            return NextResponse.json({ error: 'Missing clerkId' }, { status: 400 });
        }
        const stripeCustomerId = session.customer as string;
        const subscriptionId = session.subscription as string;

        // 1. Update Backend
        try {
            await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/users/sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: clerkId,
                    stripe_customer_id: stripeCustomerId,
                    subscription_status: 'active',
                    subscription_id: subscriptionId
                }),
            });
        } catch (error) {
            console.error('Error updating backend after checkout:', error);
        }

        // 2. Update Clerk Metadata
        const client = await clerkClient();
        await client.users.updateUserMetadata(clerkId, {
            publicMetadata: {
                subscription_status: 'active',
            }
        });
    }

    if (event.type === 'customer.subscription.deleted') {

        // We need to find the user by stripeCustomerId
        // In a real app, you'd probably have a search endpoint or local DB lookup
        // For now, we'll assume the backend handles it or we'd need another sync mechanism
    }

    return NextResponse.json({ received: true });
}
