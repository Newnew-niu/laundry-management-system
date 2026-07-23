-- ---------------------------------------------------------------------------
-- Laundry Management System — database schema
-- ---------------------------------------------------------------------------
-- Usage:
--   mysql -u root -p < schema.sql
--
-- This creates the `laundry_db` database and the two tables the app requires:
-- `customers` and `orders`. Adjust the database name here and in your .env if
-- you want something different.
-- ---------------------------------------------------------------------------

CREATE DATABASE IF NOT EXISTS laundry_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE laundry_db;

-- ---------------------------------------------------------------------------
-- Customers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    phone       VARCHAR(50),
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Orders
-- ---------------------------------------------------------------------------
-- The FK to customers has no ON DELETE CASCADE on purpose: the app relies on
-- MySQL error 1451 to warn "this customer still has orders" instead of
-- silently deleting order history.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id           INT AUTO_INCREMENT PRIMARY KEY,
    customer_id        INT NOT NULL,
    order_code         VARCHAR(100),
    order_date         DATE,
    agreed_pickup_time DATE,
    total_amount       DECIMAL(10, 2) DEFAULT 0.00,
    notes              TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

-- Helpful indexes for the app's search / sort patterns.
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_code ON orders (order_code);
