"""Base page layout wrapping all pages with sidebar + content area."""
import reflex as rx
from .sidebar import sidebar


def page_layout(*children) -> rx.Component:
    """Wrap page content with dark background and sidebar."""
    return rx.box(
        sidebar(),
        rx.box(
            *children,
            class_name="ml-52 min-h-screen bg-slate-950 text-slate-100 p-8",
        ),
        class_name="flex min-h-screen bg-slate-950",
    )
