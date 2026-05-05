"""MSE Analytica - Financial Dashboard for Mongolian Stock Exchange."""

import logging
import reflex as rx

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

from .components.layout import page_layout
from .pages.company import company_page
from .pages.data import data_page
from .pages.portfolio import portfolio_page
from .pages.screener import screener_page
from .state import AnalysisState, PortfolioState, UploadState

_NAVY   = "#4361EE"
_BLUE   = "#6B9FFF"
_POWDER = "#B4C5E4"
_TEXT   = "#DDE2F2"
_MUTED  = "#8892A8"
_FAINT  = "#5A627A"
_CARD   = "#161B27"
_BORDER = "#2A3050"


def _stat_card(label: str, value: rx.Var, sub: str = "", accent: str = _NAVY) -> rx.Component:
    return rx.box(
        rx.text(label, class_name="text-xs font-semibold uppercase tracking-wider mb-1", style={"color": _MUTED}),
        rx.text(value, class_name="text-3xl font-bold", style={"color": accent}),
        rx.text(sub, class_name="text-xs mt-1", style={"color": _FAINT}),
        class_name="rounded-2xl p-5",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
    )


def _health_badge_dash(score: rx.Var, label: rx.Var, color: rx.Var) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(score, weight="bold", size="2"),
            rx.text(label, size="1"),
            spacing="1",
            align="center",
        ),
        class_name=rx.cond(
            color == "green",
            "px-2 py-0.5 rounded-full text-xs font-medium bg-green-950/60 text-green-400 border border-green-800/50",
            rx.cond(
                color == "red",
                "px-2 py-0.5 rounded-full text-xs font-medium bg-red-950/60 text-red-400 border border-red-800/50",
                "px-2 py-0.5 rounded-full text-xs font-medium bg-amber-950/60 text-amber-400 border border-amber-800/50",
            ),
        ),
    )


def _screener_row_dash(company: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.link(
                company["company"],
                href=company["url"],
                class_name="font-semibold hover:underline text-sm",
                style={"color": _BLUE},
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["sector"], class_name="text-xs", style={"color": _MUTED}),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            _health_badge_dash(company["score"], company["label"], company["color"]),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["roe_str"], class_name="text-sm font-mono", style={"color": _TEXT}),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.button(
                rx.icon("plus", size=12),
                "Add",
                on_click=PortfolioState.add_to_portfolio(company["company"]),
                class_name="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer",
                style={"backgroundColor": _NAVY + "25", "color": _BLUE},
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b hover:bg-blue-900/10 transition-colors",
        style={"borderColor": _BORDER},
    )


def _portfolio_holding_row(h: dict) -> rx.Component:
    return rx.hstack(
        rx.text(h["company"], class_name="text-sm font-medium flex-1", style={"color": _TEXT}),
        rx.text(h["sector"], class_name="text-xs flex-1", style={"color": _FAINT}),
        rx.box(
            rx.box(
                class_name="h-1.5 rounded-full",
                style={"width": h["weight_str"], "backgroundColor": _BLUE},
            ),
            class_name="w-24 h-1.5 rounded-full",
            style={"backgroundColor": _BORDER},
        ),
        rx.text(h["weight_str"], class_name="text-xs font-mono w-10 text-right", style={"color": _NAVY}),
        spacing="3",
        align="center",
        width="100%",
        class_name="py-2 border-b",
        style={"borderColor": _BORDER},
    )


def _empty_screener() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.icon("search", size=32, style={"color": _POWDER + "60"}),
            rx.text("No companies loaded yet", class_name="font-semibold text-sm", style={"color": _TEXT}),
            rx.text("Upload financial statements to get started", class_name="text-xs", style={"color": _MUTED}),
            rx.link(
                rx.button(
                    rx.icon("upload", size=14),
                    "Upload Data",
                    class_name="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white mt-2 cursor-pointer",
                    style={"backgroundColor": _NAVY},
                ),
                href="/data",
            ),
            spacing="2",
            align="center",
        ),
        class_name="flex items-center justify-center py-16",
    )


def _empty_portfolio() -> rx.Component:
    return rx.vstack(
        rx.icon("briefcase", size=28, style={"color": _POWDER + "50"}),
        rx.text("Portfolio is empty", class_name="text-xs font-medium", style={"color": _MUTED}),
        rx.text("Add companies from the screener", class_name="text-xs", style={"color": _FAINT}),
        spacing="1",
        align="center",
        class_name="py-8",
    )


