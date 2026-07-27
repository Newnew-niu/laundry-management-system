"""Settings: service & price management plus connection info."""

import streamlit as st

import db
import ui


def render():
    st.title("⚙️ Settings")

    st.subheader("🧾 Service types")
    st.caption(
        "These are the cards staff see on the New Order page. Prices are set "
        "per order after processing, so a service is just a code + description. "
        "Untick **Active** to hide a service without losing its history."
    )

    df = db.fetch_df(
        "SELECT service_id, name, description, active FROM services "
        "ORDER BY service_id"
    )
    edited = st.data_editor(
        df,
        hide_index=True,
        width="stretch",
        disabled=["service_id"],
        column_config={
            "service_id": st.column_config.NumberColumn("ID", format="%d"),
            "name": st.column_config.TextColumn("Code", required=True),
            "description": st.column_config.TextColumn("Description"),
            "active": st.column_config.CheckboxColumn("Active"),
        },
        key="services_editor",
    )
    if st.button("💾 Save services", type="primary"):
        for _idx, row in edited.iterrows():
            db.execute(
                "UPDATE services SET name=?, description=?, active=? "
                "WHERE service_id=?",
                (row["name"], row["description"] or "",
                 int(bool(row["active"])), int(row["service_id"])),
            )
        ui.flash("Services saved.", "🧾")
        st.rerun()

    with st.form("add_service", clear_on_submit=True):
        st.markdown("**➕ Add a service**")
        c1, c2 = st.columns([1, 2])
        name = c1.text_input("Code *", placeholder="e.g. L")
        description = c2.text_input("Description", placeholder="e.g. Laundry + Dry + Fold")
        if st.form_submit_button("Add service", type="primary",
                                 width="stretch"):
            if not name.strip():
                st.error("Code is required.")
            else:
                db.execute(
                    "INSERT INTO services (name, description, price, unit, active) "
                    "VALUES (?, ?, 0, 'item', 1)",
                    (name.strip(), description.strip()),
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
