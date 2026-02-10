"use client";

import Link from 'next/link';
import { Sparkles } from 'lucide-react';
import { SignedIn } from '@clerk/nextjs';

export default function Footer() {
    return (
        <footer className="py-20 px-6 border-t border-white/5 bg-black">
            <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12">
                <div className="col-span-1 md:col-span-2">
                    <Link href="/" className="flex items-center gap-2 mb-6 group">
                        <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Sparkles className="text-white" size={16} aria-hidden="true" />
                        </div>
                        <Link href="https://automatchbooksai.com" className="text-sm font-semibold tracking-wider text-white uppercase">
                            AutoMatch Books AI
                        </Link>
                    </Link>
                    <p className="text-white/40 max-w-xs leading-relaxed">
                        Revolutionizing financial intelligence with Gemini 3 Flash. Seamlessly matching your reality to your books.
                    </p>
                </div>

                <div>
                    <h4 className="text-sm font-bold uppercase tracking-widest mb-6">Product</h4>
                    <ul className="space-y-4 text-white/40 text-sm">
                        <li><Link href="/#features" className="hover:text-brand transition-colors">Features</Link></li>
                        <li><Link href="/pricing" className="hover:text-brand transition-colors">Pricing</Link></li>
                        <SignedIn>
                            <li><Link href="/analytics" className="hover:text-brand transition-colors">Analytics</Link></li>
                        </SignedIn>
                        <li><Link href="/features" className="hover:text-brand transition-colors text-brand font-bold underline decoration-brand/30 underline-offset-4">Feature Guide</Link></li>
                        <SignedIn>
                            <li><Link href="/dashboard" className="hover:text-brand transition-colors">Dashboard</Link></li>
                        </SignedIn>
                    </ul>
                </div>

                <div>
                    <h4 className="text-sm font-bold uppercase tracking-widest mb-6">Legal & Support</h4>
                    <ul className="space-y-4 text-white/40 text-sm">
                        <li><Link href="/privacy" className="hover:text-brand transition-colors">Privacy Policy</Link></li>
                        <li><Link href="/terms" className="hover:text-brand transition-colors">Terms of Service</Link></li>
                        <li><Link href="/contact" className="hover:text-brand transition-colors">Contact Support</Link></li>
                        <li><a href="mailto:support@automatchbooks.ai" className="hover:text-brand transition-colors">Email Support</a></li>
                    </ul>
                </div>
            </div>

            <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-white/20">
                <p>&copy; 2026 AutoMatch Books AI Engine. All rights reserved.</p>
                <div className="flex items-center gap-6">
                    <p>Powered by Google Gemini 3 Flash</p>
                    <p>Bank-Grade Security</p>
                </div>
            </div>
        </footer>
    );
}
