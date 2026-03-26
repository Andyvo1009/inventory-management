import { useEffect, useState } from 'react';
import { ArrowDownLeft, ArrowUpRight, Filter, Loader2, Search, X } from 'lucide-react';

import Header from '../components/Header';
import DataTable, { type Column } from '../components/DataTable';
import FilterSelect from '../components/FilterSelect';
import type { TransactionResponse, WarehouseSummary, ProductResponse } from '../types';
import * as transactionsApi from '../api/transactions';
import * as warehousesApi from '../api/warehouses';
import * as productsApi from '../api/products';
import { ApiError } from '../api/client';

const typeConfig = {
  In: { icon: ArrowDownLeft, color: '#10b981', bg: 'rgba(16,185,129,0.1)', label: 'Stock In' },
  Out: { icon: ArrowUpRight, color: '#f43f5e', bg: 'rgba(244,63,94,0.1)', label: 'Stock Out' },
};

export default function StockMovements() {
  const [typeFilter, setTypeFilter] = useState<'In' | 'Out' | 'all'>('all');
  const [warehouseFilter, setWarehouseFilter] = useState<number | null>(null);
  const [productFilter, setProductFilter] = useState<number | null>(null);
  const [searchText, setSearchText] = useState('');

  const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseSummary[]>([]);
  const [products, setProducts] = useState<ProductResponse[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch reference data once on mount
  useEffect(() => {
    fetchReferenceData();
  }, []);

  const fetchReferenceData = async () => {
    try {
      const [warehousesRes, productsRes] = await Promise.all([
        warehousesApi.listWarehouses(),
        productsApi.listProducts(null, null, 100, 0),
      ]);
      setWarehouses(warehousesRes.warehouses);
      setProducts(productsRes.products);
    } catch (err) {
      console.error('Failed to load filter data:', err);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [typeFilter, warehouseFilter, productFilter]);

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await transactionsApi.listTransactions(
        typeFilter === 'all' ? null : typeFilter,
        warehouseFilter,
        productFilter,
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

  const q = searchText.trim().toLowerCase();
  const filtered = q
    ? transactions.filter(
        (t) =>
          t.product_name.toLowerCase().includes(q) ||
          (t.note ?? '').toLowerCase().includes(q) ||
          (t.user_name ?? '').toLowerCase().includes(q)
      )
    : transactions;

  const sorted = [...filtered].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const hasActiveFilters =
    typeFilter !== 'all' || warehouseFilter !== null || productFilter !== null || searchText !== '';

  const clearFilters = () => {
    setTypeFilter('all');
    setWarehouseFilter(null);
    setProductFilter(null);
    setSearchText('');
  };

  const fmtDate = (ts: string) =>
    new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const fmtTime = (ts: string) =>
    new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const columns: Column<TransactionResponse>[] = [
    {
      key: 'type',
      label: 'Type',
      sortable: true,
      render: (tx) => {
        const c = tx.type === 'In' ? typeConfig.In : typeConfig.Out;
        const Icon = c.icon;
        return (
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: c.bg, color: c.color }}>
              <Icon size={16} />
            </div>
            <span className="text-sm font-medium" style={{ color: c.color }}>{c.label}</span>
          </div>
        );
      },
    },
    {
      key: 'product_name',
      label: 'Product',
      sortable: true,
      render: (tx) => <span className="text-sm font-medium text-white">{tx.product_name}</span>,
    },
    {
      key: 'id',
      label: 'Operation',
      sortable: true,
      render: (op) => (
        <div>
          <p className="text-sm font-medium text-white">#{op.operation_id}</p>
        </div>
      ),
    },
    {
      key: 'quantity',
      label: 'Qty',
      sortable: true,
      render: (tx) => (
        <span className={`text-sm font-bold ${tx.type === 'In' ? 'text-emerald-400' : 'text-rose-400'}`}>
          {tx.type === 'In' ? '+' : '-'}
          {tx.quantity}
        </span>
      ),
    },
    {
      key: 'origin_warehouse_name',
      label: 'Warehouse',
      sortable: true,
      render: (tx) => {
        if (tx.type === 'In') {
          return <div className="text-sm text-slate-300">{tx.des_warehouse_name || 'N/A'}</div>;
        }
        if (tx.type === 'Out') {
          return <div className="text-sm text-slate-300">{tx.origin_warehouse_name || 'N/A'}</div>;
        }
        return <div className="text-sm text-slate-300">N/A</div>;
      },
    },
    {
      key: 'user_name',
      label: 'By',
      render: (tx) => <span className="text-sm text-slate-400">{tx.user_name || 'System'}</span>,
    },
    {
      key: 'timestamp',
      label: 'Date',
      sortable: true,
      render: (tx) => (
        <div>
          <p className="text-sm text-white">{fmtDate(tx.timestamp)}</p>
          <p className="text-xs text-slate-500">{fmtTime(tx.timestamp)}</p>
        </div>
      ),
    },
    {
      key: 'note',
      label: 'Note',
      render: (tx) =>
        tx.note ? (
          <span className="text-xs text-slate-400 whitespace-pre-wrap break-words block max-w-xs">
            {tx.note}
          </span>
        ) : (
          <span className="text-xs text-slate-600">—</span>
        ),
    },
    {
      key: 'movement_status',
      label: 'Status',
      sortable: true,
      render: (tx) => {
        const statusConfig = {
          Completed: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
          Pending: 'text-amber-300 bg-amber-300/10 border-amber-300/30',
          Failed: 'text-rose-400 bg-rose-400/10 border-rose-400/30',
          Draft: 'text-slate-300 bg-slate-400/10 border-slate-400/30',
        } as const;
        const color = statusConfig[tx.movement_status] ?? 'text-slate-300 bg-slate-400/10 border-slate-400/30';
        return <span className={`px-2 py-1 rounded-md border text-xs font-medium ${color}`}>{tx.movement_status}</span>;
      },
    }
  ];

  return (
    <div>
      <Header title="Transactions History" subtitle="Read-only audit trail of completed movements" />

      {/* Stat cards — only shown when data is loaded */}
      {!loading && !error && (
        <div className="px-8 grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {(['In', 'Out'] as const).map((type, i) => {
            const c = typeConfig[type];
            const Icon = c.icon;
            const count = transactions.filter((t) => t.type === type).length;
            const totalQty = transactions.filter((t) => t.type === type).reduce((s, t) => s + t.quantity, 0);
            return (
              <div
                key={type}
                className="glass-card glass-card-hover p-5 cursor-pointer opacity-0 animate-fade-in"
                style={{ animationDelay: `${i * 80}ms`, borderColor: typeFilter === type ? `${c.color}30` : undefined }}
                onClick={() => setTypeFilter(typeFilter === type ? 'all' : type)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-400 mb-1">{c.label}</p>
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-xs text-slate-500 mt-1">{totalQty.toLocaleString()} total units</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: c.bg, color: c.color }}>
                    <Icon size={24} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Filter bar — always rendered so dropdowns populate independently of transaction loading */}
      <div className="px-8 mb-5 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Filter size={14} />
        </div>

        {/* Type filter */}
        {(['all', 'In', 'Out'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setTypeFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${typeFilter === f ? 'bg-accent-blue/20 text-blue-300 border border-blue-500/30' : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10'}`}
          >
            {f === 'all' ? 'All' : typeConfig[f].label}
          </button>
        ))}

        <div className="w-px h-4 bg-white/10" />

        {/* Warehouse filter */}
        <FilterSelect
          value={warehouseFilter}
          onChange={(v) => setWarehouseFilter(v !== null ? Number(v) : null)}
          options={warehouses.map((w) => ({ value: w.id, label: w.name }))}
          placeholder="All Warehouses"
        />

        {/* Product filter */}
        <FilterSelect
          value={productFilter}
          onChange={(v) => setProductFilter(v !== null ? Number(v) : null)}
          options={products.map((p) => ({ value: p.id, label: p.name }))}
          placeholder="All Products"
        />

        <div className="w-px h-4 bg-white/10" />

        {/* Text search — filters by product, note, or user */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs transition-all ${searchText ? 'border-blue-500/40 bg-blue-500/10' : 'border-transparent bg-white/5 hover:bg-white/10'}`}>
          <Search size={12} className="text-slate-400 shrink-0" />
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search product, note, user…"
            className="bg-transparent text-slate-300 placeholder-slate-500 outline-none w-40 focus:w-52 transition-all duration-200"
          />
          {searchText && (
            <button onClick={() => setSearchText('')} className="text-slate-500 hover:text-slate-300 transition-colors">
              <X size={10} />
            </button>
          )}
        </div>

        {/* Clear all filters button */}
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-slate-400 border border-transparent hover:bg-white/10 transition-all flex items-center gap-1.5"
          >
            <X size={12} />
            Clear all
          </button>
        )}

        <span className="text-xs text-slate-500 ml-auto">
          {!loading && `${sorted.length} records`}
        </span>
      </div>

      {/* Table area */}
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
        <div className="px-8 pb-8">
          <DataTable
            columns={columns}
            data={sorted}
            keyExtractor={(t) => t.id.toString()}
            emptyMessage="No transaction history found"
          />
        </div>
      )}
    </div>
  );
}
