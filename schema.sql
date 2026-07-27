-- ---------------------------------------------------------------------------
-- Laundry Management System — MySQL schema (v2)
-- ---------------------------------------------------------------------------
-- Only needed when DB_ENGINE=mysql. The default SQLite engine creates its
-- tables automatically on first run.
--
-- Usage:
--   mysql -u root -p < schema.sql
--
-- Upgrading from the v1 schema (no status/paid/services)? Run
-- scripts/upgrade_mysql_v2.sql instead, so your existing data is kept.
-- ---------------------------------------------------------------------------

CREATE DATABASE IF NOT EXISTS laundry_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE laundry_db;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    phone       VARCHAR(50),
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status flow: pending -> washing -> ready -> picked_up
-- ("overdue" is derived by the app: pickup date in the past & not picked up.)
CREATE TABLE IF NOT EXISTS orders (
    order_id           INT AUTO_INCREMENT PRIMARY KEY,
    customer_id        INT NOT NULL,
    order_code         VARCHAR(100),
    order_date         DATE,
    agreed_pickup_time DATE,
    status             VARCHAR(20) DEFAULT 'pending',
    paid               TINYINT DEFAULT 0,
    total_amount       DECIMAL(10, 2) DEFAULT 0.00,
    notes              TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

-- Services are *types* (code + description); the price is decided per order
-- after processing, so the price/unit columns are legacy and unused.
CREATE TABLE IF NOT EXISTS services (
    service_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description VARCHAR(255) DEFAULT '',
    price       DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    unit        VARCHAR(50) DEFAULT 'item',
    active      TINYINT DEFAULT 1
);

-- Line items snapshot the service name & price at order time, so later price
-- changes never rewrite past bills.
CREATE TABLE IF NOT EXISTS order_items (
    item_id      INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT NOT NULL,
    service_id   INT,
    service_name VARCHAR(255) NOT NULL,
    unit_price   DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    quantity     DECIMAL(10, 2) NOT NULL DEFAULT 1,
    CONSTRAINT fk_items_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_code ON orders (order_code);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_items_order ON order_items (order_id);

-- Starter service types (the app also seeds these automatically if the table
-- is empty). total_amount on orders stays NULL ("TBD") until staff enter the
-- final price after processing.
INSERT INTO services (name, description, price, unit, active) VALUES
    ('L', 'Laundry + Dry + Fold', 0, 'item', 1),
    ('B+W/P', 'Wash + Iron', 0, 'item', 1),
    ('S+W/P', 'Wash + Iron', 0, 'item', 1),
    ('B+P/O', 'Iron Only', 0, 'item', 1),
    ('S++P/O', 'Iron Only', 0, 'item', 1),
    ('Dry Only', '', 0, 'item', 1),
    ('Duvet', '', 0, 'item', 1),
    ('Dry Clean', '', 0, 'item', 1);
