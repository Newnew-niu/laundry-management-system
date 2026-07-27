"""Customers: search, add, edit and delete (delete is blocked while the
customer still has orders, to protect history)."""

import streamlit as st

import db
import ui


@st.dialog("✏️ Edit customer")
def _edit_dialog(cid, name, phone, notes):
    new_name = st.text_input("Name *", value=name or "")
    new_phone = st.text_input("Phone", value=phone or "")
    new_notes = st.text_area("Notes", value=notes or "")
    if st.button("💾 Save changes", type="primary", width="stretch"):
        if not new_name.strip():
            st.error("Name is required.")
            return
        db.execute(
            "UPDATE customers SET name=?, phone=?, notes=? WHERE customer_id=?",
            (new_name.strip(), new_phone.strip(), new_notes.strip(), cid),
        )
        ui.flash(f"Customer “{new_name}” updated.")
        st.rerun()


@st.dialog("🗑️ Delete customer?")
def _delete_dialog(cid, name):
    n_orders = db.fetch_one(
        "SELECT COUNT(*) FROM orders WHERE customer_id = ?", (cid,)
    )[0]
    if n_orders:
        st.error(
            f"🚫 **{name}** still has {n_orders} order(s). "
            "Delete those orders first to keep the books consistent."
        )
        if st.button("OK", width="stretch"):
            st.rerun()
        return
    st.warning(f"Delete customer **{name}**? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Yes, delete", key="confirm_del_cust", width="stretch"):
        db.execute("DELETE FROM customers WHERE customer_id = ?", (cid,))
        ui.flash(f"Customer “{name}” deleted.", "🗑️")
        st.rerun()
    if c2.button("Cancel", width="stretch"):
        st.rerun()


def render():
    st.title("👥 Customers")

    with st.expander("➕ Add a new customer"):
        with st.form("add_customer", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name *")
            phone = c2.text_input("Phone")
            notes = st.text_input("Notes")
            if st.form_submit_button("Save customer", type="primary",
                                     width="stretch"):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    db.execute(
                        "INSERT INTO customers (name, phone, notes) VALUES (?, ?, ?)",
                        (name.strip(), phone.strip(), notes.strip()),
                    )
                    ui.flash(f"Customer “{name}” added.", "👥")
                    st.rerun()

    term = st.text_input(
        "Search",
        value=st.session_state.pop("customers_prefill", ""),
        placeholder="🔍 Search by name or phone…",
        label_visibility="collapsed",
    )
    customers = db.search_customers(term)

    if not customers:
        st.info("No customers yet — add your first one above. 👆")
        return

    order_counts = dict(
        db.fetch_all("SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id")
    )
    st.caption(f"{len(customers)} customer(s)")

    for cid, name, phone, notes in customers:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
            c1.markdown(f"**{name}**  \n📞 {phone or '—'}")
            c2.markdown(f"📝 {notes or '—'}")
            c3.markdown(f"🧺 {order_counts.get(cid, 0)} order(s)")
            with c4:
                if st.button("✏️ Edit", key=f"cedit_{cid}", width="stretch"):
                    _edit_dialog(cid, name, phone, notes)
                if st.button("🗑️ Delete", key=f"cdel_{cid}", width="stretch"):
                    _delete_dialog(cid, name)
