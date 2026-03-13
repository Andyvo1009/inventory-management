import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { CategoryProductPercentage } from '../types';

interface CategoryPieChartProps {
    data: CategoryProductPercentage[];
}

const COLORS = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#06b6d4', // cyan
    '#f59e0b', // amber
    '#10b981', // emerald
    '#ec4899', // pink
    '#f43f5e', // rose
    '#6366f1', // indigo
    '#14b8a6', // teal
    '#a855f7', // violet
    '#ef4444', // red
    '#84cc16', // lime
];

export default function CategoryPieChart({ data }: CategoryPieChartProps) {
    // Transform data for recharts - only show categories with products
    const chartData = data
        .filter(item => item.product_count > 0)
        .map(item => ({
            name: item.category_name,
            value: item.product_count,
            percentage: item.percentage,
        }));

    if (chartData.length === 0) {
        return (
            <div className="flex items-center justify-center h-full">
                <p className="text-sm text-slate-500">No data available</p>
            </div>
        );
    }

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0];
            return (
                <div 
                    className="px-4 py-3 rounded-xl shadow-lg"
                    style={{ 
                        background: 'rgba(15, 23, 42, 0.95)', 
                        border: '1px solid rgba(255,255,255,0.1)',
                        backdropFilter: 'blur(8px)'
                    }}
                >
                    <p className="text-sm font-semibold text-white mb-1">{data.payload.name}</p>
                    <div className="space-y-1">
                        <p className="text-xs text-slate-400">
                            Products: <span className="text-white font-medium">{data.value}</span>
                        </p>
                        <p className="text-xs text-slate-400">
                            Percentage: <span className="text-white font-medium">{data.payload.percentage.toFixed(1)}%</span>
                        </p>
                    </div>
                </div>
            );
        }
        return null;
    };

    const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }: any) => {
        // Only show label if percentage is significant enough
        if (percentage < 5) return null;

        const RADIAN = Math.PI / 180;
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                className="text-xs font-semibold"
                style={{ textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}
            >
                {`${percentage.toFixed(0)}%`}
            </text>
        );
    };

    return (
        <div className="h-full">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(props) => <CustomLabel {...props} />}
                        outerRadius="80%"
                        fill="#8884d8"
                        dataKey="value"
                        animationBegin={0}
                        animationDuration={800}
                    >
                        {chartData.map((_entry, index) => (
                            <Cell 
                                key={`cell-${index}`} 
                                fill={COLORS[index % COLORS.length]}
                                style={{
                                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
                                    cursor: 'pointer',
                                }}
                            />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        verticalAlign="bottom"
                        height={36}
                        iconType="circle"
                        wrapperStyle={{
                            fontSize: '12px',
                            color: '#cbd5e1',
                        }}
                        formatter={(value, entry: any) => (
                            <span className="text-slate-300">
                                {value} <span className="text-slate-500">({entry.payload.value})</span>
                            </span>
                        )}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
