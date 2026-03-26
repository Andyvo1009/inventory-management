import { useCallback, useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Filter, Loader2, X } from 'lucide-react';

import Header from '../components/Header';
import Modal from '../components/Modal';
import MovementForm, { type OperationFormData } from '../components/MovementForm';
import ErrorBox from '../components/ErrorBox';
import FilterSelect from '../components/FilterSelect';

import type {
  OperationCreateRequest,
  OperationItemResponse,
  OperationResponse,
  OperationStatus,
  OperationType,
  ProductResponse,
  WarehouseSummary,
} from '../types';
import { getErrorMessage } from '../api/client';
import * as operationsApi from '../api/operations';
import * as productsApi from '../api/products';
import * as warehousesApi from '../api/warehouses';

const OPERATION_TYPES: OperationType[] = ['Purchase', 'Sale', 'Transfer', 'Adjustment', 'Return'];
const OPERATION_STATUSES: OperationStatus[] = ['Draft', 'Pending', 'In_Transit', 'Completed', 'Cancelled', 'Failed'];
const STATUS_LABELS: Record<OperationStatus, string> = {
  Draft: 'Draft', Pending: 'Pending', In_Transit: 'In Transit',
  Completed: 'Completed', Cancelled: 'Cancelled', Failed: 'Failed',
};

