import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Pricing | AutoMatch Books AI",
    description: "Flexible pricing tiers for businesses of all sizes. Start your 14-day free trial of AI-powered QuickBooks automation today.",
    alternates: {
        canonical: '/pricing',
    },
    openGraph: {
        title: "Pricing | AutoMatch Books AI",
        description: "Flexible pricing tiers for businesses of all sizes. Start your 14-day free trial of AI-powered QuickBooks automation today.",
        url: "https://automatchbooksai.com/pricing",
        siteName: "AutoMatch Books AI",
        images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "AutoMatch Books AI Pricing Plans" }],
        locale: "en_US",
        type: "website",
    },
    twitter: {
        card: "summary_large_image",
        title: "Pricing | AutoMatch Books AI",
        description: "Flexible pricing tiers for businesses of all sizes. AI-powered QuickBooks automation starting free.",
        images: ["/og-image.png"],
    },
};

export default function PricingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
