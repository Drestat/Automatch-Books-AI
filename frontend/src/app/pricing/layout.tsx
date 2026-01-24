import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Pricing | AutoMatch Books AI",
    description: "Flexible pricing tiers for businesses of all sizes. Start your 14-day free trial of AI-powered QuickBooks automation today.",
    alternates: {
        canonical: '/pricing',
    }
};

export default function PricingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
