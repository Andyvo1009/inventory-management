/**
 * Base API client with authentication support
 */

import { API_BASE_URL, STORAGE_KEYS } from './config';

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

function detailsToMessage(details: unknown): string | null {
  if (!details || typeof details !== 'object') {
    return null;
  }

  const detailsRecord = details as Record<string, unknown>;

  if (typeof detailsRecord.detail === 'string' && detailsRecord.detail.trim()) {
    return detailsRecord.detail;
  }

  if (typeof detailsRecord.message === 'string' && detailsRecord.message.trim()) {
    return detailsRecord.message;
  }

  const errors = detailsRecord.errors;
  if (errors && typeof errors === 'object') {
    const firstFieldErrors = Object.values(errors as Record<string, unknown>)[0];
    if (Array.isArray(firstFieldErrors) && firstFieldErrors.length > 0) {
      const firstMessage = firstFieldErrors[0];
      if (typeof firstMessage === 'string' && firstMessage.trim()) {
        return firstMessage;
      }
    }
  }

  return null;
}

export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (error instanceof ApiError) {
    const detailMessage = detailsToMessage(error.details);
    if (detailMessage) {
      return detailMessage;
    }
    if (error.message.trim()) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  if (typeof error === 'string' && error.trim()) {
    return error;
  }

  return fallback;
}

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

/**
 * Base fetch wrapper with error handling and authentication
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requiresAuth = false, headers = {}, ...fetchOptions } = options;

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(headers as Record<string, string>),
  };

  // Add authorization header if required
  if (requiresAuth) {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }
  console.log(`Making API request to: ${API_BASE_URL}${endpoint} with options:`)
  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`Making API request to: ${url} with options`)
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: requestHeaders,
    });
   
    // Handle non-JSON responses (like 204 No Content)
    if (response.status === 204) {
      return undefined as T;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        response.status,
        data.detail || data.message || 'An error occurred',
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network or other errors
    throw new ApiError(
      0,
      error instanceof Error ? error.message : 'Network error occurred'
    );
  }
}

/**
 * Helper for GET requests
 */
export function apiGet<T>(endpoint: string, requiresAuth = false): Promise<T> {
  return apiFetch<T>(endpoint, { method: 'GET', requiresAuth });
}

/**
 * Helper for POST requests
 */
export function apiPost<T>(
  endpoint: string,
  data: any,
  requiresAuth = false
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
    requiresAuth,
  });
}

/**
 * Helper for PUT requests
 */
export function apiPut<T>(
  endpoint: string,
  data: any,
  requiresAuth = false
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
    requiresAuth,
  });
}

/**
 * Helper for PATCH requests
 */
export function apiPatch<T>(
  endpoint: string,
  data: any,
  requiresAuth = false
): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(data),
    requiresAuth,
  });
}

/**
 * Helper for DELETE requests
 */
export function apiDelete<T>(endpoint: string, requiresAuth = false): Promise<T> {
  return apiFetch<T>(endpoint, { method: 'DELETE', requiresAuth });
}
