import { useState } from 'react';
import { AlertTriangle, FileText, Download, FileSpreadsheet, ArrowDownLeft, ArrowUpRight, ArrowLeftRight, Clock } from 'lucide-react';
import Header from '../components/Header';
import DataTable, { type Column } from '../components/DataTable';
import { products, transactions, getLowStockProducts } from '../data/mockData';
import type { InventoryTransaction } from '../types';

type ReportTab = 'low-stock' | 'movement-history';

export default function Reports() {
    const [activeTab, setActiveTab] = useState<ReportTab>('low-stock');
    const [selectedProductId, setSelectedProductId] = useState<number>(products[0]?.id ?? 0);

    const lowStockProducts = getLowStockProducts();
    const productTransactions = transactions
        .filter(t => t.productId === selectedProductId)
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    const tabs = [
        { id: 'low-stock' as const, label: 'Low Stock Report', icon: AlertTriangle, count: lowStockProducts.length },
        { id: 'movement-history' as const, label: 'Movement History', icon: FileText },
    ];

    const lowStockCols: Column<(typeof lowStockProducts)[0]>[] = [
        {
            key: 'name', label: 'Product', sortable: true,
            render: (p) => (<div><p className="text-sm font-medium text-white">{p.name}</p><p className="text-xs text-slate-500">{p.description}</p></div>),
        },
        { key: 'sku', label: 'SKU', sortable: true, render: (p) => <span className="font-mono text-xs text-slate-300 bg-white/5 px-2 py-1 rounded">{p.sku}</span> },
        { key: 'categoryName', label: 'Category', render: (p) => <span className="text-sm text-slate-400">{p.categoryName}</span> },
        {
            key: 'totalStock', label: 'Current Stock', sortable: true,
            render: (p) => <span className="text-sm font-bold text-rose-400">{p.totalStock}</span>,
        },
        { key: 'reorderPoint', label: 'Reorder Point', sortable: true, render: (p) => <span className="text-sm font-semibold text-amber-400">{p.reorderPoint}</span> },
        {
            key: 'deficit', label: 'Deficit', sortable: true,
            render: (p) => {
                const deficit = p.reorderPoint - p.totalStock;
                return <span className="text-sm font-bold text-rose-400">{deficit > 0 ? `-${deficit}` : '0'}</span>;
            },
        },
    ];

    const movementCols: Column<InventoryTransaction>[] = [
        {
            key: 'type', label: 'Type',
            render: (tx) => {
                const colors = { In: '#10b981', Out: '#f43f5e', Transfer: '#6366f1' };
                const bgs = { In: 'rgba(16,185,129,0.1)', Out: 'rgba(244,63,94,0.1)', Transfer: 'rgba(99,102,241,0.1)' };
                const icons = { In: ArrowDownLeft, Out: ArrowUpRight, Transfer: ArrowLeftRight };
                const Icon = icons[tx.type];
                return (<div className="flex items-center gap-2"><div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: bgs[tx.type], color: colors[tx.type] }}><Icon size={14} /></div><span className="text-sm font-medium" style={{ color: colors[tx.type] }}>{tx.type}</span></div>);
            },
        },
        {
            key: 'quantity', label: 'Quantity',
            render: (tx) => <span className={`text-sm font-bold ${tx.type === 'In' ? 'text-emerald-400' : tx.type === 'Out' ? 'text-rose-400' : 'text-indigo-400'}`}>{tx.type === 'In' ? '+' : tx.type === 'Out' ? '-' : '↔'}{tx.quantity}</span>,
        },
        { key: 'warehouseName', label: 'Warehouse', render: (tx) => <div className="text-sm text-slate-300">{tx.warehouseName}{tx.destWarehouseName && <span className="text-slate-500"> → {tx.destWarehouseName}</span>}</div> },
        { key: 'userName', label: 'By', render: (tx) => <span className="text-sm text-slate-400">{tx.userName}</span> },
        {
            key: 'timestamp', label: 'Date',
            render: (tx) => (<div className="flex items-center gap-1.5 text-sm text-slate-300"><Clock size={13} className="text-slate-500" />{new Date(tx.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>),
        },
        { key: 'note', label: 'note', render: (tx) => <span className="text-xs text-slate-500 block max-w-[200px] truncate">{tx.note}</span> },
    ];

    return (
        <div>
            <Header title="Reports" subtitle="Generate and export inventory reports" />

            {/* Tab selector */}
            <div className="px-8 mb-6 flex items-center gap-2 animate-fade-in">
                {tabs.map(tab => {
                    const Icon = tab.icon;
                    return (
                        <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === tab.id ? 'text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                            style={activeTab === tab.id ? { background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.1))', border: '1px solid rgba(59,130,246,0.2)' } : { border: '1px solid transparent' }}>
                            <Icon size={16} />{tab.label}
                            {tab.count !== undefined && <span className="ml-1 px-2 py-0.5 rounded-full text-xs font-bold" style={{ background: 'rgba(244,63,94,0.15)', color: '#f43f5e' }}>{tab.count}</span>}
                        </button>
                    );
                })}
            </div>

            <div className="px-8 pb-8">
                {/* Export buttons */}
                <div className="flex items-center gap-3 mb-5 animate-fade-in">
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-slate-300 hover:text-white transition-all" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                        <Download size={15} /><span>Export PDF</span>
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-slate-300 hover:text-white transition-all" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                        <FileSpreadsheet size={15} /><span>Export Excel</span>
                    </button>

                    {activeTab === 'movement-history' && (
                        <div className="ml-auto flex items-center gap-2">
                            <span className="text-xs text-slate-400">Product:</span>
                            <select value={selectedProductId} onChange={e => setSelectedProductId(Number(e.target.value))}
                                className="px-4 py-2 rounded-xl text-sm text-white outline-none" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                                {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                            </select>
                        </div>
                    )}
                </div>

                {activeTab === 'low-stock' && (
                    <>
                        {lowStockProducts.length > 0 && (
                            <div className="glass-card p-4 mb-5 flex items-center gap-3 animate-fade-in" style={{ borderColor: 'rgba(245,158,11,0.2)' }}>
                                <AlertTriangle size={18} className="text-amber-400 flex-shrink-0" />
                                <p className="text-sm text-slate-300"><span className="font-bold text-amber-400">{lowStockProducts.length} products</span> are at or below their reorder point and need restocking.</p>
                            </div>
                        )}
                        <DataTable columns={lowStockCols} data={lowStockProducts} keyExtractor={(p) => p.id} emptyMessage="All products are well-stocked!" />
                    </>
                )}

                {activeTab === 'movement-history' && (
                    <DataTable columns={movementCols} data={productTransactions} keyExtractor={(t) => t.id} emptyMessage="No movement history for this product" />
                )}
            </div>
        </div>
    );
}
