import type { Metadata } from "next";

import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import Script from "next/script";
import { ToastProvider } from "@/context/ToastContext";



export const metadata: Metadata = {
  title: {
    template: '%s | AutoMatch Books AI',
    default: 'AutoMatch Books AI | AI-Powered QuickBooks Automation',
  },
  description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 3 Flash. Next-generation financial intelligence for modern businesses.",
  applicationName: 'AutoMatch Books AI',
  generator: 'Next.js',
  referrer: 'origin-when-cross-origin',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  keywords: ["QuickBooks", "Bank Transactions", "AI Matching", "AutoMatch Books AI", "Financial Automation", "Gemini 3 Flash", "Bookkeeping AI", "QuickBooks Online Sync"],
  authors: [{ name: "Andres" }],
  creator: 'Andres',
  publisher: 'AutoMatch Books AI',
  metadataBase: new URL("https://automatchbooks.ai"),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: "AutoMatch Books AI | AI-Powered QuickBooks Automation",
    description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 3 Flash.",
    url: "https://automatchbooks.ai",
    siteName: "AutoMatch Books AI",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "AutoMatch Books AI Dashboard Preview",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AutoMatch Books AI | AI-Powered QuickBooks Automation",
    description: "AI-powered transaction matching for QuickBooks Online.",
    images: ["/og-image.png"],
    creator: '@automatchbooks',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/icon.png',
    apple: '/icon.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: undefined, // customized via globals.css variables if needed, or stick to default
        variables: { colorPrimary: '#3b82f6' }
      }}
    >
      <html lang="en">
        <head>
          <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700,900&display=swap" rel="stylesheet" />
        </head>
        <body
          className="font-sans antialiased text-white selection:bg-brand selection:text-white"
        >
          {/* Google Analytics */}
          <Script
            strategy="afterInteractive"
            src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`}
          />
          <Script
            id="google-analytics"
            strategy="afterInteractive"
          >
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}', {
                page_path: window.location.pathname,
              });
            `}
          </Script>
          <ToastProvider>
            {children}
          </ToastProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
