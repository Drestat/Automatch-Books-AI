"use client";

import React from 'react';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import { motion } from 'framer-motion';
import {
    Sparkles,
    Cpu,
    Layers,
    Eye,
    Zap,
    Box,
    Code2,
    Smartphone,
    CreditCard,
    Activity,
    ArrowRightCircle,
    CheckCircle2,
    ShieldCheck,
    MessageSquareQuote,
    UserCheck,
    BarChart3,
    Tags,
    Split,
    ScanLine,
    Vibrate,
    Database
} from 'lucide-react';

export default function FeaturesPage() {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white pt-20">
            <Navbar />
            <main className="py-24 px-6 md:px-12 max-w-7xl mx-auto">

                {/* Hero section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-24 text-center"
                >
                    <div className="w-16 h-16 rounded-3xl bg-brand/10 text-brand flex items-center justify-center mb-8 mx-auto border border-brand/20">
                        <Layers size={32} />
                    </div>
                    <h1 className="text-[clamp(2.5rem,8vw,5rem)] font-black tracking-tighter leading-[0.9] mb-8">
                        The Features <span className="text-white/20">&</span> <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-brand-secondary">Mastery Guide</span>
                    </h1>
                    <p className="text-white/40 text-xl max-w-2xl mx-auto leading-relaxed">
                        Your Books, on Smart Autopilot. Experience the power of <strong>Auditable Intelligence</strong>.
                    </p>
                </motion.div>

                {/* New Section: The Trust Bridge */}
                <section className="mb-32">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-full bg-brand/20 text-brand flex items-center justify-center">
                            <ShieldCheck size={20} />
                        </div>
                        <h2 className="text-3xl font-black tracking-tight uppercase">The Trust Bridge</h2>
                    </div>
                    <p className="text-white/40 text-sm mb-12 max-w-2xl font-medium">Why we&apos;re the human-in-the-loop layer business owners desperately need.</p>

                    <div className="grid md:grid-cols-2 gap-8 mb-12">
                        <div className="glass-card p-8 border-white/5 relative overflow-hidden">
                            <div className="absolute -top-4 -right-4 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl" />
                            <h3 className="text-xl font-bold mb-4 text-rose-400">The &quot;Black Box&quot; Problem</h3>
                            <p className="text-white/40 text-sm leading-relaxed">
                                Most AI tools are &quot;black boxes&quot;—they do the work in the dark, and you just hope it&apos;s right. They guess, get it wrong, and leave you to clean up a forensic mess in your books.
                            </p>
                        </div>
                        <div className="glass-card p-8 border-brand/20 bg-brand/5 relative overflow-hidden">
                            <div className="absolute -top-4 -right-4 w-24 h-24 bg-brand/20 rounded-full blur-2xl" />
                            <h3 className="text-xl font-bold mb-4 text-brand">The Magical Mirror Solution</h3>
                            <p className="text-white/60 text-sm leading-relaxed">
                                AutoMatch isn&apos;t just automation; it&apos;s <strong>auditable intelligence</strong>. The AI explains its logic for <em>every single transaction</em> before you click &quot;Agree&quot;. We provide the trust bridge missing in fintech.
                            </p>
                        </div>
                    </div>

                    <div className="p-8 rounded-3xl bg-brand/5 border border-brand/10 relative overflow-hidden italic">
                        <div className="absolute top-0 left-0 p-4 opacity-10">
                            <MessageSquareQuote size={40} className="text-brand" />
                        </div>
                        <p className="text-xl md:text-2xl text-white/80 leading-relaxed text-center py-4">
                            &ldquo;Existing tools are black boxes—they guess, get it wrong, and leave you to clean up the mess. Your concept of <strong>&apos;Explainable AI&apos;</strong> is the trust bridge missing in fintech.&rdquo;
                        </p>
                    </div>
                </section>

                {/* Section 1: The Designer's Vision (Frontend Blueprint) */}
                <section className="mb-32">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-full bg-brand-accent/20 text-brand-accent flex items-center justify-center">
                            <Eye size={20} />
                        </div>
                        <h2 className="text-3xl font-black tracking-tight uppercase">The Designer&apos;s Vision</h2>
                    </div>
                    <p className="text-white/40 text-sm mb-12 max-w-2xl font-medium">Design Directives for maintaining the &quot;Magical Mirror&quot; aesthetic.</p>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <VisionCard
                            title="Glassmorphism v3"
                            icon={<Layers size={24} />}
                            description="Apply 'backdrop-blur-xl' with a 'bg-white/5' tint. All cards MUST have a 1px 'border-white/10' to simulate light refraction on glass edges."
                        />
                        <VisionCard
                            title="Kinetic UX"
                            icon={<Zap size={24} />}
                            description="Use Framer Motion 'layout' prop for list reordering. Approved transactions should animate with a 'x: 100, opacity: 0' exit transition."
                        />
                        <VisionCard
                            title="Confidence Palette"
                            icon={<Activity size={24} />}
                            description="Strict color tokens: Green (#10b981) for >85% confidence, Amber (#f59e0b) for 50-85%, and Rose (#f43f5e) for anomalies."
                        />
                    </div>
                </section>

                {/* Section 2: The Builder's Engine (Backend Blueprint) */}
                <section className="mb-32">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-full bg-emerald-400/20 text-emerald-400 flex items-center justify-center">
                            <Cpu size={20} />
                        </div>
                        <h2 className="text-3xl font-black tracking-tight uppercase">The Builder&apos;s Engine</h2>
                    </div>
                    <p className="text-white/40 text-sm mb-12 max-w-2xl font-medium">Technical specifications for the sync and AI matching core.</p>

                    <div className="glass-card p-8 md:p-12 border-white/5 space-y-12 overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-8 opacity-5">
                            <Code2 size={200} />
                        </div>

                        <div className="grid md:grid-cols-2 gap-12 relative z-10">
                            <div>
                                <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><Box size={18} className="text-brand" /> Mirror Database logic</h3>
                                <div className="space-y-6">
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                                        <p className="text-xs font-bold text-white mb-2">Multi-Tenant Isolation</p>
                                        <p className="text-xs text-white/40 leading-relaxed">All tables leverage <code className="text-emerald-400">realm_id</code> indexing. Row Level Security (RLS) ensures that even in shared clusters, a user&apos;s transactions are mathematically isolated.</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                                        <p className="text-xs font-bold text-white mb-2">Optimistic Sync</p>
                                        <p className="text-xs text-white/40 leading-relaxed">Frontend uses SWR or React Query to update the mirror database in <code className="text-emerald-400">~150ms</code>, then background workers push to QuickBooks asynchronously.</p>
                                    </div>
                                </div>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><Sparkles size={18} className="text-brand" /> AI Prompt Engineering</h3>
                                <div className="space-y-6">
                                    <div className="p-4 rounded-xl bg-brand/5 border border-brand/20">
                                        <p className="text-xs font-bold text-brand mb-2">Explainable Reasoners</p>
                                        <p className="text-xs text-white/60 leading-relaxed">The AI doesn&apos;t just categorize; it explains. &quot;I categorized this as &apos;Job Materials&apos; because the vendor is Home Depot.&quot; This turns automation into <strong>validation</strong>.</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/5 font-mono text-[10px] text-white/30 truncate">
                                        {"const PROMPT = `Analyze vendor '${tx.vendor}' and explain the mapping...`"}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Section 3: Feature Deep Dive */}
                <section className="mb-32">
                    <div className="flex items-center gap-4 mb-12">
                        <div className="w-10 h-10 rounded-full bg-brand/20 text-brand flex items-center justify-center">
                            <Sparkles size={20} />
                        </div>
                        <h2 className="text-3xl font-black tracking-tight uppercase">Core Capabilities</h2>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8">
                        <FeatureBlock
                            title="Superior Analytics & Tags"
                            description="The tag system and analytics QuickBooks wish they had. Know exactly where your money is going with multi-dimensional filtering and trend analysis."
                        />
                        <FeatureBlock
                            title="Automated Splitting"
                            description="AI detects receipts representing multiple departments. A $200 Target transaction is automatically split into 'Office Supplies' and 'Software' based on itemized logic."
                        />
                        <FeatureBlock
                            title="Receipt Mirroring"
                            description="Upload a photo; the engine matches it to a bank feed entry in milliseconds using fuzzy-matching on date, amount, and vendor name."
                        />
                        <FeatureBlock
                            title="Mobile Haptics"
                            description="Building for the field. Capacitor integration provides physical feedback (haptics) on every successful reconciliation."
                        />
                    </div>
                </section>

                {/* Section 4: A-Z Testing Manual (15 Steps) */}
                <section className="mb-24">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-full bg-brand/20 text-brand flex items-center justify-center">
                            <Smartphone size={20} />
                        </div>
                        <h2 className="text-3xl font-black tracking-tight uppercase">Tester&apos;s A-Z Manual (15-Step Walkthrough)</h2>
                    </div>
                    <p className="text-white/40 text-sm mb-12 max-w-2xl font-medium">Follow these exact, simple steps to experience the full power of the platform.</p>

                    <div className="grid lg:grid-cols-2 gap-8">
                        <TestStep
                            number="01"
                            title="Open the Home Page"
                            icon={<Zap className="text-brand" />}
                            image="/screenshots/step_01_hero.png"
                        >
                            Start at the beginning. Go to the main website and enjoy the "Magical Mirror" animations.
                        </TestStep>

                        <TestStep
                            number="02"
                            title="Start Free Trial"
                            icon={<ArrowRightCircle className="text-brand-secondary" />}
                            image="/screenshots/step_02_start_trial.png"
                        >
                            Look for the bright button that says <strong>"Start Free Trial"</strong> in the center or top right and click it.
                        </TestStep>

                        <TestStep
                            number="03"
                            title="Create Your Identity"
                            icon={<UserCheck className="text-brand" />}
                            image="/screenshots/step_03_login.png"
                        >
                            You'll see a secure Sign-Up box. Enter any email address and a password. This is handled safely by Clerk.
                        </TestStep>

                        <TestStep
                            number="04"
                            title="The Pricing Menu"
                            icon={<BarChart3 className="text-brand-accent" />}
                            image="/screenshots/step_04_pricing.png"
                        >
                            Once logged in, if you aren't already there, go to the <strong>Pricing</strong> page to see the plan options.
                        </TestStep>

                        <TestStep
                            number="05"
                            title="Pick the 'Founder' Plan"
                            icon={<CheckCircle2 className="text-emerald-400" />}
                            image="/screenshots/step_05_founder_plan.png"
                        >
                            Find the middle card (the Founder plan) and click the button to select it. This is our most popular tier.
                        </TestStep>

                        <TestStep
                            number="06"
                            title="Enter Test Card Details"
                            icon={<CreditCard className="text-brand" />}
                            image="/screenshots/step_06_card_details.png"
                        >
                            You'll be taken to a secure Stripe page. Use the test number <strong>4242 4242 4242 4242</strong> for a safe simulation.
                        </TestStep>

                        <TestStep
                            number="07"
                            title="Finish Payment Test"
                            icon={<ShieldCheck className="text-brand" />}
                            image="/screenshots/step_07_payment_processing.png"
                        >
                            Put in any future date and 3 numbers for CVC. Click pay to experience the seamless transaction flow.
                        </TestStep>

                        <TestStep
                            number="08"
                            title="Land on the Dashboard"
                            icon={<Layers className="text-brand-secondary" />}
                            image="/screenshots/step_08_dashboard.png"
                        >
                            After payment, you'll be redirected back. You are now officially in the "Mirror" dashboard.
                        </TestStep>

                        <TestStep
                            number="09"
                            title="Connect to QuickBooks"
                            icon={<Cpu className="text-brand" />}
                            image="/screenshots/step_09_connect_qbo.png"
                        >
                            Click <strong>"Connect Securely"</strong> to link your QuickBooks Online account to the magical mirror.
                        </TestStep>

                        <TestStep
                            number="10"
                            title="Grant Secure Access"
                            icon={<Box className="text-emerald-400" />}
                            image="/screenshots/step_10_grant_access.png"
                        >
                            A QuickBooks login will appear. Use your Sandbox credentials to authorize the secure data bridge.
                        </TestStep>

                        <TestStep
                            number="11"
                            title="View Your Feed"
                            icon={<Activity className="text-brand" />}
                            image="/screenshots/step_11_features_grid.png"
                        >
                            Transactions will start appearing! These are mirrored from your bank feed directly into our interface.
                        </TestStep>

                        <TestStep
                            number="12"
                            title="Inspect AI Reasoning"
                            icon={<Eye className="text-brand-accent" />}
                            image="/screenshots/step_12_ai_card.png"
                        >
                            Click the <strong>AI Insight</strong> icon to see the logic. "I categorized this because..." transparency is key.
                        </TestStep>

                        <TestStep
                            number="13"
                            title="Become the 'Final Boss'"
                            icon={<Sparkles className="text-brand" />}
                            image="/screenshots/step_13_approval.png"
                        >
                            When you see a suggestion that makes sense, click <strong>"Confirm Match"</strong> to finalize the entry.
                        </TestStep>

                        <TestStep
                            number="14"
                            title="Master the Tag System"
                            icon={<Tags className="text-rose-400" />}
                            image="/screenshots/step_14_tags.png"
                        >
                            Use the <strong>Tag</strong> icon to quickly organize transactions with custom labels for better tax reporting.
                        </TestStep>

                        <TestStep
                            number="15"
                            title="Advanced Analytics"
                            icon={<BarChart3 className="text-brand-secondary" />}
                            image="/screenshots/step_15_analytics.png"
                        >
                            Visit the <strong>Analytics</strong> tab to see your cash flow and spend distribution visualized in real-time.
                        </TestStep>

                        <TestStep
                            number="16"
                            title="Split a Transaction"
                            icon={<Split className="text-brand-accent" />}
                            image="/screenshots/step_16_split.png"
                        >
                            For complex receipts, use the <strong>Split</strong> tool to allocate amounts across multiple categories perfectly.
                        </TestStep>

                        <TestStep
                            number="17"
                            title="Receipt Mirroring"
                            icon={<ScanLine className="text-emerald-400" />}
                            image="/screenshots/step_17_receipt.png"
                        >
                            Upload or drop a receipt image. Our AI mirrors it to the corresponding bank entry in milliseconds.
                        </TestStep>

                        <TestStep
                            number="18"
                            title="Satisfying Haptics"
                            icon={<Vibrate className="text-brand-secondary" />}
                            image="/screenshots/step_18_haptics.png"
                        >
                            Experience physical confirmation on mobile. Every match sends a satisfying haptic pulse to your device.
                        </TestStep>

                        <TestStep
                            number="19"
                            title="Verify Export Status"
                            icon={<Database className="text-brand" />}
                            image="/screenshots/step_19_export.png"
                        >
                            Once matched, check the <strong>"Exported to QBO"</strong> badge to confirm the data has safely landed in QuickBooks.
                        </TestStep>

                        <TestStep
                            number="20"
                            title="Log Out Safely"
                            icon={<ArrowRightCircle className="text-white/20 rotate-180" />}
                            image="/screenshots/step_20_logout.png"
                        >
                            Click your profile icon and <strong>Sign Out</strong>. You've completed the full Smart Autopilot financial loop!
                        </TestStep>
                    </div>
                </section>

                <div className="text-center py-12 border-t border-white/5">
                    <p className="text-white/20 text-sm mb-6">Experience the future of financial clarity.</p>
                    <button className="btn-primary px-8 py-4 flex items-center gap-2 mx-auto">
                        Return to Dashboard <ArrowRightCircle size={18} />
                    </button>
                </div>

            </main>
            <Footer />
        </div>
    );
}

