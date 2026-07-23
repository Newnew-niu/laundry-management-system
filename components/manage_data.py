"""Manage Data page: edit / delete orders and customers, or add a customer."""

import re
from datetime import datetime

import mysql.connector
import streamlit as st

from db import get_connection, get_customer_list, get_order_list


def _render_orders_tab():
    st.subheader("Edit or Delete Orders")
    try:
        all_orders = get_order_list()
        if not all_orders:
            st.info("No orders found.")
            return

        search_order = st.text_input(
            "🔍 Search Order (Ticket No., ID, Name):", placeholder="e.g. 888"
        )
        filtered_orders = (
            [o for o in all_orders if search_order.lower() in o.lower()]
            if search_order
            else all_orders
        )

        if not filtered_orders:
            st.warning("No match.")
            return

        selected_order_str = st.selectbox("Select Order:", filtered_orders)
        match = re.search(r"SysID:\s*(\d+)", selected_order_str)
        if not match:
            return

        selected_order_id = int(match.group(1))
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT order_code, agreed_pickup_time, total_amount, notes "
            "FROM orders WHERE order_id = %s",
            (selected_order_id,),
        )
        current_data = cursor.fetchone()
        conn.close()

        if not current_data:
            return

        current_code, current_pickup, current_amount, current_notes = current_data
        with st.form("edit_order_form"):
            new_code = st.text_input("Order No.", value=current_code)

            pickup_val = (
                current_pickup
                if not isinstance(current_pickup, str)
                else datetime.strptime(current_pickup, "%Y-%m-%d").date()
            )
            new_pickup = st.date_input(
                "Pickup Date", value=pickup_val, format="DD/MM/YYYY"
            )
            new_amount = st.number_input(
                "Amount (€)", value=float(current_amount), format="%.2f"
            )
            new_notes = st.text_area("Notes", value=current_notes)

            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Update"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE orders SET order_code=%s, agreed_pickup_time=%s, "
                    "total_amount=%s, notes=%s WHERE order_id=%s",
                    (new_code, new_pickup, new_amount, new_notes, selected_order_id),
                )
                conn.commit()
                conn.close()
                st.success("Updated!")
                st.rerun()
            if c2.form_submit_button("🗑️ DELETE", type="primary"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM orders WHERE order_id=%s", (selected_order_id,)
                )
                conn.commit()
                conn.close()
                st.warning("Deleted.")
                st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")


def _render_add_customer():
    st.subheader("Add a New Customer (No Order)")
    with st.form("add_only_customer"):
        name = st.text_input("Name *")
        phone = st.text_input("Phone")
        notes = st.text_input("Notes")

        if st.form_submit_button("Save New Customer"):
            if not name:
                st.error("Name is required.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO customers (name, phone, notes) "
                        "VALUES (%s, %s, %s)",
                        (name, phone, notes),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Customer '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def _render_edit_customer():
    st.subheader("Edit or Delete Customers")
    try:
        all_customers = get_customer_list()
        if not all_customers:
            st.info("No customers found.")
            return

        search_cust = st.text_input("🔍 Search Customer:", placeholder="Name or Phone...")
        filtered_custs = (
            [c for c in all_customers if search_cust.lower() in c.lower()]
            if search_cust
            else all_customers
        )

        if not filtered_custs:
            st.warning("No match.")
            return

        selected_cust_str = st.selectbox("Select Customer:", filtered_custs)
        selected_cust_id = int(
            selected_cust_str.split("|")[0].replace("ID:", "").strip()
        )

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, phone, notes FROM customers WHERE customer_id = %s",
            (selected_cust_id,),
        )
        c_data = cursor.fetchone()
        conn.close()

        if not c_data:
            return

        c_name, c_phone, c_notes = c_data
        with st.form("edit_customer_form"):
            edit_name = st.text_input("Name", value=c_name)
            edit_phone = st.text_input("Phone", value=c_phone)
            edit_notes = st.text_area("Notes", value=c_notes)

            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Update"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE customers SET name=%s, phone=%s, notes=%s "
                    "WHERE customer_id=%s",
                    (edit_name, edit_phone, edit_notes, selected_cust_id),
                )
                conn.commit()
                conn.close()
                st.success("Customer Updated!")
                st.rerun()
            if c2.form_submit_button("🗑️ DELETE", type="primary"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM customers WHERE customer_id=%s",
                        (selected_cust_id,),
                    )
                    conn.commit()
                    conn.close()
                    st.warning("Customer Deleted.")
                    st.rerun()
                except mysql.connector.Error as err:
                    if err.errno == 1451:
                        st.error(
                            "🚫 Cannot delete: This customer has orders! "
                            "Delete orders first."
                        )
    except Exception as e:
        st.error(f"Error: {e}")


def render():
    st.title("🔧 Manage Data")

    tab1, tab2 = st.tabs(["📦 Manage Orders", "👥 Manage Customers"])

    with tab1:
        _render_orders_tab()

    with tab2:
        mode = st.radio(
            "Choose Action:",
            ["🔍 Edit / Delete Existing", "➕ Add New Customer Only"],
            horizontal=True,
        )
        if mode == "➕ Add New Customer Only":
            _render_add_customer()
        else:
            _render_edit_customer()
