-- ---------------------------------------------------------------------------
-- Upgrade an existing v1 laundry_db (customers + orders only) to schema v2,
-- keeping all existing data.
--
-- Usage:
--   mysql -u root -p laundry_db < scripts/upgrade_mysql_v2.sql
-- ---------------------------------------------------------------------------

ALTER TABLE orders
    ADD COLUMN status VARCHAR(20) DEFAULT 'pending',
    ADD COLUMN paid TINYINT DEFAULT 0;

-- Existing rows get status='pending'; adjust in the app (Orders page) or e.g.:
-- UPDATE orders SET status = 'picked_up' WHERE agreed_pickup_time < CURDATE();

CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    price      DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    unit       VARCHAR(50) DEFAULT 'item',
    active     TINYINT DEFAULT 1
);

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

CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_items_order ON order_items (order_id);