function FeatureBlock({ title, description }: { title: string, description: string }) {
    return (
        <div className="flex gap-4">
            <div className="mt-1">
                <CheckCircle2 size={18} className="text-brand" />
            </div>
            <div>
                <h4 className="font-bold mb-1">{title}</h4>
                <p className="text-sm text-white/40 leading-relaxed">{description}</p>
            </div>
        </div>
    );
}

function VisionCard({ title, icon, description }: { title: string, icon: React.ReactNode, description: string }) {
    return (
        <motion.div
            whileHover={{ y: -5 }}
            className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 group hover:border-brand/30 transition-all"
        >
            <div className="w-12 h-12 rounded-xl bg-white/5 text-white/40 group-hover:bg-brand/10 group-hover:text-brand flex items-center justify-center mb-4 transition-colors">
                {icon}
            </div>
            <h4 className="font-bold mb-2">{title}</h4>
            <p className="text-xs text-white/40 leading-relaxed">{description}</p>
        </motion.div>
    );
}

function TestStep({ number, title, children, icon, image }: { number: string, title: string, children: React.ReactNode, icon?: React.ReactNode, image?: string }) {
    return (
        <div className="glass-card p-6 border-white/5 flex gap-6 relative overflow-hidden group">
            <div className="absolute -top-12 -left-12 text-[10rem] font-black text-white/[0.02] select-none pointer-events-none group-hover:text-brand/[0.02] transition-colors">{number}</div>

            <div className="flex-1 relative z-10">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                        {icon || <Smartphone size={18} className="text-brand" />}
                    </div>
                    <div>
                        <span className="text-[10px] uppercase font-bold text-brand tracking-widest block mb-0.5">Step {number}</span>
                        <h4 className="text-lg font-bold text-white/80">{title}</h4>
                    </div>
                </div>

                <div className="text-sm text-white/40 leading-relaxed min-h-[4rem]">
                    {children}
                </div>

                {image && (
                    <div className="mt-6 rounded-xl overflow-hidden border border-white/5 opacity-80 hover:opacity-100 transition-all hover:scale-[1.02] cursor-zoom-in">
                        <img src={image} alt={title} className="w-full object-cover max-h-[200px]" />
                    </div>
                )}
            </div>
        </div>
    );
}
