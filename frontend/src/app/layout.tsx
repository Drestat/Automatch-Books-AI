import type { Metadata } from "next";

import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import Script from "next/script";
import { ToastProvider } from "@/context/ToastContext";
import MotionProvider from "@/components/MotionProvider";
import localFont from "next/font/local";
import { Space_Mono, Syncopate } from "next/font/google";

const satoshi = localFont({
  src: [
    { path: "../fonts/Satoshi-Light.woff2", weight: "300", style: "normal" },
    { path: "../fonts/Satoshi-Regular.woff2", weight: "400", style: "normal" },
    { path: "../fonts/Satoshi-Medium.woff2", weight: "500", style: "normal" },
    { path: "../fonts/Satoshi-Bold.woff2", weight: "700", style: "normal" },
    { path: "../fonts/Satoshi-Black.woff2", weight: "900", style: "normal" },
  ],
  variable: "--font-satoshi",
  display: "swap",
});

const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-space-mono",
  display: "swap",
});

const syncopate = Syncopate({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-syncopate",
  display: "swap",
});



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
  metadataBase: new URL("https://automatchbooksai.com"),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: "AutoMatch Books AI | AI-Powered QuickBooks Automation",
    description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 3 Flash.",
    url: "https://automatchbooksai.com",
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
      <html lang="en" className={`${satoshi.variable} ${spaceMono.variable} ${syncopate.variable}`}>
        <head>
          {/* PWA Manifest */}
          <link rel="manifest" href="/manifest.json" />
          {/* Apple PWA Meta Tags */}
          <meta name="apple-mobile-web-app-capable" content="yes" />
          <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
          <meta name="apple-mobile-web-app-title" content="AutoMatch" />
          <link rel="apple-touch-icon" href="/icon.png" />
          {/* Theme color for address bar */}
          <meta name="theme-color" content="#000000" />
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
          {/* Service Worker Registration for PWA */}
          <Script id="sw-register" strategy="afterInteractive">
            {`
              if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
              }
            `}
          </Script>
          <MotionProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </MotionProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
