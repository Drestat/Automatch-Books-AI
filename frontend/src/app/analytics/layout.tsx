import { Metadata } from 'next';

export const metadata: Metadata = {
    title: "Analytics | Financial Insights",
    robots: {
        index: false,
        follow: false,
    }
};

export default function AnalyticsLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
