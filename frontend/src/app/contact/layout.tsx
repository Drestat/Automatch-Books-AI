import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Contact Us | AutoMatch Books AI",
    description: "Get in touch with our team for support or inquiries about AI-powered bookkeeping.",
    alternates: {
        canonical: '/contact',
    }
};

export default function ContactLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