export default function Operations() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [operationType, setOperationType] = useState<OperationType>('Purchase');

  // Filter state
  const [typeFilter, setTypeFilter] = useState<OperationType | null>(null);
  const [statusFilter, setStatusFilter] = useState<OperationStatus | null>(null);
  const [warehouseFilter, setWarehouseFilter] = useState<number | null>(null);

  const [operations, setOperations] = useState<OperationResponse[]>([]);
  const [products, setProducts] = useState<ProductResponse[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseSummary[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [processingTransactionId, setProcessingTransactionId] = useState<number | null>(null);
  const [expandedOperationId, setExpandedOperationId] = useState<number | null>(null);
  const [showReceiveConfirmModal, setShowReceiveConfirmModal] = useState(false);
  const [receiveConfirmValue, setReceiveConfirmValue] = useState<number>(0);
  const [selectedInTransaction, setSelectedInTransaction] = useState<{
    operationId: number;
    transactionId: number;
    expectedQty: number;
  } | null>(null);

  const fetchOperations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await operationsApi.listOperations(typeFilter, statusFilter, warehouseFilter, 100, 0);
      setOperations(response.operations);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load operations'));
    } finally {
      setLoading(false);
    }
  }, [typeFilter, statusFilter, warehouseFilter]);

  useEffect(() => {
    fetchOperations();
  }, [fetchOperations]);

  useEffect(() => {
    fetchProductsAndWarehouses();
  }, []);

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

  const mapOperationToPayload = (data: OperationFormData): OperationCreateRequest => {
    if (data.operation_type === 'Purchase' || data.operation_type === 'Return') {
      return {
        operation_type: data.operation_type,
        source_warehouse_id: null,
        destination_warehouse_id: data.destination_warehouse_id,
        reference_code: null,
        note: data.note ?? null,
        status: 'Pending',
        items: [
          {
            product_id: data.product_id,
            type: 'In',
            warehouse_id: data.destination_warehouse_id as number,
            quantity: data.quantity,
          },
        ],
      };
    }

    if (data.operation_type === 'Sale') {
      return {
        operation_type: data.operation_type,
        source_warehouse_id: data.source_warehouse_id,
        destination_warehouse_id: null,
        reference_code: null,
        note: data.note ?? null,
        status: 'Pending',
        items: [
          {
            product_id: data.product_id,
            type: 'Out',
            warehouse_id: data.source_warehouse_id as number,
            quantity: data.quantity,
          },
        ],
      };
    }

    if (data.operation_type === 'Transfer') {
      return {
        operation_type: data.operation_type,
        source_warehouse_id: data.source_warehouse_id,
        destination_warehouse_id: data.destination_warehouse_id,
        reference_code: null,
        note: data.note ?? null,
        status: 'Pending',
        items: [
          {
            product_id: data.product_id,
            type: 'Out',
            warehouse_id: data.source_warehouse_id as number,
            quantity: data.quantity,
          },
          {
            product_id: data.product_id,
            type: 'In',
            warehouse_id: data.destination_warehouse_id as number,
            quantity: data.quantity,
          },
        ],
      };
    }

    if (data.adjustment_direction === 'In') {
      return {
        operation_type: 'Adjustment',
        source_warehouse_id: null,
        destination_warehouse_id: data.destination_warehouse_id,
        reference_code: null,
        note: data.note ?? null,
        status: 'Pending',
        items: [
          {
            product_id: data.product_id,
            type: 'In',
            warehouse_id: data.destination_warehouse_id as number,
            quantity: data.quantity,
          },
        ],
      };
    }

    return {
      operation_type: 'Adjustment',
      source_warehouse_id: data.source_warehouse_id,
      destination_warehouse_id: null,
      reference_code: null,
      note: data.note ?? null,
      status: 'Pending',
      items: [
        {
          product_id: data.product_id,
          type: 'Out',
          warehouse_id: data.source_warehouse_id as number,
          quantity: data.quantity,
        },
      ],
    };
  };

  const handleCreateOperation = async (data: OperationFormData) => {
    try {
      const payload = mapOperationToPayload(data);
      await operationsApi.createOperation(payload);
      setShowAddModal(false);
      await fetchOperations();
    } catch (err) {
      throw new Error(getErrorMessage(err, 'Failed to create operation'));
    }
  };

  const handleCompleteTransaction = async (operationId: number, transactionId: number) => {
    setProcessingTransactionId(transactionId);
    setActionError(null);
    try {
      await operationsApi.completeTransaction(operationId, transactionId);
      await fetchOperations();
    } catch (err) {
      setActionError(getErrorMessage(err, 'Failed to complete transaction'));
      await fetchOperations();
    } finally {
      setProcessingTransactionId(null);
    }
  };

  const requestInReceiveConfirmation = (
    operationId: number,
    transactionId: number,
    expectedQty: number,
  ) => {
    setSelectedInTransaction({ operationId, transactionId, expectedQty });
    setReceiveConfirmValue(expectedQty);
    setShowReceiveConfirmModal(true);
  };

  const submitInReceiveConfirmation = async () => {
    if (!selectedInTransaction) {
      return;
    }
    const { operationId, transactionId } = selectedInTransaction;
    setProcessingTransactionId(transactionId);
    try {
      await operationsApi.completeTransaction(operationId, transactionId, receiveConfirmValue);
      setShowReceiveConfirmModal(false);
      setSelectedInTransaction(null);
      await fetchOperations();
    } catch (err) {
      setActionError(getErrorMessage(err, 'Failed to complete IN transaction'));
      await fetchOperations();
    } finally {
      setProcessingTransactionId(null);
    }
  };

  const handleFailTransaction = async (operationId: number, transactionId: number) => {
    setProcessingTransactionId(transactionId);
    setActionError(null);
    try {
      await operationsApi.failTransaction(operationId, transactionId);
      await fetchOperations();
    } catch (err) {
      setActionError(getErrorMessage(err, 'Failed to mark transaction as failed'));
      await fetchOperations();
    } finally {
      setProcessingTransactionId(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30';
      case 'In_Transit':
        return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
      case 'Pending':
        return 'text-amber-300 bg-amber-300/10 border-amber-300/30';
      case 'Cancelled':
        return 'text-red-400 bg-red-400/10 border-red-400/30';
      case 'Failed':
        return 'text-red-400 bg-red-400/10 border-red-400/30';
      default:
        return 'text-slate-300 bg-slate-400/10 border-slate-400/30';
    }
  };

  const getTransactionStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'text-emerald-400 bg-emerald-400/5 border-emerald-400/30';
      case 'Failed':
        return 'text-red-400 bg-red-400/5 border-red-400/30';
      case 'Pending':
        return 'text-amber-300 bg-amber-300/5 border-amber-300/30';
      default:
        return 'text-slate-400 bg-slate-400/5 border-slate-400/30';
    }
  };

  const areAllTransferOutCompleted = (operation: OperationResponse): boolean => {
    const outItems = operation.items.filter((item) => item.type === 'Out');
    return outItems.length > 0 && outItems.every((item) => item.movement_status === 'Completed');
  };

  const canCompleteTransaction = (
    operation: OperationResponse,
    item: OperationItemResponse,
  ): boolean => {
    if (item.movement_status !== 'Pending') {
      return false;
    }

    if (operation.operation_type === 'Transfer' && item.type === 'In') {
      return areAllTransferOutCompleted(operation);
    }

    return true;
  };

  return (
    <div>
      <Header
        title="Operations"
        subtitle="Create and manage operation lifecycle"
        onAddNew={() => setShowAddModal(true)}
        addNewLabel="New Operation"
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-blue-400" />
        </div>
      ) : error ? (
        <div className="mx-auto max-w-4xl px-8 py-20">
          <ErrorBox
            message={error}
            title="Unable to load operations"
            className="mx-auto"
            onClose={() => setError(null)}
          />
          <button
            onClick={fetchOperations}
            className="mt-4 rounded-lg bg-white/5 px-4 py-2 text-sm text-white transition-colors hover:bg-white/10"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="px-8 pb-8">
          {actionError && (
            <div className="mb-4">
              <ErrorBox
                message={actionError}
                title="Action failed"
                onClose={() => setActionError(null)}
              />
            </div>
          )}

          {/* Filter bar */}
          <div className="mb-5 flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Filter size={14} />
            </div>

            {/* Operation type pills */}
            {OPERATION_TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(typeFilter === t ? null : t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${typeFilter === t ? 'bg-accent-blue/20 text-blue-300 border border-blue-500/30' : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10'}`}
              >
                {t}
              </button>
            ))}

            <div className="w-px h-4 bg-white/10" />

            {/* Status dropdown */}
            <FilterSelect
              value={statusFilter}
              onChange={(v) => setStatusFilter(v !== null ? (v as OperationStatus) : null)}
              options={OPERATION_STATUSES.map((s) => ({ value: s, label: STATUS_LABELS[s] }))}
              placeholder="All Statuses"
            />

            {/* Warehouse dropdown */}
            <FilterSelect
              value={warehouseFilter}
              onChange={(v) => setWarehouseFilter(v !== null ? Number(v) : null)}
              options={warehouses.map((w) => ({ value: w.id, label: w.name }))}
              placeholder="All Warehouses"
            />

            {/* Clear button */}
            {(typeFilter !== null || statusFilter !== null || warehouseFilter !== null) && (
              <button
                onClick={() => { setTypeFilter(null); setStatusFilter(null); setWarehouseFilter(null); }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 text-slate-400 border border-transparent hover:bg-white/10 transition-all flex items-center gap-1.5"
              >
                <X size={12} />
                Clear
              </button>
            )}

            <span className="text-xs text-slate-500 ml-auto">{operations.length} operations</span>
          </div>

          <div className="space-y-4">
            {operations.length === 0 ? (
              <div className="py-12 text-center text-slate-400">No operations found</div>
            ) : (
              operations.map((op) => (
                <div key={op.id} className="overflow-hidden rounded-lg border border-slate-700">
                  <div className="flex items-center justify-between bg-slate-800/50 p-4 transition-colors hover:bg-slate-800/70">
                    <div className="flex flex-1 items-center gap-4">
                      <div>
                        <p className="text-sm font-medium text-white">#{op.id}</p>
                        <p className="text-xs text-slate-400">{op.operation_type}</p>
                      </div>

                      <div>
                        <span className={`rounded-md border px-2 py-1 text-xs font-medium ${getStatusColor(op.status)}`}>
                          {op.status}
                        </span>
                      </div>

                      <div>
                        <p className="text-xs text-slate-400">Lines</p>
                        <p className="text-sm text-white">
                          {op.items.filter((i) => i.movement_status === 'Completed').length}/{op.items.length}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-400">Route</p>
                        <p className="text-sm text-slate-300">
                          {op.source_warehouse_name || 'N/A'} - {op.destination_warehouse_name || 'N/A'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setExpandedOperationId(expandedOperationId === op.id ? null : op.id)}
                        className="rounded-lg bg-slate-700 px-2 py-1.5 text-xs font-semibold text-white hover:bg-slate-600"
                      >
                        {expandedOperationId === op.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </div>
                  </div>

                  {expandedOperationId === op.id && (
                    <div className="border-t border-slate-700 bg-slate-900/50 p-4">
                      <div className="space-y-2">
                        {op.items.map((item: OperationItemResponse) => (
                          <div
                            key={item.id}
                            className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/50 p-3"
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-3">
                                <div>
                                  <p className="text-sm font-medium text-white">{item.product_name}</p>
                                  <p className="text-xs text-slate-400">{item.product_sku}</p>
                                </div>

                                <span className="rounded border border-blue-400/30 bg-blue-400/10 px-2 py-1 text-xs font-semibold text-blue-300">
                                  {item.type}
                                </span>

                                <span
                                  className={`rounded border px-2 py-1 text-xs font-semibold ${getTransactionStatusColor(item.movement_status)}`}
                                >
                                  {item.movement_status}
                                </span>

                                <span className="ml-2 text-sm text-slate-300">
                                  Qty: <span className="font-semibold text-white">{item.quantity}</span>
                                </span>

                                {item.warehouse_name && (
                                  <span className="text-xs text-slate-400">
                                    @ <span className="font-medium text-slate-300">{item.warehouse_name}</span>
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="ml-4 flex items-center gap-2">
                              {item.movement_status === 'Pending' && (
                                <>
                                  <button
                                    onClick={() =>
                                      item.type === 'In'
                                        ? requestInReceiveConfirmation(op.id, item.id, item.quantity)
                                        : handleCompleteTransaction(op.id, item.id)
                                    }
                                    disabled={processingTransactionId === item.id || !canCompleteTransaction(op, item)}
                                    className="rounded bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    {processingTransactionId === item.id
                                      ? 'Completing...'
                                      : item.type === 'In'
                                        ? 'Confirm Receive'
                                        : 'Complete'}
                                  </button>
                                  <button
                                    onClick={() => handleFailTransaction(op.id, item.id)}
                                    disabled={processingTransactionId === item.id}
                                    className="rounded bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    {processingTransactionId === item.id ? 'Failing...' : 'Fail'}
                                  </button>
                                  {op.operation_type === 'Transfer' &&
                                    item.type === 'In' &&
                                    !areAllTransferOutCompleted(op) && (
                                      <span className="text-xs text-amber-300">
                                        Waiting for OUT completion
                                      </span>
                                    )}
                                </>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Create Pending Operation"
        size="lg"
      >
        <MovementForm
          operationType={operationType}
          setOperationType={setOperationType}
          products={products}
          warehouses={warehouses}
          onSubmit={handleCreateOperation}
          onClose={() => setShowAddModal(false)}
        />
      </Modal>

      <Modal
        isOpen={showReceiveConfirmModal}
        onClose={() => {
          setShowReceiveConfirmModal(false);
          setSelectedInTransaction(null);
        }}
        title="Confirm Received Quantity"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-300">
            Confirm the real quantity received in warehouse before completing this IN transaction.
          </p>
          <p className="text-xs text-slate-400">
            Partial receipt is allowed. If received quantity is less than expected, a partial-receipt note will be added automatically.
          </p>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-400">
              Received Quantity
            </label>
            <input
              type="number"
              min={1}
              value={receiveConfirmValue}
              onChange={(e) => setReceiveConfirmValue(Number(e.target.value || 0))}
              className="w-full rounded-lg border border-white/10 bg-slate-900/70 px-3 py-2 text-white focus:border-blue-400 focus:outline-none"
            />
            {selectedInTransaction && (
              <p className="mt-2 text-xs text-slate-400">
                Expected quantity: <span className="font-semibold text-white">{selectedInTransaction.expectedQty}</span>
              </p>
            )}
          </div>
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => {
                setShowReceiveConfirmModal(false);
                setSelectedInTransaction(null);
              }}
              className="rounded-lg bg-white/5 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/10"
            >
              Cancel
            </button>
            <button
              onClick={submitInReceiveConfirmation}
              disabled={
                !selectedInTransaction ||
                receiveConfirmValue <= 0 ||
                processingTransactionId === selectedInTransaction.transactionId
              }
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {selectedInTransaction && processingTransactionId === selectedInTransaction.transactionId
                ? 'Confirming...'
                : 'Confirm & Complete'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
