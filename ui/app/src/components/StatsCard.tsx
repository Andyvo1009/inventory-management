import { TrendingUp, TrendingDown } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface StatsCardProps {
    title: string;
    value: string | number;
    change?: number;
    icon: LucideIcon;
    color: string;
    delay?: number;
}

export default function StatsCard({ title, value, change, icon: Icon, color, delay = 0 }: StatsCardProps) {
    const isPositive = change !== undefined && change >= 0;

    return (
        <div
            className="glass-card glass-card-hover p-5 opacity-0 animate-fade-in"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="flex items-start justify-between mb-4">
                <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center"
                    style={{ background: `${color}15`, color }}
                >
                    <Icon size={22} />
                </div>
                {change !== undefined && (
                    <div
                        className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${isPositive ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                        style={{
                            background: isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                        }}
                    >
                        {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                        {Math.abs(change)}%
                    </div>
                )}
            </div>
            <p className="text-2xl font-bold text-white mb-1">{value}</p>
            <p className="text-sm text-slate-400">{title}</p>
        </div>
    );
}
