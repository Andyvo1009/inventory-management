/**
 * Dashboard API client
 */

import { apiGet } from './client';
import { API_ENDPOINTS } from './config';
import type {
  TotalProductsResponse,
  TotalWarehousesResponse,
  TotalTransactionsResponse,
  AllTransactionsResponse,
  StockByProductResponse,
  LowStockProductsResponse,
} from '../types';

/**
 * Get total number of products in the tenant's inventory
 */
export async function getTotalProducts(): Promise<TotalProductsResponse> {
  return apiGet<TotalProductsResponse>(API_ENDPOINTS.DASHBOARD.TOTAL_PRODUCTS, true);
}

/**
 * Get total number of warehouses for the tenant
 */
export async function getTotalWarehouses(): Promise<TotalWarehousesResponse> {
  return apiGet<TotalWarehousesResponse>(API_ENDPOINTS.DASHBOARD.TOTAL_WAREHOUSES, true);
}

/**
 * Get total number of inventory transactions for the tenant
 */
export async function getTotalTransactions(): Promise<TotalTransactionsResponse> {
  return apiGet<TotalTransactionsResponse>(API_ENDPOINTS.DASHBOARD.TOTAL_TRANSACTIONS, true);
}

/**
 * Get all transaction records for the tenant with pagination
 */
export async function getAllTransactions(
  limit: number = 100,
  offset: number = 0
): Promise<AllTransactionsResponse> {
  return apiGet<AllTransactionsResponse>(
    `${API_ENDPOINTS.DASHBOARD.TRANSACTIONS}?limit=${limit}&offset=${offset}`,
    true
  );
}

/**
 * Get stock levels aggregated by product across all warehouses
 */
export async function getStockByProduct(): Promise<StockByProductResponse> {
  return apiGet<StockByProductResponse>(API_ENDPOINTS.DASHBOARD.STOCK_BY_PRODUCT, true);
}

/**
 * Get products at or below reorder point
 */
export async function getLowStockProducts(): Promise<LowStockProductsResponse> {
  return apiGet<LowStockProductsResponse>(API_ENDPOINTS.DASHBOARD.LOW_STOCK_PRODUCTS, true);
}
