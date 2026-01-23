"use client";

import React, { useState } from 'react';
import TransactionCard from '@/components/TransactionCard';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { useQBO } from '@/hooks/useQBO';
import {
  TrendingUp,
  ShieldCheck,
  Zap,
  Clock,
  Layers,
  Sparkles,
  ArrowRight,
  Lock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserButton } from "@clerk/nextjs";

export default function Home() {
  const [approvedCount, setApprovedCount] = useState(0);
  const { isConnected, loading, transactions, connect, sync, approveMatch } = useQBO();

  const handleAccept = async (id: string) => {
    const success = await approveMatch(id);
    if (success) {
      setApprovedCount(prev => prev + 1);
    }
  };

  if (!isConnected && !loading) {
    return (
      <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-12 max-w-2xl w-full border-brand/20 relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand via-brand-secondary to-brand" />
          <div className="w-20 h-20 rounded-3xl bg-brand/10 text-brand flex items-center justify-center mx-auto mb-8">
            <Zap size={40} />
          </div>
          <h1 className="text-4xl font-black tracking-tight mb-4">Connect QuickBooks</h1>
          <p className="text-white/40 text-lg mb-8 leading-relaxed">
            To start the magic, we need access to your QuickBooks Online transaction feed.
            We use a secure, read-only connection to mirror your data locally.
          </p>
          <button
            onClick={connect}
            className="btn-primary w-full py-4 text-lg flex items-center justify-center gap-3 group"
          >
            <Lock size={20} />
            Secure Connect
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </button>
          <p className="mt-6 text-xs text-white/20 flex items-center justify-center gap-2">
            <ShieldCheck size={14} />
            Bank-Grade Encryption • Read-Only Access
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-6 lg:px-12 max-w-7xl mx-auto">
      <header className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center">
              <Sparkles className="text-white" size={16} />
            </div>
            <span className="text-sm font-bold tracking-[0.3em] uppercase text-brand">Mirror Sync Active</span>
          </div>
          <h1 className="text-[clamp(2.5rem,8vw,4rem)] font-black tracking-tight mb-4 leading-[1.1]">
            Financial <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Intelligence</span>
          </h1>
          <p className="text-white/40 text-base md:text-lg max-w-md">
            AI-powered transaction matching. Review and approve matches to keep your books perfect.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex flex-wrap gap-4 items-center"
        >
          <button className="btn-glass px-6 py-4 flex items-center gap-3 group border-brand/30 hover:bg-brand/10">
            <ShieldCheck size={20} className="text-brand" />
            <div className="text-left">
              <span className="block text-[10px] uppercase tracking-wider font-bold text-brand">Bulk Action</span>
              <span className="text-xs font-bold text-white">Approve High Confidence</span>
            </div>
          </button>

          <div className="glass-panel px-6 py-4 flex flex-col items-center min-w-[120px]">
            <span className="text-3xl font-black text-brand leading-none mb-1">{approvedCount}</span>
            <span className="text-[10px] uppercase tracking-[0.1em] font-bold text-white/30 text-center">Approved Today</span>
          </div>
          <button
            onClick={sync}
            disabled={loading}
            className="btn-primary h-full min-h-[64px] px-8 flex items-center gap-3 group disabled:opacity-50"
          >
            <Zap size={20} className={`group-hover:animate-pulse ${loading ? 'animate-spin' : ''}`} />
            <span className="font-bold">{loading ? 'Syncing...' : 'Sync Now'}</span>
          </button>
          <div className="ml-2">
            <UserButton afterSignOutUrl="/" />
          </div>
        </motion.div>
      </header>

      <main>
        <BentoGrid>
          {/* Quick Stats & Action Cards */}
          <BentoTile className="md:col-span-1 bg-gradient-to-br from-brand/10 to-transparent border-brand/20">
            <div className="flex flex-col h-full justify-between">
              <div>
                <ShieldCheck className="text-brand mb-4" size={32} />
                <h3 className="text-xl font-bold mb-2">Automated Accuracy</h3>
                <p className="text-sm text-white/50 leading-relaxed">
                  Gemini 1.5 Pro is currently maintaining a <span className="text-brand font-bold">94.2%</span> accuracy rate across your vendor history.
                </p>
              </div>
              <div className="mt-8">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-xs font-bold text-white/30 uppercase tracking-wider">Historical Trend</span>
                  <span className="text-xs font-bold text-emerald-400">+2.4%</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "94.2%" }}
                    transition={{ duration: 1.5, delay: 0.5 }}
                    className="h-full bg-brand"
                  />
                </div>
              </div>
            </div>
          </BentoTile>

          <BentoTile className="md:col-span-1 border-white/5">
            <div className="flex flex-col h-full justify-between">
              <div>
                <Clock className="text-brand-secondary mb-4" size={32} />
                <h3 className="text-xl font-bold mb-2">Pending Review</h3>
                <p className="text-sm text-white/50 leading-relaxed">
                  You have <span className="text-white font-bold">{transactions.length}</span> transactions waiting for your confirmation.
                </p>
              </div>
              <button className="btn-glass w-full text-xs font-bold py-3 mt-6">
                View History
              </button>
            </div>
          </BentoTile>

          <BentoTile className="md:col-span-1 border-white/5 bg-white/[0.01]">
            <div className="flex flex-col h-full justify-between">
              <div>
                <Layers className="text-brand-accent mb-4" size={32} />
                <h3 className="text-xl font-bold mb-2">Multi-Factor Matching</h3>
                <p className="text-sm text-white/50 leading-relaxed">
                  Syncing across 3 checking accounts and 2 credit cards.
                </p>
              </div>
              <div className="mt-6 flex -space-x-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="w-10 h-10 rounded-full border-2 border-slate-900 bg-white/10 flex items-center justify-center overflow-hidden">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-brand to-brand-accent opacity-50" />
                  </div>
                ))}
                <div className="w-10 h-10 rounded-full border-2 border-slate-900 bg-white/5 flex items-center justify-center text-[10px] font-bold">
                  +2
                </div>
              </div>
            </div>
          </BentoTile>

          {/* Transactions List */}
          <div className="md:col-span-3 mt-8">
            <div className="flex items-center gap-4 mb-8">
              <h2 className="text-2xl font-black tracking-tight">Daily Matches</h2>
              <div className="h-[1px] flex-1 bg-white/5" />
              <div className="flex gap-2">
                <button className="px-4 py-2 rounded-full border border-white/10 text-xs font-bold hover:bg-white/5 transition-colors">By Date</button>
                <button className="px-4 py-2 rounded-full border border-brand/30 bg-brand/10 text-brand text-xs font-bold">By Confidence</button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AnimatePresence mode="popLayout">
                {transactions.map((tx, index) => (
                  <motion.div
                    key={tx.id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8, filter: 'blur(10px)' }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                  >
                    <TransactionCard tx={tx} onAccept={handleAccept} />
                  </motion.div>
                ))}
              </AnimatePresence>

              {transactions.length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="col-span-full py-20 flex flex-col items-center justify-center glass-panel"
                >
                  <div className="w-20 h-20 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-6">
                    <ShieldCheck size={40} />
                  </div>
                  <h3 className="text-2xl font-bold mb-2">All Caught Up!</h3>
                  <p className="text-white/40">You've cleared all pending transactions for today.</p>
                </motion.div>
              )}
            </div>
          </div>
        </BentoGrid>
      </main>

      <footer className="mt-24 border-t border-white/5 pt-12 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Sparkles className="text-brand animate-pulse" size={16} />
          <span className="text-xs font-bold uppercase tracking-[0.4em] text-white/20">Next-Gen Accounting</span>
        </div>
        <p className="text-white/20 text-xs">MirrorSync Engine &copy; 2026. Powered by Google Gemini 1.5 Pro.</p>
      </footer>
    </div>
  );
}
