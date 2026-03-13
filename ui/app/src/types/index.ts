// ===== Enums =====
export type UserRole = 'Admin' | 'Staff';
export type TransactionType = 'In' | 'Out' | 'Transfer';

// ===== Core Models =====
export interface Tenant {
    id: number;
    name: string;
    createdAt: string;
}

export interface User {
    id: number;
    tenantId: number;
    name: string;
    email: string;
    role: UserRole;
    avatar?: string;
}

export interface Category {
    id: number;
    tenantId: number;
    parentId: number | null;
    name: string;
    children?: Category[];
}

export interface Warehouse {
    id: number;
    tenantId: number;
    name: string;
    location: string | null;
}

export interface Product {
    id: number;
    tenantId: number;
    categoryId: number | null;
    sku: string;
    name: string;
    description: string | null;
    reorderPoint: number;
    categoryName?: string;
}

export interface Stock {
    productId: number;
    warehouseId: number;
    quantity: number;
    productName?: string;
    warehouseName?: string;
    sku?: string;
}

export interface InventoryTransaction {
    id: number;
    tenantId: number;
    productId: number;
    userId: number | null;
    warehouseId: number | null;
    destWarehouseId: number | null;
    type: TransactionType;
    quantity: number;
    notes: string;
    timestamp: string;
    productName?: string;
    userName?: string;
    warehouseName?: string;
    destWarehouseName?: string;
}

// ===== UI State =====
export interface NavItem {
    label: string;
    path: string;
    icon: string;
    badge?: number;
}

export interface StatsCard {
    title: string;
    value: string | number;
    change?: number;
    icon: string;
    color: string;
}

// ===== Dashboard API Responses =====
export interface TotalProductsResponse {
    total_products: number;
}

export interface TotalWarehousesResponse {
    total_warehouses: number;
}

export interface TotalTransactionsResponse {
    total_transactions: number;
}

export interface TransactionDetail {
    id: number;
    product_id: number;
    product_name: string;
    product_sku: string;
    warehouse_id: number | null;
    warehouse_name: string | null;
    des_warehouse_id: number | null;
    des_warehouse_name: string | null;
    type: TransactionType;
    quantity: number;
    notes: string;
    timestamp: string;
    user_id: number | null;
    user_name: string | null;
}

export interface AllTransactionsResponse {
    transactions: TransactionDetail[];
    total: number;
    limit: number;
    offset: number;
}

export interface StockByProductItem {
    product_id: number;
    product_name: string;
    product_sku: string;
    total_stock: number;
}

export interface StockByProductResponse {
    stock_by_product: StockByProductItem[];
}

export interface LowStockProductItem {
    product_id: number;
    product_name: string;
    product_sku: string;
    reorder_point: number;
    total_stock: number;
}

export interface LowStockProductsResponse {
    low_stock_products: LowStockProductItem[];
}

// ===== Product API Request/Response Types =====
export interface ProductCreateRequest {
    sku: string;
    name: string;
    description?: string | null;
    category_id?: number | null;
    reorder_point?: number;
}

export interface ProductUpdateRequest {
    name?: string;
    description?: string | null;
    category_name?: string | null;
    reorder_point?: number;
}

export interface ProductResponse {
    id: number;
    tenant_id: number;
    category_name: string | null;
    sku: string;
    name: string;
    description: string | null;
    reorder_point: number;
}

export interface ProductListResponse {
    products: ProductResponse[];
    total: number;
    limit: number;
    offset: number;
}

// ===== Warehouse API Request/Response Types =====
export interface WarehouseCreateRequest {
    name: string;
    location?: string | null;
}

export interface WarehouseUpdateRequest {
    name?: string;
    location?: string | null;
}

export interface WarehouseResponse {
    id: number;
    tenant_id: number;
    name: string;
    location: string | null;
}

export interface WarehouseSummary {
    id: number;
    tenant_id: number;
    name: string;
    location: string | null;
    total_unique_products: number;
    total_stock: number;
}

export interface WarehouseListResponse {
    warehouses: WarehouseSummary[];
}

export interface WarehouseProductStock {
    product_id: number;
    product_name: string;
    product_sku: string;
    quantity: number;
}

export interface WarehouseDetailResponse {
    id: number;
    tenant_id: number;
    name: string;
    location: string | null;
    total_unique_products: number;
    total_stock: number;
    products: WarehouseProductStock[];
}

// ===== Transaction/Stock Movement API Request/Response Types =====
export interface TransactionCreateRequest {
    product_id: number;
    type: TransactionType;
    quantity: number;
    origin_warehouse_id?: number | null;
    des_warehouse_id?: number | null;
    notes?: string | null;
}

export interface TransactionResponse {
    id: number;
    tenant_id: number;
    type: TransactionType;
    product_id: number;
    product_name: string;
    product_sku: string;
    quantity: number;
    origin_warehouse_id: number | null;
    origin_warehouse_name: string | null;
    des_warehouse_id: number | null;
    des_warehouse_name: string | null;
    user_id: number | null;
    user_name: string | null;
    notes: string | null;
    timestamp: string;
}

export interface TransactionListResponse {
    transactions: TransactionResponse[];
    total: number;
    limit: number;
    offset: number;
}

// ===== User API Request/Response Types =====
export interface UserCreateRequest {
    name: string;
    email: string;
    password: string;
    role: UserRole;
}

export interface UserUpdateRequest {
    name?: string;
    role?: UserRole;
}

export interface UserSelfUpdateRequest {
    name: string;
}

export interface UserPasswordUpdateRequest {
    new_password: string;
}

export interface UserResponse {
    id: number;
    tenant_id: number;
    name: string;
    email: string;
    role: UserRole;
}

export interface UserListResponse {
    users: UserResponse[];
    total: number;
}

// ===== Category API Request/Response Types =====
export interface CategoryCreateRequest {
    name: string;
    parent_id?: number | null;
}

export interface CategoryUpdateRequest {
    name?: string;
    parent_id?: number | null;
}

export interface CategoryResponse {
    id: number;
    tenant_id: number;
    name: string;
    parent_id: number | null;
}

export interface CategoryListResponse {
    categories: CategoryResponse[];
    total: number;
}

export interface CategoryProductPercentage {
    category_id: number | null;
    category_name: string;
    product_count: number;
    percentage: number;
}

export interface CategoryProductPercentageResponse {
    distribution: CategoryProductPercentage[];
    total_products: number;
}
