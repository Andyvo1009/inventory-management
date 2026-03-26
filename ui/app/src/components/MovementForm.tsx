import { useEffect, useState, type CSSProperties, type ComponentType } from 'react';
import {
  ArrowLeftRight,
  Loader2,
  PackagePlus,
  RefreshCcw,
  ShoppingCart,
  SlidersHorizontal,
} from 'lucide-react';

import type {
  OperationType,
  ProductResponse,
  WarehouseSummary,
} from '../types';

const operationConfig: Record<OperationType, { icon: ComponentType<{ size?: number; className?: string; style?: CSSProperties }>; color: string; bg: string; label: string }> = {
  Purchase: { icon: PackagePlus, color: '#10b981', bg: 'rgba(16,185,129,0.1)', label: 'Purchase' },
  Sale: { icon: ShoppingCart, color: '#f43f5e', bg: 'rgba(244,63,94,0.1)', label: 'Sale' },
  Transfer: { icon: ArrowLeftRight, color: '#6366f1', bg: 'rgba(99,102,241,0.1)', label: 'Transfer' },
  Adjustment: { icon: SlidersHorizontal, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: 'Adjustment' },
  Return: { icon: RefreshCcw, color: '#22c55e', bg: 'rgba(34,197,94,0.1)', label: 'Return' },
};

export interface OperationFormData {
  operation_type: OperationType;
  product_id: number;
  quantity: number;
  source_warehouse_id: number | null;
  destination_warehouse_id: number | null;
  note: string | null;
  adjustment_direction: 'In' | 'Out' | null;
}

interface MovementFormProps {
  operationType: OperationType;
  setOperationType: (t: OperationType) => void;
  products: ProductResponse[];
  warehouses: WarehouseSummary[];
  onSubmit: (data: OperationFormData) => Promise<void>;
  onClose: () => void;
}

