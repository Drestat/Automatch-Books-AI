import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Features & Testing Guide | AutoMatch Books AI",
    description: "Detailed breakdown of features, architecture vision, and A-Z testing instructions for AutoMatch Books AI.",
    alternates: {
        canonical: '/features',
    }
};

export default function FeaturesLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
