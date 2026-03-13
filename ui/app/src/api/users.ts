/**
 * Users API Client
 * Handles all user-related API requests
 */

import { apiGet, apiPost, apiPut, apiDelete } from './client';
import { API_ENDPOINTS } from './config';
import type {
    UserCreateRequest,
    UserUpdateRequest,
    UserSelfUpdateRequest,
    UserPasswordUpdateRequest,
    UserResponse,
    UserListResponse,
} from '../types';

/**
 * Create a new user (Admin only)
 */
export async function createUser(data: UserCreateRequest): Promise<UserResponse> {
    return apiPost<UserResponse>(API_ENDPOINTS.USERS.CREATE, data,true);
}

/**
 * List all users in the current tenant
 */
export async function listUsers(): Promise<UserListResponse> {
    let url = API_ENDPOINTS.USERS.LIST;
    return apiGet<UserListResponse>(url, true);
}

/**
 * Get current user's profile information
 */
export async function getCurrentUserProfile(): Promise<UserResponse> {
    return apiGet<UserResponse>(API_ENDPOINTS.USERS.ME,true);
}

/**
 * Update own profile information
 */
export async function updateSelf(data: UserSelfUpdateRequest): Promise<UserResponse> {
    return apiPut<UserResponse>(API_ENDPOINTS.USERS.UPDATE_ME, data, true);
}

/**
 * Get a specific user by ID
 */
export async function getUserById(userId: number): Promise<UserResponse> {
    return apiGet<UserResponse>(API_ENDPOINTS.USERS.GET(userId), true);
}

/**
 * Update a user's information (Admin only)
 */
export async function updateUser(userId: number, data: UserUpdateRequest): Promise<UserResponse> {
    return apiPut<UserResponse>(API_ENDPOINTS.USERS.UPDATE(userId), data, true);
}

/**
 * Update a user's password (Admin only)
 */
export async function updateUserPassword(userId: number, data: UserPasswordUpdateRequest): Promise<void> {
    return apiPut<void>(API_ENDPOINTS.USERS.UPDATE_PASSWORD(userId), data, true);
}

/**
 * Delete a user (Admin only)
 */
export async function deleteUser(userId: number): Promise<void> {
    return apiDelete(API_ENDPOINTS.USERS.DELETE(userId), true);
}
