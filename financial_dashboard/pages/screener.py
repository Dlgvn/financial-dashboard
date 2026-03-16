"""Screener page: browse all uploaded companies with health scores."""

import reflex as rx

from ..components.layout import page_layout
from ..state import AnalysisState, PortfolioState


def health_badge(score: rx.Var, label: rx.Var, color: rx.Var) -> rx.Component:
    """Render a colored badge showing the composite health score and label."""
    return rx.box(
        rx.hstack(
            rx.text(score, weight="bold", size="3"),
            rx.text(label, size="2"),
            spacing="1",
            align="center",
        ),
        class_name=rx.cond(
            color == "green",
            "px-3 py-1 rounded-full border text-sm font-medium bg-green-500/20 text-green-400 border-green-500/30",
            rx.cond(
                color == "red",
                "px-3 py-1 rounded-full border text-sm font-medium bg-red-500/20 text-red-400 border-red-500/30",
                "px-3 py-1 rounded-full border text-sm font-medium bg-amber-500/20 text-amber-400 border-amber-500/30",
            ),
        ),
    )


def company_row(company: dict) -> rx.Component:
    """Render a single table row for one company."""
    return rx.table.row(
        rx.table.cell(
            rx.link(
                company["company"],
                href="/company/" + company["company"],
                class_name="text-green-400 hover:text-green-300 font-medium",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["year"], class_name="text-slate-400 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            health_badge(company["score"], company["label"], company["color"]),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(
                rx.cond(
                    company["f_score"] != None,  # noqa: E711
                    company["f_score"].to_string() + " / 9",
                    "N/A",
                ),
                class_name="text-slate-300 text-sm",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(
                rx.cond(
                    company["roe"] != None,  # noqa: E711
                    (company["roe"] * 100).to_string() + "%",
                    "N/A",
                ),
                class_name="text-slate-300 text-sm",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.button(
                rx.icon("plus", size=14),
                rx.text("Add", size="1"),
                on_click=PortfolioState.add_to_portfolio(company["company"]),
                class_name=(
                    "flex items-center gap-1 px-3 py-1 rounded "
                    "bg-slate-700 hover:bg-green-600 text-slate-200 "
                    "hover:text-white text-xs transition-colors"
                ),
                size="1",
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b border-slate-800 hover:bg-slate-900/50 transition-colors",
    )


def screener_page() -> rx.Component:
    """Full screener page with header and company table."""
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(
                    "Company Screener",
                    size="6",
                    class_name="text-slate-100",
                ),
                rx.text(
                    AnalysisState.all_companies.length().to_string()
                    + " companies",
                    class_name="text-slate-500 text-sm self-end",
                ),
                justify="between",
                width="100%",
                align="end",
            ),
            # Table
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                "Company",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Year",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Health Score",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "F-Score",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "ROE",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "",
                                class_name="px-4 py-3",
                            ),
                        ),
                        class_name="bg-slate-900/50",
                    ),
                    rx.table.body(
                        rx.foreach(
                            AnalysisState.all_companies,
                            company_row,
                        ),
                    ),
                    class_name="w-full",
                    variant="ghost",
                ),
                class_name="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden w-full",
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
