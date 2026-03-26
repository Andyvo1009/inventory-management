import { useState, useEffect } from 'react';
import {
    Package,
    Warehouse,
    ArrowLeftRight,
    AlertTriangle,
    ArrowDownLeft,
    ArrowUpRight,
    Clock,
    Loader2,
} from 'lucide-react';
import Header from '../components/Header';
import StatsCard from '../components/StatsCard';
import {
    getTotalProducts,
    getTotalWarehouses,
    getTotalTransactions,
    getAllTransactions,
    getStockByProduct,
    getLowStockProducts,
} from '../api/dashboard';
import type {
    LowStockProductItem,
    TransactionDetail,
    StockByProductItem,
} from '../types';

export default function Dashboard() {
    const [totalProducts, setTotalProducts] = useState<number>(0);
    const [totalWarehouses, setTotalWarehouses] = useState<number>(0);
    const [totalTransactions, setTotalTransactions] = useState<number>(0);
    const [lowStockProducts, setLowStockProducts] = useState<LowStockProductItem[]>([]);
    const [recentTransactions, setRecentTransactions] = useState<TransactionDetail[]>([]);
    const [stockByProduct, setStockByProduct] = useState<StockByProductItem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch all dashboard data in parallel
                const [
                    productsRes,
                    warehousesRes,
                    transactionsRes,
                    allTransactionsRes,
                    stockRes,
                    lowStockRes,
                ] = await Promise.all([
                    getTotalProducts(),
                    getTotalWarehouses(),
                    getTotalTransactions(),
                    getAllTransactions(6, 0), // Get 6 recent transactions
                    getStockByProduct(),
                    getLowStockProducts(),
                ]);

                setTotalProducts(productsRes.total_products);
                setTotalWarehouses(warehousesRes.total_warehouses);
                setTotalTransactions(transactionsRes.total_transactions);
                setRecentTransactions(allTransactionsRes.transactions);
                setLowStockProducts(lowStockRes.low_stock_products);
                setStockByProduct(stockRes.stock_by_product);
            } catch (err) {
                console.error('Error fetching dashboard data:', err);
                setError('Failed to load dashboard data. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    const formatTime = (ts: string) => {
        const d = new Date(ts);
        const now = new Date();
        const diffMs = now.getTime() - d.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        if (diffHours < 1) return 'Just now';
        if (diffHours < 24) return `${diffHours}h ago`;
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    };

    if (loading) {
        return (
            <div>
                <Header title="Dashboard" subtitle="Overview of your inventory at a glance" />
                <div className="flex items-center justify-center h-96">
                    <Loader2 className="w-8 h-8 text-accent-blue animate-spin" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <Header title="Dashboard" subtitle="Overview of your inventory at a glance" />
                <div className="px-8">
                    <div className="glass-card p-6 text-center">
                        <p className="text-red-400">{error}</p>
                        <button
                            onClick={() => window.location.reload()}
                            className="mt-4 px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-blue-600 transition-colors"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const lowStockCount = lowStockProducts.length;

    return (
        <div>
            <Header title="Dashboard" subtitle="Overview of your inventory at a glance" />

            {/* Stats Grid */}
            <div className="px-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                <StatsCard title="Total Products" value={totalProducts}  icon={Package} color="#3b82f6" delay={0} />
                <StatsCard title="Warehouses" value={totalWarehouses} icon={Warehouse} color="#8b5cf6" delay={80} />
                <StatsCard title="Transactions" value={totalTransactions}  icon={ArrowLeftRight} color="#06b6d4" delay={160} />
                <StatsCard title="Low Stock Alerts" value={lowStockCount}  icon={AlertTriangle} color="#f43f5e" delay={240} />
            </div>

            <div className="px-8 grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Recent Activity */}
                <div className="lg:col-span-2 glass-card p-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
                    <div className="flex items-center justify-between mb-5">
                        <h2 className="text-lg font-bold text-white">Recent Activity</h2>
                        {/* <button className="text-xs font-medium text-accent-blue hover:text-blue-300 transition-colors">View All</button> */}
                    </div>
                    <div className="space-y-1">
                        {recentTransactions.map((tx, i) => (
                            <div
                                key={tx.id}
                                className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-white/[0.03] transition-colors opacity-0 animate-fade-in"
                                style={{ animationDelay: `${300 + i * 60}ms` }}
                            >
                                <div
                                    className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                                    style={{
                                        background:
                                            tx.type === 'In'
                                                ? 'rgba(16, 185, 129, 0.12)'
                                                : tx.type === 'Out'
                                                    ? 'rgba(244, 63, 94, 0.12)'
                                                    : 'rgba(99, 102, 241, 0.12)',
                                        color:
                                            tx.type === 'In' ? '#10b981' : tx.type === 'Out' ? '#f43f5e' : '#6366f1',
                                    }}
                                >
                                    {tx.type === 'In' ? <ArrowDownLeft size={16} /> : tx.type === 'Out' ? <ArrowUpRight size={16} /> : <ArrowLeftRight size={16} />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-white truncate">
                                        {tx.product_name}
                                        <span className="text-slate-500 font-normal"> — {tx.type === 'Transfer' ? 'Transferred' : tx.type === 'In' ? 'Received' : 'Shipped'} </span>
                                        <span className="text-slate-300">{tx.quantity} units</span>
                                    </p>
                                    <p className="text-xs text-slate-500 mt-0.5 truncate">{tx.note}</p>
                                </div>
                                <div className="flex items-center gap-1.5 text-xs text-slate-500 flex-shrink-0">
                                    <Clock size={12} />
                                    {formatTime(tx.timestamp)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Low Stock Alerts */}
                <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.3s' }}>
                    <div className="flex items-center gap-2 mb-5">
                        <AlertTriangle size={18} className="text-amber-400" />
                        <h2 className="text-lg font-bold text-white">Low Stock Alerts</h2>
                    </div>
                    <div className="space-y-3">
                        {lowStockProducts.length === 0 ? (
                            <p className="text-sm text-slate-500 text-center py-8">All products are well-stocked!</p>
                        ) : (
                            lowStockProducts.map((p, i) => (
                                <div
                                    key={p.product_id}
                                    className="p-4 rounded-xl opacity-0 animate-fade-in"
                                    style={{
                                        animationDelay: `${400 + i * 80}ms`,
                                        background: 'rgba(244, 63, 94, 0.05)',
                                        border: '1px solid rgba(244, 63, 94, 0.1)',
                                    }}
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="text-sm font-medium text-white truncate">{p.product_name}</p>
                                        <span className="text-xs font-mono text-slate-500">{p.product_sku}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-slate-400">Stock:</span>
                                            <span className="text-sm font-bold text-rose-400">{p.total_stock}</span>
                                        </div>
                                        {/* <div className="flex items-center gap-2">
                                            <span className="text-xs text-slate-400">Min:</span>
                                            <span className="text-sm font-semibold text-amber-400">{p.reorder_point}</span>
                                        </div> */}
                                    </div>
                                    {/* Stock bar */}
                                    {/* <div className="mt-2 h-1.5 rounded-full bg-white/5 overflow-hidden">
                                        <div
                                            className="h-full rounded-full transition-all duration-1000"
                                            style={{
                                                width: `${Math.min(100, (p.total_stock / p.reorder_point) * 100)}%`,
                                                background: p.total_stock / p.reorder_point < 0.5
                                                    ? 'linear-gradient(90deg, #f43f5e, #fb7185)'
                                                    : 'linear-gradient(90deg, #f59e0b, #fbbf24)',
                                            }}
                                        />
                                    </div> */}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Quick Stock Overview */}
            <div className="px-8 pb-8">
                <h2 className="text-lg font-bold text-white mb-4">Stock by Product</h2>
                <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.3s' }}>
                    <div className="space-y-4">
                        {stockByProduct.length === 0 ? (
                            <p className="text-sm text-slate-500 text-center py-8">No stock data available</p>
                        ) : (
                            console.log('Rendering stock by product:', stockByProduct),
                            stockByProduct.slice(0, 8).map((item, i) => {
                                const maxStock = 150;
                                const percentage = Math.min(100, (item.total_stock / maxStock) * 100);
                                // Check if this product is in low stock list
                                const lowStockItem = lowStockProducts.find(lsp => lsp.product_id === item.product_id);
                                const isLow = lowStockItem !== undefined;

                                return (
                                    <div key={item.product_id} className="opacity-0 animate-fade-in" style={{ animationDelay: `${400 + i * 50}ms` }}>
                                        <div className="flex items-center justify-between mb-1.5">
                                            <div className="flex items-center gap-3">
                                                <span className="text-sm font-medium text-white">{item.product_name}</span>
                                                <span className="text-xs font-mono text-slate-500">{item.product_sku}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                {isLow && (
                                                    <span className="text-xs font-medium text-rose-400 flex items-center gap-1">
                                                        <AlertTriangle size={12} /> Low
                                                    </span>
                                                )}
                                                <span className="text-sm font-bold text-white">{item.total_stock}</span>
                                            </div>
                                        </div>
                                        <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                                            <div
                                                className="h-full rounded-full transition-all duration-1000 ease-out"
                                                style={{
                                                    width: `${percentage}%`,
                                                    background: isLow
                                                        ? 'linear-gradient(90deg, #f43f5e, #fb7185)'
                                                        : 'linear-gradient(90deg, #3b82f6, #06b6d4)',
                                                }}
                                            />
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
