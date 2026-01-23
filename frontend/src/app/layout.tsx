import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
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
  title: "AutoMatch Books AI | AI-Powered QuickBooks Automation",
  description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 1.5 Pro. Next-generation financial intelligence for modern businesses.",
  keywords: ["QuickBooks", "Bank Transactions", "AI Matching", "AutoMatch Books AI", "Financial Automation", "Gemini 1.5 Pro"],
  authors: [{ name: "Andres" }],
  openGraph: {
    title: "AutoMatch Books AI | AI-Powered QuickBooks Automation",
    description: "Seamlessly match and sync your bank transactions with QuickBooks Online using Gemini 1.5 Pro.",
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
  },
  metadataBase: new URL("https://automatchbooks.ai"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body
          className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        >
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
