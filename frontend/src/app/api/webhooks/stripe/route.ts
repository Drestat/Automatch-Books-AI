import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';
import { clerkClient } from '@clerk/nextjs/server';

// @ts-ignore - Some Stripe versions use custom identifiers
const stripe = process.env.STRIPE_SECRET_KEY
    ? new Stripe(process.env.STRIPE_SECRET_KEY, {
        apiVersion: '2024-06-20' as any,
    })
    : null as any;

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run';

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

    // Handle checkout completion — user just paid
    if (event.type === 'checkout.session.completed') {
        const session = event.data.object as Stripe.Checkout.Session;
        const clerkId = session.metadata?.clerkId;
        const tierName = session.metadata?.tierName;

        if (!clerkId) {
            console.error('Stripe webhook: Missing clerkId in session metadata');
            return NextResponse.json({ error: 'Missing clerkId' }, { status: 400 });
        }

        const stripeCustomerId = session.customer as string;

        // 1. Sync user with backend — set tier + stripe customer ID
        try {
            const syncRes = await fetch(`${BACKEND_URL}/api/v1/users/sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: clerkId,
                    stripe_customer_id: stripeCustomerId,
                    subscription_tier: tierName || 'personal',
                    subscription_status: 'active',
                }),
            });
            console.log(`Stripe webhook: Synced user ${clerkId} → tier=${tierName}, status=${syncRes.status}`);
        } catch (error) {
            console.error('Stripe webhook: Error syncing user with backend:', error);
        }

        // 2. Update Clerk public metadata so frontend can read tier immediately
        try {
            const client = await clerkClient();
            await client.users.updateUserMetadata(clerkId, {
                publicMetadata: {
                    subscription_status: 'active',
                    subscription_tier: tierName || 'personal',
                }
            });
        } catch (error) {
            console.error('Stripe webhook: Error updating Clerk metadata:', error);
        }
    }

    // Handle subscription cancellation — user cancelled or payment failed
    if (event.type === 'customer.subscription.deleted') {
        const subscription = event.data.object as Stripe.Subscription;
        const stripeCustomerId = subscription.customer as string;

        // Look up the user by Stripe customer ID and downgrade to free
        try {
            // Use Stripe to get the customer's metadata (which has clerkId)
            const customer = await stripe.customers.retrieve(stripeCustomerId);
            const clerkId = (customer as Stripe.Customer).metadata?.clerkId;

            if (clerkId) {
                // Downgrade in backend
                await fetch(`${BACKEND_URL}/api/v1/users/sync`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        id: clerkId,
                        subscription_tier: 'free',
                        subscription_status: 'cancelled',
                    }),
                });

                // Update Clerk metadata
                const client = await clerkClient();
                await client.users.updateUserMetadata(clerkId, {
                    publicMetadata: {
                        subscription_status: 'cancelled',
                        subscription_tier: 'free',
                    }
                });

                console.log(`Stripe webhook: Downgraded user ${clerkId} to free tier`);
            }
        } catch (error) {
            console.error('Stripe webhook: Error handling subscription deletion:', error);
        }
    }

    // Handle payment failure — notify but don't downgrade immediately
    if (event.type === 'invoice.payment_failed') {
        const invoice = event.data.object as Stripe.Invoice;
        console.warn(`Stripe webhook: Payment failed for customer ${invoice.customer}`);
        // Stripe will retry — downgrade happens on subscription.deleted
    }

    return NextResponse.json({ received: true });
}
