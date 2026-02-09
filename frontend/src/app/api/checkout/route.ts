import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import Stripe from 'stripe';

// @ts-ignore - Some Stripe versions use custom identifiers
const stripe = process.env.STRIPE_SECRET_KEY
    ? new Stripe(process.env.STRIPE_SECRET_KEY, {
        apiVersion: '2024-06-20' as any,
    })
    : null as any;

export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { tierName } = await req.json();

    try {
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price_data: {
                        currency: 'usd',
                        product_data: {
                            name: tierName || 'Founder Plan',
                            description: 'AutoMatch Books AI Subscription',
                        },
                        unit_amount: tierName === 'Founder' ? 2900 : tierName === 'Empire' ? 7900 : 900,
                        recurring: {
                            interval: 'month',
                        },
                    },
                    quantity: 1,
                },
            ],
            mode: 'subscription',
            success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
            metadata: {
                clerkId: userId,
                tierName: tierName,
            },
        });

        return NextResponse.json({ url: session.url });
    } catch (err: unknown) {
        console.error('Error creating checkout session:', err);
        return NextResponse.json({ error: (err as Error).message }, { status: 500 });
    }
}
