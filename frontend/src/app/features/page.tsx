"use client";

import React from 'react';
import Footer from '@/components/Footer';
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
        <div className="min-h-screen bg-black text-white selection:bg-brand selection:text-white">
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
                            Start at the beginning. Go to the main website and enjoy the &quot;Magical Mirror&quot; animations.
                        </TestStep>

                        <TestStep
                            number="02"
                            title="Start Free Trial"
                            icon={<ArrowRightCircle className="text-brand-secondary" />}
                        >
                            Look for the bright button that says <strong>&quot;Start Free Trial&quot;</strong> in the center or top right and click it.
                            <div className="mt-4 p-8 rounded-xl bg-brand/5 border border-brand/20 flex items-center justify-center">
                                <button className="btn-primary px-6 py-2">Start Free Trial</button>
                            </div>
                        </TestStep>

                        <TestStep
                            number="03"
                            title="Create Your Identity"
                            icon={<UserCheck className="text-brand" />}
                            image="/screenshots/step_03_login.png"
                        >
                            You&apos;ll see a secure Sign-Up box. Enter any email address and a password. This is handled safely by Clerk.
                        </TestStep>

                        <TestStep
                            number="04"
                            title="The Pricing Menu"
                            icon={<BarChart3 className="text-brand-accent" />}
                            image="/screenshots/step_04_pricing.png"
                        >
                            Once logged in, if you aren&apos;t already there, go to the <strong>Pricing</strong> page to see the plan options.
                        </TestStep>

                        <TestStep
                            number="05"
                            title="Pick the &apos;Founder&apos; Plan"
                            icon={<CheckCircle2 className="text-emerald-400" />}
                        >
                            Find the middle card (the Founder plan) and click the button to select it. This is our most popular tier.
                            <div className="mt-4 p-6 rounded-xl bg-emerald-400/5 border border-emerald-400/20 flex flex-col items-center">
                                <span className="text-xs uppercase font-bold text-emerald-400 mb-2">Recommended Plan</span>
                                <div className="text-2xl font-black italic">$49/mo</div>
                            </div>
                        </TestStep>

                        <TestStep
                            number="06"
                            title="Enter Test Card Details"
                            icon={<CreditCard className="text-brand" />}
                        >
                            You&apos;ll be taken to a secure Stripe page. Do not use a real card! Use the number <strong>4242 4242 4242 4242</strong>.
                            <div className="mt-4 p-4 rounded-xl bg-white/5 border border-brand/20 flex flex-col gap-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] uppercase font-bold text-white/30">Visa Test Number</span>
                                    <span className="text-xs font-mono font-bold text-white">4242 4242 4242 4242</span>
                                </div>
                            </div>
                        </TestStep>

                        <TestStep
                            number="07"
                            title="Finish Payment Test"
                            icon={<ShieldCheck className="text-brand" />}
                        >
                            Put in any future date (like 12/26) and any 3 numbers for the CVC. Click pay to simulate a real purchase.
                            <div className="mt-4 flex items-center gap-4">
                                <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                                    <div className="w-full h-full bg-brand animate-pulse" />
                                </div>
                                <span className="text-[10px] font-bold text-brand uppercase">Processing...</span>
                            </div>
                        </TestStep>

                        <TestStep
                            number="08"
                            title="Land on the Dashboard"
                            icon={<Layers className="text-brand-secondary" />}
                            image="/screenshots/step_08_dashboard.png"
                        >
                            After payment, you&apos;ll be redirected back. You are now officially in the &quot;Mirror&quot; dashboard.
                        </TestStep>

                        <TestStep
                            number="09"
                            title="Connect to QuickBooks"
                            icon={<Cpu className="text-brand" />}
                        >
                            Click the big button that says <strong>&quot;Sync with QuickBooks&quot;</strong>. This links your financial data.
                            <div className="mt-4 p-6 rounded-xl bg-brand/5 border border-brand/20 flex items-center justify-center gap-4">
                                <img src="https://quickbooks.intuit.com/static/0724816c7fb4cc556a3108f9720f2694.svg" alt="QBO" className="h-6 invert opacity-50" />
                                <ArrowRightCircle className="text-brand" />
                                <Sparkles className="text-brand" />
                            </div>
                        </TestStep>

                        <TestStep
                            number="10"
                            title="Grant Secure Access"
                            icon={<Box className="text-emerald-400" />}
                        >
                            A QuickBooks login will pop up. Use your <strong>Sandbox Company</strong> credentials to authorize the connection.
                            <div className="mt-4 p-4 rounded-xl bg-emerald-400/5 border border-emerald-400/20 flex items-center gap-3">
                                <ShieldCheck className="text-emerald-400" size={20} />
                                <span className="text-xs font-bold text-white/60">Connection Secure</span>
                            </div>
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
                            Hover your mouse over the &quot;Eye&quot; or &quot;Info&quot; icon on a transaction. Read <em>why</em> the AI made its suggestion.
                        </TestStep>

                        <TestStep
                            number="13"
                            title="Become the &apos;Final Boss&apos;"
                            icon={<Sparkles className="text-brand" />}
                        >
                            When you see a suggestion that makes sense, click the <strong>Green Checkmark</strong> to &quot;Agree.&quot;
                            <div className="mt-4 p-6 rounded-xl bg-brand/10 border border-brand/30 flex items-center justify-center">
                                <div className="w-12 h-12 rounded-full bg-emerald-400 flex items-center justify-center text-black shadow-[0_0_20px_rgba(52,211,153,0.3)]">
                                    <CheckCircle2 size={32} />
                                </div>
                            </div>
                        </TestStep>

                        <TestStep
                            number="14"
                            title="Master the Tag System"
                            icon={<Tags className="text-rose-400" />}
                        >
                            Click the &quot;Tag&quot; icon to categorize expenses with granular precision. Select from &apos;Office&apos;, &apos;Travel&apos;, or &apos;Meals&apos;.
                            <div className="mt-4 flex gap-2">
                                <span className="px-3 py-1 rounded-full bg-brand/10 text-[10px] font-bold text-brand border border-brand/20">#Office</span>
                                <span className="px-3 py-1 rounded-full bg-rose-500/10 text-[10px] font-bold text-rose-400 border border-rose-500/20">#Travel</span>
                                <span className="px-3 py-1 rounded-full bg-amber-500/10 text-[10px] font-bold text-amber-500 border border-amber-500/20">#Meals</span>
                            </div>
                        </TestStep>

                        <TestStep
                            number="15"
                            title="Check Your Analytics"
                            icon={<BarChart3 className="text-brand-secondary" />}
                            image="/screenshots/step_14_analytics.png"
                        >
                            Go to the <strong>Analytics</strong> page to see how your approved transactions are sorted into beautiful charts.
                        </TestStep>

                        <TestStep
                            number="16"
                            title="Split a Transaction"
                            icon={<Split className="text-brand-accent" />}
                        >
                            Have a receipt for both &apos;Meals&apos; and &apos;Supplies&apos;? Click the <strong>Split</strong> icon to divide the amount.
                            <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10 space-y-2">
                                <div className="flex justify-between text-[10px] text-white/60">
                                    <span>Total: <span className="text-white font-bold">$100.00</span></span>
                                </div>
                                <div className="h-2 flex rounded-full overflow-hidden">
                                    <div className="w-1/2 bg-brand" />
                                    <div className="w-1/2 bg-rose-400" />
                                </div>
                            </div>
                        </TestStep>

                        <TestStep
                            number="17"
                            title="Receipt Mirroring"
                            icon={<ScanLine className="text-emerald-400" />}
                        >
                            Upload a receipt image. Watch our engine &quot;Mirror&quot; it to the bank feed transaction automatically.
                            <div className="mt-4 p-8 rounded-xl border border-dashed border-white/20 flex flex-col items-center justify-center text-white/30">
                                <ScanLine size={24} className="mb-2 opacity-50" />
                                <span className="text-[10px] uppercase font-bold">Drop Receipt Here</span>
                            </div>
                        </TestStep>

                        <TestStep
                            number="18"
                            title="Feel the Pulse (Haptics)"
                            icon={<Vibrate className="text-brand-secondary" />}
                        >
                            On mobile? Every successful approval sends a satisfying haptic vibration to confirm the action.
                            <div className="mt-4 flex justify-center gap-1">
                                <div className="w-1 h-6 bg-brand/40 rounded-full animate-bounce [animation-delay:0ms]" />
                                <div className="w-1 h-8 bg-brand/80 rounded-full animate-bounce [animation-delay:100ms]" />
                                <div className="w-1 h-6 bg-brand/40 rounded-full animate-bounce [animation-delay:200ms]" />
                            </div>
                        </TestStep>

                        <TestStep
                            number="19"
                            title="Verify Export Status"
                            icon={<Database className="text-brand" />}
                        >
                            Check the &quot;Exported&quot; tab. Verify that your transactions have landed safely in your QBO Sandbox.
                        </TestStep>

                        <TestStep
                            number="20"
                            title="Log Out Safely"
                            icon={<ArrowRightCircle className="text-white/20 rotate-180" />}
                        >
                            Click your user profile icon and select <strong>Sign Out</strong>. You&apos;ve completed the full Smart Autopilot loop!
                            <div className="mt-4 flex items-center justify-end">
                                <div className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-bold text-white/40">
                                    Sign Out
                                </div>
                            </div>
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
