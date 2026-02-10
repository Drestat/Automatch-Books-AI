"use client";

import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info';

interface ToastAction {
    label: string;
    onClick: () => void;
}

interface Toast {
    id: string;
    message: string;
    type: ToastType;
    action?: ToastAction;
}

interface ToastContextType {
    showToast: (message: string, type?: ToastType, action?: ToastAction) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback((message: string, type: ToastType = 'info', action?: ToastAction) => {
        const id = Math.random().toString(36).substring(2, 9);
        setToasts(prev => [...prev, { id, message, type, action }]);

        // Extended duration for toasts with actions
        const duration = action ? 8000 : 5000;

        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, duration);
    }, []);

    const removeToast = (id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <div className="fixed bottom-8 right-8 z-[100] flex flex-col gap-3 pointer-events-none">
                <AnimatePresence>
                    {toasts.map(toast => (
                        <motion.div
                            key={toast.id}
                            initial={{ opacity: 0, x: 20, scale: 0.9 }}
                            animate={{ opacity: 1, x: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8, x: 20 }}
                            className="pointer-events-auto"
                        >
                            <div className={`glass-panel px-6 py-4 flex items-center gap-4 min-w-[320px] shadow-2xl border-white/10 ${toast.type === 'success' ? 'bg-emerald-500/10' :
                                toast.type === 'error' ? 'bg-rose-500/10' : 'bg-white/5'
                                }`}>
                                <div className={
                                    toast.type === 'success' ? 'text-emerald-400' :
                                        toast.type === 'error' ? 'text-rose-400' : 'text-brand'
                                }>
                                    {toast.type === 'success' && <CheckCircle size={20} />}
                                    {toast.type === 'error' && <AlertCircle size={20} />}
                                    {toast.type === 'info' && <Info size={20} />}
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm font-bold text-white/90">{toast.message}</p>
                                    {toast.action && (
                                        <button
                                            onClick={() => {
                                                toast.action?.onClick();
                                                removeToast(toast.id);
                                            }}
                                            className="mt-2 text-[10px] uppercase tracking-widest font-black text-brand-accent hover:brightness-110 transition-all border border-brand-accent/30 px-3 py-1 rounded-lg bg-brand-accent/10"
                                        >
                                            {toast.action.label}
                                        </button>
                                    )}
                                </div>
                                <button
                                    onClick={() => removeToast(toast.id)}
                                    className="text-white/20 hover:text-white/40 transition-colors"
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
};

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) throw new Error('useToast must be used within ToastProvider');
    return context;
};
