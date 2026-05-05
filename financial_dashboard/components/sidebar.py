"""Navigation sidebar — dark bg, bright navy active states, language toggle."""
import reflex as rx
from ..state import UploadState

_GRAPHITE = "#111520"
_NAVY     = "#4361EE"
_BLUE     = "#6B9FFF"
_POWDER   = "#B4C5E4"


def nav_link(label: str, href: str, icon: str) -> rx.Component:
    is_active = rx.State.router.page.path == href
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, size="2", weight="medium"),
            spacing="2",
            align="center",
        ),
        href=href,
        class_name=rx.cond(
            is_active,
            "flex items-center gap-2 px-3 py-2 rounded-lg w-full text-sm font-semibold transition-colors duration-150",
            "flex items-center gap-2 px-3 py-2 rounded-lg w-full text-sm transition-colors duration-150",
        ),
        style=rx.cond(
            is_active,
            {"backgroundColor": _NAVY, "color": "#FFFFFF"},
            {"color": _POWDER, "backgroundColor": "transparent"},
        ),
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Logo
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.text("M", class_name="font-black text-lg leading-none", style={"color": "#FFFFFF"}),
                        class_name="w-8 h-8 rounded-lg flex items-center justify-center",
                        style={"backgroundColor": _NAVY},
                    ),
                    rx.vstack(
                        rx.text("MSE Analytica", class_name="font-bold text-sm leading-tight", style={"color": "#DDE2F2"}),
                        rx.text("Financial Dashboard", class_name="text-xs leading-tight", style={"color": _POWDER}),
                        spacing="0",
                        align="start",
                    ),
                    spacing="2",
                    align="center",
                ),
                class_name="px-3 py-5",
            ),
            rx.box(class_name="w-full mx-3", style={"borderTop": f"1px solid {_POWDER}20", "marginLeft": "12px", "marginRight": "12px", "width": "calc(100% - 24px)"}),
            # Nav links
            rx.vstack(
                nav_link("Dashboard", "/",          "layout-dashboard"),
                nav_link("Screener",  "/screener",  "search"),
                nav_link("Portfolio", "/portfolio", "briefcase"),
                nav_link("Data",      "/data",      "database"),
                spacing="1",
                width="100%",
                padding_x="2",
                padding_y="3",
            ),
            rx.spacer(),
            # Language toggle footer
            rx.box(
                rx.hstack(
                    rx.text("EN", class_name="text-xs font-semibold", style={"color": rx.cond(UploadState.lang == "EN", "#DDE2F2", _POWDER + "80")}),
                    rx.box(
                        rx.box(
                            class_name="w-4 h-4 rounded-full transition-transform duration-200",
                            style={
                                "backgroundColor": "#DDE2F2",
                                "transform": rx.cond(UploadState.lang == "MN", "translateX(20px)", "translateX(0px)"),
                            },
                        ),
                        on_click=UploadState.toggle_lang,
                        class_name="w-10 h-5 rounded-full flex items-center px-0.5 cursor-pointer transition-colors duration-200",
                        style={"backgroundColor": rx.cond(UploadState.lang == "MN", _NAVY, _POWDER + "40")},
                    ),
                    rx.text("MN", class_name="text-xs font-semibold", style={"color": rx.cond(UploadState.lang == "MN", "#DDE2F2", _POWDER + "80")}),
                    spacing="2",
                    align="center",
                    justify="center",
                ),
                class_name="px-3 py-4 w-full",
            ),
            spacing="0",
            width="100%",
            align="start",
            height="100%",
        ),
        class_name="fixed left-0 top-0 h-full w-56 flex flex-col z-10",
        style={"backgroundColor": _GRAPHITE},
    )
