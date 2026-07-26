"""Settings: service & price management plus connection info."""

import streamlit as st

import db
import ui


def render():
    st.title("⚙️ Settings")

    st.subheader("🧾 Services & prices")
    st.caption(
        "These are the buttons staff see on the New Order page. "
        "Untick **Active** to hide a service without losing its history."
    )

    df = db.fetch_df(
        "SELECT service_id, name, price, unit, active FROM services ORDER BY service_id"
    )
    edited = st.data_editor(
        df,
        hide_index=True,
        width="stretch",
        disabled=["service_id"],
        column_config={
            "service_id": st.column_config.NumberColumn("ID", format="%d"),
            "name": st.column_config.TextColumn("Service", required=True),
            "price": st.column_config.NumberColumn("Price (€)", format="%.2f",
                                                   min_value=0.0),
            "unit": st.column_config.TextColumn("Unit"),
            "active": st.column_config.CheckboxColumn("Active"),
        },
        key="services_editor",
    )
    if st.button("💾 Save services", type="primary"):
        for _idx, row in edited.iterrows():
            db.execute(
                "UPDATE services SET name=?, price=?, unit=?, active=? "
                "WHERE service_id=?",
                (row["name"], float(row["price"]), row["unit"],
                 int(bool(row["active"])), int(row["service_id"])),
            )
        ui.flash("Services saved.", "🧾")
        st.rerun()

    with st.form("add_service", clear_on_submit=True):
        st.markdown("**➕ Add a service**")
        c1, c2, c3 = st.columns([3, 1, 1])
        name = c1.text_input("Name *")
        price = c2.number_input("Price (€)", min_value=0.0, format="%.2f")
        unit = c3.text_input("Unit", value="item")
        if st.form_submit_button("Add service", width="stretch"):
            if not name.strip():
                st.error("Name is required.")
            else:
                db.execute(
                    "INSERT INTO services (name, price, unit, active) "
                    "VALUES (?, ?, ?, 1)",
                    (name.strip(), price, unit.strip() or "item"),
                )
                ui.flash(f"Service “{name}” added.", "🧾")
                st.rerun()

    st.divider()
    st.subheader("🔌 Database")
    if db.ENGINE == "mysql":
        import os
        st.markdown(
            f"Engine: **MySQL** — `{os.getenv('DB_USER','root')}@"
            f"{os.getenv('DB_HOST','localhost')}/{os.getenv('DB_NAME','laundry_db')}`"
        )
    else:
        st.markdown(f"Engine: **SQLite** — local file `{db.DB_PATH}`")
    st.caption(
        "Switch engines via DB_ENGINE in your .env file (sqlite / mysql). "
        "See README for details."
    )
