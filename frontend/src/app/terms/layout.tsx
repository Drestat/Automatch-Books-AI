import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Terms of Service | AutoMatch Books AI",
    description: "Terms and conditions for using AutoMatch Books AI. Understand your rights and responsibilities.",
    alternates: {
        canonical: '/terms',
    },
    openGraph: {
        title: "Terms of Service | AutoMatch Books AI",
        description: "Terms and conditions for using AutoMatch Books AI.",
        url: "https://automatchbooksai.com/terms",
        siteName: "AutoMatch Books AI",
        locale: "en_US",
        type: "website",
    },
};

export default function TermsLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
