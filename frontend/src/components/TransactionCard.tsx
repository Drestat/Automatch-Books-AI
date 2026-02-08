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
        <motion.div layout className="glass-card overflow-hidden group w-full mb-4 ring-1 ring-white/5 hover:ring-brand-accent/30 transition-all duration-500">
            <div className="p-4 md:p-6 relative z-10">
                {/* Main Columnar Row */}
                <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-6 mb-4 md:mb-6">
                    {/* Column 1: Date & Type */}
                    <div className="flex items-center gap-4 min-w-[140px]">
                        <div>
                            <p className="text-[13px] text-white/90 font-black uppercase tracking-wider mb-0.5">
                                {new Intl.DateTimeFormat('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric',
                                    timeZone: 'UTC'
                                }).format(new Date(tx.date))}
                            </p>
                            <span className="text-[10px] font-bold text-brand-accent/80 uppercase tracking-tighter border border-brand-accent/20 px-1.5 py-0.5 rounded leading-tight block w-fit mt-1">
                                {tx.transaction_type || 'TX'}
                            </span>
                        </div>
                    </div>

                    {/* Column 2: Identity (Payee & Bank Description) */}
                    <div className="flex-[2] min-w-[250px]">
                        <span className="text-[9px] uppercase tracking-widest font-black text-white/20 mb-1 block">Payee / Description</span>

                        <div className="relative">
                            <h3 className={`text-sm font-bold tracking-tight line-clamp-1 ${(tx.payee || tx.suggested_payee) ? 'text-white' : 'text-rose-400 italic'}`}>
                                {tx.payee || tx.suggested_payee || "Unassigned"}
                            </h3>
                            <p className="text-[10px] text-white/40 line-clamp-1 mt-0.5 italic">
                                {(!tx.description || tx.description.trim() === '') ? "No Bank Description" : tx.description}
                            </p>
                        </div>

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
                    </div>

                    {/* Column 3: Category Selector */}
                    <div className="flex-1 min-w-[180px]">
                        <span className="text-[9px] uppercase tracking-widest font-black text-white/20 mb-1 block">Category</span>
                        {!tx.category_name && tx.suggested_category_name && (
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => onCategoryChange && onCategoryChange(tx.id, tx.suggested_category_id || '', tx.suggested_category_name)}
                                className="flex items-center gap-1.5 px-2 py-1 rounded bg-brand/10 border border-brand-accent/40 text-brand-accent text-[10px] font-bold mb-1 hover:bg-brand-accent/10 transition-all"
                            >
                                <Sparkles size={8} className="text-brand-accent" />
                                Suggested: {tx.suggested_category_name}
                            </motion.button>
                        )}
                        <div className="flex items-center gap-2 group/edit cursor-pointer" onClick={() => setIsEditingCategory(true)}>
                            <p className={`text-sm font-medium ${tx.category_name ? 'text-white/90' : 'text-white/40'} group-hover:text-brand transition-colors`}>
                                {tx.category_name || tx.suggested_category_name || "Select Category"}
                            </p>
                            <Edit2 size={12} className="text-white/20 opacity-0 group-hover/edit:opacity-100 transition-all" />
                        </div>
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
                    </div>

                    {/* Column 5: Amount & Confidence */}
                    <div className="flex flex-col items-end min-w-[120px]">
                        <p className={`text-lg font-black ${isExpense ? 'text-white/90' : 'text-emerald-400'} tracking-tight`}>
                            {tx.amount === 0 ? '' : (isExpense ? '-' : '+')}{Math.abs(tx.amount).toLocaleString('en-US', { style: 'currency', currency: tx.currency })}
                        </p>
                        <div className={`flex items-center gap-1.5 mt-1 px-2 py-0.5 rounded-full border ${tx.confidence > 0.9 ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                            tx.confidence > 0.7 ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                                'bg-rose-500/10 border-rose-500/20 text-rose-400'
                            }`}>
                            {isExpense ? <ArrowUpRight className="rotate-180" size={12} /> : <ArrowUpRight size={12} />}
                            <span className="text-[9px] font-black uppercase">{Math.round(tx.confidence * 100)}%</span>
                        </div>
                    </div>
                </div>

                {/* AI Basement Section */}
                <div className="bg-gradient-to-br from-brand-trend/[0.05] to-brand/[0.05] border border-brand-trend/10 rounded-2xl p-4 mb-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-brand-trend/5 blur-3xl rounded-full -translate-y-1/2 translate-x-1/2" />
                    <div className="flex flex-col md:flex-row gap-6">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-[10px] font-bold text-brand-accent uppercase tracking-[0.2em]">AI Intelligence</span>
                                <div className="h-[1px] flex-1 bg-white/5" />
                            </div>

                            <div className="space-y-3">
                                {(tx.vendor_reasoning || tx.category_reasoning || tx.reasoning) && (
                                    <div className="flex gap-3">
                                        <div className="p-1.5 rounded-lg bg-brand/10 text-brand shrink-0 h-fit">
                                            <Sparkles size={14} />
                                        </div>
                                        <div className="space-y-2">
                                            {tx.vendor_reasoning && (
                                                <p className="text-[11px] text-white/70 leading-relaxed">
                                                    <span className="text-brand-accent/60 font-bold mr-1">VENDOR:</span> <StreamingText text={tx.vendor_reasoning} speed={15} />
                                                </p>
                                            )}
                                            {tx.category_reasoning && (
                                                <p className="text-[11px] text-white/70 leading-relaxed">
                                                    <span className="text-brand-accent/60 font-bold mr-1">MATCH:</span> <StreamingText text={tx.category_reasoning} speed={15} />
                                                </p>
                                            )}
                                            {!tx.vendor_reasoning && !tx.category_reasoning && tx.reasoning && (
                                                <p className="text-[11px] text-white/50 leading-relaxed italic">
                                                    <StreamingText text={tx.reasoning} speed={10} />
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {tx.tax_deduction_note && (
                                    <div className="p-3 rounded-xl bg-brand/5 border border-brand/20 relative overflow-hidden group/tip">
                                        <div className="absolute inset-0 bg-gradient-to-r from-brand/10 to-transparent opacity-0 group-hover/tip:opacity-100 transition-opacity" />
                                        <div className="flex items-center gap-2 relative z-10">
                                            <div className="p-1 rounded-md bg-brand/20 text-brand">
                                                <Info size={12} />
                                            </div>
                                            <span className="text-[10px] font-black text-brand uppercase tracking-[0.2em]">Tax Strategy</span>
                                            <p className="text-[11px] text-white/80 leading-relaxed font-medium">
                                                <StreamingText text={tx.tax_deduction_note} speed={20} />
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex-1 md:border-l md:border-white/5 md:pl-6">
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Collaboration</span>
                                <div className="h-[1px] flex-1 bg-white/5" />
                            </div>

                            <div className="space-y-4">
                                <input
                                    type="text"
                                    defaultValue={tx.note || ''}
                                    placeholder="Add team note..."
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-brand/40 transition-all font-medium"
                                    onBlur={(e) => {
                                        if (e.target.value !== (tx.note || '') && onNoteChange) {
                                            onNoteChange(tx.id, e.target.value);
                                        }
                                    }}
                                />

                                <div className="flex flex-wrap gap-2 items-center">
                                    {tx.tags && tx.tags.map((tag, i) => (
                                        <span key={i} className="px-2 py-1 rounded-md bg-brand/20 border border-brand/30 text-[10px] text-brand flex items-center gap-1.5 group/tag">
                                            <Tags size={10} /> {tag}
                                            {onTagRemove && (
                                                <button onClick={() => onTagRemove(tx.id, tag)} className="hover:text-rose-400 opacity-0 group-hover/tag:opacity-100 transition-opacity">×</button>
                                            )}
                                        </span>
                                    ))}
                                    {tx.suggested_tags && tx.suggested_tags.filter(t => !tx.tags?.includes(t)).map((tag, i) => (
                                        <motion.button
                                            key={`suggested-${i}`}
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                            onClick={() => onTagAdd && onTagAdd(tx.id, tag)}
                                            className="px-2 py-1 rounded-md bg-white/5 border border-dashed border-white/20 text-[10px] text-white/40 flex items-center gap-1.5 hover:border-brand/40 hover:text-brand/60 transition-colors"
                                        >
                                            <Sparkles size={10} /> {tag} +
                                        </motion.button>
                                    ))}
                                    {isAddingTag ? (
                                        <div className="flex items-center gap-2">
                                            <input
                                                autoFocus
                                                type="text"
                                                value={newTag}
                                                onChange={(e) => setNewTag(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter' && newTag.trim()) {
                                                        onTagAdd && onTagAdd(tx.id, newTag.trim());
                                                        setNewTag("");
                                                        setIsAddingTag(false);
                                                    } else if (e.key === 'Escape') {
                                                        setIsAddingTag(false);
                                                    }
                                                }}
                                                onBlur={() => {
                                                    if (!newTag.trim()) setIsAddingTag(false);
                                                }}
                                                placeholder="New tag..."
                                                className="bg-black/40 border border-brand/30 rounded px-2 py-1 text-[10px] text-white focus:outline-none focus:border-brand w-24"
                                            />
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => setIsAddingTag(true)}
                                            className="px-2 py-1 rounded-md border border-dashed border-brand/30 text-[10px] text-brand hover:bg-brand/10 transition-colors"
                                        >
                                            + Tag
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Actions Section */}
                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex gap-2">
                        <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept="image/*" />
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isUploading}
                            className={`h-12 px-6 ${isUploading
                                ? 'bg-brand/20 border-brand/30'
                                : tx.receipt_url
                                    ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400'
                                    : 'bg-brand/10 hover:bg-brand/20 border-brand/20 text-brand'
                                } border rounded-xl flex items-center justify-center font-bold gap-2 transition-all shadow-sm`}
                            title={tx.receipt_url ? "Replace Receipt" : "Upload Receipt"}
                        >
                            {isUploading ? (
                                <div className="w-4 h-4 border-2 border-brand border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    {tx.receipt_url ? <FileCheck size={18} /> : <FilePlus size={18} />}
                                    <span>{tx.receipt_url ? 'Receipt Added' : 'Upload Receipt'}</span>
                                </>
                            )}
                        </motion.button>

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

                    <div className="flex items-center gap-3 ml-auto">
                        <motion.button
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={async () => {
                                if (onAnalyze) {
                                    setIsAnalyzing(true);
                                    await onAnalyze(tx.id);
                                    setIsAnalyzing(false);
                                }
                            }}
                            disabled={isAnalyzing}
                            className={`h-12 px-6 ${isAnalyzing ? 'bg-brand/20 border-brand/30' : 'bg-brand/10 hover:bg-brand-accent/10 border-brand-accent/30'} border rounded-xl flex items-center justify-center text-brand-accent font-bold gap-2 transition-all relative overflow-hidden group/sparkle`}
                        >
                            {isAnalyzing ? (
                                <div className="w-4 h-4 border-2 border-brand-accent border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Sparkles size={18} className="group-hover/sparkle:rotate-12 transition-transform text-brand-accent" />
                                    <span>Analyze with AI</span>
                                </>
                            )}
                        </motion.button>

                        <motion.button
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleAccept}
                            disabled={isSyncing}
                            className={`min-w-[180px] h-12 ${isSyncing ? 'bg-brand/50 cursor-wait' : 'bg-brand hover:bg-brand/90'} text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-brand/20 hover:shadow-brand-accent/20 transition-all border border-white/10 ring-1 ring-transparent hover:ring-brand-accent/50`}
                        >
                            {isSyncing ? (
                                <div className="w-4 h-4 border-2 border-white/80 border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Check size={18} />
                                    Confirm Match
                                </>
                            )}
                        </motion.button>
                    </div>
                </div>

                {(tx.is_exported || tx.receipt_url) && (
                    <div className="mt-4 pt-4 border-t border-white/5 flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            {tx.is_exported && (
                                <div className="flex items-center gap-2 text-emerald-400">
                                    <CheckCircle2 size={14} />
                                    <span className="text-[10px] font-bold uppercase tracking-wider">Exported to QBO</span>
                                </div>
                            )}
                            {tx.receipt_url && (
                                <div className="flex items-center gap-2 text-brand">
                                    <FilePlus size={14} />
                                    <span className="text-[10px] font-bold uppercase tracking-wider">Receipt Attached</span>
                                </div>
                            )}
                        </div>
                        {tx.is_exported && <ExternalLink size={12} className="text-white/20" />}
                    </div>
                )}
            </div>
            <div className="h-1 w-full bg-gradient-to-r from-transparent via-brand-trend/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-0 left-0" />
        </motion.div>
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
            className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-all ${active
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
