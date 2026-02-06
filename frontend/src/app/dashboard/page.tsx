"use client";

import React, { useState, Suspense, useEffect } from 'react';
import Link from 'next/link';
import TransactionCard from '@/components/TransactionCard';
import { BentoGrid } from '@/components/BentoGrid';
import { BentoTile } from '@/components/BentoTile';
import { useQBO } from '@/hooks/useQBO';
import {
  ShieldCheck,
  Zap,
  Clock,
  Layers,
  Sparkles,
  ArrowRight,
  Lock,
  BarChart3,
  Coins,
  Filter,
  Edit2,
  Building2,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import { AccountSelectorModal } from '@/components/AccountSelectorModal';
import { TokenDepletedModal } from '@/components/TokenDepletedModal';
import { motion, AnimatePresence } from 'framer-motion';
import { UserButton } from "@clerk/nextjs";
import { track } from '@/lib/analytics';
import { useUser } from '@/hooks/useUser';

import { SubscriptionGuard } from '@/components/SubscriptionGuard';

function DashboardContent() {
  const {
    profile
  } = useUser();

  const {
    isConnected,
    loading: qboLoading,
    transactions,
    connect,
    sync,
    approveMatch,
    bulkApprove,
    uploadReceipt,
    isLoaded,
    isDemo,
    enableDemo,
    user,
    subscriptionStatus,
    daysRemaining,
    accounts,
    fetchTransactions,
    updateTransaction,
    updateBankNickname,
    createTag,
    tags,
    categories,
    reAnalyze,
    disconnect,
    excludeTransaction,
    includeTransaction,
    vendors,
    showTokenModal,
    setShowTokenModal
  } = useQBO();

  const [loading, setLoading] = useState(false); // Local loading for UI actions
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [sortConfig, setSortConfig] = useState<{ key: 'date' | 'confidence', direction: 'asc' | 'desc' }>({ key: 'date', direction: 'desc' });
  const [activeTab, setActiveTab] = useState<'review' | 'matched' | 'excluded'>('review');

  const toggleSort = (key: 'date' | 'confidence') => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  // SHOW ALL TRANSACTIONS: Bank feed imports + manual entries
  // User wants complete view of all Mastercard activity

  // CORRECT STRATEGY: Use is_qbo_matched (which checks LinkedTxn in QBO)
  // A transaction is "Categorized" ONLY if QBO has accepted/matched it (LinkedTxn exists)
  // Everything else is "For Review", even if it has a suggested category
  // FILTERING LOGIC
  // 1. Filter by Selected Accounts (if active)
  const filteredTransactions = selectedAccounts.length > 0
    ? transactions.filter(tx => tx.account_id && selectedAccounts.includes(tx.account_id))
    : transactions;

  // 2. Filter by Status (Review vs Matched vs Excluded)
  const toReviewTxs = filteredTransactions.filter(tx => {
    return !tx.is_excluded && !tx.is_qbo_matched;
  });

  const alreadyMatchedTxs = filteredTransactions.filter(tx =>
    !tx.is_excluded &&
    tx.is_qbo_matched
  );

  const excludedTxs = filteredTransactions.filter(tx => tx.is_excluded === true);

  const currentTabTransactions =
    activeTab === 'review' ? toReviewTxs :
      activeTab === 'matched' ? alreadyMatchedTxs :
        excludedTxs;

  const sortedTransactions = [...currentTabTransactions].sort((a, b) => {
    let comparison = 0;
    if (sortConfig.key === 'date') {
      comparison = new Date(a.date).getTime() - new Date(b.date).getTime();
    } else if (sortConfig.key === 'confidence') {
      comparison = (a.confidence || 0) - (b.confidence || 0);
    }
    return sortConfig.direction === 'asc' ? comparison : -comparison;
  });


  // Auto-open modal if connected but no accounts active (and not demo)
  useEffect(() => {
    if (isConnected && !isDemo && isLoaded) {
      const urlParams = new URLSearchParams(window.location.search);
      const isNewConnection = localStorage.getItem('is_new_connection') === 'true';

      if ((urlParams.get('code') && urlParams.get('realmId')) || isNewConnection) {
        setShowAccountModal(true);
        // Clear the flag so it doesn't re-trigger
        localStorage.removeItem('is_new_connection');
      }
    }
  }, [isConnected, isDemo, isLoaded]);

  // Auto-filter is now handled by useQBO hook (Effect 4)
  // selectedAccounts is only used for manual UI filtering in the dropdown

  const toggleAccount = (accId: string) => {
    setSelectedAccounts(prev =>
      prev.includes(accId) ? prev.filter(id => id !== accId) : [...prev, accId]
    );
  };

  const handleAccept = async (txId: string) => {
    setLoading(true);
    await approveMatch(txId);
    setLoading(false);
  };

  const handleReceiptUpload = async (txId: string, file: File) => {
    await uploadReceipt(txId, file);
  };

  const handleBulkApprove = async () => {
    // Bulk approve high confidence items in NEEDS_REVIEW
    const highConfidence = transactions.filter(tx =>
      tx.confidence > 0.9 &&
      tx.status === 'NEEDS_REVIEW' // Only approve things needing review
    ).map(tx => tx.id);

    if (highConfidence.length > 0) {
      setLoading(true);
      await bulkApprove(highConfidence);
      setLoading(false);
    }
  };

  const approvedCount = transactions.filter(tx => tx.status === 'CATEGORIZED').length;

  if (!isConnected && !isDemo) {
    return (
      <SubscriptionGuard status={subscriptionStatus} daysRemaining={daysRemaining}>
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.02] -z-10" />
          <div className="w-full max-w-md space-y-8 relative z-10">
            <div className="text-center space-y-4">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="w-20 h-20 bg-brand/10 rounded-3xl flex items-center justify-center mx-auto ring-1 ring-brand/20 shadow-2xl shadow-brand/20"
              >
                <Lock size={32} className="text-brand" />
              </motion.div>
              <h1 className="text-4xl font-black tracking-tight">Connect QBO</h1>
              <p className="text-white/40 text-lg">
                Link your QuickBooks Online account to unlock the magical mirror.
              </p>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={connect}
              disabled={false} // DEBUG: Force enabled
              className="w-full btn-primary py-4 text-lg font-bold flex items-center justify-center gap-3 group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              {qboLoading || !isLoaded ? (
                <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Connect Securely
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </motion.button>

            <button
              onClick={enableDemo}
              disabled={qboLoading || !isLoaded}
              className="w-full py-4 text-sm font-bold text-white/40 hover:text-white transition-colors disabled:opacity-50"
            >
              Try Demo Mode
            </button>

            <p className="text-center text-xs text-white/20 font-medium">
              Uses bank-grade 256-bit encryption.
            </p>
          </div>
        </div>
      </SubscriptionGuard>
    );
  }

  return (
    <SubscriptionGuard status={subscriptionStatus} daysRemaining={daysRemaining}>
      <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white pb-20">

        <AccountSelectorModal
          isOpen={showAccountModal}
          onClose={() => setShowAccountModal(false)}
          onSuccess={() => {
            // Refresh data
            const realm = localStorage.getItem('qbo_realm_id');
            if (realm) {
              // Force refresh of accounts and transactions
              window.location.reload(); // Simplest way to refresh everything including hook state
            }
          }}
          realmId={localStorage.getItem('qbo_realm_id') || ''}
        />

        <TokenDepletedModal
          isOpen={showTokenModal}
          onClose={() => setShowTokenModal(false)}
        />

        <header className="pt-12 pb-8 px-6 md:px-12 max-w-[1400px] mx-auto flex flex-col md:flex-row md:items-end justify-between gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${isDemo ? 'bg-amber-400' : 'bg-brand'} animate-pulse`} />
              <span className={`text-xs font-bold tracking-[0.2em] ${isDemo ? 'text-amber-400' : 'text-brand'} uppercase`}>
                {isDemo ? 'Demo Mode Active' : 'Live Sync Active'}
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight">
              Financial <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Intelligence</span>
            </h1>
            <p className="text-white/40 text-base md:text-lg max-w-md">
              Leverage <strong className="text-white/90">Gemini 3 Flash&apos;s brain</strong> to automatically categorize your transactions, then explain the reasoning. All you have to do is click approve.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex flex-wrap gap-4 items-center"
          >
            {profile && (
              <div className="btn-glass px-4 py-3 flex items-center gap-2 border-brand/30 bg-brand/5">
                <Coins size={18} className="text-yellow-400" />
                <div>
                  <p className="text-[10px] uppercase text-white/40 font-bold tracking-wider">Balance</p>
                  <p className="font-mono font-bold text-white/90 leading-none">{profile.token_balance.toLocaleString()} <span className="text-xs text-white/40">/ {profile.monthly_token_allowance.toLocaleString()}</span></p>
                </div>
              </div>
            )}

            {/* Manage Accounts Button */}
            {isConnected && !isDemo && (
              <button
                onClick={() => setShowAccountModal(true)}
                className="btn-glass px-4 py-3 flex items-center gap-2 border-brand/30 hover:bg-brand/10 text-sm"
              >
                <Building2 size={16} className="text-brand" />
                <span>Manage Accounts</span>
              </button>
            )}

            {/* Account Filter */}
            {isConnected && accounts.length > 0 && !isDemo && (
              <div className="relative group/filter">
                <button className="btn-glass px-4 py-3 flex items-center gap-2 border-brand/30 hover:bg-brand/10 text-sm">
                  <Filter size={16} className={selectedAccounts.length > 0 ? 'text-brand' : 'text-white/40'} />
                  <span>{selectedAccounts.length > 0 ? `${selectedAccounts.length} Filtered` : 'All Accounts'}</span>
                </button>
                {/* Dropdown */}
                <div className="absolute top-full right-0 mt-2 w-56 bg-[#0a0a0a] border border-white/10 rounded-xl shadow-xl overflow-hidden hidden group-hover/filter:block z-50">
                  <div className="p-2 space-y-1">
                    {accounts.map(acc => (
                      <div
                        key={acc.id}
                        className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-colors group/acc ${selectedAccounts.includes(acc.id) ? 'bg-brand/20 text-brand' : 'hover:bg-white/5 text-white/60'}`}
                      >
                        <button onClick={() => toggleAccount(acc.id)} className="flex-1 text-left truncate">
                          {acc.nickname || acc.name}
                        </button>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              const newName = window.prompt("Rename this account (Nickname):", acc.nickname || acc.name);
                              if (newName) updateBankNickname(acc.id, newName);
                            }}
                            className="opacity-0 group-hover/acc:opacity-100 hover:text-white transition-opacity text-white/40"
                          >
                            <Edit2 size={10} />
                          </button>
                          {selectedAccounts.includes(acc.id) && <div className="w-2 h-2 rounded-full bg-brand" />}
                        </div>
                      </div>
                    ))}
                    {selectedAccounts.length > 0 && (
                      <button
                        onClick={() => setSelectedAccounts([])}
                        className="w-full text-center py-2 text-xs text-brand hover:underline border-t border-white/5 mt-2"
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            <Link href="/analytics" onClick={() => track('nav_analytics', {}, user?.id)}>
              <button className="btn-glass px-6 py-4 flex items-center gap-3 group border-brand/30 hover:bg-brand/10">
                <BarChart3 size={20} className="text-brand" />
                <div className="text-left">
                  <span className="block text-[10px] uppercase tracking-wider font-bold text-brand">Insights</span>
                  <span className="text-xs font-bold text-white">View Analytics</span>
                </div>
              </button>
            </Link>

            <button
              onClick={handleBulkApprove}
              disabled={loading || transactions.filter(tx => tx.confidence > 0.9 && tx.status !== 'approved').length === 0}
              className="btn-glass px-6 py-4 flex items-center gap-3 group border-brand/30 hover:bg-brand/10 disabled:opacity-50 relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-brand/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <div className="relative z-10 p-2 rounded-full bg-brand/10 text-brand group-hover:bg-brand group-hover:text-white transition-colors">
                <ShieldCheck size={20} />
              </div>
              <div className="text-left relative z-10">
                <span className="block text-[10px] uppercase tracking-wider font-bold text-brand group-hover:text-brand-secondary transition-colors">Bulk Action</span>
                <span className="text-xs font-bold text-white">Approve High Confidence</span>
              </div>
            </button>

            <div className="glass-panel px-6 py-4 flex flex-col items-center min-w-[120px]">
              <span className="text-3xl font-black text-brand leading-none mb-1">{approvedCount}</span>
              <span className="text-[10px] uppercase tracking-[0.1em] font-bold text-white/30 text-center">Approved Today</span>
            </div>
            <button
              onClick={() => sync()}
              disabled={loading}
              className="btn-primary h-full min-h-[64px] px-8 flex items-center gap-3 group disabled:opacity-50"
            >
              <Zap size={20} className={`group-hover:animate-pulse ${loading ? 'animate-spin' : ''}`} />
              <span className="font-bold">{loading ? 'Syncing...' : 'Sync Now'}</span>
            </button>
            <div className="ml-2 flex items-center gap-3">
              <button
                onClick={disconnect}
                className="px-4 py-2 text-red-400 hover:text-red-300 transition-colors rounded-lg hover:bg-red-500/10 border border-red-500/20 hover:border-red-500/40 flex items-center gap-2"
                title="Disconnect from QuickBooks"
              >
                <Zap size={14} className="rotate-45" />
                <span className="text-sm font-medium">Disconnect</span>
              </button>
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
                    Gemini 3 Flash is currently maintaining a <span className="text-brand font-bold">94.2%</span> accuracy rate across your vendor history.
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
                    You have <span className="text-white font-bold">{transactions.filter(t => t.status !== 'approved').length}</span> transactions waiting for your confirmation.
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
              <div className="flex flex-col md:flex-row md:items-center gap-6 mb-8">
                <div className="flex bg-[#0a0a0a] p-1 rounded-xl border border-white/5 shadow-2xl">
                  <button
                    onClick={() => setActiveTab('review')}
                    className={`px-6 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 flex items-center gap-2 ${activeTab === 'review' ? 'bg-brand text-black shadow-lg shadow-brand/20' : 'text-white/40 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    For review
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-black ${activeTab === 'review' ? 'bg-black/20 text-black' : 'bg-white/5 text-white/40'}`}>
                      {toReviewTxs.length}
                    </span>
                  </button>
                  <button
                    onClick={() => setActiveTab('matched')}
                    className={`px-6 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 flex items-center gap-2 ${activeTab === 'matched' ? 'bg-brand text-black shadow-lg shadow-brand/20' : 'text-white/40 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    Categorized
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-black ${activeTab === 'matched' ? 'bg-black/20 text-black' : 'bg-white/5 text-white/40'}`}>
                      {alreadyMatchedTxs.length}
                    </span>
                  </button>
                  <button
                    onClick={() => setActiveTab('excluded')}
                    className={`px-6 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 flex items-center gap-2 ${activeTab === 'excluded' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-white/40 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    Excluded
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-black ${activeTab === 'excluded' ? 'bg-black/20 text-white' : 'bg-white/5 text-white/40'}`}>
                      {excludedTxs.length}
                    </span>
                  </button>
                </div>

                <div className="h-[1px] md:hidden bg-white/5" />
                <div className="hidden md:block h-[1px] flex-1 bg-white/5" />

                <div className="flex gap-2">
                  <button
                    onClick={() => toggleSort('date')}
                    className={`px-4 py-2 rounded-full border text-xs font-bold transition-colors flex items-center gap-2 ${sortConfig.key === 'date'
                      ? 'border-brand/30 bg-brand/10 text-brand'
                      : 'border-white/10 hover:bg-white/5 text-white/60'
                      }`}
                  >
                    By Date
                    {sortConfig.key === 'date' && (
                      sortConfig.direction === 'desc' ? <ArrowDown size={12} /> : <ArrowUp size={12} />
                    )}
                  </button>
                  <button
                    onClick={() => toggleSort('confidence')}
                    className={`px-4 py-2 rounded-full border text-xs font-bold transition-colors flex items-center gap-2 ${sortConfig.key === 'confidence'
                      ? 'border-brand/30 bg-brand/10 text-brand'
                      : 'border-white/10 hover:bg-white/5 text-white/60'
                      }`}
                  >
                    By Confidence
                    {sortConfig.key === 'confidence' && (
                      sortConfig.direction === 'desc' ? <ArrowDown size={12} /> : <ArrowUp size={12} />
                    )}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6">
                <AnimatePresence mode="popLayout">
                  {sortedTransactions.map((tx, index) => (
                    <motion.div
                      key={tx.id}
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8, filter: 'blur(10px)' }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                      <TransactionCard
                        tx={tx}
                        onAccept={handleAccept}
                        onReceiptUpload={handleReceiptUpload}
                        onAnalyze={reAnalyze}
                        onPayeeChange={(txId, payee) => updateTransaction(txId, { payee })}
                        availableTags={tags}
                        availableCategories={categories}
                        availableVendors={vendors}
                        onCategoryChange={(txId, catId, catName) => updateTransaction(txId, { suggested_category_id: catId, suggested_category_name: catName })}
                        onTagAdd={async (txId, tag) => {
                          const currentTags = tx.tags || [];
                          if (!currentTags.includes(tag)) {
                            await updateTransaction(txId, { tags: [...currentTags, tag] });
                            // Create global tag if new
                            if (!tags.find(t => t.name === tag)) {
                              createTag(tag);
                            }
                          }
                        }}
                        onTagRemove={async (txId, tag) => {
                          const currentTags = tx.tags || [];
                          await updateTransaction(txId, { tags: currentTags.filter(t => t !== tag) });
                        }}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>

                {currentTabTransactions.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="col-span-full py-20 flex flex-col items-center justify-center glass-panel"
                  >
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 ${activeTab === 'review' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-brand/10 text-brand'}`}>
                      {activeTab === 'review' ? <ShieldCheck size={40} /> : <Building2 size={40} />}
                    </div>
                    <h3 className="text-2xl font-bold mb-2">
                      {activeTab === 'review' ? 'All Caught Up!' : 'No Matches Found'}
                    </h3>
                    <p className="text-white/40">
                      {activeTab === 'review'
                        ? "You've cleared all pending transactions for today."
                        : "No transactions were automatically matched by QuickBooks."}
                    </p>
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
          <p className="text-white/20 text-xs">AutoMatch Books AI Engine &copy; 2026. Powered by Google Gemini 3 Flash. <span className="ml-2 px-1.5 py-0.5 rounded border border-white/5 bg-white/[0.02] text-[10px] font-bold">v3.26.0</span></p>
        </footer>

      </div>
    </SubscriptionGuard>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black" />}>
      <DashboardContent />
    </Suspense>
  );
}
