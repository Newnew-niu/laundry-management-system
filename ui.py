"""Shared UI helpers: status badges, global CSS, flash toasts, formatting.

Status colors follow a fixed, accessible status palette and are always paired
with an icon + text label, so state is never communicated by color alone.
"""

import datetime as _dt

import streamlit as st

# ---------------------------------------------------------------------------
# Order status model
# ---------------------------------------------------------------------------
# Stored values are English keys; OVERDUE is derived (not stored): any order
# past its pickup date that is not picked up yet renders as overdue.

STATUS_FLOW = ["pending", "washing", "ready", "picked_up"]

STATUS_META = {
    # key: (label, icon, text color, background tint)
    "pending":   ("Pending",   "🕐", "#52514e", "#f0efec"),
    "washing":   ("Washing",   "🌀", "#1c5cab", "rgba(42,120,214,.13)"),
    "ready":     ("Ready",     "✅", "#006300", "rgba(12,163,12,.13)"),
    "picked_up": ("Picked up", "📦", "#898781", "#f7f6f3"),
    "overdue":   ("Overdue",   "⚠️", "#d03b3b", "rgba(208,59,59,.12)"),
}

NEXT_ACTION = {
    # status -> (button label, next status)
    "pending": ("🌀 Start washing", "washing"),
    "washing": ("✅ Mark ready", "ready"),
    "ready": ("📦 Picked up", "picked_up"),
}


def to_date(value):
    """Normalise DB date values (str from SQLite, date/datetime from MySQL)."""
    if value is None:
        return None
    if isinstance(value, _dt.datetime):  # before date: datetime subclasses date
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return _dt.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def effective_status(status, pickup_date):
    """Derive 'overdue' for un-collected orders past their pickup date."""
    pickup = to_date(pickup_date)
    if status != "picked_up" and pickup and pickup < _dt.date.today():
        return "overdue"
    return status


def badge(status_key):
    """Return an HTML pill badge (icon + label, tinted background)."""
    label, icon, color, bg = STATUS_META[status_key]
    return (
        f'<span style="background:{bg};color:{color};padding:4px 12px;'
        f'border-radius:999px;font-size:0.85rem;font-weight:600;'
        f'white-space:nowrap;">{icon} {label}</span>'
    )


def paid_chip(paid):
    if paid:
        return (
            '<span style="color:#006300;font-size:0.85rem;font-weight:600;">'
            "💶 Paid</span>"
        )
    return (
        '<span style="color:#d03b3b;font-size:0.85rem;font-weight:600;">'
        "💶 Unpaid</span>"
    )


def euro(amount):
    """Format an amount; a NULL price (not yet decided) reads as TBD."""
    if amount is None:
        return "TBD"
    return f"€ {float(amount):,.2f}"


def amount_display(amount):
    """HTML snippet for an order amount: bold € value, or an amber TBD tag."""
    if amount is None:
        return '<span style="color:#b97d0e;font-weight:700;">💶 TBD</span>'
    return f"<b>{euro(amount)}</b>"


@st.dialog("💶 Set final price")
def price_dialog(order_id, code, advance_to=None):
    """Enter the final price once processing is done.

    When ``advance_to`` is given (e.g. 'ready'), saving also moves the order
    to that status; a skip button advances without pricing yet.
    """
    import db  # local import: keep ui free of a hard db dependency

    st.markdown(f"Order **{code or order_id}** — enter the final price (€).")
    amount = st.number_input(
        "Final price (€)", min_value=0.0, value=None, step=1.0, format="%.2f",
        placeholder="e.g. 24.50",
    )
    label = "💾 Save price" if advance_to is None else "💾 Save price & mark ready"
    if st.button(label, type="primary", width="stretch",
                 disabled=amount is None):
        if advance_to:
            db.execute(
                "UPDATE orders SET total_amount=?, status=? WHERE order_id=?",
                (amount, advance_to, order_id),
            )
            flash(f"Order {code or order_id} priced {euro(amount)} → "
                  f"{STATUS_META[advance_to][0]}.", "💶")
        else:
            db.execute(
                "UPDATE orders SET total_amount=? WHERE order_id=?",
                (amount, order_id),
            )
            flash(f"Order {code or order_id} priced {euro(amount)}.", "💶")
        st.rerun()
    if advance_to and st.button("Skip — price later", width="stretch"):
        db.execute(
            "UPDATE orders SET status=? WHERE order_id=?", (advance_to, order_id)
        )
        flash(f"Order {code or order_id} → {STATUS_META[advance_to][0]} "
              "(price still TBD).")
        st.rerun()


def fmt_date(value):
    d = to_date(value)
    return d.strftime("%d/%m/%Y") if d else "—"


# ---------------------------------------------------------------------------
# Flash messages (survive st.rerun): set flash() then rerun; app shows it.
# ---------------------------------------------------------------------------

def flash(message, icon="✅"):
    st.session_state["_flash"] = (message, icon)


def show_flash():
    if "_flash" in st.session_state:
        message, icon = st.session_state.pop("_flash")
        st.toast(message, icon=icon)


# ---------------------------------------------------------------------------
# Global CSS: bigger type, bigger touch targets, KPI card styling.
# ---------------------------------------------------------------------------

def inject_css():
    st.markdown(
        """
        <style>
        /* Roomier page padding */
        .block-container { padding-top: 1.2rem; padding-bottom: 3rem; }

        /* KPI metric cards: bordered tiles with big values */
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid rgba(11,11,11,0.10);
            border-radius: 14px;
            padding: 14px 18px;
        }
        div[data-testid="stMetricValue"] { font-size: 2.1rem; font-weight: 700; }
        div[data-testid="stMetricLabel"] { font-size: 1.0rem; }

        /* Big, easy-to-hit buttons */
        .stButton button, .stFormSubmitButton button {
            min-height: 3rem;
            font-size: 1.05rem;
            border-radius: 10px;
        }

        /* Centre table text */
        .stDataFrame th, .stDataFrame td { text-align: center !important; }

        /* Delete buttons: red, clearly distinct from blue primary actions */
        div[class*="st-key-del_"] button,
        div[class*="st-key-cdel_"] button {
            color: #d03b3b;
            border: 1px solid #d03b3b;
        }
        div[class*="st-key-confirm_del"] button {
            background: #d03b3b !important;
            border: 1px solid #d03b3b !important;
            color: #ffffff !important;
        }

        /* Order list rows */
        .order-row {
            background: #ffffff;
            border: 1px solid rgba(11,11,11,0.10);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
