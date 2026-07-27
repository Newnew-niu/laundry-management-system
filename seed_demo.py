"""Seed the database with FAKE demo data so the UI has something to show.

Usage:
    python seed_demo.py            # seeds the SQLite database (safe)
    python seed_demo.py --force    # required to seed a MySQL database

All names and phone numbers below are invented — never seed a production
database that already holds real customer data.
"""

import argparse
import datetime as dt
import random
import sys

import db

FAKE_CUSTOMERS = [
    ("Demo Alice", "+00 600 000 001", "Prefers unscented detergent"),
    ("Demo Bob", "+00 600 000 002", ""),
    ("Demo Carla", "+00 600 000 003", "Regular — every Monday"),
    ("Demo David", "+00 600 000 004", ""),
    ("Demo Elena", "+00 600 000 005", "Allergic to softener"),
    ("Demo Frank", "+00 600 000 006", ""),
    ("Demo Grace", "+00 600 000 007", "Company account"),
    ("Demo Henry", "+00 600 000 008", ""),
]

STATUS_WEIGHTS = [
    ("pending", 2),
    ("washing", 3),
    ("ready", 3),
    ("picked_up", 4),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="allow seeding a MySQL database")
    args = parser.parse_args()

    if db.ENGINE == "mysql" and not args.force:
        sys.exit(
            "Refusing to seed a MySQL database (it may hold real data). "
            "Re-run with --force if you are sure."
        )

    db.init_db()
    random.seed(42)

    customer_ids = [
        db.execute(
            "INSERT INTO customers (name, phone, notes) VALUES (?, ?, ?)", c
        )
        for c in FAKE_CUSTOMERS
    ]

    services = db.get_active_services()
    statuses = [s for s, w in STATUS_WEIGHTS for _ in range(w)]
    today = dt.date.today()

    n_orders = 16
    for i in range(n_orders):
        order_date = today - dt.timedelta(days=random.randint(0, 9))
        pickup = order_date + dt.timedelta(days=random.randint(1, 4))
        status = random.choice(statuses)

        picks = random.sample(services, k=random.randint(1, 2))
        selected = [(sid, name) for sid, name, _desc in picks]
        code = f"L{order_date.strftime('%y%m%d')}-{i + 1:03d}"

        order_id = db.create_order(
            random.choice(customer_ids), code, pickup, selected, "Demo order"
        )

        # Pricing happens after processing: most ready/picked-up orders are
        # priced (a couple stay TBD); pending/washing orders have no price yet.
        amount = None
        paid = 0
        if status in ("ready", "picked_up") and random.random() < 0.8:
            amount = float(random.randint(8, 60))
            paid = 1 if (status == "picked_up" or random.random() < 0.5) else 0
        db.execute(
            "UPDATE orders SET status = ?, order_date = ?, total_amount = ?, "
            "paid = ? WHERE order_id = ?",
            (status, order_date, amount, paid, order_id),
        )

    print(f"Seeded {len(customer_ids)} demo customers and {n_orders} demo orders "
          f"into the {db.ENGINE} database.")


if __name__ == "__main__":
    main()
