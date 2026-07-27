"""Orders: searchable, status-filtered list with one-tap status advance,
mark-paid, edit dialog and delete confirmation."""

import streamlit as st

import db
import ui

FILTERS = ["All", "Pending", "Washing", "Ready", "Overdue", "Picked up"]
FILTER_TO_STATUS = {
    "Pending": "pending",
    "Washing": "washing",
    "Ready": "ready",
    "Picked up": "picked_up",
}


@st.dialog("✏️ Edit order")
def _edit_dialog(order):
    (oid, code, _name, _phone, _odate, pickup, status, paid, amount, notes, _cid) = order
    new_code = st.text_input("Ticket no.", value=code or "")
    new_pickup = st.date_input(
        "Pickup date", value=ui.to_date(pickup), format="DD/MM/YYYY"
    )
    new_status = st.selectbox(
        "Status",
        ui.STATUS_FLOW,
        index=ui.STATUS_FLOW.index(status),
        format_func=lambda s: f"{ui.STATUS_META[s][1]} {ui.STATUS_META[s][0]}",
    )
    new_amount = st.number_input(
        "Amount (€) — leave empty for TBD",
        value=None if amount is None else float(amount),
        min_value=0.0,
        format="%.2f",
        placeholder="TBD",
    )
    new_paid = st.toggle("Paid 💶", value=bool(paid))
    new_notes = st.text_area("Notes", value=notes or "")
    if st.button("💾 Save changes", type="primary", width="stretch"):
        db.execute(
            "UPDATE orders SET order_code=?, agreed_pickup_time=?, status=?, "
            "total_amount=?, paid=?, notes=? WHERE order_id=?",
            (new_code, new_pickup, new_status, new_amount,
             1 if new_paid else 0, new_notes, oid),
        )
        ui.flash(f"Order {new_code or oid} updated.")
        st.rerun()


@st.dialog("🗑️ Delete order?")
def _delete_dialog(oid, code):
    st.warning(f"Delete order **{code or oid}**? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Yes, delete", key="confirm_del_order", width="stretch"):
        db.execute("DELETE FROM order_items WHERE order_id = ?", (oid,))
        db.execute("DELETE FROM orders WHERE order_id = ?", (oid,))
        ui.flash(f"Order {code or oid} deleted.", "🗑️")
        st.rerun()
    if c2.button("Cancel", width="stretch"):
        st.rerun()


def render():
    st.title("📦 Orders")

    col_search, col_filter = st.columns([2, 3])
    term = col_search.text_input(
        "Search",
        value=st.session_state.pop("orders_prefill", ""),
        placeholder="🔍 Ticket no., customer name or phone…",
        label_visibility="collapsed",
    )
    choice = col_filter.pills("Filter", FILTERS, default="All",
                              label_visibility="collapsed")

    status = FILTER_TO_STATUS.get(choice)
    orders = db.get_orders(status=status, term=term)

    if choice == "Overdue":
        orders = [
            o for o in orders if ui.effective_status(o[6], o[5]) == "overdue"
        ]

    if not orders:
        st.info(
            "No orders match. Create one from the **New Order** page — "
            "it takes about 20 seconds. 🧺"
        )
        return

    items_by_order = db.get_order_items([o[0] for o in orders])
    st.caption(f"{len(orders)} order(s)")

    for order in orders:
        (oid, code, name, phone, odate, pickup, status_, paid,
         amount, _notes, _cid) = order
        eff = ui.effective_status(status_, pickup)
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
            c1.markdown(
                f"{ui.badge(eff)}&nbsp;&nbsp;**{code or f'#{oid}'}**<br>"
                f"<span style='color:#898781;font-size:0.85rem;'>"
                f"📅 pickup {ui.fmt_date(pickup)}</span>",
                unsafe_allow_html=True,
            )
            c2.markdown(
                f"**{name}**  \n"
                f"🧾 {items_by_order.get(oid, '—')}"
            )
            c3.markdown(
                f"{ui.amount_display(amount)}<br>{ui.paid_chip(paid)}",
                unsafe_allow_html=True,
            )
            with c4:
                if status_ in ui.NEXT_ACTION:
                    label, nxt = ui.NEXT_ACTION[status_]
                    if st.button(label, key=f"adv_{oid}", type="primary",
                                 width="stretch"):
                        if nxt == "ready" and amount is None:
                            # Processing done: time to enter the final price.
                            ui.price_dialog(oid, code, advance_to="ready")
                        else:
                            db.execute(
                                "UPDATE orders SET status=? WHERE order_id=?",
                                (nxt, oid),
                            )
                            ui.flash(
                                f"Order {code or oid} → {ui.STATUS_META[nxt][0]}."
                            )
                            st.rerun()
                if amount is None:
                    if st.button("💶 Set price", key=f"price_{oid}",
                                 type="primary", width="stretch"):
                        ui.price_dialog(oid, code)
                elif not paid:
                    if st.button("💶 Mark paid", key=f"pay_{oid}",
                                 type="primary", width="stretch"):
                        db.execute(
                            "UPDATE orders SET paid=1 WHERE order_id=?", (oid,)
                        )
                        ui.flash(f"Order {code or oid} marked paid.", "💶")
                        st.rerun()
            with c5:
                if st.button("✏️ Edit", key=f"edit_{oid}", width="stretch"):
                    _edit_dialog(order)
                if st.button("🗑️ Delete", key=f"del_{oid}", width="stretch"):
                    _delete_dialog(oid, code)
