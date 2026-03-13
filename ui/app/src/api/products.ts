/**
 * Products API client
 */

import { apiGet, apiPost, apiPut, apiDelete } from './client';
import { API_ENDPOINTS } from './config';
import type {
  ProductCreateRequest,
  ProductUpdateRequest,
  ProductResponse,
  ProductListResponse,
} from '../types';

/**
 * Create a new product (Admin only)
 */
export async function createProduct(
  data: ProductCreateRequest
): Promise<ProductResponse> {
  return apiPost<ProductResponse>(API_ENDPOINTS.PRODUCTS.CREATE, data, true);
}

/**
 * List all products with optional filters
 */
export async function listProducts(
  categoryId?: number | null,
  search?: string | null,
  limit: number = 50,
  offset: number = 0
): Promise<ProductListResponse> {
  const params = new URLSearchParams();
  
  if (categoryId !== null && categoryId !== undefined) {
    params.append('category_id', categoryId.toString());
  }
  if (search) {
    params.append('search', search);
  }
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());
  
  const queryString = params.toString();
  const url = queryString 
    ? `${API_ENDPOINTS.PRODUCTS.LIST}?${queryString}`
    : API_ENDPOINTS.PRODUCTS.LIST;
  return apiGet<ProductListResponse>(url, true);
}

/**
 * Get a specific product by ID
 */
export async function getProductById(productId: number): Promise<ProductResponse> {
  return apiGet<ProductResponse>(API_ENDPOINTS.PRODUCTS.GET(productId), true);
}

/**
 * Update an existing product (Admin only)
 */
export async function updateProduct(
  productId: number,
  data: ProductUpdateRequest
): Promise<ProductResponse> {
  return apiPut<ProductResponse>(API_ENDPOINTS.PRODUCTS.UPDATE(productId), data, true);
}

/**
 * Delete a product (Admin only)
 */
export async function deleteProduct(productId: number): Promise<void> {
  return apiDelete<void>(API_ENDPOINTS.PRODUCTS.DELETE(productId), true);
}
