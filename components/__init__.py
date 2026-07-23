"""UI components for the Laundry Management System.

Each module exposes a single ``render()`` function that draws one page of the
Streamlit app. ``app.py`` wires them to the sidebar navigation.
"""

from components import create_order, dashboard, manage_data

__all__ = ["dashboard", "create_order", "manage_data"]