export default function MovementForm({
  operationType,
  setOperationType,
  products,
  warehouses,
  onSubmit,
  onClose,
}: MovementFormProps) {
  const [formData, setFormData] = useState<OperationFormData>({
    operation_type: operationType,
    product_id: 0,
    quantity: 1,
    source_warehouse_id: null,
    destination_warehouse_id: null,
    note: null,
    adjustment_direction: null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      operation_type: operationType,
      source_warehouse_id: operationType === 'Purchase' || operationType === 'Return' ? null : prev.source_warehouse_id,
      destination_warehouse_id: operationType === 'Sale' ? null : prev.destination_warehouse_id,
      adjustment_direction: operationType === 'Adjustment' ? prev.adjustment_direction : null,
    }));
  }, [operationType]);

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

    if (formData.operation_type === 'Purchase' || formData.operation_type === 'Return') {
      if (!formData.destination_warehouse_id) {
        setValidationError('Destination warehouse is required');
        return false;
      }
    } else if (formData.operation_type === 'Sale') {
      if (!formData.source_warehouse_id) {
        setValidationError('Source warehouse is required');
        return false;
      }
    } else if (formData.operation_type === 'Transfer') {
      if (!formData.source_warehouse_id || !formData.destination_warehouse_id) {
        setValidationError('Both source and destination warehouses are required');
        return false;
      }
      if (formData.source_warehouse_id === formData.destination_warehouse_id) {
        setValidationError('Source and destination warehouses must be different');
        return false;
      }
    } else if (formData.operation_type === 'Adjustment') {
      if (!formData.source_warehouse_id && !formData.destination_warehouse_id) {
        setValidationError('Warehouse is required for adjustment');
        return false;
      }
      if (!formData.adjustment_direction) {
        setValidationError('Adjustment direction is required');
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
      setFormData({
        operation_type: operationType,
        product_id: 0,
        quantity: 1,
        source_warehouse_id: null,
        destination_warehouse_id: null,
        note: null,
        adjustment_direction: null,
      });
    } catch (err) {
      setValidationError(err instanceof Error ? err.message : 'Failed to create operation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-3">Operation Type</label>
        <div className="grid grid-cols-2 gap-3">
          {(['Purchase', 'Sale', 'Transfer', 'Adjustment', 'Return'] as const).map((type) => {
            const c = operationConfig[type];
            const Icon = c.icon;
            return (
              <button
                key={type}
                type="button"
                onClick={() => setOperationType(type)}
                className={`p-4 rounded-xl text-center transition-all ${operationType === type ? 'ring-2' : ''}`}
                style={{
                  background: operationType === type ? c.bg : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${operationType === type ? `${c.color}30` : 'rgba(255,255,255,0.05)'}`,
                }}
              >
                <Icon size={20} className="mx-auto mb-2" style={{ color: c.color }} />
                <p className="text-sm font-medium" style={{ color: operationType === type ? c.color : '#94a3b8' }}>
                  {c.label}
                </p>
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
            {products.map((p) => (
              <option key={p.id} value={p.id} style={{ background: '#1e293b', color: 'white' }}>
                {p.name} ({p.sku})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-2">Quantity *</label>
          <input
            type="number"
            required
            min={1}
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
            placeholder="Enter quantity"
          />
        </div>
      </div>

      <div className={`grid gap-4 ${operationType === 'Transfer' ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {(operationType === 'Sale' || operationType === 'Transfer' || operationType === 'Adjustment') && (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">
              {operationType === 'Transfer' ? 'Source Warehouse *' : 'Warehouse *'}
            </label>
            <select
              required
              value={formData.source_warehouse_id || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  source_warehouse_id: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
            >
              <option value="" style={{ background: '#1e293b', color: 'white' }}>
                {operationType === 'Adjustment' ? 'Select warehouse' : 'Select origin'}
              </option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id} style={{ background: '#1e293b', color: 'white' }}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {(operationType === 'Purchase' || operationType === 'Transfer' || operationType === 'Return') && (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">
              {operationType === 'Transfer' ? 'Destination Warehouse *' : 'Warehouse *'}
            </label>
            <select
              required
              value={formData.destination_warehouse_id || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  destination_warehouse_id: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="w-full px-4 py-3 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500/30"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
            >
              <option value="" style={{ background: '#1e293b', color: 'white' }}>Select destination</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id} style={{ background: '#1e293b', color: 'white' }}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {operationType === 'Adjustment' && (
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-2">Adjustment Direction *</label>
          <div className="grid grid-cols-2 gap-3">
            {(['In', 'Out'] as const).map((dir) => (
              <button
                key={dir}
                type="button"
                onClick={() =>
                  setFormData({
                    ...formData,
                    adjustment_direction: dir,
                    destination_warehouse_id: dir === 'In' ? formData.source_warehouse_id ?? formData.destination_warehouse_id : null,
                    source_warehouse_id: dir === 'Out' ? formData.source_warehouse_id ?? formData.destination_warehouse_id : formData.source_warehouse_id,
                  })
                }
                className={`p-3 rounded-xl text-sm font-medium transition-all ${formData.adjustment_direction === dir ? 'ring-2' : ''}`}
                style={{
                  background: formData.adjustment_direction === dir ? 'rgba(99,102,241,0.16)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${formData.adjustment_direction === dir ? 'rgba(99,102,241,0.4)' : 'rgba(255,255,255,0.05)'}`,
                  color: formData.adjustment_direction === dir ? '#a5b4fc' : '#94a3b8',
                }}
              >
                {dir === 'In' ? 'Increase Stock' : 'Decrease Stock'}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <label className="block text-xs font-medium text-slate-400 mb-2">note</label>
        <textarea
          value={formData.note || ''}
          onChange={(e) => setFormData({ ...formData, note: e.target.value || null })}
          className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-blue-500/30 resize-none"
          rows={3}
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
          placeholder="Add note..."
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
            background: `linear-gradient(135deg, ${operationConfig[operationType].color}, #334155)`,
            boxShadow: `0 4px 16px ${operationConfig[operationType].color}40`,
          }}
        >
          {submitting && <Loader2 size={16} className="animate-spin" />}
          {submitting ? 'Creating...' : `Create Pending ${operationConfig[operationType].label}`}
        </button>
      </div>
    </form>
  );
}
