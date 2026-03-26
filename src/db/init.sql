-- 1. Create Custom Types
CREATE TYPE transaction_type AS ENUM ('In', 'Out');
CREATE TYPE user_role AS ENUM ('Admin', 'Staff');
CREATE TYPE movement_status AS ENUM ('Draft', 'Pending', 'Completed', 'Failed', 'Cancelled');

CREATE TYPE operation_type AS ENUM (
    'Purchase',
    'Sale',
    'Transfer',
    'Adjustment',
    'Return'
);

CREATE TYPE operation_status AS ENUM (
    'Draft',
    'Pending',
    'In_Transit',
    'Completed',
    'Cancelled',
    'Failed'
);

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
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    UNIQUE (tenant_id, parent_id, name)
);

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    location TEXT,
    UNIQUE (tenant_id, name)
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
    reorder_point INTEGER NOT NULL DEFAULT 0,
    UNIQUE (tenant_id, sku)
);

-- many-to-many relationship table with quantity
CREATE TABLE stocks (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (product_id, warehouse_id)
);

-- 5. Business Layer: Inventory Operations
CREATE TABLE inventory_operations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    operation_type operation_type NOT NULL,
    status operation_status NOT NULL DEFAULT 'Draft',

    source_warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE RESTRICT,
    destination_warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE RESTRICT,

    reference_code VARCHAR(100),
    note TEXT,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_operation_warehouses_not_same
        CHECK (
            source_warehouse_id IS NULL
            OR destination_warehouse_id IS NULL
            OR source_warehouse_id <> destination_warehouse_id
        )
);

-- 6. Transaction Logging / Stock Movements
CREATE TABLE inventory_transactions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    operation_id INTEGER NOT NULL REFERENCES inventory_operations(id) ON DELETE CASCADE,

    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE SET NULL,

    type transaction_type NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    movement_status movement_status NOT NULL DEFAULT 'Draft',

    note TEXT,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. Performance Indexes
CREATE INDEX idx_products_tenant ON products(tenant_id);
CREATE INDEX idx_products_sku ON products(tenant_id, sku);

CREATE INDEX idx_transactions_tenant_product
    ON inventory_transactions(tenant_id, product_id);

CREATE INDEX idx_transactions_operation_id
    ON inventory_transactions(operation_id);

CREATE INDEX idx_transactions_timestamp
    ON inventory_transactions(tenant_id, timestamp DESC);

CREATE INDEX idx_stocks_warehouse
    ON stocks(warehouse_id);

CREATE INDEX idx_categories_parent
    ON categories(parent_id);

CREATE INDEX idx_operations_tenant_status
    ON inventory_operations(tenant_id, status);

CREATE INDEX idx_operations_source_warehouse
    ON inventory_operations(source_warehouse_id);

CREATE INDEX idx_operations_destination_warehouse
    ON inventory_operations(destination_warehouse_id);
