/**
 * API Configuration
 */

export var API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    ME: '/api/auth/me',
    CHANGE_PASSWORD: '/api/auth/change-password',
  },
  DASHBOARD: {
    TOTAL_PRODUCTS: '/api/dashboard/total-products',
    TOTAL_WAREHOUSES: '/api/dashboard/total-warehouses',
    TOTAL_TRANSACTIONS: '/api/dashboard/total-transactions',
    TRANSACTIONS: '/api/dashboard/transactions',
    STOCK_BY_PRODUCT: '/api/dashboard/stock-by-product',
    LOW_STOCK_PRODUCTS: '/api/dashboard/low-stock-products',
  },
  PRODUCTS: {
    LIST: '/api/products/',
    CREATE: '/api/products/',
    GET: (id: number) => `/api/products/${id}`,
    UPDATE: (id: number) => `/api/products/${id}`,
    DELETE: (id: number) => `/api/products/${id}`,
  },
  WAREHOUSES: {
    LIST: '/api/warehouses/',
    CREATE: '/api/warehouses/',
    GET: (id: number) => `/api/warehouses/${id}`,
    UPDATE: (id: number) => `/api/warehouses/${id}`,
    DELETE: (id: number) => `/api/warehouses/${id}`,
  },
  TRANSACTIONS: {
    LIST: '/api/transactions/',
    CREATE: '/api/transactions/',
    GET: (id: number) => `/api/transactions/${id}`,
  },
  USERS: {
    LIST: '/api/users/',
    CREATE: '/api/users/',
    ME: '/api/users/me',
    UPDATE_ME: '/api/users/me',
    GET: (id: number) => `/api/users/${id}`,
    UPDATE: (id: number) => `/api/users/${id}`,
    UPDATE_PASSWORD: (id: number) => `/api/users/${id}/password`,
    DELETE: (id: number) => `/api/users/${id}`,
  },
  CATEGORIES: {
    LIST: '/api/categories/',
    CREATE: '/api/categories/',
    GET: (id: number) => `/api/categories/${id}`,
    UPDATE: (id: number) => `/api/categories/${id}`,
    DELETE: (id: number) => `/api/categories/${id}`,
    PRODUCT_DISTRIBUTION: '/api/categories/stats/product-distribution',
  },
} as const;
/**
 * Storage keys for persisting auth data
 */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  USER: 'user',
} as const;
