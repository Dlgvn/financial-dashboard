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


def sort_header(label: str, col: str) -> rx.Component:
    """Clickable column header that triggers sort."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, class_name="text-slate-400 text-xs uppercase tracking-wider"),
            rx.cond(
                AnalysisState.screener_sort_col == col,
                rx.cond(
                    AnalysisState.screener_sort_asc,
                    rx.icon("chevron-up", size=12, class_name="text-green-400"),
                    rx.icon("chevron-down", size=12, class_name="text-green-400"),
                ),
                rx.icon("chevrons-up-down", size=12, class_name="text-slate-600"),
            ),
            spacing="1",
            align="center",
            cursor="pointer",
            on_click=AnalysisState.sort_screener(col),
        ),
        class_name="px-4 py-3",
    )


def company_row(company: dict) -> rx.Component:
    """Render a single table row for one company."""
    return rx.table.row(
        rx.table.cell(
            rx.link(
                company["company"],
                href=company["url"],
                class_name="text-green-400 hover:text-green-300 font-medium",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["year"], class_name="text-slate-400 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["sector"], class_name="text-slate-300 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            health_badge(company["score"], company["label"], company["color"]),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["f_score_str"], class_name="text-slate-300 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["roe_str"], class_name="text-slate-300 text-sm"),
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


def methodology_panel() -> rx.Component:
    """Collapsible methodology & quality panel shown above the screener table."""
    return rx.el.details(
        rx.el.summary(
            rx.hstack(
                rx.icon("info", size=14, class_name="text-slate-400"),
                rx.text(
                    "Methodology & Validation",
                    class_name="text-slate-300 text-sm font-medium cursor-pointer select-none",
                ),
                spacing="2",
                align="center",
            ),
            class_name="list-none cursor-pointer",
        ),
        rx.box(
            rx.grid(
                # --- Models Used ---
                rx.box(
                    rx.text(
                        "Models Used",
                        class_name="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Piotroski F-Score — 9-point rule-based fundamental strength signal, no ML required",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Beneish M-Score — forensic fraud detection via 8 accounting ratios (threshold: −1.78)",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Altman Z-Score — bankruptcy prediction, academically validated on emerging markets",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Composite 0–100 — weighted blend (profitability 25%, liquidity 20%, solvency 20%, activity 15%, Z-score 10%, Piotroski 10%)",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="2",
                        align="start",
                    ),
                ),
                # --- Quality Evidence ---
                rx.box(
                    rx.text(
                        "Quality Evidence",
                        class_name="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Company",  class_name="text-slate-500 text-xs px-2 py-1"),
                                rx.table.column_header_cell("Check",    class_name="text-slate-500 text-xs px-2 py-1"),
                                rx.table.column_header_cell("System",   class_name="text-slate-500 text-xs px-2 py-1"),
                                rx.table.column_header_cell("Verified", class_name="text-slate-500 text-xs px-2 py-1"),
                            ),
                        ),
                        rx.table.body(
                            rx.table.row(
                                rx.table.cell(rx.text("АПУ", class_name="text-slate-300 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Piotroski", class_name="text-slate-400 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("6 / 8", class_name="text-slate-300 text-xs font-mono"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("6 / 8 ✓", class_name="text-green-400 text-xs font-mono"), class_name="px-2 py-1"),
                            ),
                            rx.table.row(
                                rx.table.cell(rx.text("Хаан банк", class_name="text-slate-300 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("M-Score", class_name="text-slate-400 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("< −1.78", class_name="text-slate-300 text-xs font-mono"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("No audit flags ✓", class_name="text-green-400 text-xs"), class_name="px-2 py-1"),
                            ),
                            rx.table.row(
                                rx.table.cell(rx.text("Сүү", class_name="text-slate-300 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Current Ratio", class_name="text-slate-400 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Manual calc", class_name="text-slate-300 text-xs font-mono"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Matches ✓", class_name="text-green-400 text-xs"), class_name="px-2 py-1"),
                            ),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                ),
                # --- Known Limitations ---
                rx.box(
                    rx.text(
                        "Known Limitations",
                        class_name="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Dataset: 7 MSE companies, 1–2 years of data",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
                            rx.text(
                                "DEPI index always N/A — MSE filings don't disclose depreciation separately",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
                            rx.text(
                                "No market price data — P/E ratio and market cap analysis out of scope",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="2",
                        align="start",
                    ),
                ),
                columns="3",
                spacing="6",
                width="100%",
            ),
            class_name="mt-3 pt-3 border-t border-slate-800",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 px-4 py-3 w-full",
    )


def screener_page() -> rx.Component:
    """Full screener page with header, methodology panel, and company table."""
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(
                    "Company Screener",
                    size="6",
                    class_name="text-slate-100",
                ),
                rx.hstack(
                    rx.text(
                        AnalysisState.filtered_companies.length().to_string()
                        + " companies",
                        class_name="text-slate-500 text-sm self-end",
                    ),
                    rx.select(
                        ["All", "Banking", "Insurance", "Manufacturing", "Food", "Textiles", "Holding"],
                        value=AnalysisState.screener_filter,
                        on_change=AnalysisState.set_screener_filter,
                        class_name="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1 text-sm",
                    ),
                    spacing="3",
                    align="center",
                ),
                justify="between",
                width="100%",
                align="end",
            ),
            # Methodology & validation panel
            methodology_panel(),
            # Empty state or table
            rx.cond(
                AnalysisState.all_companies.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("database", size=40, class_name="text-slate-600"),
                        rx.text(
                            "No companies loaded.",
                            class_name="text-slate-400",
                        ),
                        rx.link(
                            "← Go to Upload and click Load Demo Data",
                            href="/",
                            class_name="text-green-400 hover:text-green-300 text-sm mt-1",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    class_name=(
                        "bg-slate-900 rounded-lg border border-slate-800 "
                        "p-16 w-full flex items-center justify-center"
                    ),
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                sort_header("Company", "company"),
                                rx.table.column_header_cell(
                                    "Year",
                                    class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                                ),
                                sort_header("Sector", "sector"),
                                sort_header("Health Score", "score"),
                                sort_header("F-Score", "f_score"),
                                sort_header("ROE", "roe"),
                                rx.table.column_header_cell(
                                    "",
                                    class_name="px-4 py-3",
                                ),
                            ),
                            class_name="bg-slate-900/50",
                        ),
                        rx.table.body(
                            rx.foreach(
                                AnalysisState.filtered_companies,
                                company_row,
                            ),
                        ),
                        class_name="w-full",
                        variant="ghost",
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden w-full",
                ),
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
