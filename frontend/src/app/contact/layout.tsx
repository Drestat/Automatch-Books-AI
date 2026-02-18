import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Contact Us | AutoMatch Books AI",
    description: "Get in touch with our team for support or inquiries about AI-powered bookkeeping.",
    alternates: {
        canonical: '/contact',
    },
    openGraph: {
        title: "Contact Us | AutoMatch Books AI",
        description: "Have questions about AI-powered bookkeeping? Our team is here to help you automate your financial future.",
        url: "https://automatchbooksai.com/contact",
        siteName: "AutoMatch Books AI",
        images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Contact AutoMatch Books AI" }],
        locale: "en_US",
        type: "website",
    },
    twitter: {
        card: "summary_large_image",
        title: "Contact Us | AutoMatch Books AI",
        description: "Have questions about AI-powered bookkeeping? Our team is here to help.",
        images: ["/og-image.png"],
    },
};

export default function ContactLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
