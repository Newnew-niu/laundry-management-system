"""Dashboard page: read-only overview of recent orders and customers."""

import pandas as pd
import streamlit as st

from db import get_connection


def render():
    st.title("👕 Dashboard - Overview")
    try:
        conn = get_connection()

        # --- Recent orders ---
        st.subheader("📦 Recent Orders")
        query_orders = """
            SELECT
                o.order_id AS 'System ID',
                o.order_code AS 'Order No.',
                o.order_date AS 'Date Created',
                c.name AS 'Customer',
                o.total_amount AS 'Amount',
                o.agreed_pickup_time AS 'Pickup Date',
                o.notes AS 'Notes'
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            ORDER BY o.order_id DESC LIMIT 10
        """
        df_orders = pd.read_sql(query_orders, conn)

        if not df_orders.empty:
            st.dataframe(
                df_orders,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "System ID": st.column_config.NumberColumn(format="%d"),
                    "Order No.": st.column_config.TextColumn(),
                    "Amount": st.column_config.NumberColumn(format="€ %.2f"),
                    "Date Created": st.column_config.DateColumn(format="DD/MM/YYYY"),
                    "Pickup Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                },
            )
        else:
            st.info("No orders found yet.")

        # --- Customer list ---
        st.subheader("👥 Customer List")
        df_customers = pd.read_sql(
            "SELECT customer_id as 'ID', name as 'Name', phone as 'Phone', "
            "notes as 'Notes' FROM customers ORDER BY customer_id DESC",
            conn,
        )
        st.dataframe(
            df_customers,
            use_container_width=True,
            hide_index=True,
            column_config={"ID": st.column_config.NumberColumn(format="%d")},
        )
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")
