"use client";

export const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="glass-panel p-4 border border-white/10 rounded-2xl shadow-2xl backdrop-blur-xl bg-black/80 min-w-[160px]">
                <p className="text-white/40 text-[10px] mb-3 font-black uppercase tracking-widest">{label}</p>
                <div className="space-y-2">
                    {payload.map((item: any, index: number) => (
                        <div key={index} className="flex items-center justify-between gap-4">
                            <span className="text-xs text-white/60 font-medium">{item.name}</span>
                            <span className="text-sm font-black" style={{ color: item.color || item.fill }}>
                                {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.value)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    return null;
};
