import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Terms of Service | AutoMatch Books AI",
    description: "The rules and guidelines for using AutoMatch Books AI.",
    alternates: {
        canonical: '/terms',
    }
};

export default function TermsLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
