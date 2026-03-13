/**
 * Categories API Client
 * Handles all category-related API requests
 */

import { apiGet, apiPost, apiPut, apiDelete } from './client';
import { API_ENDPOINTS } from './config';
import type {
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    CategoryListResponse,
    CategoryProductPercentageResponse,
} from '../types';

/**
 * Create a new category (Admin only)
 */
export async function createCategory(data: CategoryCreateRequest): Promise<CategoryResponse> {
    return apiPost<CategoryResponse>(API_ENDPOINTS.CATEGORIES.CREATE, data, true);
}

/**
 * List all categories in the current tenant
 */
export async function listCategories(
    parentId?: number | null,
    rootsOnly?: boolean
): Promise<CategoryListResponse> {
    const params = new URLSearchParams();
    
    if (parentId !== undefined && parentId !== null) {
        params.append('parent_id', parentId.toString());
    }
    
    if (rootsOnly) {
        params.append('roots_only', 'true');
    }
    
    const url = params.toString() 
        ? `${API_ENDPOINTS.CATEGORIES.LIST}?${params.toString()}`
        : API_ENDPOINTS.CATEGORIES.LIST;
    
    return apiGet<CategoryListResponse>(url, true);
}

/**
 * Get a specific category by ID
 */
export async function getCategoryById(categoryId: number): Promise<CategoryResponse> {
    return apiGet<CategoryResponse>(API_ENDPOINTS.CATEGORIES.GET(categoryId), true);
}

/**
 * Update a category's information (Admin only)
 */
export async function updateCategory(
    categoryId: number,
    data: CategoryUpdateRequest
): Promise<CategoryResponse> {
    return apiPut<CategoryResponse>(API_ENDPOINTS.CATEGORIES.UPDATE(categoryId), data, true);
}

/**
 * Delete a category (Admin only)
 */
export async function deleteCategory(categoryId: number): Promise<void> {
    return apiDelete(API_ENDPOINTS.CATEGORIES.DELETE(categoryId), true);
}

/**
 * Get product distribution by category
 */
export async function getProductDistribution(): Promise<CategoryProductPercentageResponse> {
    return apiGet<CategoryProductPercentageResponse>(API_ENDPOINTS.CATEGORIES.PRODUCT_DISTRIBUTION, true);
}
