"use client";

import React from 'react';
import { Check, Edit2, Info, ArrowUpRight, FilePlus, FileCheck, Tags, Split as SplitIcon, ExternalLink, CheckCircle2, Sparkles, Building2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import VendorSelector from './VendorSelector';
import CategorySelector from './CategorySelector';
import StreamingText from './StreamingText';

interface Split {
    category_name: string;
    amount: number;
    description: string;
}

interface Category {
    id: string;
    name: string;
}

interface Vendor {
    id: string;
    display_name: string;
}

interface Tag {
    id: string;
    name: string;
}

interface Transaction {
    id: string;
    date: string;
    description: string | null;
    amount: number;
    currency: string;
    transaction_type?: string;
    note?: string;
    tags?: string[];
    suggested_tags?: string[];
    status: string;
    reasoning: string;
    confidence: number;
    is_split?: boolean;
    splits?: Split[];
    receipt_url?: string;
    vendor_reasoning?: string;
    category_reasoning?: string;
    note_reasoning?: string;
    tax_deduction_note?: string;
    is_exported?: boolean;
    is_qbo_matched?: boolean;
    is_excluded?: boolean;
    forced_review?: boolean;
    suggested_category_name: string;
    suggested_category_id?: string;
    suggested_payee?: string;
    category_id?: string;
    category_name?: string;
    payee?: string;
}

interface TransactionCardProps {
    tx: Transaction;
    onAccept: (id: string) => Promise<void> | void;
    onReceiptUpload?: (id: string, file: File) => void;
    availableCategories?: Category[];
    availableTags?: Tag[];
    availableVendors?: Vendor[];
    onCategoryChange?: (txId: string, categoryId: string, categoryName: string) => void;
    onTagAdd?: (txId: string, tagName: string) => void;
    onTagRemove?: (txId: string, tagName: string) => void;
    onAnalyze?: (id: string) => void;
    onExclude?: (id: string) => void;
    onInclude?: (id: string) => void;
    onPayeeChange?: (txId: string, payee: string) => void;
    onNoteChange?: (txId: string, note: string) => void;
    onUpdate?: (txId: string, updates: Partial<Transaction>) => void;
}

export default function TransactionCard({
    tx,
    onAccept,
    onReceiptUpload,
    availableCategories = [],
    availableTags = [],
    availableVendors = [],
    onCategoryChange,
    onTagAdd,
    onTagRemove,
    onAnalyze,
    onExclude,
    onInclude,
    onPayeeChange,
    onNoteChange,
    onUpdate
}: TransactionCardProps) {
    const expenseTypes = ['Purchase', 'Expense', 'Check', 'CreditCard', 'BillPayment', 'Cash', 'CreditCardCharge'];
    // QBO sends positive TotalAmt for expenses. Identify by type OR if manually negative.
    const isExpenseType = expenseTypes.includes(tx.transaction_type || '') || (tx.transaction_type === 'JournalEntry' && tx.amount < 0);
    const isExpense = tx.amount < 0 || isExpenseType;

    const [showReasoning, setShowReasoning] = React.useState(false);
    const [isUploading, setIsUploading] = React.useState(false);
    const [isEditingCategory, setIsEditingCategory] = React.useState(false);
    const [isEditingPayee, setIsEditingPayee] = React.useState(false);
    const [isAddingTag, setIsAddingTag] = React.useState(false);
    const [isSyncing, setIsSyncing] = React.useState(false);
    const [newTag, setNewTag] = React.useState("");
    const [payeeInput, setPayeeInput] = React.useState(tx.payee || "");
    const [isAnalyzing, setIsAnalyzing] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleAccept = async () => {
        const { triggerHapticFeedback } = await import('@/lib/haptics');
        triggerHapticFeedback();
        await onAccept(tx.id);
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && onReceiptUpload) {
            setIsUploading(true);
            await onReceiptUpload(tx.id, file);
            setIsUploading(false);
        }
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.005, y: -2 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="glass-card overflow-hidden group w-full mb-6 ring-1 ring-white/10 hover:ring-brand-accent/40 transition-all duration-500"
        >
            <div className="p-5 md:p-8 relative z-10">
                {/* 1. High-Fidelity Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-8">
                    <div className="flex gap-4 sm:gap-6 items-start">
                        {/* Date & Time */}
                        <div className="text-white shrink-0 min-w-[3.5rem]">
                            <h4 className="text-base sm:text-lg font-black tracking-tight leading-none uppercase">
                                {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(tx.date))}
                            </h4>
                            <p className="text-[10px] sm:text-sm font-black text-white/40 uppercase mt-1 leading-none">
                                {new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).format(new Date(tx.date))}
                            </p>
                        </div>

                        {/* Payee Identity */}
                        <div className="min-w-0">
                            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight leading-tight sm:leading-none break-words">
                                {tx.payee || tx.suggested_payee || "Unassigned"}
                            </h2>
                            <p className="text-[10px] sm:text-xs font-medium text-white/30 mt-2 line-clamp-2 sm:line-clamp-none">
                                {(!tx.description || tx.description.trim() === '') ? "No bank description at the moment" : tx.description}
                            </p>
                        </div>
                    </div>

                    {/* Right Side: Confidence & Amount */}
                    <div className="flex items-center justify-between w-full sm:w-auto gap-4 sm:gap-4 mt-2 sm:mt-0 pt-4 sm:pt-0 border-t border-white/5 sm:border-0">
                        {/* Confidence Circle (esk) */}
                        <motion.div
                            className="relative w-12 h-12 flex items-center justify-center"
                            animate={tx.confidence > 0.9 ? {
                                filter: ["drop-shadow(0 0 2px var(--color-brand-accent))", "drop-shadow(0 0 8px var(--color-brand-accent))", "drop-shadow(0 0 2px var(--color-brand-accent))"],
                            } : {}}
                            transition={{ duration: 2, repeat: Infinity }}
                        >
                            <svg className="absolute inset-0 w-full h-full -rotate-90">
                                <circle
                                    cx="24"
                                    cy="24"
                                    r="20"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2.5"
                                    className="text-white/5"
                                />
                                <motion.circle
                                    cx="24"
                                    cy="24"
                                    r="20"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2.5"
                                    strokeDasharray="125.66"
                                    initial={{ strokeDashoffset: 125.66 }}
                                    animate={{ strokeDashoffset: 125.66 * (1 - tx.confidence) }}
                                    transition={{ duration: 1.5, ease: "circOut" }}
                                    className="text-brand-accent"
                                />
                            </svg>
                            <span className="text-[12px] font-black text-brand-accent relative z-10">{Math.round(tx.confidence * 100)}%</span>
                        </motion.div>

                        <span className="text-2xl font-black text-white/90 ml-2">
                            {tx.amount === 0 ? '' : (isExpense ? '-' : '+')} {Math.abs(tx.amount).toLocaleString('en-US', { style: 'currency', currency: tx.currency })}
                        </span>
                    </div>
                </div>

                {/* 2. Bento Grid Selectors */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    {/* Payee Hub */}
                    <div className="flex flex-col gap-2">
                        <div className="flex items-center justify-between px-1">
                            <span className="text-[10px] uppercase tracking-widest font-black text-white/30">Payee</span>
                            {tx.suggested_payee && (
                                <button
                                    onClick={() => onPayeeChange && onPayeeChange(tx.id, tx.suggested_payee!)}
                                    className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-brand-accent/5 border border-brand-accent/20 text-brand-accent text-[8px] font-black uppercase hover:bg-brand-accent/10 transition-all"
                                >
                                    <Sparkles size={8} /> Suggested: {tx.suggested_payee}
                                </button>
                            )}
                        </div>
                        <div
                            onClick={() => setIsEditingPayee(true)}
                            className="bg-white/5 border border-white/5 rounded-2xl p-4 hover:bg-white/10 hover:border-white/10 transition-all cursor-pointer group/selector"
                        >
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-bold text-white/90">
                                    {tx.payee || tx.suggested_payee || "Select Payee"}
                                </p>
                                <Edit2 size={12} className="opacity-20 group-hover/selector:opacity-100 transition-opacity" />
                            </div>
                        </div>
                    </div>

                    {/* Category Hub */}
                    <div className="flex flex-col gap-2">
                        <div className="flex items-center justify-between px-1">
                            <span className="text-[10px] uppercase tracking-widest font-black text-white/30">Category</span>
                            {!tx.category_name && tx.suggested_category_name && (
                                <button
                                    onClick={() => onCategoryChange && onCategoryChange(tx.id, tx.suggested_category_id || '', tx.suggested_category_name)}
                                    className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-brand-accent/5 border border-brand-accent/20 text-brand-accent text-[8px] font-black uppercase hover:bg-brand-accent/10 transition-all"
                                >
                                    <Sparkles size={8} /> Suggested: {tx.suggested_category_name}
                                </button>
                            )}
                        </div>
                        <div
                            onClick={() => setIsEditingCategory(true)}
                            className="bg-white/5 border border-white/5 rounded-2xl p-4 hover:bg-white/10 hover:border-white/10 transition-all cursor-pointer group/selector"
                        >
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-bold text-white/90">
                                    {tx.category_name || tx.suggested_category_name || "Select Category"}
                                </p>
                                <Edit2 size={12} className="opacity-20 group-hover/selector:opacity-100 transition-opacity" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* 3. AI Intelligence Module */}
                <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{
                        opacity: 1,
                        x: 0,
                        backgroundColor: isAnalyzing ? ["rgba(0, 223, 216, 0.02)", "rgba(0, 223, 216, 0.08)", "rgba(0, 223, 216, 0.02)"] : "rgba(255, 255, 255, 0.02)"
                    }}
                    transition={{
                        opacity: { delay: 0.2 },
                        backgroundColor: { duration: 2, repeat: Infinity, ease: "linear" }
                    }}
                    className={`border border-white/5 rounded-3xl p-5 mb-4 relative overflow-hidden group/ai-module ${isAnalyzing ? 'ring-1 ring-brand-accent/20' : ''}`}
                >
                    {isAnalyzing && (
                        <motion.div
                            initial={{ x: "-100%" }}
                            animate={{ x: "200%" }}
                            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-0 bg-gradient-to-r from-transparent via-brand-accent/10 to-transparent skew-x-12"
                        />
                    )}
                    <div className="flex items-center gap-2 mb-4">
                        <span className="text-[10px] font-black text-brand-accent uppercase tracking-widest opacity-70 group-hover/ai-module:opacity-100 transition-opacity">AI Intelligence</span>
                        <div className="h-[1px] flex-1 bg-white/5 group-hover/ai-module:bg-brand-accent/10 transition-colors" />
                    </div>

                    <div className="space-y-5">
                        <div className="flex gap-4">
                            <div className="w-10 h-10 rounded-xl bg-brand-accent/10 flex items-center justify-center shrink-0 border border-brand-accent/20 group-hover/ai-module:shadow-[0_0_15px_-3px_rgba(0,223,216,0.3)] transition-all">
                                <Sparkles size={18} className="text-brand-accent" />
                            </div>
                            <div className="space-y-2">
                                {tx.vendor_reasoning && (
                                    <p className="text-[13px] text-white/70 leading-relaxed font-medium">
                                        <span className="text-brand-accent/80 font-black mr-2 text-[10px] uppercase tracking-tighter">Vendor:</span>
                                        {tx.vendor_reasoning}
                                    </p>
                                )}
                                {tx.category_reasoning && (
                                    <p className="text-[13px] text-white/70 leading-relaxed font-medium">
                                        <span className="text-brand-accent/80 font-black mr-2 text-[10px] uppercase tracking-tighter">Match:</span>
                                        {tx.category_reasoning}
                                    </p>
                                )}
                            </div>
                        </div>

                        {tx.tax_deduction_note && (
                            <div className="p-4 rounded-2xl bg-white/[0.01] border border-white/5 flex gap-4 hover:bg-white/[0.03] transition-colors">
                                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center shrink-0">
                                    <Info size={14} className="text-white/40" />
                                </div>
                                <div className="flex flex-col gap-0.5">
                                    <span className="text-[9px] font-black text-brand-accent/60 uppercase tracking-widest">Tax Strategy</span>
                                    <p className="text-[11px] text-white/60 leading-relaxed font-medium">
                                        {tx.tax_deduction_note}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* 4. Collaboration Drawer */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white/[0.04] border border-white/5 rounded-3xl p-5 mb-8 group/collab"
                >
                    <div className="flex items-center gap-2 mb-4">
                        <span className="text-[10px] font-black text-white/30 uppercase tracking-widest group-hover/collab:text-white/50 transition-colors">Collaboration</span>
                        <div className="h-[1px] flex-1 bg-white/5 group-hover/collab:bg-white/10 transition-colors" />
                    </div>

                    <div className="space-y-4">
                        <div className="relative">
                            <input
                                type="text"
                                defaultValue={tx.note || ''}
                                placeholder="Add a collaborative note..."
                                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-4 text-sm text-white placeholder:text-white/10 focus:outline-none focus:border-brand-accent/20 transition-all font-bold focus:bg-black/60"
                                onBlur={(e) => {
                                    if (e.target.value !== (tx.note || '') && onNoteChange) {
                                        onNoteChange(tx.id, e.target.value);
                                    }
                                }}
                            />
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-20">
                                <Edit2 size={14} className="text-white" />
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-2 items-center">
                            {tx.tags && tx.tags.map((tag, i) => (
                                <span key={i} className="px-3 py-1.5 rounded-xl bg-brand-accent/10 border border-brand-accent/20 text-[10px] text-brand-accent font-black uppercase flex items-center gap-2 group/tag hover:bg-brand-accent/20 transition-all">
                                    <Tags size={10} /> {tag}
                                    <button onClick={() => onTagRemove && onTagRemove(tx.id, tag)} className="hover:text-rose-400 opacity-50 hover:opacity-100 transition-opacity">×</button>
                                </span>
                            ))}
                            {tx.suggested_tags && tx.suggested_tags.filter(t => !tx.tags?.includes(t)).map((tag, i) => (
                                <button
                                    key={`suggested-${i}`}
                                    onClick={() => onTagAdd && onTagAdd(tx.id, tag)}
                                    className="px-3 py-1.5 rounded-xl bg-white/5 border border-dashed border-white/10 text-[10px] text-white/30 font-black uppercase flex items-center gap-2 hover:border-brand-accent/40 hover:text-brand-accent transition-all hover:bg-brand-accent/5 backdrop-blur-sm"
                                >
                                    <Sparkles size={10} /> {tag}
                                </button>
                            ))}
                            <button
                                onClick={() => setIsAddingTag(true)}
                                className="px-3 py-1.5 rounded-xl border border-dashed border-white/10 text-[10px] text-white/20 font-black uppercase hover:bg-white/5 transition-all flex items-center gap-1.5"
                            >
                                <span className="text-base leading-none">+</span> Tag
                            </button>
                        </div>
                    </div>
                </motion.div>

                {/* 5. Master Actions */}
                <div className="space-y-4">
                    {/* Row 1: Actions & Icons */}
                    <div className="flex gap-3 h-14">
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isUploading}
                            className={`flex-[3] sm:flex-[2] px-4 bg-[#061a18] border border-brand-accent/20 rounded-2xl flex items-center justify-center font-bold gap-2 sm:gap-3 text-brand-trend transition-all active:scale-95 hover:bg-[#0a2825] hover:border-brand-accent/40 hover:shadow-[0_0_20px_-5px_var(--glow-brand)]`}
                        >
                            {isUploading ? (
                                <div className="w-4 h-4 border-2 border-brand-accent border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    <FilePlus size={18} />
                                    <span className="text-[10px] sm:text-xs uppercase tracking-[0.15em] font-black">Upload Receipt</span>
                                </>
                            )}
                        </button>

                        <IconButton
                            icon={<SplitIcon size={18} />}
                            title="Split"
                        />

                        <IconButton
                            icon={<Edit2 size={18} />}
                            title="Edit"
                            onClick={() => setIsEditingPayee(true)}
                        />

                        {tx.is_excluded ? (
                            <IconButton
                                icon={<CheckCircle2 size={18} />}
                                title="Include"
                                onClick={() => onInclude && onInclude(tx.id)}
                                active={true}
                            />
                        ) : (
                            <IconButton
                                icon={<SplitIcon size={18} className="rotate-45" />}
                                title="Exclude"
                                onClick={() => onExclude && onExclude(tx.id)}
                            />
                        )}
                    </div>

                    {/* Row 2: AI & Confirm */}
                    <div className="flex gap-3 h-16">
                        <button
                            onClick={async () => {
                                if (onAnalyze) {
                                    setIsAnalyzing(true);
                                    await onAnalyze(tx.id);
                                    setIsAnalyzing(false);
                                }
                            }}
                            className="flex-1 bg-[#061a18] border border-brand-accent/10 hover:border-brand-accent/40 rounded-2xl flex items-center justify-center text-brand-trend font-black text-xs uppercase tracking-[0.2em] transition-all active:scale-95 group/ai hover:bg-[#0a2825] hover:shadow-[0_0_25px_-10px_var(--glow-brand)]"
                        >
                            <Sparkles size={16} className="mr-3 text-brand-accent group-hover/ai:rotate-12 group-hover/ai:scale-110 transition-transform" />
                            {isAnalyzing ? "Analyzing..." : "Analyze with AI"}
                        </button>

                        <button
                            onClick={handleAccept}
                            disabled={isSyncing}
                            className="flex-1 bg-brand hover:brightness-110 rounded-2xl flex items-center justify-center text-white font-black text-xs uppercase tracking-[0.2em] transition-all active:scale-95 shadow-xl shadow-brand/20 border border-white/10 group/confirm"
                        >
                            {isSyncing ? (
                                <div className="w-4 h-4 border-2 border-white/80 border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Check size={18} className="mr-3 group-hover/confirm:scale-110 transition-transform" />
                                    Confirm Match
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Selectors */}
                <VendorSelector
                    isOpen={isEditingPayee}
                    onClose={() => setIsEditingPayee(false)}
                    onSelect={(vendorName) => {
                        if (onPayeeChange) onPayeeChange(tx.id, vendorName);
                        setIsEditingPayee(false);
                    }}
                    availableVendors={availableVendors}
                    currentPayee={tx.payee}
                    transactionDescription={tx.description}
                />
                <CategorySelector
                    isOpen={isEditingCategory}
                    onClose={() => setIsEditingCategory(false)}
                    onSelect={(categoryName, categoryId) => {
                        if (onCategoryChange) {
                            onCategoryChange(tx.id, categoryId, categoryName);
                            setIsEditingCategory(false);
                        }
                    }}
                    availableCategories={availableCategories}
                    currentCategory={tx.category_name || tx.suggested_category_name}
                />
                <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept="image/*" />
            </div>
        </motion.div >
    );

}

function IconButton({
    icon,
    onClick,
    title,
    active = false,
    loading = false
}: {
    icon: React.ReactNode,
    onClick?: () => void,
    title: string,
    active?: boolean,
    loading?: boolean
}) {
    return (
        <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClick}
            disabled={loading}
            className={`w-14 h-14 rounded-2xl flex items-center justify-center border transition-all ${active
                ? 'bg-brand/20 text-brand border-brand/30'
                : 'bg-white/5 text-white/60 hover:text-white hover:bg-white/10 border-white/10'
                }`}
            title={title}
        >
            {loading ? (
                <div className="w-4 h-4 border-2 border-brand border-t-transparent rounded-full animate-spin" />
            ) : icon}
        </motion.button>
    );
}
