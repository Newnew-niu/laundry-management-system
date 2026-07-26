"""Laundry Management System — main entry point.

Run with:  streamlit run app.py

Works out of the box on SQLite (default). Point DB_ENGINE=mysql in .env for a
MySQL setup — see README.md.
"""

import streamlit as st
from streamlit_option_menu import option_menu

import db
import ui
from components import customers, dashboard, new_order, orders, settings

PAGES = [
    ("Dashboard", "speedometer2", dashboard.render),
    ("New Order", "plus-circle", new_order.render),
    ("Orders", "box-seam", orders.render),
    ("Customers", "people", customers.render),
    ("Settings", "gear", settings.render),
]
PAGE_NAMES = [p[0] for p in PAGES]


def _goto(page_name):
    st.session_state["goto_idx"] = PAGE_NAMES.index(page_name)
    st.rerun()


def _global_search_results(term):
    """Compact cross-page search: orders + customers, with jump buttons."""
    with st.container(border=True):
        hits_o = db.get_orders(term=term, limit=5)
        hits_c = db.search_customers(term)[:5]

        if not hits_o and not hits_c:
            st.caption(f"No orders or customers match “{term}”.")
            return

        col_o, col_c = st.columns(2)
        with col_o:
            st.markdown("**📦 Orders**")
            for o in hits_o:
                oid, code, name, _ph, _od, pickup, status, _paid, amount = o[:9]
                eff = ui.effective_status(status, pickup)
                st.markdown(
                    f"{ui.badge(eff)} **{code or f'#{oid}'}** · {name} · "
                    f"{ui.euro(amount)}",
                    unsafe_allow_html=True,
                )
            if hits_o and st.button("Open in Orders →", width="stretch"):
                st.session_state["orders_prefill"] = term
                _goto("Orders")
        with col_c:
            st.markdown("**👥 Customers**")
            for cid, name, phone, _notes in hits_c:
                st.markdown(f"• **{name}** · 📞 {phone or '—'}")
            if hits_c and st.button("Open in Customers →", width="stretch"):
                st.session_state["customers_prefill"] = term
                _goto("Customers")


def main():
    st.set_page_config(page_title="Laundry Manager", page_icon="👕", layout="wide")
    db.init_db()
    ui.inject_css()
    ui.show_flash()

    # --- Sidebar navigation ---
    with st.sidebar:
        selected = option_menu(
            "👕 Laundry",
            PAGE_NAMES,
            icons=[p[1] for p in PAGES],
            default_index=0,
            manual_select=st.session_state.pop("goto_idx", None),
            key="main_nav",
        )
    selected = selected or "Dashboard"

    # --- Top bar: global search + prominent New Order button ---
    col_search, col_new = st.columns([5, 1.4])
    term = col_search.text_input(
        "Global search",
        key="global_search",
        placeholder="🔍 Find anything: customer name, phone or ticket no.…",
        label_visibility="collapsed",
    )
    with col_new:
        if selected != "New Order" and st.button(
            "➕ New order", type="primary", width="stretch"
        ):
            _goto("New Order")

    if term.strip():
        _global_search_results(term.strip())

    # --- Selected page ---
    dict(zip(PAGE_NAMES, [p[2] for p in PAGES]))[selected]()


if __name__ == "__main__":
    main()
