import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Privacy Policy | AutoMatch Books AI",
    description: "Our commitment to your financial data sovereignty and security. Learn how AutoMatch Books AI protects your QuickBooks data.",
    alternates: {
        canonical: '/privacy',
    },
    openGraph: {
        title: "Privacy Policy | AutoMatch Books AI",
        description: "Our commitment to your financial data sovereignty and security.",
        url: "https://automatchbooksai.com/privacy",
        siteName: "AutoMatch Books AI",
        locale: "en_US",
        type: "website",
    },
};

export default function PrivacyLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
