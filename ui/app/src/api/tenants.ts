/**
 * Tenants API client
 */

import { apiGet } from './client';
import { API_ENDPOINTS } from './config';

export interface TenantResponse {
  id: number;
  name: string;
  created_at: string;
}

/**
 * Get current tenant profile information
 */
export async function getCurrentTenantProfile(): Promise<TenantResponse> {
  return apiGet<TenantResponse>(API_ENDPOINTS.TENANTS.ME, true);
}
