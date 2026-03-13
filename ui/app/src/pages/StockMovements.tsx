import { useState, useEffect } from 'react';
import { ArrowDownLeft, ArrowUpRight, ArrowLeftRight, Filter, Loader2 } from 'lucide-react';
import Header from '../components/Header';
import DataTable, { type Column } from '../components/DataTable';
import Modal from '../components/Modal';
import type {
    TransactionResponse,
    TransactionType,
    TransactionCreateRequest,
    ProductResponse,
    WarehouseSummary,
} from '../types';
import * as transactionsApi from '../api/transactions';
import * as productsApi from '../api/products';
import * as warehousesApi from '../api/warehouses';
import { ApiError } from '../api/client';

const typeConfig = {
    In: { icon: ArrowDownLeft, color: '#10b981', bg: 'rgba(16,185,129,0.1)', label: 'Stock In' },
    Out: { icon: ArrowUpRight, color: '#f43f5e', bg: 'rgba(244,63,94,0.1)', label: 'Stock Out' },
    Transfer: { icon: ArrowLeftRight, color: '#6366f1', bg: 'rgba(99,102,241,0.1)', label: 'Transfer' },
};

export default function StockMovements() {
    const [showAddModal, setShowAddModal] = useState(false);
    const [typeFilter, setTypeFilter] = useState<TransactionType | 'all'>('all');
    const [movementType, setMovementType] = useState<TransactionType>('In');

    // Data state
    const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Data for dropdowns
    const [products, setProducts] = useState<ProductResponse[]>([]);
    const [warehouses, setWarehouses] = useState<WarehouseSummary[]>([]);

    // Fetch transactions
    useEffect(() => {
        fetchTransactions();
    }, [typeFilter]);

    // Fetch products and warehouses for form
    useEffect(() => {
        fetchProductsAndWarehouses();
    }, []);

    const fetchTransactions = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await transactionsApi.listTransactions(
                typeFilter === 'all' ? null : typeFilter,
                null,
                null,
                100,
                0
            );
            setTransactions(response.transactions);
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to load transactions';
            setError(errorMsg);
            console.error('Error fetching transactions:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchProductsAndWarehouses = async () => {
        try {
            const [productsRes, warehousesRes] = await Promise.all([
                productsApi.listProducts(null, null, 100, 0),
                warehousesApi.listWarehouses(),
            ]);
            setProducts(productsRes.products);
            setWarehouses(warehousesRes.warehouses);
        } catch (err) {
            console.error('Error fetching products/warehouses:', err);
        }
    };

    const handleCreateTransaction = async (data: TransactionCreateRequest) => {
        try {
            await transactionsApi.createTransaction(data);
            setShowAddModal(false);
            fetchTransactions();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to create transaction';
            throw new Error(errorMsg);
        }
    };

    const filtered = typeFilter === 'all' ? transactions : transactions.filter(t => t.type === typeFilter);
    const sorted = [...filtered].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    const fmtDate = (ts: string) => new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const fmtTime = (ts: string) => new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    const columns: Column<TransactionResponse>[] = [
        {
            key: 'type', label: 'Type', sortable: true,
            render: (tx) => {
                const c = typeConfig[tx.type]; const Icon = c.icon;
                return (<div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: c.bg, color: c.color }}><Icon size={16} /></div>
                    <span className="text-sm font-medium" style={{ color: c.color }}>{c.label}</span>
                </div>);
            },
        },
        { key: 'product_name', label: 'Product', sortable: true, render: (tx) => <span className="text-sm font-medium text-white">{tx.product_name}</span> },
        {
            key: 'quantity', label: 'Qty', sortable: true,
            render: (tx) => (<span className={`text-sm font-bold ${tx.type === 'In' ? 'text-emerald-400' : tx.type === 'Out' ? 'text-rose-400' : 'text-indigo-400'}`}>
                {tx.type === 'In' ? '+' : tx.type === 'Out' ? '-' : '↔'}{tx.quantity}
            </span>),
        },
        {
            key: 'origin_warehouse_name', label: 'Warehouse', sortable: true,
            render: (tx) => {
                if (tx.type === 'In') {
                    return <div className="text-sm text-slate-300">{tx.des_warehouse_name || 'N/A'}</div>;
                } else if (tx.type === 'Out') {
                    return <div className="text-sm text-slate-300">{tx.origin_warehouse_name || 'N/A'}</div>;
                } else {
                    return (
                        <div className="text-sm text-slate-300">
                            {tx.origin_warehouse_name || 'N/A'}
                            <span className="text-slate-500"> → </span>
                            {tx.des_warehouse_name || 'N/A'}
                        </div>
                    );
                }
            },
        },
        { key: 'user_name', label: 'By', render: (tx) => <span className="text-sm text-slate-400">{tx.user_name || 'System'}</span> },
        {
            key: 'timestamp', label: 'Date', sortable: true,
            render: (tx) => (<div><p className="text-sm text-white">{fmtDate(tx.timestamp)}</p><p className="text-xs text-slate-500">{fmtTime(tx.timestamp)}</p></div>),
        },
        { key: 'notes', label: 'Notes', render: (tx) => <span className="text-xs text-slate-500 truncate block max-w-[200px]" title={tx.notes || ''}>{tx.notes || '-'}</span> },
    ];

    return (
        <div>
            <Header title="Stock Movements" subtitle="Track all inventory changes" onAddNew={() => setShowAddModal(true)} addNewLabel="Record Movement" />

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 size={32} className="text-blue-400 animate-spin" />
                </div>
            ) : error ? (
                <div className="text-center py-20">
                    <p className="text-rose-400 text-sm">{error}</p>
                    <button
                        onClick={fetchTransactions}
                        className="mt-4 px-4 py-2 rounded-lg text-sm text-white bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        Retry
                    </button>
                </div>
            ) : (
                <>
                    {/* Summary cards */}
                    <div className="px-8 grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                        {(['In', 'Out', 'Transfer'] as const).map((type, i) => {
                            const c = typeConfig[type]; const Icon = c.icon;
                            const count = transactions.filter(t => t.type === type).length;
                            const totalQty = transactions.filter(t => t.type === type).reduce((s, t) => s + t.quantity, 0);
                            return (
                                <div key={type} className="glass-card glass-card-hover p-5 cursor-pointer opacity-0 animate-fade-in" style={{ animationDelay: `${i * 80}ms`, borderColor: typeFilter === type ? `${c.color}30` : undefined }} onClick={() => setTypeFilter(typeFilter === type ? 'all' : type)}>
                                    <div className="flex items-center justify-between">
                                        <div><p className="text-xs font-medium text-slate-400 mb-1">{c.label}</p><p className="text-2xl font-bold text-white">{count}</p><p className="text-xs text-slate-500 mt-1">{totalQty.toLocaleString()} total units</p></div>
                                        <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: c.bg, color: c.color }}><Icon size={24} /></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Filter */}
                    <div className="px-8 mb-5 flex items-center gap-3 animate-fade-in">
                        <div className="flex items-center gap-2 text-sm text-slate-400"><Filter size={14} /><span>Type:</span></div>
                        {(['all', 'In', 'Out', 'Transfer'] as const).map(f => (
                            <button key={f} onClick={() => setTypeFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${typeFilter === f ? 'bg-accent-blue/20 text-blue-300 border border-blue-500/30' : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10'}`}>
                                {f === 'all' ? 'All' : typeConfig[f].label}
                            </button>
                        ))}
                        <span className="text-xs text-slate-500 ml-auto">{sorted.length} records</span>
                    </div>

                    <div className="px-8 pb-8">
                        <DataTable columns={columns} data={sorted} keyExtractor={(t) => t.id.toString()} emptyMessage="No movements recorded" />
                    </div>
                </>
            )}

            {/* Record Movement Modal */}
            <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Record Stock Movement" size="lg">
                <MovementForm
                    movementType={movementType}
                    setMovementType={setMovementType}
                    products={products}
                    warehouses={warehouses}
                    onSubmit={handleCreateTransaction}
                    onClose={() => setShowAddModal(false)}
                />
            </Modal>
        </div>
    );
}

