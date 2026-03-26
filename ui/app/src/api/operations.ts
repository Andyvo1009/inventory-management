/**
 * Operations API client - primary write API for stock workflows
 */

import { apiGet, apiPatch, apiPost } from './client';
import { API_ENDPOINTS } from './config';
import type {
  OperationCreateRequest,
  OperationListResponse,
  OperationResponse,
  OperationType,
  OperationStatus,
} from '../types';

export async function createOperation(
  data: OperationCreateRequest
): Promise<OperationResponse> {
  return apiPost<OperationResponse>(API_ENDPOINTS.OPERATIONS.CREATE, data, true);
}

export async function completeOperation(
  operationId: number
): Promise<OperationResponse> {
  return apiPost<OperationResponse>(API_ENDPOINTS.OPERATIONS.COMPLETE(operationId), {}, true);
}

export async function updateOperationStatus(
  operationId: number,
  status: OperationStatus
): Promise<OperationResponse> {
  return apiPatch<OperationResponse>(
    API_ENDPOINTS.OPERATIONS.UPDATE_STATUS(operationId),
    { status },
    true
  );
}

export async function listOperations(
  operationType?: OperationType | null,
  opStatus?: OperationStatus | null,
  warehouseId?: number | null,
  limit: number = 100,
  offset: number = 0
): Promise<OperationListResponse> {
  const params = new URLSearchParams();

  if (operationType) {
    params.append('operation_type', operationType);
  }
  if (opStatus) {
    params.append('status', opStatus);
  }
  if (warehouseId != null) {
    params.append('warehouse_id', warehouseId.toString());
  }
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const queryString = params.toString();
  const url = queryString
    ? `${API_ENDPOINTS.OPERATIONS.LIST}?${queryString}`
    : API_ENDPOINTS.OPERATIONS.LIST;
  return apiGet<OperationListResponse>(url, true);
}

export async function getOperationById(
  operationId: number
): Promise<OperationResponse> {
  return apiGet<OperationResponse>(API_ENDPOINTS.OPERATIONS.GET(operationId), true);
}

export async function completeTransaction(
  operationId: number,
  transactionId: number,
  receivedQuantity?: number
): Promise<OperationResponse> {
  return apiPost<OperationResponse>(
    API_ENDPOINTS.OPERATIONS.COMPLETE_TRANSACTION(operationId, transactionId),
    receivedQuantity != null ? { received_quantity: receivedQuantity } : {},
    true
  );
}

export async function failTransaction(
  operationId: number,
  transactionId: number
): Promise<OperationResponse> {
  return apiPost<OperationResponse>(
    API_ENDPOINTS.OPERATIONS.FAIL_TRANSACTION(operationId, transactionId),
    {},
    true
  );
}
