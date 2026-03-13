-- 1. Create Custom Types
CREATE TYPE transaction_type AS ENUM ('In', 'Out', 'Transfer');
CREATE TYPE user_role AS ENUM ('Admin', 'Staff');

-- 2. Base Tenant Table
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Supporting Tables (Tenant-specific)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,  -- hierarchy support
    name VARCHAR(100) NOT NULL,
    UNIQUE(tenant_id, parent_id, name)
);

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    location TEXT
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'Staff'
);

-- 4. Core Inventory Tables
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    reorder_point INTEGER NOT NULL DEFAULT 0,  -- minimum stock level for low-stock alerts
    UNIQUE(tenant_id, sku)  -- SKU must be unique per tenant
);

-- many-to-many relationship table with quantity
CREATE TABLE stocks (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (product_id, warehouse_id)
);

-- 5. Transaction Logging
CREATE TABLE inventory_transactions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    origin_warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE SET NULL,           -- source warehouse
    des_warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE SET NULL,     -- destination (for Transfer type)
    type transaction_type NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),

    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. Performance Indexes
CREATE INDEX idx_products_tenant ON products(tenant_id);
CREATE INDEX idx_products_sku ON products(tenant_id, sku);
CREATE INDEX idx_transactions_tenant_product ON inventory_transactions(tenant_id, product_id);
CREATE INDEX idx_transactions_timestamp ON inventory_transactions(tenant_id, timestamp DESC);
CREATE INDEX idx_stocks_warehouse ON stocks(warehouse_id);
CREATE INDEX idx_categories_parent ON categories(parent_id);
