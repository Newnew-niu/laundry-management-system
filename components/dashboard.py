"""Dashboard: KPI overview cards + today's pickups action list."""

import datetime as dt

import streamlit as st

import db
import ui


def _kpis():
    today = dt.date.today()
    today_orders = db.fetch_one(
        "SELECT COUNT(*) FROM orders WHERE order_date = ?", (today,)
    )[0]
    ready = db.fetch_one(
        "SELECT COUNT(*) FROM orders WHERE status = 'ready'", ()
    )[0]
    washing = db.fetch_one(
        "SELECT COUNT(*) FROM orders WHERE status IN ('pending','washing')", ()
    )[0]
    overdue = db.fetch_one(
        "SELECT COUNT(*) FROM orders "
        "WHERE status != 'picked_up' AND agreed_pickup_time < ?",
        (today,),
    )[0]
    unpaid = db.fetch_one(
        "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE paid = 0", ()
    )[0]
    unpaid_tbd = db.fetch_one(
        "SELECT COUNT(*) FROM orders WHERE paid = 0 AND total_amount IS NULL", ()
    )[0]
    return today_orders, ready, washing, overdue, unpaid, unpaid_tbd


def render():
    st.title("👕 Today at a Glance")

    today_orders, ready, washing, overdue, unpaid, unpaid_tbd = _kpis()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🧺 Orders today", today_orders)
    c2.metric("✅ Ready for pickup", ready)
    c3.metric("🌀 In progress", washing)
    c4.metric("⚠️ Overdue", overdue)
    c5.metric(
        "💶 Unpaid total",
        ui.euro(unpaid),
        delta=f"+{unpaid_tbd} TBD" if unpaid_tbd else None,
        delta_color="off",
        help="Sum of priced, unpaid orders. TBD = unpaid orders not priced yet.",
    )

    st.divider()
    st.subheader("📦 Pickups due today")

    today = dt.date.today()
    rows = db.fetch_all(
        """
        SELECT o.order_id, o.order_code, c.name, c.phone,
               o.agreed_pickup_time, o.status, o.paid, o.total_amount
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.status != 'picked_up' AND o.agreed_pickup_time <= ?
        ORDER BY o.agreed_pickup_time, o.order_id
        """,
        (today,),
    )

    if not rows:
        st.info("Nothing due today. 🎉  New orders appear here on their pickup date.")
        return

    for oid, code, name, phone, pickup, status, paid, amount in rows:
        eff = ui.effective_status(status, pickup)
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
            col1.markdown(
                f"{ui.badge(eff)}&nbsp;&nbsp;**{code or f'#{oid}'}**",
                unsafe_allow_html=True,
            )
            col2.markdown(f"**{name}**  \n📞 {phone or '—'}")
            col3.markdown(
                f"{ui.amount_display(amount)}<br>{ui.paid_chip(paid)}",
                unsafe_allow_html=True,
            )
            if status == "ready":
                if col4.button(
                    "📦 Picked up", key=f"dash_pick_{oid}", type="primary",
                    width="stretch",
                ):
                    db.execute(
                        "UPDATE orders SET status = 'picked_up' WHERE order_id = ?",
                        (oid,),
                    )
                    ui.flash(f"Order {code or oid} marked as picked up.")
                    st.rerun()
            else:
                label, nxt = ui.NEXT_ACTION[status]
                if col4.button(label, key=f"dash_adv_{oid}", type="primary",
                               width="stretch"):
                    if nxt == "ready" and amount is None:
                        ui.price_dialog(oid, code, advance_to="ready")
                    else:
                        db.execute(
                            "UPDATE orders SET status = ? WHERE order_id = ?",
                            (nxt, oid),
                        )
                        ui.flash(f"Order {code or oid} → {ui.STATUS_META[nxt][0]}.")
                        st.rerun()
