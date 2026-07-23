"""Laundry Management System — main entry point.

A lightweight Streamlit app for a laundry/dry-cleaning shop to manage customers
and orders. Run with:

    streamlit run app.py

Configuration (database credentials) is read from a local ``.env`` file; see
``.env.example`` for the required variables.
"""

import streamlit as st

from components import create_order, dashboard, manage_data

PAGES = {
    "Dashboard": dashboard.render,
    "Create New Order": create_order.render,
    "Manage Orders & Customers": manage_data.render,
}


def main():
    st.set_page_config(page_title="Laundry Manager", page_icon="👕", layout="wide")

    # Force table cells to be centre-aligned.
    st.markdown(
        """
        <style>
        .stDataFrame th { text-align: center !important; }
        .stDataFrame td { text-align: center !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("Navigation")
    choice = st.sidebar.selectbox("Go to", list(PAGES.keys()))

    # Dispatch to the selected page's render function.
    PAGES[choice]()


if __name__ == "__main__":
    main()
