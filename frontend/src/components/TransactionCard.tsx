"use client";

import React from 'react';

interface Transaction {
    id: string;
    date: string;
    description: string;
    amount: number;
    currency: string;
    suggested_category_name?: string;
    reasoning?: string;
    confidence?: number;
}

export default function TransactionCard({ tx, onAccept }: { tx: Transaction, onAccept: (id: string) => void }) {
    const confidenceColor = tx.confidence && tx.confidence > 0.8 ? 'text-emerald-400' : 'text-amber-400';

    return (
        <div className="glass-card p-6 flex flex-col gap-4">
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-sm text-white/50">{tx.date}</p>
                    <h3 className="text-xl font-semibold mt-1">{tx.description}</h3>
                </div>
                <div className="text-right">
                    <p className="text-2xl font-bold">{tx.amount.toLocaleString()} {tx.currency}</p>
                </div>
            </div>

            {tx.suggested_category_name && (
                <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-brand">AI Suggestion</span>
                        <span className={`text-xs font-bold ${confidenceColor}`}>
                            {(tx.confidence! * 100).toFixed(0)}% Confidence
                        </span>
                    </div>
                    <p className="text-lg font-medium text-white/90">{tx.suggested_category_name}</p>
                    <p className="text-sm text-white/60 mt-2 italic">"{tx.reasoning}"</p>
                </div>
            )}

            <div className="flex gap-3 pt-2">
                <button
                    onClick={() => onAccept(tx.id)}
                    className="btn-primary flex-1 py-2"
                    aria-label={`Accept matched category ${tx.suggested_category_name} for ${tx.description}`}
                >
                    Accept Match
                </button>
                <button className="btn-glass flex-1 py-2" aria-label={`Edit transaction ${tx.description}`}>
                    Edit
                </button>
            </div>
        </div>
    );
}
