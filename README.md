# 👕 Laundry Management System

A friendly, **big-type** point-of-sale and order tracker for laundry & dry-cleaning
shops — built with [Streamlit](https://streamlit.io/) so non-technical staff can
run the counter with zero training. Works out of the box on **SQLite** (no
database setup at all) and scales up to **MySQL**.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.45%2B-ff4b4b)
![License](https://img.shields.io/badge/license-MIT-green)

> 🖼️ **Screenshots coming soon** — see `docs/screenshots/` for the shot list.
> The dashboard shows a row of colored KPI cards (orders today, ready for
> pickup, in progress, overdue, unpaid €) above a one-tap "pickups due today" list.

---

## ✨ Features

- **📊 KPI dashboard** — today's orders, ready-for-pickup, in-progress, overdue
  and unpaid totals as big metric cards, plus a *pickups due today* action list.
- **🧺 POS-style order entry** — search a customer by phone, tap services with
  quantity steppers, watch the total update live, hit one big button. ~20 seconds
  per order.
- **🎨 Color status badges** — `🕐 Pending → 🌀 Washing → ✅ Ready → 📦 Picked up`,
  with `⚠️ Overdue` derived automatically; every state is icon + label, never
  color alone.
- **💶 Payment tracking** — paid/unpaid per order, one-tap *Mark paid*, unpaid
  total on the dashboard.
- **🔍 Global search** — one box finds customers and orders by name, phone or
  ticket number from anywhere in the app.
- **🧾 Services & prices** — manage your service menu (name, price, unit,
  active) in Settings; line items snapshot prices so old bills never change.
- **🔒 Safe by default** — credentials live in a git-ignored `.env`, customer
  deletion is blocked while orders exist, destructive actions get confirmation
  dialogs.

## 🚀 Quick start (SQLite — one minute)

```bash
git clone https://github.com/Newnew-niu/laundry-management-system.git
cd laundry-management-system
pip install -r requirements.txt
python seed_demo.py        # optional: fake demo data so the UI isn't empty
streamlit run app.py
```

That's it — no database server needed. A local `laundry.db` file is created and
the service menu is seeded automatically. Open http://localhost:8501.

## 🐬 Using MySQL instead

1. Create the schema:

   ```bash
   mysql -u root -p < schema.sql
   ```

   (Upgrading from the v1 schema? Use `scripts/upgrade_mysql_v2.sql` to keep
   your data.)

2. Configure `.env`:

   ```bash
   cp .env.example .env
   ```

   ```ini
   DB_ENGINE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password_here
   DB_NAME=laundry_db
   ```

3. `streamlit run app.py`

## ☁️ Deploy free on Streamlit Community Cloud

1. Fork / push this repo to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub
   and click **New app**.
3. Pick this repo, branch `main`, main file `app.py` → **Deploy**.
4. Done — you get a public `https://<your-app>.streamlit.app` URL.

Notes:

- With the default SQLite engine the cloud demo works instantly, but the file
  system is **ephemeral** — data resets when the app restarts. Fine for demos.
- For persistent data, point the app at a hosted MySQL instance by adding the
  `DB_*` values in the app's **Settings → Secrets** (they're read via
  `st.secrets` automatically):

  ```toml
  DB_ENGINE = "mysql"
  DB_HOST = "your-mysql-host"
  DB_PORT = "3306"
  DB_USER = "user"
  DB_PASSWORD = "password"
  DB_NAME = "laundry_db"
  ```

## 🗂️ Project structure

```
├── app.py                        # Entry point: theme, nav, global search
├── ui.py                         # Status badges, colors, CSS, toast helpers
├── db.py                         # DB layer: SQLite/MySQL engines + queries
├── components/
│   ├── dashboard.py              # KPI cards + pickups due today
│   ├── new_order.py              # POS-style order entry
│   ├── orders.py                 # Search/filter list, status flow, edit/delete
│   ├── customers.py              # Customer directory & management
│   └── settings.py               # Service menu & prices, DB info
├── .streamlit/config.toml        # Light theme, 18px base font
├── schema.sql                    # MySQL schema (v2)
├── scripts/upgrade_mysql_v2.sql  # v1 → v2 migration (keeps data)
├── seed_demo.py                  # Fake demo data (SQLite by default)
├── .env.example                  # Configuration template
└── requirements.txt
```

## 🔄 Order status flow

```
🕐 Pending ──▶ 🌀 Washing ──▶ ✅ Ready ──▶ 📦 Picked up
                                 │
             past pickup date ▼ (derived, not stored)
                            ⚠️ Overdue
```

Advance an order with one tap from the Dashboard or Orders page.

## 🙏 Acknowledgements

Interaction ideas (ticket-number lookup, status workflow, service-quantity
ordering) were informed by studying open-source projects
[openlaundry](https://github.com/vmasdani/openlaundry),
[laundrymanagement](https://github.com/abhyudaya3/laundrymanagement) and
[laundry_managment_system](https://github.com/MeetSherasiya/laundry_managment_system).
All code in this repository is written from scratch.

## 🤝 Contributing

Issues and PRs welcome. Keep UI logic in `components/`, data access in `db.py`
(write SQL with `?` placeholders so both engines keep working), and shared
styling in `ui.py`.

## 📄 License

[MIT](LICENSE)
