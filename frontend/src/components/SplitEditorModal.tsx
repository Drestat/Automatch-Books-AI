"use client";

import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, AlertCircle, Check, DollarSign } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CategorySelector from './CategorySelector';

interface SplitLine {
    id: string;
    category_id: string;
    category_name: string;
    amount: number;
    description: string;
}

interface SplitEditorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (splits: { category_name: string, amount: number, description: string }[]) => Promise<void>;
    totalAmount: number;
    currency: string;
    availableCategories: { id: string, name: string }[];
    initialSplits?: { category_name: string, amount: number, description: string }[];
    transactionDescription?: string;
}

export default function SplitEditorModal({
    isOpen,
    onClose,
    onSave,
    totalAmount,
    currency,
    availableCategories,
    initialSplits = [],
    transactionDescription = ""
}: SplitEditorModalProps) {
    const [lines, setLines] = useState<SplitLine[]>([]);
    const [isEditingCategoryIndex, setIsEditingCategoryIndex] = useState<number | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (isOpen) {
            if (initialSplits.length > 0) {
                setLines(initialSplits.map((s, i) => ({
                    id: Math.random().toString(36).substr(2, 9),
                    category_id: availableCategories.find(c => c.name === s.category_name)?.id || "",
                    category_name: s.category_name,
                    amount: s.amount,
                    description: s.description
                })));
            } else {
                // Default to one line with full amount
                setLines([{
                    id: Math.random().toString(36).substr(2, 9),
                    category_id: "",
                    category_name: "",
                    amount: totalAmount,
                    description: transactionDescription
                }]);
            }
        }
    }, [isOpen, initialSplits, totalAmount, transactionDescription, availableCategories]);

    const currentTotal = lines.reduce((sum, line) => sum + line.amount, 0);
    const remaining = totalAmount - currentTotal;
    const isBalanced = Math.abs(remaining) < 0.01;

    const addLine = () => {
        setLines([...lines, {
            id: Math.random().toString(36).substr(2, 9),
            category_id: "",
            category_name: "",
            amount: remaining > 0 ? remaining : 0,
            description: transactionDescription
        }]);
    };

    const removeLine = (index: number) => {
        if (lines.length > 1) {
            setLines(lines.filter((_, i) => i !== index));
        }
    };

    const updateLine = (index: number, updates: Partial<SplitLine>) => {
        const newLines = [...lines];
        newLines[index] = { ...newLines[index], ...updates };
        setLines(newLines);
    };

    const handleSave = async () => {
        if (!isBalanced) return;
        setIsSaving(true);
        try {
            await onSave(lines.map(l => ({
                category_name: l.category_name,
                amount: l.amount,
                description: l.description
            })));
            onClose();
        } catch (err) {
            console.error("Save split failed", err);
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                />

                <motion.div
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    className="relative w-full max-w-2xl bg-[#020405] border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                        <div>
                            <h2 className="text-xl font-black text-white tracking-tight">Split Transaction</h2>
                            <p className="text-xs text-white/40 mt-1 font-medium">Distribute {Math.abs(totalAmount).toLocaleString('en-US', { style: 'currency', currency })} across multiple categories.</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="w-10 h-10 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 hover:border-white/20 transition-all"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    {/* Balance Bar */}
                    <div className={`px-6 py-4 flex items-center justify-between border-b transition-colors ${isBalanced ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-rose-500/10 border-rose-500/20'}`}>
                        <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isBalanced ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>
                                {isBalanced ? <Check size={16} /> : <AlertCircle size={16} />}
                            </div>
                            <div>
                                <p className={`text-[10px] font-black uppercase tracking-widest ${isBalanced ? 'text-emerald-500' : 'text-rose-500'}`}>
                                    {isBalanced ? 'Balanced' : 'Unbalanced'}
                                </p>
                                <p className="text-lg font-black text-white">
                                    Remaining: {remaining.toLocaleString('en-US', { style: 'currency', currency })}
                                </p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] font-black text-white/30 uppercase tracking-widest">Total</p>
                            <p className="text-lg font-black text-white/60">{Math.abs(totalAmount).toLocaleString('en-US', { style: 'currency', currency })}</p>
                        </div>
                    </div>

                    {/* Lines List */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {lines.map((line, index) => (
                            <motion.div
                                key={line.id}
                                layout
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="glass-card p-4 ring-1 ring-white/5 relative group"
                            >
                                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                                    {/* Category Select */}
                                    <div className="md:col-span-5 space-y-1.5 text-left">
                                        <label className="text-[9px] font-bold text-white/30 uppercase tracking-widest px-1">Category</label>
                                        <div
                                            onClick={() => setIsEditingCategoryIndex(index)}
                                            className="bg-black/40 border border-white/5 rounded-xl p-3 hover:bg-black/60 hover:border-white/10 transition-all cursor-pointer truncate text-sm font-semibold text-white/90"
                                        >
                                            {line.category_name || "Select Category"}
                                        </div>
                                    </div>

                                    {/* Amount Input */}
                                    <div className="md:col-span-3 space-y-1.5 text-left">
                                        <label className="text-[9px] font-bold text-white/30 uppercase tracking-widest px-1">Amount</label>
                                        <div className="relative">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none">
                                                <DollarSign size={14} />
                                            </div>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={line.amount}
                                                onChange={(e) => updateLine(index, { amount: parseFloat(e.target.value) || 0 })}
                                                className="w-full bg-black/40 border border-white/5 rounded-xl pl-8 pr-3 py-3 text-sm font-black text-white focus:outline-none focus:border-brand-accent/50 focus:shadow-[0_0_15px_-5px_rgba(0,223,216,0.2)] transition-all"
                                            />
                                        </div>
                                    </div>

                                    {/* Description */}
                                    <div className="md:col-span-3 space-y-1.5 text-left">
                                        <label className="text-[9px] font-bold text-white/30 uppercase tracking-widest px-1">Memo</label>
                                        <input
                                            type="text"
                                            value={line.description}
                                            onChange={(e) => updateLine(index, { description: e.target.value })}
                                            placeholder="Optional memo..."
                                            className="w-full bg-black/40 border border-white/5 rounded-xl px-3 py-3 text-sm font-semibold text-white focus:outline-none focus:border-white/20 transition-all placeholder:text-white/10"
                                        />
                                    </div>

                                    {/* Delete Button */}
                                    <div className="md:col-span-1 pt-6 flex justify-end">
                                        <button
                                            onClick={() => removeLine(index)}
                                            disabled={lines.length === 1}
                                            className="w-10 h-10 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center text-white/40 hover:text-rose-500 hover:bg-rose-500/10 hover:border-rose-500/20 transition-all disabled:opacity-20 disabled:cursor-not-allowed group/del"
                                        >
                                            <Trash2 size={16} className="group-hover/del:scale-110 transition-transform" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ))}

                        <button
                            onClick={addLine}
                            className="w-full py-4 border-2 border-dashed border-white/5 rounded-2xl flex items-center justify-center gap-2 text-white/30 hover:text-brand-accent hover:border-brand-accent/30 hover:bg-brand-accent/5 transition-all group/add"
                        >
                            <Plus size={18} className="group-hover/add:rotate-90 transition-transform duration-500" />
                            <span className="text-[10px] font-black uppercase tracking-widest">Add Split Line</span>
                        </button>
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-white/5 bg-white/[0.02] flex gap-3">
                        <button
                            onClick={onClose}
                            className="flex-1 px-6 py-4 rounded-xl bg-white/5 border border-white/5 text-white/60 font-black text-[10px] uppercase tracking-widest hover:bg-white/10 hover:text-white transition-all"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={!isBalanced || isSaving}
                            className={`flex-[2] px-6 py-4 rounded-xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 transition-all ${isBalanced && !isSaving
                                    ? 'bg-brand hover:brightness-110 shadow-xl shadow-brand/20 active:scale-95 text-white border border-white/10'
                                    : 'bg-white/5 text-white/20 border border-white/5 cursor-not-allowed'
                                }`}
                        >
                            {isSaving ? (
                                <div className="w-4 h-4 border-2 border-white/40 border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Check size={16} />
                                    Save Splits
                                </>
                            )}
                        </button>
                    </div>

                    {/* Internal Modal for Category Selection */}
                    <CategorySelector
                        isOpen={isEditingCategoryIndex !== null}
                        onClose={() => setIsEditingCategoryIndex(null)}
                        onSelect={(name, id) => {
                            if (isEditingCategoryIndex !== null) {
                                updateLine(isEditingCategoryIndex, { category_name: name, category_id: id });
                            }
                            setIsEditingCategoryIndex(null);
                        }}
                        availableCategories={availableCategories}
                        currentCategory={isEditingCategoryIndex !== null ? lines[isEditingCategoryIndex].category_name : ""}
                    />
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
