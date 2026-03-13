/**
 * Transactions/Stock Movements API client
 */

import { apiGet, apiPost } from './client';
import { API_ENDPOINTS } from './config';
import type {
  TransactionCreateRequest,
  TransactionResponse,
  TransactionListResponse,
  TransactionType,
} from '../types';

/**
 * Create a new inventory transaction (stock movement)
 */
export async function createTransaction(
  data: TransactionCreateRequest
): Promise<TransactionResponse> {
  return apiPost<TransactionResponse>(API_ENDPOINTS.TRANSACTIONS.CREATE, data, true);
}

/**
 * List all transactions with optional filters
 */
export async function listTransactions(
  type?: TransactionType | null,
  warehouseId?: number | null,
  productId?: number | null,
  limit: number = 100,
  offset: number = 0
): Promise<TransactionListResponse> {
  const params = new URLSearchParams();
  
  if (type) {
    params.append('type', type);
  }
  if (warehouseId !== null && warehouseId !== undefined) {
    params.append('warehouse_id', warehouseId.toString());
  }
  if (productId !== null && productId !== undefined) {
    params.append('product_id', productId.toString());
  }
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());
  
  const queryString = params.toString();
  const url = queryString 
    ? `${API_ENDPOINTS.TRANSACTIONS.LIST}?${queryString}`
    : API_ENDPOINTS.TRANSACTIONS.LIST;
  return apiGet<TransactionListResponse>(url, true);
}

/**
 * Get a specific transaction by ID
 */
export async function getTransactionById(
  transactionId: number
): Promise<TransactionResponse> {
  return apiGet<TransactionResponse>(API_ENDPOINTS.TRANSACTIONS.GET(transactionId), true);
}
