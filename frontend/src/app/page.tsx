"use client";

import React, { useState } from 'react';
import TransactionCard from '@/components/TransactionCard';
import Link from 'next/link';
import { TrendingUp } from 'lucide-react';

const MOCK_TRANSACTIONS = [
  {
    id: '1',
    date: 'Jan 22, 2026',
    description: 'Starbucks Coffee',
    amount: -12.50,
    currency: 'USD',
    suggested_category_name: 'Meals & Entertainment',
    reasoning: 'Merchant identified as food/beverage provider based on previous history.',
    confidence: 0.95
  },
  {
    id: '2',
    date: 'Jan 21, 2026',
    description: 'Amazon AWS Billing',
    amount: -450.00,
    currency: 'USD',
    suggested_category_name: 'Software & Technology',
    reasoning: 'Recurring payment detected for cloud infrastructure services.',
    confidence: 0.88
  },
  {
    id: '3',
    date: 'Jan 20, 2026',
    description: 'Zelle Payment: John Smith',
    amount: 1500.00,
    currency: 'USD',
    suggested_category_name: 'Uncategorized Income',
    reasoning: 'Peer-to-peer transfer received; likely customer payment or reimbursement.',
    confidence: 0.65
  }
];

export default function Home() {
  const [approvedCount, setApprovedCount] = useState(0);

  const handleAccept = (id: string) => {
    console.log(`Accepted transaction ${id}`);
    setApprovedCount(prev => prev + 1);
    // Real logic would call an API route to write-back to QBO
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Easy Bank Transactions",
            "operatingSystem": "Web",
            "applicationCategory": "FinanceApplication",
            "description": "AI-powered transaction matching for QuickBooks Online.",
            "offers": {
              "@type": "Offer",
              "price": "0",
              "priceCurrency": "USD"
            }
          })
        }}
      />
      <div className="max-w-xl mx-auto py-12 px-6">
        <header className="mb-12">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold tracking-tight">Daily Matches</h1>
              <p className="text-white/60 mt-2">Approve your AI-matched transactions</p>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/analytics" className="btn-glass text-xs py-2 px-4 flex items-center gap-2">
                <TrendingUp size={14} />
                View Analytics
              </Link>
              <div className="glass-panel px-4 py-2 flex flex-col items-center">
                <span className="text-2xl font-bold text-brand">{approvedCount}</span>
                <span className="text-[10px] uppercase tracking-tighter text-white/40">Approved</span>
              </div>
            </div>
          </div>
        </header>

        <main className="space-y-6">
          <section aria-label="Transactions matching feed" className="space-y-6">
            {MOCK_TRANSACTIONS.map(tx => (
              <article key={tx.id}>
                <TransactionCard tx={tx} onAccept={handleAccept} />
              </article>
            ))}
          </section>
        </main>

        <footer className="mt-20 text-center">
          <p className="text-white/30 text-xs">Powered by Gemini 1.5 Pro & Direct QBO Connect</p>
        </footer>
      </div>
    </>
  );
}
