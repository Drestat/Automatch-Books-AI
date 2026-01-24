import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Privacy Policy | AutoMatch Books AI",
    description: "Our commitment to your financial data sovereignty and security.",
    alternates: {
        canonical: '/privacy',
    }
};

export default function PrivacyLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
