"""Base page layout wrapping all pages with sidebar + content area."""
import reflex as rx
from .sidebar import sidebar

_BG = "#0E1117"


def page_layout(*children) -> rx.Component:
    return rx.box(
        sidebar(),
        rx.box(
            *children,
            class_name="ml-56 min-h-screen p-8",
            style={"backgroundColor": _BG, "color": "#DDE2F2"},
        ),
        style={"backgroundColor": _BG},
        class_name="flex min-h-screen",
    )
