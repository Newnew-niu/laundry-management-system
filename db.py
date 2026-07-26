"""Database layer for the Laundry Management System.

Supports two engines, selected via the ``DB_ENGINE`` environment variable:

* ``sqlite`` (default) — zero-setup local file database (``DB_PATH``,
  default ``laundry.db``). Tables are created automatically on first run.
* ``mysql`` — production-style setup using the ``DB_HOST/PORT/USER/PASSWORD/NAME``
  variables. Create the tables with ``schema.sql`` first.

All UI code goes through the small helpers here (``fetch_all`` / ``fetch_one`` /
``fetch_df`` / ``execute``) and writes SQL with ``?`` placeholders; the layer
adapts them to the active engine. Keep every SQL statement in this style so both
engines keep working.
"""

import datetime as _dt
import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
DB_PATH = os.getenv("DB_PATH", "laundry.db")

DEFAULT_SERVICES = [
    ("Wash & Fold", 8.00, "kg"),
    ("Dry Cleaning", 12.00, "item"),
    ("Ironing", 3.00, "item"),
    ("Bedding / Duvet", 15.00, "item"),
    ("Shoes Cleaning", 10.00, "pair"),
    ("Express (24h) Surcharge", 5.00, "order"),
]

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    phone       TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS orders (
    order_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id        INTEGER NOT NULL REFERENCES customers (customer_id),
    order_code         TEXT,
    order_date         TEXT,
    agreed_pickup_time TEXT,
    status             TEXT DEFAULT 'pending',
    paid               INTEGER DEFAULT 0,
    total_amount       REAL DEFAULT 0,
    notes              TEXT,
    created_at         TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    price      REAL NOT NULL DEFAULT 0,
    unit       TEXT DEFAULT 'item',
    active     INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS order_items (
    item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders (order_id),
    service_id   INTEGER,
    service_name TEXT NOT NULL,
    unit_price   REAL NOT NULL DEFAULT 0,
    quantity     REAL NOT NULL DEFAULT 1
);
"""


def get_connection():
    """Open a new connection to the active engine."""
    if ENGINE == "mysql":
        import mysql.connector

        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "laundry_db"),
            port=int(os.getenv("DB_PORT", "3306")),
        )
    return sqlite3.connect(DB_PATH)


def _adapt(sql, params):
    """Convert `?` placeholders and date params for the active engine."""
    if ENGINE == "mysql":
        sql = sql.replace("?", "%s")
    params = tuple(
        p.isoformat() if isinstance(p, (_dt.date, _dt.datetime)) else p
        for p in params
    )
    return sql, params


def fetch_all(sql, params=()):
    sql, params = _adapt(sql, params)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def fetch_df(sql, params=()):
    """Run a query and return a pandas DataFrame (engine-agnostic)."""
    import pandas as pd

    sql, params = _adapt(sql, params)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [d[0] for d in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)
    finally:
        conn.close()


def execute(sql, params=()):
    """Run a write statement; returns the last inserted row id (if any)."""
    sql, params = _adapt(sql, params)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


_initialised = False


def init_db():
    """Create tables (SQLite) and seed default services if none exist yet."""
    global _initialised
    if _initialised:
        return
    if ENGINE != "mysql":
        conn = get_connection()
        try:
            conn.executescript(_SQLITE_SCHEMA)
            conn.commit()
        finally:
            conn.close()
    if fetch_one("SELECT COUNT(*) FROM services")[0] == 0:
        for name, price, unit in DEFAULT_SERVICES:
            execute(
                "INSERT INTO services (name, price, unit, active) VALUES (?, ?, ?, 1)",
                (name, price, unit),
            )
    _initialised = True


# ---------------------------------------------------------------------------
# Shared queries
# ---------------------------------------------------------------------------

def next_order_code():
    """Generate a ticket number like L260726-003 (date + daily sequence)."""
    today = _dt.date.today()
    prefix = f"L{today.strftime('%y%m%d')}"
    row = fetch_one(
        "SELECT COUNT(*) FROM orders WHERE order_code LIKE ?", (prefix + "%",)
    )
    return f"{prefix}-{row[0] + 1:03d}"


def search_customers(term=""):
    """Customers matching name or phone, newest first."""
    like = f"%{term.strip()}%"
    return fetch_all(
        """
        SELECT customer_id, name, phone, notes FROM customers
        WHERE name LIKE ? OR phone LIKE ?
        ORDER BY customer_id DESC
        """,
        (like, like),
    )


def get_active_services():
    return fetch_all(
        "SELECT service_id, name, price, unit FROM services "
        "WHERE active = 1 ORDER BY service_id"
    )


def get_orders(status=None, term="", limit=100):
    """Orders joined with customer info, newest first, optional filters."""
    sql = """
        SELECT o.order_id, o.order_code, c.name, c.phone,
               o.order_date, o.agreed_pickup_time, o.status, o.paid,
               o.total_amount, o.notes, o.customer_id
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
    """
    where, params = [], []
    if status:
        where.append("o.status = ?")
        params.append(status)
    if term.strip():
        like = f"%{term.strip()}%"
        where.append("(o.order_code LIKE ? OR c.name LIKE ? OR c.phone LIKE ?)")
        params += [like, like, like]
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY o.order_id DESC LIMIT ?"
    params.append(limit)
    return fetch_all(sql, tuple(params))


def get_order_items(order_ids):
    """Return {order_id: 'Service ×qty, …'} for the given ids."""
    if not order_ids:
        return {}
    marks = ",".join("?" * len(order_ids))
    rows = fetch_all(
        f"SELECT order_id, service_name, quantity FROM order_items "
        f"WHERE order_id IN ({marks}) ORDER BY item_id",
        tuple(order_ids),
    )
    summary = {}
    for oid, name, qty in rows:
        qty_txt = f"{qty:g}"
        summary.setdefault(oid, []).append(f"{name} ×{qty_txt}")
    return {oid: ", ".join(parts) for oid, parts in summary.items()}


def create_order(customer_id, order_code, pickup_date, items, paid, notes):
    """Insert an order plus its line items; returns (order_id, total)."""
    total = sum(price * qty for _sid, _name, price, qty in items)
    order_id = execute(
        """
        INSERT INTO orders (customer_id, order_code, order_date,
                            agreed_pickup_time, status, paid, total_amount, notes)
        VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
        """,
        (
            customer_id,
            order_code,
            _dt.date.today(),
            pickup_date,
            1 if paid else 0,
            total,
            notes,
        ),
    )
    for service_id, name, price, qty in items:
        execute(
            "INSERT INTO order_items (order_id, service_id, service_name, "
            "unit_price, quantity) VALUES (?, ?, ?, ?, ?)",
            (order_id, service_id, name, price, qty),
        )
    return order_id, total
