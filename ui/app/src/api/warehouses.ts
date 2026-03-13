/**
 * Warehouses API client
 */

import { apiGet, apiPost, apiPut, apiDelete } from './client';
import { API_ENDPOINTS } from './config';
import type {
  WarehouseCreateRequest,
  WarehouseUpdateRequest,
  WarehouseResponse,
  WarehouseListResponse,
  WarehouseDetailResponse,
} from '../types';

/**
 * Create a new warehouse (Admin only)
 */
export async function createWarehouse(
  data: WarehouseCreateRequest
): Promise<WarehouseResponse> {
  return apiPost<WarehouseResponse>(API_ENDPOINTS.WAREHOUSES.CREATE, data, true);
}

/**
 * List all warehouses with stock summaries
 */
export async function listWarehouses(): Promise<WarehouseListResponse> {
  return apiGet<WarehouseListResponse>(API_ENDPOINTS.WAREHOUSES.LIST, true);
}

/**
 * Get detailed warehouse information including all products
 */
export async function getWarehouseById(
  warehouseId: number
): Promise<WarehouseDetailResponse> {
  return apiGet<WarehouseDetailResponse>(API_ENDPOINTS.WAREHOUSES.GET(warehouseId), true);
}

/**
 * Update an existing warehouse (Admin only)
 */
export async function updateWarehouse(
  warehouseId: number,
  data: WarehouseUpdateRequest
): Promise<WarehouseResponse> {
  return apiPut<WarehouseResponse>(API_ENDPOINTS.WAREHOUSES.UPDATE(warehouseId), data, true);
}

/**
 * Delete a warehouse (Admin only)
 */
export async function deleteWarehouse(warehouseId: number): Promise<void> {
  return apiDelete<void>(API_ENDPOINTS.WAREHOUSES.DELETE(warehouseId), true);
}
