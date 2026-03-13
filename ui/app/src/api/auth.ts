/**
 * Authentication API client
 */

import { apiGet, apiPost } from './client';
import { API_ENDPOINTS, STORAGE_KEYS } from './config';
import type { User, UserRole } from '../types';

// ===== Request Types =====

export interface RegisterRequest {
    tenant_name: string;
    name: string;
    email: string;
    password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

// ===== Response Types =====

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  tenant_id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

// ===== API Functions =====

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<UserResponse> {
    console.log('Registering user with data:', data);
  return apiPost<UserResponse>(API_ENDPOINTS.AUTH.REGISTER, data);
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiPost<TokenResponse>(API_ENDPOINTS.AUTH.LOGIN, data);
  
  // Store the token
  if (response.access_token) {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
  }
  
  return response;
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<UserResponse> {
  return apiGet<UserResponse>(API_ENDPOINTS.AUTH.ME, true);
}

/**
 * Change current user's password
 */
export async function changePassword(
  data: ChangePasswordRequest
): Promise<void> {
  return apiPost<void>(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, data, true);
}

/**
 * Logout - clear stored authentication data
 */
export function logout(): void {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USER);
}

/**
 * Check if user is authenticated (has token)
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Get stored access token
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Convert UserResponse from API to User type
 */
export function mapUserResponse(userResponse: UserResponse): User {
  return {
    id: userResponse.id,
    tenantId: userResponse.tenant_id,
    name: userResponse.name,
    email: userResponse.email,
    role: userResponse.role,
  };
}
