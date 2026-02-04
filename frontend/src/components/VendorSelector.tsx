"use client";

import React, { useState, useMemo, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Plus, Sparkles, Building2, X, Command, Check } from 'lucide-react';

interface Vendor {
    id: string;
    display_name: string;
}

interface VendorSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (vendorName: string) => void;
    availableVendors: Vendor[];
    currentPayee?: string;
    transactionDescription?: string;
}

export default function VendorSelector({
    isOpen,
    onClose,
    onSelect,
    availableVendors,
    currentPayee,
    transactionDescription
}: VendorSelectorProps) {
    const [search, setSearch] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    // Simple weighted search / scoring
    const filteredVendors = useMemo(() => {
        if (!search) return availableVendors.slice(0, 10);

        const searchLower = search.toLowerCase();
        return availableVendors
            .map(v => {
                const name = v.display_name.toLowerCase();
                let score = 0;
                if (name === searchLower) score = 100;
                else if (name.startsWith(searchLower)) score = 80;
                else if (name.includes(searchLower)) score = 40;

                return { ...v, score };
            })
            .filter(v => v.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 8);
    }, [search, availableVendors]);

    const showCreateOption = useMemo(() => {
        if (!search) return false;
        const exists = availableVendors.some(v => v.display_name.toLowerCase() === search.toLowerCase());
        return !exists;
    }, [search, availableVendors]);

    // Handle Keyboard Navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!isOpen) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, filteredVendors.length + (showCreateOption ? 0 : -1)));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(prev => Math.max(prev - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (selectedIndex < filteredVendors.length) {
                    onSelect(filteredVendors[selectedIndex].display_name);
                } else if (showCreateOption) {
                    onSelect(search);
                }
            } else if (e.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, filteredVendors, selectedIndex, showCreateOption, search, onSelect, onClose]);

    // Focus input on open
    useEffect(() => {
        if (isOpen) {
            setSearch("");
            setSelectedIndex(0);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    // Scroll selected into view
    useEffect(() => {
        const selectedEl = listRef.current?.children[selectedIndex] as HTMLElement;
        if (selectedEl) {
            selectedEl.scrollIntoView({ block: 'nearest' });
        }
    }, [selectedIndex]);

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/60 backdrop-blur-md"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-xl bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden glass-panel"
                    >
                        {/* Header / Search Area */}
                        <div className="p-4 border-b border-white/5 relative flex items-center gap-3">
                            <Search className="text-white/20" size={20} />
                            <input
                                ref={inputRef}
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Search or create a vendor..."
                                className="bg-transparent border-none outline-none text-lg text-white placeholder:text-white/20 flex-1"
                            />
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-white/20 px-1.5 py-0.5 border border-white/10 rounded uppercase tracking-widest flex items-center gap-1">
                                    <Command size={10} /> Enter
                                </span>
                                <button onClick={onClose} className="p-1 hover:bg-white/5 rounded-md text-white/20 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>
                        </div>

                        {/* List Area */}
                        <div ref={listRef} className="max-h-[400px] overflow-y-auto p-2 custom-scrollbar">
                            {filteredVendors.length > 0 ? (
                                filteredVendors.map((v, i) => (
                                    <button
                                        key={v.id}
                                        onClick={() => onSelect(v.display_name)}
                                        onMouseEnter={() => setSelectedIndex(i)}
                                        className={`w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200 group ${selectedIndex === i ? 'bg-brand/10 border-brand/20' : 'hover:bg-white/5 border-transparent'
                                            } border`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${selectedIndex === i ? 'bg-brand/20 text-brand' : 'bg-white/5 text-white/40'}`}>
                                                <Building2 size={18} />
                                            </div>
                                            <div className="text-left">
                                                <p className="text-sm font-bold text-white">{v.display_name}</p>
                                                <p className="text-[10px] text-white/40 uppercase tracking-widest">QuickBooks Vendor</p>
                                            </div>
                                        </div>
                                        {currentPayee === v.display_name && (
                                            <Check size={16} className="text-brand" />
                                        )}
                                    </button>
                                ))
                            ) : !showCreateOption && (
                                <div className="py-12 text-center space-y-2">
                                    <Building2 size={32} className="mx-auto text-white/10" />
                                    <p className="text-sm text-white/40 italic">Start typing to see vendors...</p>
                                </div>
                            )}

                            {/* Create Option */}
                            {showCreateOption && (
                                <button
                                    onClick={() => onSelect(search)}
                                    onMouseEnter={() => setSelectedIndex(filteredVendors.length)}
                                    className={`w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200 mt-2 border ${selectedIndex === filteredVendors.length ? 'bg-brand/10 border-brand/20' : 'bg-brand/5 border-brand/20'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-brand/20 text-brand">
                                            <Plus size={18} />
                                        </div>
                                        <div className="text-left">
                                            <p className="text-sm font-bold text-white">Create "{search}"</p>
                                            <div className="flex items-center gap-1.5">
                                                <Sparkles size={10} className="text-brand animate-pulse" />
                                                <p className="text-[10px] text-brand uppercase font-bold tracking-widest">New AI Vendor</p>
                                            </div>
                                        </div>
                                    </div>
                                    <span className="text-[10px] font-black text-brand bg-brand/10 px-2 py-1 rounded border border-brand/20">NEW</span>
                                </button>
                            )}
                        </div>

                        {/* Footer / Context */}
                        <div className="p-4 bg-white/[0.02] border-t border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="text-[10px] text-white/30 truncate max-w-[300px]">
                                    <span className="font-bold uppercase tracking-wider mr-2">Original:</span>
                                    {transactionDescription}
                                </div>
                            </div>
                            <div className="flex items-center gap-3 text-[10px] font-bold text-white/20">
                                <span className="flex items-center gap-1"><Command size={10} /> J/K to Navigate</span>
                                <span className="flex items-center gap-1"><Command size={10} /> Esc to Close</span>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
