import type { User, Category, Warehouse, Product, Stock, InventoryTransaction } from '../types';

// ===== Current User =====
export const currentUser: User = {
    id: 1,
    tenantId: 1,
    name: 'Alex Johnson',
    email: 'alex@acmecorp.com',
    role: 'Admin',
};

export const tenantName = 'Acme Corporation';

// ===== Users =====
export const users: User[] = [
    currentUser,
    { id: 2, tenantId: 1, name: 'Sarah Chen', email: 'sarah@acmecorp.com', role: 'Staff' },
    { id: 3, tenantId: 1, name: 'Marcus Williams', email: 'marcus@acmecorp.com', role: 'Staff' },
    { id: 4, tenantId: 1, name: 'Priya Patel', email: 'priya@acmecorp.com', role: 'Admin' },
    { id: 5, tenantId: 1, name: 'James Lee', email: 'james@acmecorp.com', role: 'Staff' },
];

// ===== Categories =====
export const categories: Category[] = [
    { id: 1, tenantId: 1, parentId: null, name: 'Electronics' },
    { id: 2, tenantId: 1, parentId: 1, name: 'Smartphones' },
    { id: 3, tenantId: 1, parentId: 1, name: 'Laptops' },
    { id: 4, tenantId: 1, parentId: 1, name: 'Accessories' },
    { id: 5, tenantId: 1, parentId: null, name: 'Furniture' },
    { id: 6, tenantId: 1, parentId: 5, name: 'Desks' },
    { id: 7, tenantId: 1, parentId: 5, name: 'Chairs' },
    { id: 8, tenantId: 1, parentId: null, name: 'Office Supplies' },
    { id: 9, tenantId: 1, parentId: 8, name: 'Paper' },
    { id: 10, tenantId: 1, parentId: 8, name: 'Writing Tools' },
];

// ===== Warehouses =====
export const warehouses: Warehouse[] = [
    { id: 1, tenantId: 1, name: 'Warehouse Alpha', location: 'Downtown District, Building 12' },
    { id: 2, tenantId: 1, name: 'Warehouse Beta', location: 'Industrial Park, Zone 3' },
    { id: 3, tenantId: 1, name: 'Warehouse Gamma', location: 'Airport Logistics Center' },
];

// ===== Products =====
export const products: Product[] = [
    { id: 1, tenantId: 1, categoryId: 2, sku: 'ELEC-SP-001', name: 'iPhone 15 Pro', description: 'Apple iPhone 15 Pro 256GB', reorderPoint: 15, categoryName: 'Smartphones' },
    { id: 2, tenantId: 1, categoryId: 2, sku: 'ELEC-SP-002', name: 'Samsung Galaxy S24', description: 'Samsung Galaxy S24 Ultra 512GB', reorderPoint: 10, categoryName: 'Smartphones' },
    { id: 3, tenantId: 1, categoryId: 3, sku: 'ELEC-LP-001', name: 'MacBook Pro 16"', description: 'Apple MacBook Pro M3 Max 16"', reorderPoint: 5, categoryName: 'Laptops' },
    { id: 4, tenantId: 1, categoryId: 3, sku: 'ELEC-LP-002', name: 'ThinkPad X1 Carbon', description: 'Lenovo ThinkPad X1 Carbon Gen 11', reorderPoint: 8, categoryName: 'Laptops' },
    { id: 5, tenantId: 1, categoryId: 4, sku: 'ELEC-AC-001', name: 'AirPods Pro 2', description: 'Apple AirPods Pro 2nd Gen USB-C', reorderPoint: 20, categoryName: 'Accessories' },
    { id: 6, tenantId: 1, categoryId: 4, sku: 'ELEC-AC-002', name: 'Magic Mouse', description: 'Apple Magic Mouse - White', reorderPoint: 12, categoryName: 'Accessories' },
    { id: 7, tenantId: 1, categoryId: 6, sku: 'FURN-DK-001', name: 'Standing Desk Pro', description: 'Electric Standing Desk 60x30"', reorderPoint: 3, categoryName: 'Desks' },
    { id: 8, tenantId: 1, categoryId: 7, sku: 'FURN-CH-001', name: 'Ergonomic Chair Elite', description: 'Herman Miller Aeron Chair', reorderPoint: 4, categoryName: 'Chairs' },
    { id: 9, tenantId: 1, categoryId: 9, sku: 'OFFC-PP-001', name: 'A4 Copy Paper', description: 'Premium White A4 Paper 500 sheets', reorderPoint: 50, categoryName: 'Paper' },
    { id: 10, tenantId: 1, categoryId: 10, sku: 'OFFC-WT-001', name: 'Gel Pen Set', description: 'Multi-color Gel Pen Set 12pcs', reorderPoint: 30, categoryName: 'Writing Tools' },
    { id: 11, tenantId: 1, categoryId: 4, sku: 'ELEC-AC-003', name: 'USB-C Hub 7-in-1', description: 'Anker 7-in-1 USB-C Hub', reorderPoint: 15, categoryName: 'Accessories' },
    { id: 12, tenantId: 1, categoryId: 3, sku: 'ELEC-LP-003', name: 'Dell XPS 15', description: 'Dell XPS 15 OLED i9 32GB', reorderPoint: 6, categoryName: 'Laptops' },
];

