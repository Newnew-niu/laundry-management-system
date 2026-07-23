# 👕 Laundry Management System

A lightweight, self-hosted management tool for laundry and dry-cleaning shops,
built with [Streamlit](https://streamlit.io/) and MySQL. Track customers,
create and edit orders, and get a quick daily overview — all from a clean web UI
that runs on your own machine.

---

## ✨ Features

- **Dashboard** — see the 10 most recent orders and the full customer list at a
  glance, with amounts in € and dates in `DD/MM/YYYY`.
- **Create Order** — register an order for an existing customer (with live
  search) or add a brand-new customer in the same step.
- **Manage Data** — edit or delete existing orders and customers, or add a
  customer without an order. Deleting a customer who still has orders is blocked
  to protect your order history.
- **Secure configuration** — database credentials live in a git-ignored `.env`
  file, never in the source code.

---

## 🗂️ Project structure

```
Laundryapp/
├── app.py                 # Main entry point: page config + sidebar navigation
├── db.py                  # Database connection (from .env) + shared queries
├── components/            # UI pages, one render() per module
│   ├── __init__.py
│   ├── dashboard.py       # Dashboard / overview page
│   ├── create_order.py    # Create New Order page
│   └── manage_data.py     # Manage Orders & Customers page
├── schema.sql             # Database + table creation script
├── requirements.txt       # Python dependencies
├── .env.example           # Template for your local .env
├── .gitignore             # Keeps .env and build artifacts out of git
├── LICENSE                # MIT License
└── README.md              # This file
```

---

## 🚀 Getting started

### 1. Prerequisites

- Python 3.9+
- A running MySQL server (8.0+ recommended)

### 2. Clone and install dependencies

```bash
git clone <your-repo-url>
cd Laundryapp

# (optional but recommended) create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Set up the database

Run the schema script to create the `laundry_db` database and its tables:

```bash
mysql -u root -p < schema.sql
```

### 4. Configure your credentials

Copy the template and fill in your own MySQL details:

```bash
cp .env.example .env
```

```ini
# .env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=laundry_db
```

> The `.env` file is listed in `.gitignore`, so your password will **not** be
> committed to the repository.

### 5. Run the app

```bash
streamlit run app.py
```

Streamlit will open the app in your browser (default: http://localhost:8501).

---

## ⚙️ Configuration reference

| Variable      | Description                     | Default      |
| ------------- | ------------------------------- | ------------ |
| `DB_HOST`     | MySQL host                      | `localhost`  |
| `DB_PORT`     | MySQL port                      | `3306`       |
| `DB_USER`     | MySQL username                  | `root`       |
| `DB_PASSWORD` | MySQL password                  | *(none)*     |
| `DB_NAME`     | Database name                   | `laundry_db` |

---

## 🤝 Contributing

Issues and pull requests are welcome. Please keep UI logic inside the
`components/` package and all data access inside `db.py` so the separation of
concerns stays intact.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