function MovementForm({
    movementType,
    setMovementType,
    products,
    warehouses,
    onSubmit,
    onClose,
}: {
    movementType: TransactionType;
    setMovementType: (t: TransactionType) => void;
    products: ProductResponse[];
    warehouses: WarehouseSummary[];
    onSubmit: (data: TransactionCreateRequest) => Promise<void>;
    onClose: () => void;
}) {
    const [formData, setFormData] = useState<TransactionCreateRequest>({
        product_id: 0,
        type: movementType,
        quantity: 1,
        origin_warehouse_id: null,
        des_warehouse_id: null,
        notes: null,
    });
    const [submitting, setSubmitting] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    // Update type when movementType changes
    useEffect(() => {
        setFormData(prev => ({ ...prev, type: movementType }));
    }, [movementType]);

    const validateForm = (): boolean => {
        setValidationError(null);

        if (!formData.product_id || formData.product_id === 0) {
            setValidationError('Please select a product');
            return false;
        }

        if (formData.quantity <= 0) {
            setValidationError('Quantity must be greater than 0');
            return false;
        }

        // Validate based on transaction type
        if (formData.type === 'In') {
            if (!formData.des_warehouse_id) {
                setValidationError('Destination warehouse is required for Stock In');
                return false;
            }
        } else if (formData.type === 'Out') {
            if (!formData.origin_warehouse_id) {
                setValidationError('Source warehouse is required for Stock Out');
                return false;
            }
        } else if (formData.type === 'Transfer') {
            if (!formData.origin_warehouse_id || !formData.des_warehouse_id) {
                setValidationError('Both source and destination warehouses are required for Transfer');
                return false;
            }
            if (formData.origin_warehouse_id === formData.des_warehouse_id) {
                setValidationError('Source and destination warehouses must be different');
                return false;
            }
        }

        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit(formData);
            // Reset form on success
            setFormData({
                product_id: 0,
                type: movementType,
                quantity: 1,
                origin_warehouse_id: null,
                des_warehouse_id: null,
                notes: null,
            });
        } catch (err) {
            setValidationError(err instanceof Error ? err.message : 'Failed to create transaction');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-5">
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-3">Movement Type</label>
                <div className="grid grid-cols-3 gap-3">
                    {(['In', 'Out', 'Transfer'] as const).map(type => {
                        const c = typeConfig[type]; const Icon = c.icon;
                        return (
                            <button key={type} type="button" onClick={() => setMovementType(type)}
                                className={`p-4 rounded-xl text-center transition-all ${movementType === type ? 'ring-2' : ''}`}
                                style={{ background: movementType === type ? c.bg : 'rgba(255,255,255,0.03)', border: `1px solid ${movementType === type ? `${c.color}30` : 'rgba(255,255,255,0.05)'}` }}>
                                <Icon size={20} className="mx-auto mb-2" style={{ color: c.color }} />
                                <p className="text-sm font-medium" style={{ color: movementType === type ? c.color : '#94a3b8' }}>{c.label}</p>
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-2">Product *</label>
                    <select
                        required
                        value={formData.product_id}
                        onChange={(e) => setFormData({ ...formData, product_id: parseInt(e.target.value) })}
                        className="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
                    >
                        <option value="0" style={{ background: '#1e293b', color: 'white' }}>Select product</option>
                        {products.map(p => <option key={p.id} value={p.id} style={{ background: '#1e293b', color: 'white' }}>{p.name} ({p.sku})</option>)}
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-2">Quantity *</label>
                    <input
                        type="number"
                        required
                        min={0}
                        value={formData.quantity}
                        onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
                        className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                        placeholder="Enter quantity"
                    />
                </div>
            </div>

            <div className={`grid gap-4 ${movementType === 'Transfer' ? 'grid-cols-2' : 'grid-cols-1'}`}>
                {(movementType === 'Out' || movementType === 'Transfer') && (
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">
                            {movementType === 'Transfer' ? 'Source Warehouse *' : 'Warehouse *'}
                        </label>
                        <select
                            required
                            value={formData.origin_warehouse_id || ''}
                            onChange={(e) => setFormData({ ...formData, origin_warehouse_id: e.target.value ? parseInt(e.target.value) : null })}
                            className="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
                        >
                            <option value="" style={{ background: '#1e293b', color: 'white' }}>Select origin</option>
                            {warehouses.map(w => <option key={w.id} value={w.id} style={{ background: '#1e293b', color: 'white' }}>{w.name}</option>)}
                        </select>
                    </div>
                )}
                {(movementType === 'In' || movementType === 'Transfer') && (
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">
                            {movementType === 'Transfer' ? 'Destination Warehouse *' : 'Warehouse *'}
                        </label>
                        <select
                            required
                            value={formData.des_warehouse_id || ''}
                            onChange={(e) => setFormData({ ...formData, des_warehouse_id: e.target.value ? parseInt(e.target.value) : null })}
                            className="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
                        >
                            <option value="" style={{ background: '#1e293b', color: 'white' }}>Select destination</option>
                            {warehouses.map(w => <option key={w.id} value={w.id} style={{ background: '#1e293b', color: 'white' }}>{w.name}</option>)}
                        </select>
                    </div>
                )}
            </div>

            <div>
                <label className="block text-xs font-medium text-slate-400 mb-2">Notes</label>
                <textarea
                    value={formData.notes || ''}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value || null })}
                    className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30 resize-none"
                    rows={3}
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    placeholder="Add notes..."
                />
            </div>

            {validationError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
                    {validationError}
                </div>
            )}

            <div className="flex justify-end gap-3 pt-3">
                <button
                    type="button"
                    onClick={onClose}
                    disabled={submitting}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    style={{
                        background: `linear-gradient(135deg, ${typeConfig[movementType].color}, ${movementType === 'In' ? '#059669' : movementType === 'Out' ? '#e11d48' : '#4f46e5'})`,
                        boxShadow: `0 4px 16px ${typeConfig[movementType].color}40`
                    }}
                >
                    {submitting && <Loader2 size={16} className="animate-spin" />}
                    {submitting ? 'Recording...' : `Record ${typeConfig[movementType].label}`}
                </button>
            </div>
        </form>
    );
}
