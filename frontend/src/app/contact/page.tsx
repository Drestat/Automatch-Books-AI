"use client";

import React from 'react';
import Footer from '@/components/Footer';
import { motion } from 'framer-motion';
import { Mail, MessageSquare, Send } from 'lucide-react';
import { useToast } from "@/context/ToastContext";

export default function ContactPage() {
    const { showToast } = useToast();
    return (
        <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white">
            <main className="py-24 px-6 max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-16 text-center"
                >
                    <div className="w-12 h-12 rounded-2xl bg-brand/10 text-brand flex items-center justify-center mb-6 mx-auto">
                        <MessageSquare size={24} />
                    </div>
                    <h1 className="text-5xl font-black tracking-tight mb-4">Get in Touch</h1>
                    <p className="text-white/40 text-lg max-w-xl mx-auto">
                        Have questions about the Magical Mirror? Our team is here to help you automate your financial future.
                    </p>
                </motion.div>

                <div className="grid md:grid-cols-2 gap-8 mb-24">
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="glass-card p-8 border-white/5"
                    >
                        <h2 className="text-2xl font-bold mb-6">Contact Info</h2>
                        <div className="space-y-6">
                            <div className="flex items-start gap-4">
                                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-white/40">
                                    <Mail size={18} />
                                </div>
                                <div>
                                    <p className="font-bold text-white">General Inquiries</p>
                                    <a href="mailto:hello@automatchbooks.ai" className="text-white/40 hover:text-brand transition-colors text-sm">hello@automatchbooks.ai</a>
                                </div>
                            </div>

                            <div className="flex items-start gap-4">
                                <div className="w-10 h-10 rounded-xl bg-brand/10 flex items-center justify-center text-brand">
                                    <MessageSquare size={18} />
                                </div>
                                <div>
                                    <p className="font-bold text-white">Technical Support</p>
                                    <a href="mailto:support@automatchbooks.ai" className="text-white/40 hover:text-brand transition-colors text-sm">support@automatchbooks.ai</a>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="glass-card p-8 border-white/5"
                    >
                        <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-widest text-white/40 mb-2">Name</label>
                                <input type="text" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-brand transition-colors text-sm" placeholder="Your Name" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-widest text-white/40 mb-2">Email</label>
                                <input type="email" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-brand transition-colors text-sm" placeholder="email@example.com" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-widest text-white/40 mb-2">Message</label>
                                <textarea rows={4} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-brand transition-colors text-sm resize-none" placeholder="How can we help?"></textarea>
                            </div>
                            <button
                                onClick={() => showToast("Message sent! We'll get back to you shortly.", "success")}
                                className="btn-primary w-full py-4 flex items-center justify-center gap-2 group"
                            >
                                Send Message
                                <Send size={16} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                            </button>
                        </form>
                    </motion.div>
                </div>
            </main>
            <Footer />
        </div>
    );
}
