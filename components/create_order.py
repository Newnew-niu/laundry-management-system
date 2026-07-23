"""Create Order page: register a new order for an existing or new customer."""

from datetime import datetime, timedelta

import streamlit as st

from db import get_connection, get_customer_list


def render():
    st.title("🧺 Create New Order")

    try:
        st.write("Is this an Existing Customer or a New Customer?")
        customer_type = st.radio(
            "Select Type:", ["Existing Customer", "New Customer"], horizontal=True
        )

        with st.form("create_order_form"):
            customer_id_str = None
            new_name = new_phone = new_notes = None

            if customer_type == "Existing Customer":
                all_customers = get_customer_list()
                search_term = st.text_input("🔍 Search Customer (Name/Phone):")
                if search_term:
                    filtered = [
                        c for c in all_customers if search_term.lower() in c.lower()
                    ]
                else:
                    filtered = all_customers

                if filtered:
                    customer_id_str = st.selectbox("Select Customer:", filtered)
                else:
                    st.warning("No match found.")
            else:
                st.markdown("### 👤 New Customer Details")
                new_name = st.text_input("New Customer Name")
                new_phone = st.text_input("New Customer Phone")
                new_notes = st.text_input("Customer Notes (Optional)")

            st.divider()
            st.markdown("### 📝 Order Details")

            today_obj = datetime.now()
            st.info(f"📅 **Date:** {today_obj.strftime('%d/%m/%Y')}")

            order_code = st.text_input(
                "Order Number / Ticket No.", placeholder="e.g. A-101"
            )

            col1, col2 = st.columns(2)
            with col1:
                default_pickup = datetime.now() + timedelta(days=3)
                pickup_time = st.date_input(
                    "Agreed Pickup Date", default_pickup, format="DD/MM/YYYY"
                )
            with col2:
                amount = st.number_input(
                    "Total Amount (€)", min_value=0.0, step=1.0, format="%.2f"
                )

            order_notes = st.text_area(
                "Items / Description", placeholder="E.g., 3 Shirts (Dry Clean)"
            )

            submitted = st.form_submit_button("Confirm & Create Order (€)")

            if submitted:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    if customer_type == "New Customer":
                        if not new_name:
                            st.error("⚠️ Name is required!")
                            st.stop()
                        cursor.execute(
                            "INSERT INTO customers (name, phone, notes) "
                            "VALUES (%s, %s, %s)",
                            (new_name, new_phone, new_notes),
                        )
                        conn.commit()
                        final_customer_id = cursor.lastrowid
                    else:
                        if customer_id_str:
                            final_customer_id = int(
                                customer_id_str.split("|")[0]
                                .replace("ID:", "")
                                .strip()
                            )
                        else:
                            st.error("⚠️ Please select a customer.")
                            st.stop()

                    cursor.execute(
                        "INSERT INTO orders (customer_id, order_code, "
                        "agreed_pickup_time, total_amount, notes, order_date) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (
                            final_customer_id,
                            order_code,
                            pickup_time,
                            amount,
                            order_notes,
                            today_obj.date(),
                        ),
                    )
                    conn.commit()
                    st.success("✅ Order Created Successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                finally:
                    conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