// ===== Stocks =====
export const stocks: Stock[] = [
    { productId: 1, warehouseId: 1, quantity: 42, productName: 'iPhone 15 Pro', warehouseName: 'Warehouse Alpha', sku: 'ELEC-SP-001' },
    { productId: 1, warehouseId: 2, quantity: 18, productName: 'iPhone 15 Pro', warehouseName: 'Warehouse Beta', sku: 'ELEC-SP-001' },
    { productId: 2, warehouseId: 1, quantity: 8, productName: 'Samsung Galaxy S24', warehouseName: 'Warehouse Alpha', sku: 'ELEC-SP-002' },
    { productId: 2, warehouseId: 3, quantity: 25, productName: 'Samsung Galaxy S24', warehouseName: 'Warehouse Gamma', sku: 'ELEC-SP-002' },
    { productId: 3, warehouseId: 1, quantity: 3, productName: 'MacBook Pro 16"', warehouseName: 'Warehouse Alpha', sku: 'ELEC-LP-001' },
    { productId: 3, warehouseId: 2, quantity: 7, productName: 'MacBook Pro 16"', warehouseName: 'Warehouse Beta', sku: 'ELEC-LP-001' },
    { productId: 4, warehouseId: 2, quantity: 12, productName: 'ThinkPad X1 Carbon', warehouseName: 'Warehouse Beta', sku: 'ELEC-LP-002' },
    { productId: 5, warehouseId: 1, quantity: 5, productName: 'AirPods Pro 2', warehouseName: 'Warehouse Alpha', sku: 'ELEC-AC-001' },
    { productId: 5, warehouseId: 3, quantity: 10, productName: 'AirPods Pro 2', warehouseName: 'Warehouse Gamma', sku: 'ELEC-AC-001' },
    { productId: 6, warehouseId: 1, quantity: 8, productName: 'Magic Mouse', warehouseName: 'Warehouse Alpha', sku: 'ELEC-AC-002' },
    { productId: 7, warehouseId: 2, quantity: 2, productName: 'Standing Desk Pro', warehouseName: 'Warehouse Beta', sku: 'FURN-DK-001' },
    { productId: 8, warehouseId: 1, quantity: 6, productName: 'Ergonomic Chair Elite', warehouseName: 'Warehouse Alpha', sku: 'FURN-CH-001' },
    { productId: 8, warehouseId: 3, quantity: 3, productName: 'Ergonomic Chair Elite', warehouseName: 'Warehouse Gamma', sku: 'FURN-CH-001' },
    { productId: 9, warehouseId: 1, quantity: 120, productName: 'A4 Copy Paper', warehouseName: 'Warehouse Alpha', sku: 'OFFC-PP-001' },
    { productId: 9, warehouseId: 2, quantity: 80, productName: 'A4 Copy Paper', warehouseName: 'Warehouse Beta', sku: 'OFFC-PP-001' },
    { productId: 10, warehouseId: 1, quantity: 15, productName: 'Gel Pen Set', warehouseName: 'Warehouse Alpha', sku: 'OFFC-WT-001' },
    { productId: 11, warehouseId: 1, quantity: 22, productName: 'USB-C Hub 7-in-1', warehouseName: 'Warehouse Alpha', sku: 'ELEC-AC-003' },
    { productId: 11, warehouseId: 2, quantity: 9, productName: 'USB-C Hub 7-in-1', warehouseName: 'Warehouse Beta', sku: 'ELEC-AC-003' },
    { productId: 12, warehouseId: 3, quantity: 4, productName: 'Dell XPS 15', warehouseName: 'Warehouse Gamma', sku: 'ELEC-LP-003' },
];

