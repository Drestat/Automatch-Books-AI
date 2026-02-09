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
  ArrowDown,
  LayoutDashboard,
  PieChart,
  Home,
  Check,
  User
} from 'lucide-react';
import { AccountSelectorModal } from '@/components/AccountSelectorModal';
import { TokenDepletedModal } from '@/components/TokenDepletedModal';
import { motion, AnimatePresence } from 'framer-motion';
import { track } from '@/lib/analytics';
import { useUser } from '@/hooks/useUser';

import { SubscriptionGuard } from '@/components/SubscriptionGuard';
import Skeleton from '@/components/Skeleton';

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
    return !tx.is_excluded && !tx.is_qbo_matched && tx.status !== 'approved';
  });

  const alreadyMatchedTxs = filteredTransactions.filter(tx =>
    !tx.is_excluded &&
    (tx.is_qbo_matched || tx.status === 'approved')
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

  const approvedCount = transactions.filter(tx => tx.status === 'approved').length;

  if (!isConnected && !isDemo) {
    return (
      <SubscriptionGuard status={subscriptionStatus} daysRemaining={daysRemaining}>
        <div className="min-h-screen text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
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
              aria-label="Connect to QuickBooks Online"
              className="w-full btn-primary py-4 text-lg font-bold flex items-center justify-center gap-3 group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              {qboLoading || !isLoaded ? (
                <div role="status" className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Connect Securely
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" aria-hidden="true" />
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
      <div className="min-h-screen text-white selection:bg-brand selection:text-white pb-20">

        {/* Sticky Token HUD */}
        {profile && (
          <div className="fixed top-4 right-6 sm:top-8 sm:right-12 z-[100] pointer-events-none">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="btn-glass px-5 py-3 flex items-center gap-3 border-brand-accent/30 bg-[#020405]/80 backdrop-blur-2xl shadow-2xl pointer-events-auto rounded-2xl"
            >
              <Coins size={18} className="text-brand-accent" />
              <div>
                <p className="text-[9px] uppercase text-brand-accent/60 font-bold tracking-widest mb-0.5">Refill Status</p>
                <p className="font-mono font-bold text-white/90 leading-none text-sm">{profile.token_balance.toLocaleString()} <span className="text-[10px] text-white/30">/ {profile.monthly_token_allowance.toLocaleString()}</span></p>
              </div>
            </motion.div>
          </div>
        )}

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

        <header className="pt-8 sm:pt-14 pb-8 sm:pb-10 px-6 sm:px-12 max-w-[1600px] mx-auto flex flex-col md:flex-row md:items-end justify-between gap-6 sm:gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="flex items-center gap-2.5 mb-2 text-xs sm:text-sm">
              <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${isDemo ? 'bg-brand-accent' : 'bg-brand'} animate-pulse shadow-[0_0_10px_rgba(0,223,216,0.5)]`} />
              <span className={`text-[10px] sm:text-xs font-bold tracking-[0.2em] ${isDemo ? 'text-brand-accent' : 'text-brand'} uppercase opacity-80`}>
                {isDemo ? 'Demo Environment' : 'Live Sync Active'}
              </span>
            </div>
            <h1 className="text-4xl sm:text-6xl font-bold tracking-tighter mb-2 text-white">
              Dashboard
            </h1>
            <p className="text-white/40 text-sm sm:text-base max-w-md font-medium leading-relaxed">
              Welcome back, <strong className="text-white/90">{user?.firstName || 'User'}</strong>.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex md:flex-wrap gap-4 items-center overflow-x-auto pb-4 md:pb-0 scrollbar-hide -mx-4 px-4 md:mx-0 md:px-0"
          >
            {/* Tokens are now handled by a sticky fixed overlay */}

            {/* Manage Accounts Button */}
            {(isConnected || isDemo) && (
              <button
                onClick={() => setShowAccountModal(true)}
                aria-label="Manage Bank Accounts"
                className="btn-glass px-5 py-3.5 flex items-center gap-2.5 border-white/10 hover:bg-white/5 text-sm font-semibold text-white/70 hover:text-white transition-all"
              >
                <Building2 size={18} aria-hidden="true" />
                <span>Accounts</span>
              </button>
            )}


            <button
              onClick={handleBulkApprove}
              disabled={loading || transactions.filter(tx => tx.confidence > 0.9 && tx.status !== 'approved').length === 0}
              aria-label="Batch Approve High Confidence Transactions"
              className="btn-glass px-6 py-3.5 flex items-center gap-3 group border-brand/20 hover:border-brand/40 hover:bg-brand/5 disabled:opacity-50 relative overflow-hidden transition-all"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-brand/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <div className="relative z-10 p-1.5 rounded-lg bg-brand/10 text-brand group-hover:bg-brand group-hover:text-white transition-colors">
                <ShieldCheck size={18} aria-hidden="true" />
              </div>
              <div className="text-left relative z-10">
                <span className="block text-[9px] uppercase tracking-widest font-bold text-brand group-hover:text-white transition-colors">Auto-Pilot</span>
                <span className="text-xs font-bold text-white">Batch Approve</span>
              </div>
            </button>

            {/* Desktop Unified Navigation */}
            <div className="hidden lg:flex items-center gap-8 ml-4 mr-2">
              <Link href="/dashboard" className="flex flex-col items-center gap-1 opacity-100 text-brand group transition-all">
                <Home size={22} className="group-hover:scale-110 transition-transform" />
                <span className="text-[9px] font-bold">Home</span>
              </Link>

              <Link href="/analytics" className="flex flex-col items-center gap-1 opacity-40 text-white hover:opacity-100 group transition-all">
                <PieChart size={22} className="group-hover:scale-110 transition-transform" />
                <span className="text-[9px] font-bold">Insights</span>
              </Link>

              <Link href="/profile" className="flex flex-col items-center gap-1 opacity-40 text-white hover:opacity-100 group transition-all">
                <User size={22} className="group-hover:scale-110 transition-transform" />
                <span className="text-[9px] font-bold">Profile</span>
              </Link>
            </div>
          </motion.div>
        </header>

        <main className="px-4 sm:px-6 md:px-12 pb-24 md:pb-0 max-w-[1600px] mx-auto">
          <BentoGrid>
            {/* Quick Stats & Action Cards */}

            {/* Transactions List */}
            <div className="md:col-span-3 mt-8">
              <div className="flex flex-col md:flex-row md:items-center gap-6 mb-8 -mx-4 px-4 md:mx-0">
                <div className="flex glass-panel p-1.5 rounded-2xl border border-white/5 bg-[#020405]/60 backdrop-blur-xl shadow-2xl w-full md:w-auto overflow-x-auto no-scrollbar relative">
                  {[
                    { id: 'review', label: 'For review', count: toReviewTxs.length, accent: 'brand-accent' },
                    { id: 'matched', label: 'Categorized', count: alreadyMatchedTxs.length, accent: 'brand' },
                    { id: 'excluded', label: 'Excluded', count: excludedTxs.length, accent: 'rose-500' }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`relative flex-1 md:flex-none px-6 py-2.5 rounded-xl text-sm font-bold transition-all duration-500 flex items-center justify-center gap-2.5 group/tab select-none ${activeTab === tab.id ? 'text-white' : 'text-white/40 hover:text-white/80'
                        }`}
                    >
                      {activeTab === tab.id && (
                        <motion.div
                          layoutId="activeTab"
                          className={`absolute inset-0 rounded-xl bg-white/[0.08] border border-white/5 shadow-lg`}
                          transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                        />
                      )}
                      <span className="relative z-10 flex items-center gap-2.5">
                        {tab.label}
                        <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold transition-colors ${activeTab === tab.id ? `bg-${tab.accent}/10 text-${tab.accent}` : 'bg-white/5 text-white/30'
                          }`}>
                          {tab.count}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>

                <div className="flex-1" />

                <div className="flex gap-2.5">
                  <button
                    onClick={() => toggleSort('date')}
                    className={`px-4 py-2.5 rounded-xl border text-xs font-bold transition-colors flex items-center gap-2 ${sortConfig.key === 'date'
                      ? 'border-brand/20 bg-brand/5 text-brand'
                      : 'border-white/5 bg-white/[0.02] hover:bg-white/5 text-white/40 hover:text-white/80'
                      }`}
                  >
                    Date
                    {sortConfig.key === 'date' && (
                      sortConfig.direction === 'desc' ? <ArrowDown size={14} /> : <ArrowUp size={14} />
                    )}
                  </button>
                  <button
                    onClick={() => toggleSort('confidence')}
                    className={`px-4 py-2.5 rounded-xl border text-xs font-bold transition-colors flex items-center gap-2 ${sortConfig.key === 'confidence'
                      ? 'border-brand/20 bg-brand/5 text-brand'
                      : 'border-white/5 bg-white/[0.02] hover:bg-white/5 text-white/40 hover:text-white/80'
                      }`}
                  >
                    Confidence
                    {sortConfig.key === 'confidence' && (
                      sortConfig.direction === 'desc' ? <ArrowDown size={14} /> : <ArrowUp size={14} />
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
                      transition={{ duration: 0.4, delay: index * 0.05 }}
                    >
                      <TransactionCard
                        tx={tx}
                        onAccept={handleAccept}
                        onReceiptUpload={handleReceiptUpload}
                        onAnalyze={reAnalyze}
                        onPayeeChange={(txId, payee) => updateTransaction(txId, { payee })}
                        onNoteChange={(txId, note) => updateTransaction(txId, { note })}
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
                        onUpdate={updateTransaction}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>

                {currentTabTransactions.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="col-span-full py-24 flex flex-col items-center justify-center glass-panel border border-white/5 text-center px-10 relative overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-b from-brand/10 to-transparent opacity-30" />

                    {/* Shimmering background glow */}
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.1, 0.2, 0.1]
                      }}
                      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute w-[500px] h-[500px] bg-brand/20 blur-[100px] rounded-full -z-10"
                    />

                    <motion.div
                      initial={{ y: 0 }}
                      animate={{
                        y: [-10, 10, -10],
                        boxShadow: activeTab === 'review' ? [
                          "0 0 0px 0px rgba(0,223,216,0)",
                          "0 0 50px 10px rgba(0,223,216,0.1)",
                          "0 0 0px 0px rgba(0,223,216,0)"
                        ] : "none"
                      }}
                      transition={{
                        y: { duration: 6, repeat: Infinity, ease: "easeInOut" },
                        boxShadow: { duration: 3, repeat: Infinity, ease: "easeInOut" }
                      }}
                      className={`w-28 h-28 rounded-[2.5rem] flex items-center justify-center mb-8 relative z-10 ${activeTab === 'review' ? 'bg-brand/10 border border-brand/20 text-brand' : 'bg-white/5 border border-white/10 text-white/40'}`}
                    >
                      {activeTab === 'review' ? (
                        <div className="relative">
                          <ShieldCheck size={56} className="drop-shadow-[0_0_12px_rgba(0,223,216,0.5)]" />
                          <motion.div
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.8, type: "spring", stiffness: 200 }}
                            className="absolute -top-1 -right-1 w-8 h-8 bg-brand-accent rounded-full border-4 border-[#020405] flex items-center justify-center shadow-lg"
                          >
                            <Check size={16} className="text-[#020405] stroke-[4]" />
                          </motion.div>
                        </div>
                      ) : <Building2 size={56} />}
                    </motion.div>

                    <h3 className="text-4xl font-black mb-3 relative z-10 tracking-tight">
                      {activeTab === 'review' ? 'Perfectly Sync’d' : 'Nothing To Show'}
                    </h3>
                    <p className="text-white/40 max-w-sm relative z-10 text-lg leading-relaxed font-medium">
                      {activeTab === 'review'
                        ? "You've crushed your bookkeeping goal. Every transaction is accounted for and matched with precision."
                        : "We couldn't find any historical records matching this specific filter."}
                    </p>

                    {activeTab === 'review' && (
                      <motion.div
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 1.2, type: "spring" }}
                        className="mt-12 group"
                      >
                        <div className="relative">
                          <div className="absolute inset-0 bg-brand/40 blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                          <div className="relative px-8 py-3 rounded-2xl bg-brand/5 border border-brand/20 text-brand text-[10px] font-black uppercase tracking-[0.3em] backdrop-blur-md">
                            AI Performance: Peak Efficiency
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </div>
            </div>
          </BentoGrid>
        </main>

        <footer className="mt-24 border-t border-white/5 pt-12 pb-32 md:pb-12 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="text-brand animate-pulse" size={16} />
            <span className="text-xs font-bold uppercase tracking-[0.4em] text-white/20">Next-Gen Accounting</span>
          </div>
          <p className="text-white/20 text-xs text-center">AutoMatch Books AI Engine &copy; 2026. Powered by Google Gemini 3 Flash. <span className="ml-2 px-1.5 py-0.5 rounded border border-white/5 bg-white/[0.02] text-[10px] font-bold">v3.53.1</span></p>
        </footer>

        {/* Mobile/Tablet Bottom Nav */}
        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-50 px-6 pb-6 pt-2 bg-gradient-to-t from-background via-background/95 to-transparent pointer-events-none">
          <div className="glass-panel py-3 px-6 flex items-center justify-around border-white/10 shadow-2xl pointer-events-auto backdrop-blur-xl">
            <Link href="/dashboard" className="flex flex-col items-center gap-1 opacity-100 text-brand">
              <Home size={20} />
              <span className="text-[9px] font-bold">Home</span>
            </Link>

            <Link href="/analytics" className="flex flex-col items-center gap-1 opacity-40 text-white hover:opacity-100 transition-opacity">
              <PieChart size={20} />
              <span className="text-[9px] font-bold">Insights</span>
            </Link>

            <Link href="/profile" className="flex flex-col items-center gap-1 opacity-40 text-white hover:opacity-100 transition-opacity">
              <User size={20} />
              <span className="text-[9px] font-bold">Profile</span>
            </Link>
          </div>
        </div>

      </div>
    </SubscriptionGuard>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={
      <div className="min-h-screen p-12 space-y-8">
        <div className="flex justify-between items-end">
          <div className="space-y-4">
            <Skeleton width="200px" height="20px" />
            <Skeleton width="400px" height="60px" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton height="200px" className="md:col-span-1" />
          <Skeleton height="200px" className="md:col-span-1" />
          <Skeleton height="200px" className="md:col-span-1" />
          <Skeleton height="600px" className="md:col-span-3" />
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
