import { useState, useEffect } from 'react';
import {
    Warehouse as WarehouseIcon,
    MapPin,
    Package,
    Layers,
    Eye,
    Loader2,
    Trash2,
} from 'lucide-react';
import Header from '../components/Header';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import ErrorBox from '../components/ErrorBox';
import { useAuth } from '../context/AuthContext';
import type {
    WarehouseSummary,
    WarehouseDetailResponse,
    WarehouseCreateRequest,
    WarehouseUpdateRequest,
} from '../types';
import * as warehousesApi from '../api/warehouses';
import { getErrorMessage } from '../api/client';

export default function Warehouses() {
    const { isAdmin } = useAuth();
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [confirmDialog, setConfirmDialog] = useState<{
        isOpen: boolean;
        warehouseId: number | null;
    }>({ isOpen: false, warehouseId: null });
    const [selectedWarehouse, setSelectedWarehouse] = useState<WarehouseDetailResponse | null>(null);

    // Data state
    const [warehouses, setWarehouses] = useState<WarehouseSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);

    // Form state for create
    const [createForm, setCreateForm] = useState<WarehouseCreateRequest>({
        name: '',
        location: null,
    });

    // Form state for update
    const [updateForm, setUpdateForm] = useState<WarehouseUpdateRequest>({
        name: '',
        location: null,
    });

    const [submitting, setSubmitting] = useState(false);

    // Fetch warehouses
    useEffect(() => {
        fetchWarehouses();
    }, []);

    const fetchWarehouses = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await warehousesApi.listWarehouses();
            setWarehouses(response.warehouses);
        } catch (err) {
            const errorMsg = getErrorMessage(err, 'Failed to load warehouses');
            setError(errorMsg);
            console.error('Error fetching warehouses:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateWarehouse = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setActionError(null);
        try {
            await warehousesApi.createWarehouse(createForm);
            setShowAddModal(false);
            setCreateForm({ name: '', location: null });
            fetchWarehouses();
        } catch (err) {
            const errorMsg = getErrorMessage(err, 'Failed to create warehouse');
            setActionError(errorMsg);
            console.error('Error creating warehouse:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const handleUpdateWarehouse = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedWarehouse) return;

        setSubmitting(true);
        setActionError(null);
        try {
            await warehousesApi.updateWarehouse(selectedWarehouse.id, updateForm);
            setShowEditModal(false);
            setSelectedWarehouse(null);
            fetchWarehouses();
            if (showDetailModal) {
                // Refresh detail view
                const updated = await warehousesApi.getWarehouseById(selectedWarehouse.id);
                setSelectedWarehouse(updated);
            }
        } catch (err) {
            const errorMsg = getErrorMessage(err, 'Failed to update warehouse');
            setActionError(errorMsg);
            console.error('Error updating warehouse:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteWarehouse = async (warehouseId: number) => {
        setConfirmDialog({ isOpen: true, warehouseId });
    };

    const confirmDeleteWarehouse = async () => {
        if (!confirmDialog.warehouseId) return;

        setConfirmDialog({ isOpen: false, warehouseId: null });
        setActionError(null);
        try {
            await warehousesApi.deleteWarehouse(confirmDialog.warehouseId);
            fetchWarehouses();
            if (showDetailModal) {
                setShowDetailModal(false);
                setSelectedWarehouse(null);
            }
        } catch (err) {
            const errorMsg = getErrorMessage(err, 'Failed to delete warehouse');
            setActionError(errorMsg);
            console.error('Error deleting warehouse:', err);
        }
    };

    const openDetail = async (w: WarehouseSummary) => {
        setActionError(null);
        try {
            const details = await warehousesApi.getWarehouseById(w.id);
            setSelectedWarehouse(details);
            setShowDetailModal(true);
        } catch (err) {
            const errorMsg = getErrorMessage(err, 'Failed to load warehouse details');
            setActionError(errorMsg);
            console.error('Error fetching warehouse details:', err);
        }
    };

    const openEdit = (w: WarehouseDetailResponse) => {
        setSelectedWarehouse(w);
        setUpdateForm({
            name: w.name,
            location: w.location,
        });
        setShowEditModal(true);
    };

    const colors = [
        { gradient: 'linear-gradient(135deg, #3b82f6, #6366f1)', glow: 'rgba(59,130,246,0.15)' },
        { gradient: 'linear-gradient(135deg, #8b5cf6, #a855f7)', glow: 'rgba(139,92,246,0.15)' },
        { gradient: 'linear-gradient(135deg, #06b6d4, #10b981)', glow: 'rgba(6,182,212,0.15)' },
    ];

    if (loading) {
        return (
            <div>
                <Header title="Warehouses" subtitle="Loading..." />
                <div className="flex items-center justify-center py-20">
                    <Loader2 size={32} className="text-blue-400 animate-spin" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <Header title="Warehouses" subtitle="Error loading warehouses" />
                <div className="mx-auto max-w-2xl px-8 py-20">
                    <ErrorBox
                        message={error}
                        title="Unable to load warehouses"
                        className="mx-auto"
                        onClose={() => setError(null)}
                    />
                    <button
                        onClick={fetchWarehouses}
                        className="mt-4 px-4 py-2 rounded-lg text-sm text-white bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div>
            <Header
                title="Warehouses"
                subtitle={`${warehouses.length} locations active`}
                onAddNew={isAdmin ? () => setShowAddModal(true) : undefined}
                addNewLabel="Add Warehouse"
            />

            {actionError && (
                <div className="px-8 pb-4">
                    <ErrorBox
                        message={actionError}
                        title="Request failed"
                        onClose={() => setActionError(null)}
                    />
                </div>
            )}

            {/* Warehouse Cards */}
            <div className="px-8 pb-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {warehouses.map((w, i) => {
                    const color = colors[i % colors.length];
                    return (
                        <div
                            key={w.id}
                            className="glass-card glass-card-hover overflow-hidden cursor-pointer opacity-0 animate-fade-in"
                            style={{ animationDelay: `${i * 100}ms` }}
                            onClick={() => openDetail(w)}
                        >
                            {/* Color accent bar */}
                            <div className="h-1" style={{ background: color.gradient }} />

                            <div className="p-6">
                                {/* Header */}
                                <div className="flex items-start justify-between mb-5">
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-12 h-12 rounded-xl flex items-center justify-center"
                                            style={{ background: color.glow }}
                                        >
                                            <WarehouseIcon size={24} style={{ color: color.gradient.includes('#3b82f6') ? '#3b82f6' : color.gradient.includes('#8b5cf6') ? '#8b5cf6' : '#06b6d4' }} />
                                        </div>
                                        <div>
                                            <h3 className="text-base font-bold text-white">{w.name}</h3>
                                            <div className="flex items-center gap-1 mt-1 text-xs text-slate-500">
                                                <MapPin size={12} />
                                                <span>{w.location || 'No location'}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-1">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); openDetail(w); }}
                                            className="p-2 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-blue-400/10 transition-all"
                                        >
                                            <Eye size={16} />
                                        </button>
                                        {isAdmin && (
                                            <button
                                                onClick={(e) => { 
                                                    e.stopPropagation(); 
                                                    handleDeleteWarehouse(w.id);
                                                }}
                                                className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 transition-all"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* Stats */}
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
                                        <div className="flex items-center gap-2 text-slate-400 mb-2">
                                            <Package size={14} />
                                            <span className="text-xs font-medium">Products</span>
                                        </div>
                                        <p className="text-2xl font-bold text-white">{w.total_unique_products}</p>
                                    </div>
                                    <div className="p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
                                        <div className="flex items-center gap-2 text-slate-400 mb-2">
                                            <Layers size={14} />
                                            <span className="text-xs font-medium">Total Units</span>
                                        </div>
                                        <p className="text-2xl font-bold text-white">{w.total_stock.toLocaleString()}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Add Warehouse Modal */}
            <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add New Warehouse">
                <form onSubmit={handleCreateWarehouse} className="space-y-5">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Warehouse Name *</label>
                        <input
                            type="text"
                            required
                            value={createForm.name}
                            onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                            placeholder="e.g., Warehouse Delta"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Location</label>
                        <input
                            type="text"
                            value={createForm.location || ''}
                            onChange={(e) => setCreateForm({ ...createForm, location: e.target.value || null })}
                            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                            placeholder="Full address or description"
                        />
                    </div>
                    <div className="flex justify-end gap-3 pt-3">
                        <button
                            type="button"
                            onClick={() => setShowAddModal(false)}
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
                            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)', boxShadow: '0 4px 16px rgba(59,130,246,0.3)' }}
                        >
                            {submitting && <Loader2 size={16} className="animate-spin" />}
                            {submitting ? 'Creating...' : 'Create Warehouse'}
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Edit Warehouse Modal */}
            <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title="Edit Warehouse">
                <form onSubmit={handleUpdateWarehouse} className="space-y-5">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Warehouse Name</label>
                        <input
                            type="text"
                            value={updateForm.name || ''}
                            onChange={(e) => setUpdateForm({ ...updateForm, name: e.target.value })}
                            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                            placeholder="Warehouse name"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Location</label>
                        <input
                            type="text"
                            value={updateForm.location || ''}
                            onChange={(e) => setUpdateForm({ ...updateForm, location: e.target.value || null })}
                            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                            placeholder="Full address or description"
                        />
                    </div>
                    <div className="flex justify-end gap-3 pt-3">
                        <button
                            type="button"
                            onClick={() => setShowEditModal(false)}
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
                            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)', boxShadow: '0 4px 16px rgba(59,130,246,0.3)' }}
                        >
                            {submitting && <Loader2 size={16} className="animate-spin" />}
                            {submitting ? 'Updating...' : 'Update Warehouse'}
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Warehouse Detail Modal */}
            <Modal
                isOpen={showDetailModal}
                onClose={() => { setShowDetailModal(false); setSelectedWarehouse(null); }}
                title="Warehouse Details"
                size="lg"
            >
                {selectedWarehouse && (
                    <div className="space-y-6">
                        <div className="flex items-start gap-4">
                            <div
                                className="w-14 h-14 rounded-xl flex items-center justify-center"
                                style={{ background: 'rgba(139,92,246,0.12)', color: '#8b5cf6' }}
                            >
                                <WarehouseIcon size={28} />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-xl font-bold text-white">{selectedWarehouse.name}</h3>
                                <div className="flex items-center gap-1.5 mt-1 text-sm text-slate-400">
                                    <MapPin size={14} />
                                    {selectedWarehouse.location || 'No location specified'}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl" style={{ background: 'rgba(59,130,246,0.08)' }}>
                                <p className="text-xs text-slate-400 mb-1">Products Stored</p>
                                <p className="text-2xl font-bold text-blue-400">{selectedWarehouse.total_unique_products}</p>
                            </div>
                            <div className="p-4 rounded-xl" style={{ background: 'rgba(16,185,129,0.08)' }}>
                                <p className="text-xs text-slate-400 mb-1">Total Units</p>
                                <p className="text-2xl font-bold text-emerald-400">{selectedWarehouse.total_stock.toLocaleString()}</p>
                            </div>
                        </div>

                        {selectedWarehouse.products.length > 0 ? (
                            <div>
                                <h4 className="text-sm font-semibold text-slate-300 mb-3">All Products</h4>
                                <div className="space-y-2 max-h-80 overflow-y-auto">
                                    {selectedWarehouse.products.map(p => (
                                        <div
                                            key={p.product_id}
                                            className="flex items-center justify-between px-4 py-3 rounded-xl"
                                            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                                        >
                                            <div>
                                                <p className="text-sm font-medium text-white">{p.product_name}</p>
                                                <p className="text-xs text-slate-500 mt-0.5 font-mono">{p.product_sku}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-lg font-bold text-white">{p.quantity}</p>
                                                <p className="text-xs text-slate-500">units</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <Package size={40} className="mx-auto text-slate-600 mb-3" />
                                <p className="text-sm text-slate-500">No products in this warehouse yet</p>
                            </div>
                        )}

                        {/* Action buttons */}
                        {isAdmin && (
                            <div className="flex gap-3 pt-4 border-t border-white/5">
                                <button
                                    onClick={() => {
                                        setShowDetailModal(false);
                                        openEdit(selectedWarehouse);
                                    }}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:scale-[1.02]"
                                    style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
                                >
                                    Edit Warehouse
                                </button>
                                <button
                                    onClick={() => handleDeleteWarehouse(selectedWarehouse.id)}
                                    className="px-4 py-2.5 rounded-xl text-sm font-medium text-rose-400 hover:bg-rose-400/10 transition-all"
                                    style={{ border: '1px solid rgba(244,63,94,0.3)' }}
                                >
                                    Delete
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </Modal>

            {/* Confirmation Dialog */}
            <ConfirmDialog
                isOpen={confirmDialog.isOpen}
                title="Delete Warehouse"
                message="Are you sure you want to delete this warehouse? This will also delete related stock records."
                onConfirm={confirmDeleteWarehouse}
                onCancel={() => setConfirmDialog({ isOpen: false, warehouseId: null })}
            />
        </div>
    );
}