def index() -> rx.Component:
    """Dashboard landing: screener table + portfolio summary."""
    s = PortfolioState
    ps = PortfolioState

    return page_layout(
        rx.vstack(
            # Page header
            rx.hstack(
                rx.vstack(
                    rx.heading("Dashboard", size="8", class_name="font-bold", style={"color": _TEXT}),
                    rx.text("Mongolian Stock Exchange — Financial Analysis", class_name="text-sm", style={"color": _MUTED}),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        rx.icon("upload", size=14),
                        "Upload Data",
                        class_name="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white cursor-pointer",
                        style={"backgroundColor": _NAVY},
                    ),
                    href="/data",
                ),
                width="100%",
                align="center",
            ),
            # Stats row
            rx.grid(
                _stat_card("Companies Loaded",  s.all_companies.length(), "uploaded financial statements"),
                _stat_card("Portfolio Size",    ps.holdings.length(),     "active positions", _BLUE),
                _stat_card(
                    "Portfolio Health",
                    rx.cond(ps.holdings.length() > 0, ps.portfolio_health.to_string() + " / 100", "—"),
                    "weighted avg score",
                    "#34D399",
                ),
                _stat_card(
                    "Sectors Covered",
                    rx.cond(s.all_companies.length() > 0, s.all_companies.length().to_string() + " co.", "No data"),
                    "companies analyzed",
                    "#FBBF24",
                ),
                columns="4",
                spacing="4",
                width="100%",
            ),
            # Main content: screener (2/3) + portfolio (1/3)
            rx.grid(
                # ── Left: Company Screener ──────────────────────────────────
                rx.box(
                    rx.hstack(
                        rx.hstack(
                            rx.icon("list", size=16, style={"color": _NAVY}),
                            rx.text("Company Screener", class_name="font-bold text-sm", style={"color": _TEXT}),
                            spacing="2",
                            align="center",
                        ),
                        rx.spacer(),
                        rx.link(
                            rx.text("View all →", class_name="text-xs font-medium", style={"color": _BLUE}),
                            href="/screener",
                        ),
                        width="100%",
                        align="center",
                        class_name="mb-4",
                    ),
                    rx.cond(
                        s.all_companies.length() == 0,
                        _empty_screener(),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Company", class_name="text-xs uppercase tracking-wider px-4 py-3", style={"color": _FAINT}),
                                    rx.table.column_header_cell("Sector",  class_name="text-xs uppercase tracking-wider px-4 py-3", style={"color": _FAINT}),
                                    rx.table.column_header_cell("Health",  class_name="text-xs uppercase tracking-wider px-4 py-3", style={"color": _FAINT}),
                                    rx.table.column_header_cell("ROE",     class_name="text-xs uppercase tracking-wider px-4 py-3", style={"color": _FAINT}),
                                    rx.table.column_header_cell("",        class_name="px-4 py-3"),
                                ),
                                class_name="border-b",
                                style={"borderColor": _BORDER},
                            ),
                            rx.table.body(
                                rx.foreach(s.filtered_companies, _screener_row_dash),
                            ),
                            variant="ghost",
                            class_name="w-full",
                        ),
                    ),
                    class_name="rounded-2xl p-5 col-span-2",
                    style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                ),
                # ── Right: Portfolio Summary ────────────────────────────────
                rx.box(
                    rx.hstack(
                        rx.hstack(
                            rx.icon("briefcase", size=16, style={"color": _NAVY}),
                            rx.text("My Portfolio", class_name="font-bold text-sm", style={"color": _TEXT}),
                            spacing="2",
                            align="center",
                        ),
                        rx.spacer(),
                        rx.link(
                            rx.text("Manage →", class_name="text-xs font-medium", style={"color": _BLUE}),
                            href="/portfolio",
                        ),
                        width="100%",
                        align="center",
                        class_name="mb-4",
                    ),
                    rx.cond(
                        ps.holdings.length() == 0,
                        _empty_portfolio(),
                        rx.vstack(
                            rx.box(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Health Score", class_name="text-xs font-semibold uppercase tracking-wider", style={"color": _MUTED}),
                                        rx.text(ps.portfolio_health.to_string() + " / 100", class_name="text-2xl font-bold", style={"color": _NAVY}),
                                        spacing="0",
                                        align="start",
                                    ),
                                    spacing="0",
                                    width="100%",
                                ),
                                class_name="rounded-xl p-4 mb-3",
                                style={"backgroundColor": _POWDER + "10", "border": f"1px solid {_BORDER}"},
                            ),
                            rx.text("Holdings", class_name="text-xs font-semibold uppercase tracking-wider mb-1", style={"color": _MUTED}),
                            rx.foreach(ps.holdings, _portfolio_holding_row),
                            spacing="0",
                            width="100%",
                        ),
                    ),
                    class_name="rounded-2xl p-5",
                    style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                ),
                columns="3",
                spacing="4",
                width="100%",
            ),
            spacing="6",
            width="100%",
            align="start",
        ),
    )


app = rx.App(theme=rx.theme(appearance="dark", accent_color="indigo"))
app.add_page(index, on_load=PortfolioState.load_screener)
app.add_page(screener_page, route="/screener", on_load=PortfolioState.load_screener)
app.add_page(
    company_page,
    route="/company/[company]",
    on_load=AnalysisState.on_load_company,
)
app.add_page(portfolio_page, route="/portfolio")
app.add_page(data_page, route="/data", on_load=UploadState.on_load)
