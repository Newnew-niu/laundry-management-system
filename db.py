"""Database layer for the Laundry Management System.

Centralises the MySQL connection (loaded from environment variables) and the
shared query helpers used across the UI components. Keeping all data access in
one module lets the ``components`` package stay focused on presentation.
"""

import os

import mysql.connector
import streamlit as st
from dotenv import load_dotenv

# Load variables from a local .env file into os.environ (no-op if absent).
load_dotenv()


def get_connection():
    """Open a new MySQL connection using credentials from environment variables.

    Expected variables (see ``.env.example``):
        DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "laundry_db"),
        port=int(os.getenv("DB_PORT", "3306")),
    )


def get_customer_list():
    """Return customers formatted as 'ID: <id> | <name> (<phone>)' strings."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT customer_id, name, phone FROM customers ORDER BY customer_id DESC"
        )
        customers = cursor.fetchall()
    finally:
        conn.close()
    return [f"ID: {c[0]} | {c[1]} ({c[2]})" for c in customers]


def get_order_list():
    """Return orders formatted for selection dropdowns.

    Format: 'Ticket: <code> | <customer> | (SysID: <id>) | €<amount>'
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT o.order_id, o.order_code, c.name, o.total_amount
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            ORDER BY o.order_id DESC
            """
        )
        orders = cursor.fetchall()
    finally:
        conn.close()

    formatted_list = []
    for o in orders:
        code = o[1] if o[1] else "N/A"
        formatted_list.append(f"Ticket: {code} | {o[2]} | (SysID: {o[0]}) | €{o[3]}")
    return formatted_list
