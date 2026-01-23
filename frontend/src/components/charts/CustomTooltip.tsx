"use client";

export const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="glass-panel p-3 border border-white/10 rounded-xl shadow-xl backdrop-blur-md bg-black/80">
                <p className="text-white/60 text-xs mb-1 font-bold">{label}</p>
                <p className="text-brand font-bold text-sm">
                    {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(payload[0].value)}
                </p>
            </div>
        );
    }
    return null;
};
