"""UI pages for the Laundry Management System.

Each module exposes a single ``render()`` function that draws one page of the
Streamlit app. ``app.py`` wires them to the sidebar navigation.
"""

from components import customers, dashboard, new_order, orders, settings

__all__ = ["dashboard", "new_order", "orders", "customers", "settings"]
