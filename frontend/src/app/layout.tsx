import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Easy Bank Transactions | AI-Powered QuickBooks Automation",
  description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 1.5 Pro. Next-generation financial intelligence for modern businesses.",
  keywords: ["QuickBooks", "Bank Transactions", "AI Matching", "Easy Bank Transactions", "Financial Automation", "Gemini 1.5 Pro"],
  authors: [{ name: "Andres" }],
  openGraph: {
    title: "Easy Bank Transactions | AI-Powered QuickBooks Automation",
    description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 1.5 Pro.",
    url: "https://easybanktransactions.app",
    siteName: "Easy Bank Transactions",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Easy Bank Transactions Dashboard Preview",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Easy Bank Transactions | AI-Powered QuickBooks Automation",
    description: "AI-powered transaction matching for QuickBooks Online.",
    images: ["/og-image.png"],
  },
  metadataBase: new URL("https://easybanktransactions.app"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
