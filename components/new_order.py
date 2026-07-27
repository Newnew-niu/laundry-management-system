"""New Order: POS-style flow — pick customer, tap service types, one big
submit button. Pricing happens later, from the Orders page, once the items
have been processed."""

import datetime as dt

import streamlit as st

import db
import ui


def _reset_selection():
    for key in list(st.session_state):
        if key.startswith("svc_"):
            del st.session_state[key]


def _customer_picker():
    """Returns (customer_id or None, new_customer dict or None)."""
    kind = st.radio(
        "Customer",
        ["🔍 Existing customer", "➕ New customer"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if kind.startswith("🔍"):
        term = st.text_input(
            "Search by phone or name", placeholder="Type a phone number or name…"
        )
        matches = db.search_customers(term)
        if not matches:
            st.warning("No customer found — switch to **New customer** to add one.")
            return None, None
        options = {
            f"{name}  ·  📞 {phone or '—'}  (ID {cid})": cid
            for cid, name, phone, _notes in matches[:30]
        }
        choice = st.selectbox("Select customer", list(options.keys()))
        return options[choice], None

    col1, col2 = st.columns(2)
    name = col1.text_input("Name *")
    phone = col2.text_input("Phone")
    return None, {"name": name.strip(), "phone": phone.strip()}


def render():
    st.title("🧺 New Order")

    # --- Step 1: customer ---
    st.markdown("#### 1️⃣ Who is it for?")
    customer_id, new_customer = _customer_picker()

    # --- Step 2: service types (multi-select cards, no prices) ---
    st.markdown("#### 2️⃣ Service")
    services = db.get_active_services()
    if not services:
        st.info("No services configured yet — add some in **Settings** first.")
        return

    selected = []
    cols = st.columns(4)
    for i, (sid, name, description) in enumerate(services):
        with cols[i % 4].container(border=True):
            st.markdown(f"**{name}**")
            st.caption(description or "&nbsp;", unsafe_allow_html=True)
            if st.toggle("Select", key=f"svc_{sid}"):
                selected.append((sid, name))

    # --- Step 3: details + big submit (no price yet — entered after
    # processing, from the Orders page) ---
    st.markdown("#### 3️⃣ Confirm")
    col1, col2 = st.columns(2)
    order_code = col1.text_input("Ticket no.", value=db.next_order_code())
    pickup = col2.date_input(
        "Pickup date", dt.date.today() + dt.timedelta(days=2), format="DD/MM/YYYY"
    )
    notes = st.text_input("Notes (optional)", placeholder="E.g. red wine stain on shirt")

    if selected:
        st.markdown("🧾 " + "  ·  ".join(name for _sid, name in selected))

    if st.button(
        "✅ Create order",
        type="primary",
        width="stretch",
        disabled=not selected,
    ):
        if new_customer is not None:
            if not new_customer["name"]:
                st.error("⚠️ Customer name is required.")
                st.stop()
            customer_id = db.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?)",
                (new_customer["name"], new_customer["phone"]),
            )
        if customer_id is None:
            st.error("⚠️ Please select or add a customer first.")
            st.stop()

        db.create_order(
            customer_id, order_code.strip(), pickup, selected, notes.strip()
        )
        _reset_selection()
        ui.flash(f"Order {order_code} created — price to be set after processing.",
                 "🧺")
        st.rerun()

    if not selected:
        st.caption("Tap at least one service card above to enable the button.")