// ===== Transactions =====
export const transactions: InventoryTransaction[] = [
    { id: 1, tenantId: 1, productId: 1, userId: 1, warehouseId: 1, destWarehouseId: null, type: 'In', quantity: 50, notes: 'Initial restocking from Apple supplier', timestamp: '2026-03-02T08:30:00Z', productName: 'iPhone 15 Pro', userName: 'Alex Johnson', warehouseName: 'Warehouse Alpha' },
    { id: 2, tenantId: 1, productId: 1, userId: 2, warehouseId: 1, destWarehouseId: null, type: 'Out', quantity: 8, notes: 'Sold to retail outlet #3', timestamp: '2026-03-02T09:15:00Z', productName: 'iPhone 15 Pro', userName: 'Sarah Chen', warehouseName: 'Warehouse Alpha' },
    { id: 3, tenantId: 1, productId: 1, userId: 1, warehouseId: 1, destWarehouseId: 2, type: 'Transfer', quantity: 18, notes: 'Moving stock to Beta warehouse', timestamp: '2026-03-01T14:00:00Z', productName: 'iPhone 15 Pro', userName: 'Alex Johnson', warehouseName: 'Warehouse Alpha', destWarehouseName: 'Warehouse Beta' },
    { id: 4, tenantId: 1, productId: 3, userId: 3, warehouseId: 1, destWarehouseId: null, type: 'In', quantity: 10, notes: 'Quarterly laptop restock', timestamp: '2026-03-01T10:00:00Z', productName: 'MacBook Pro 16"', userName: 'Marcus Williams', warehouseName: 'Warehouse Alpha' },
    { id: 5, tenantId: 1, productId: 3, userId: 2, warehouseId: 1, destWarehouseId: null, type: 'Out', quantity: 7, notes: 'Corporate bulk order', timestamp: '2026-02-28T16:30:00Z', productName: 'MacBook Pro 16"', userName: 'Sarah Chen', warehouseName: 'Warehouse Alpha' },
    { id: 6, tenantId: 1, productId: 5, userId: 1, warehouseId: 1, destWarehouseId: null, type: 'In', quantity: 30, notes: 'Restock from distributor', timestamp: '2026-02-28T11:00:00Z', productName: 'AirPods Pro 2', userName: 'Alex Johnson', warehouseName: 'Warehouse Alpha' },
    { id: 7, tenantId: 1, productId: 5, userId: 3, warehouseId: 1, destWarehouseId: null, type: 'Out', quantity: 25, notes: 'Flash sale orders fulfilled', timestamp: '2026-02-27T09:00:00Z', productName: 'AirPods Pro 2', userName: 'Marcus Williams', warehouseName: 'Warehouse Alpha' },
    { id: 8, tenantId: 1, productId: 7, userId: 4, warehouseId: 2, destWarehouseId: null, type: 'In', quantity: 5, notes: 'New furniture arrival', timestamp: '2026-02-27T13:00:00Z', productName: 'Standing Desk Pro', userName: 'Priya Patel', warehouseName: 'Warehouse Beta' },
    { id: 9, tenantId: 1, productId: 7, userId: 5, warehouseId: 2, destWarehouseId: null, type: 'Out', quantity: 3, notes: 'Office renovation order', timestamp: '2026-02-26T15:00:00Z', productName: 'Standing Desk Pro', userName: 'James Lee', warehouseName: 'Warehouse Beta' },
    { id: 10, tenantId: 1, productId: 9, userId: 2, warehouseId: 1, destWarehouseId: 2, type: 'Transfer', quantity: 80, notes: 'Redistribute paper stock', timestamp: '2026-02-26T10:00:00Z', productName: 'A4 Copy Paper', userName: 'Sarah Chen', warehouseName: 'Warehouse Alpha', destWarehouseName: 'Warehouse Beta' },
    { id: 11, tenantId: 1, productId: 2, userId: 1, warehouseId: 3, destWarehouseId: null, type: 'In', quantity: 30, notes: 'Samsung shipment received', timestamp: '2026-02-25T08:00:00Z', productName: 'Samsung Galaxy S24', userName: 'Alex Johnson', warehouseName: 'Warehouse Gamma' },
    { id: 12, tenantId: 1, productId: 2, userId: 3, warehouseId: 3, destWarehouseId: null, type: 'Out', quantity: 5, notes: 'Online marketplace fulfillment', timestamp: '2026-02-25T14:30:00Z', productName: 'Samsung Galaxy S24', userName: 'Marcus Williams', warehouseName: 'Warehouse Gamma' },
    { id: 13, tenantId: 1, productId: 10, userId: 5, warehouseId: 1, destWarehouseId: null, type: 'Out', quantity: 15, notes: 'School supply donation', timestamp: '2026-02-24T09:00:00Z', productName: 'Gel Pen Set', userName: 'James Lee', warehouseName: 'Warehouse Alpha' },
    { id: 14, tenantId: 1, productId: 12, userId: 4, warehouseId: 3, destWarehouseId: null, type: 'In', quantity: 8, notes: 'Dell shipment received', timestamp: '2026-02-24T11:00:00Z', productName: 'Dell XPS 15', userName: 'Priya Patel', warehouseName: 'Warehouse Gamma' },
    { id: 15, tenantId: 1, productId: 12, userId: 2, warehouseId: 3, destWarehouseId: null, type: 'Out', quantity: 4, notes: 'Engineering team upgrade', timestamp: '2026-02-23T16:00:00Z', productName: 'Dell XPS 15', userName: 'Sarah Chen', warehouseName: 'Warehouse Gamma' },
];

// ===== Derived Data Helpers =====
export function getTotalStockForProduct(productId: number): number {
    return stocks
        .filter(s => s.productId === productId)
        .reduce((sum, s) => sum + s.quantity, 0);
}

export function getLowStockProducts(): (Product & { totalStock: number })[] {
    return products
        .map(p => ({ ...p, totalStock: getTotalStockForProduct(p.id) }))
        .filter(p => p.totalStock <= p.reorderPoint);
}

export function getCategoryPath(categoryId: number | null): string {
    if (!categoryId) return 'Uncategorized';
    const parts: string[] = [];
    let current = categories.find(c => c.id === categoryId);
    while (current) {
        parts.unshift(current.name);
        current = current.parentId ? categories.find(c => c.id === current!.parentId) : undefined;
    }
    return parts.join(' › ');
}

export function buildCategoryTree(): Category[] {
    const map = new Map<number, Category & { children: Category[] }>();
    categories.forEach(c => map.set(c.id, { ...c, children: [] }));
    const roots: Category[] = [];
    map.forEach(c => {
        if (c.parentId && map.has(c.parentId)) {
            map.get(c.parentId)!.children!.push(c);
        } else {
            roots.push(c);
        }
    });
    return roots;
}
