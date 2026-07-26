"""New Order: POS-style flow — pick customer, tap services, auto total, one
big submit button. Widgets stay outside st.form so the total updates live."""

import datetime as dt

import streamlit as st

import db
import ui


def _reset_quantities():
    for key in list(st.session_state):
        if key.startswith("qty_"):
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

    # --- Step 2: services with quantity steppers ---
    st.markdown("#### 2️⃣ What are we washing?")
    services = db.get_active_services()
    if not services:
        st.info("No services configured yet — add some in **Settings** first.")
        return

    items = []
    cols = st.columns(3)
    for i, (sid, name, price, unit) in enumerate(services):
        with cols[i % 3].container(border=True):
            st.markdown(f"**{name}**  \n{ui.euro(price)} / {unit}")
            qty = st.number_input(
                f"Qty — {name}",
                min_value=0.0,
                step=1.0,
                format="%g",
                key=f"qty_{sid}",
                label_visibility="collapsed",
            )
            if qty > 0:
                items.append((sid, name, float(price), float(qty)))

    total = sum(price * qty for _s, _n, price, qty in items)

    # --- Step 3: details + big submit ---
    st.markdown("#### 3️⃣ Confirm")
    col1, col2, col3 = st.columns(3)
    order_code = col1.text_input("Ticket no.", value=db.next_order_code())
    pickup = col2.date_input(
        "Pickup date", dt.date.today() + dt.timedelta(days=2), format="DD/MM/YYYY"
    )
    paid = col3.toggle("Paid now 💶", value=False)
    notes = st.text_input("Notes (optional)", placeholder="E.g. red wine stain on shirt")

    if items:
        summary = "  ·  ".join(f"{n} ×{q:g}" for _s, n, _p, q in items)
        st.markdown(f"🧾 {summary}")

    if st.button(
        f"✅ Create order — {ui.euro(total)}",
        type="primary",
        width="stretch",
        disabled=not items,
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

        _oid, total = db.create_order(
            customer_id, order_code.strip(), pickup, items, paid, notes.strip()
        )
        _reset_quantities()
        ui.flash(f"Order {order_code} created — {ui.euro(total)}", "🧺")
        st.rerun()

    if not items:
        st.caption("Tap a quantity above to add services — the total updates live.")
