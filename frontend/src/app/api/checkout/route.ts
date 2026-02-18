import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import Stripe from 'stripe';

const stripe = process.env.STRIPE_SECRET_KEY
    ? new Stripe(process.env.STRIPE_SECRET_KEY)
    : null! as Stripe;

export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { tierName } = await req.json();

    // Map tier backend key → price in cents
    const TIER_PRICES: Record<string, number> = {
        personal: 299,    // $2.99/mo
        business: 899,    // $8.99/mo
        corporate: 4999,  // $49.99/mo
    };

    const TIER_LABELS: Record<string, string> = {
        personal: 'Personal Plan',
        business: 'Business Plan',
        corporate: 'Corporate Plan',
    };

    const unitAmount = TIER_PRICES[tierName] || 2900;
    const label = TIER_LABELS[tierName] || 'Founder Plan';

    try {
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price_data: {
                        currency: 'usd',
                        product_data: {
                            name: label,
                            description: 'AutoMatch Books AI Subscription',
                        },
                        unit_amount: unitAmount,
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
            client_reference_id: userId,
            metadata: {
                clerkId: userId,
                tierName: tierName,  // backend key: starter, founder, empire
            },
        });

        return NextResponse.json({ url: session.url });
    } catch (err: unknown) {
        return NextResponse.json({ error: 'Failed to create checkout session' }, { status: 500 });
    }
}
