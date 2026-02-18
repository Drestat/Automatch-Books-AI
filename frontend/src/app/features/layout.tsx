import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Features & Testing Guide | AutoMatch Books AI",
    description: "Detailed breakdown of features, architecture vision, and A-Z testing instructions for AutoMatch Books AI.",
    alternates: {
        canonical: '/features',
    },
    openGraph: {
        title: "Features & Testing Guide | AutoMatch Books AI",
        description: "Explore AI-powered transaction matching, receipt mirroring, split transactions, and auditable intelligence for QuickBooks Online.",
        url: "https://automatchbooksai.com/features",
        siteName: "AutoMatch Books AI",
        images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "AutoMatch Books AI Features Overview" }],
        locale: "en_US",
        type: "website",
    },
    twitter: {
        card: "summary_large_image",
        title: "Features & Testing Guide | AutoMatch Books AI",
        description: "Explore AI-powered transaction matching, receipt mirroring, and auditable intelligence for QuickBooks.",
        images: ["/og-image.png"],
    },
};

export default function FeaturesLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
