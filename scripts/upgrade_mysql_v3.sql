-- ---------------------------------------------------------------------------
-- Upgrade a v2 laundry_db to schema v3: service *types* + deferred pricing.
--
-- v3 changes:
--   * services gains a description column
--   * the old priced services are deactivated (kept for order history)
--   * the 8 real service-type codes are inserted
--   * order prices are now entered after processing; new orders store
--     total_amount = NULL ("TBD") — no structural change needed, the column
--     was already nullable.
--
-- Usage:
--   mysql -u root -p laundry_db < scripts/upgrade_mysql_v3.sql
-- ---------------------------------------------------------------------------

ALTER TABLE services ADD COLUMN description VARCHAR(255) DEFAULT '';

UPDATE services SET active = 0;

INSERT INTO services (name, description, price, unit, active) VALUES
    ('L', 'Laundry + Dry + Fold', 0, 'item', 1),
    ('B+W/P', 'Wash + Iron', 0, 'item', 1),
    ('S+W/P', 'Wash + Iron', 0, 'item', 1),
    ('B+P/O', 'Iron Only', 0, 'item', 1),
    ('S++P/O', 'Iron Only', 0, 'item', 1),
    ('Dry Only', '', 0, 'item', 1),
    ('Duvet', '', 0, 'item', 1),
    ('Dry Clean', '', 0, 'item', 1);
