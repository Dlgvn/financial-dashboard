"""Screener page: browse all uploaded companies with health scores."""
import reflex as rx

from ..components.layout import page_layout
from ..state import AnalysisState, PortfolioState

_NAVY   = "#4361EE"
_BLUE   = "#6B9FFF"
_POWDER = "#B4C5E4"
_TEXT   = "#DDE2F2"
_MUTED  = "#8892A8"
_FAINT  = "#5A627A"
_CARD   = "#161B27"
_BORDER = "#2A3050"


def health_badge(score: rx.Var, label: rx.Var, color: rx.Var) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(score, weight="bold", size="2"),
            rx.text(label, size="1"),
            spacing="1",
            align="center",
        ),
        class_name=rx.cond(
            color == "green",
            "px-3 py-1 rounded-full text-sm font-medium bg-green-950/60 text-green-400 border border-green-800/50",
            rx.cond(
                color == "red",
                "px-3 py-1 rounded-full text-sm font-medium bg-red-950/60 text-red-400 border border-red-800/50",
                "px-3 py-1 rounded-full text-sm font-medium bg-amber-950/60 text-amber-400 border border-amber-800/50",
            ),
        ),
    )


def sort_header(label: str, col: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, class_name="text-xs uppercase tracking-wider", style={"color": _FAINT}),
            rx.cond(
                PortfolioState.screener_sort_col == col,
                rx.cond(
                    PortfolioState.screener_sort_asc,
                    rx.icon("chevron-up", size=12, style={"color": _NAVY}),
                    rx.icon("chevron-down", size=12, style={"color": _NAVY}),
                ),
                rx.icon("chevrons-up-down", size=12, style={"color": _POWDER + "60"}),
            ),
            spacing="1",
            align="center",
            cursor="pointer",
            on_click=PortfolioState.sort_screener(col),
        ),
        class_name="px-4 py-3",
    )


def company_row(company: dict) -> rx.Component:
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
            rx.text(company["year"], class_name="text-xs", style={"color": _FAINT}),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["sector"], class_name="text-sm", style={"color": _MUTED}),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            health_badge(company["score"], company["label"], company["color"]),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(company["roe_str"], class_name="text-sm font-mono", style={"color": _TEXT}),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.button(
                rx.icon("plus", size=14),
                rx.text("Add", size="1"),
                on_click=PortfolioState.add_to_portfolio(company["company"]),
                class_name="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer",
                style={"backgroundColor": _NAVY + "25", "color": _BLUE},
                size="1",
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b hover:bg-blue-900/10 transition-colors cursor-pointer",
        style={"borderColor": _BORDER},
    )


def _check(text: str) -> rx.Component:
    return rx.hstack(
        rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
        rx.text(text, class_name="text-xs", style={"color": _MUTED}),
        spacing="2",
        align="start",
    )


def _warn(text: str) -> rx.Component:
    return rx.hstack(
        rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
        rx.text(text, class_name="text-xs", style={"color": _MUTED}),
        spacing="2",
        align="start",
    )


def _section_label(text: str) -> rx.Component:
    return rx.text(text, class_name="text-xs font-semibold uppercase tracking-wider mb-2", style={"color": _TEXT})


def methodology_panel() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            rx.hstack(
                rx.icon("info", size=14, style={"color": _BLUE}),
                rx.text("Methodology & Validation", class_name="text-sm font-medium cursor-pointer select-none", style={"color": _TEXT}),
                spacing="2",
                align="center",
            ),
            class_name="list-none cursor-pointer",
        ),
        rx.box(
            rx.grid(
                # Column 1 — Score by Sector
                rx.box(
                    _section_label("Score by Sector"),
                    rx.vstack(
                        # Non-financial
                        rx.text("Non-financial companies", class_name="text-xs font-medium mt-1", style={"color": _POWDER}),
                        _check("Profitability 25% — ROA, ROE, net margin"),
                        _check("Liquidity 20% — current, quick, cash ratios"),
                        _check("Solvency 20% — D/E, D/A, interest coverage"),
                        _check("Activity 15% — asset turnover, DSO, inventory turns"),
                        _check("Altman Z-Score 10% — Z' private-firm variant"),
                        _check("Piotroski F-Score 10% — 9-point fundamental signal"),
                        # Banks
                        rx.text("Banks", class_name="text-xs font-medium mt-2", style={"color": _POWDER}),
                        _check("CAMELS-inspired: Capital 25%, Asset Quality 25%, Earnings 20%, Liquidity 20%, Efficiency 10%"),
                        # Insurance
                        rx.text("Insurance", class_name="text-xs font-medium mt-2", style={"color": _POWDER}),
                        _check("IRIS/Solvency II: Underwriting 30%, Solvency 25%, Profitability 25%, Liquidity 20%"),
                        # Finance / NBFI
                        rx.text("Finance / NBFI", class_name="text-xs font-medium mt-2", style={"color": _POWDER}),
                        _check("Profitability 30%, Solvency 25%, Liquidity 25%, Activity 20%"),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                ),
                # Column 2 — Universal Adjustments + Limitations
                rx.vstack(
                    rx.box(
                        _section_label("Universal Adjustments"),
                        rx.vstack(
                            _check("Beneish M-Score — 8 accounting-ratio fraud screen applied to all sectors; −10 pt penalty when M > −1.78 and ≥5 indices are available"),
                            _check("Missing-data normalisation — if a pillar has no data its weight is redistributed proportionally to pillars that do"),
                            spacing="2",
                            align="start",
                        ),
                        width="100%",
                    ),
                    rx.box(
                        _section_label("Known Limitations"),
                        rx.vstack(
                            _warn("Piotroski F-Score and Altman Z-Score are not applied to Banking, Insurance, or Finance sectors — those sectors use their own dedicated frameworks above"),
                            _warn("Beneish DEPI index is always N/A — MSE filings do not disclose depreciation separately"),
                            _warn("Altman Z' uses the standard private-firm model; no Mongolia-specific recalibration has been done"),
                            _warn("Dataset: MSE-listed companies only, typically 1–2 years of financial data"),
                            _warn("Benchmarks are global standards — MSE-specific averages require a larger sample"),
                            spacing="2",
                            align="start",
                        ),
                        width="100%",
                    ),
                    spacing="5",
                    align="start",
                    width="100%",
                ),
                columns="2",
                spacing="6",
                width="100%",
            ),
            class_name="mt-3 pt-3",
            style={"borderTop": f"1px solid {_BORDER}"},
        ),
        class_name="rounded-2xl px-5 py-4 w-full",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
    )


def screener_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.heading("Company Screener", size="8", class_name="font-bold", style={"color": _TEXT}),
                    rx.text("Sort, filter and compare all uploaded companies", class_name="text-sm", style={"color": _MUTED}),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(PortfolioState.filtered_companies.length(), " companies", class_name="text-sm", style={"color": _FAINT}),
                    rx.select(
                        ["All", "Banking", "Insurance", "Finance", "Manufacturing", "Food", "Textiles", "Holding"],
                        value=PortfolioState.screener_filter,
                        on_change=PortfolioState.set_screener_filter,
                        class_name="rounded-lg px-3 py-1 text-sm border cursor-pointer",
                        style={"borderColor": _BORDER, "color": _TEXT, "backgroundColor": _CARD},
                    ),
                    spacing="3",
                    align="center",
                ),
                width="100%",
                align="end",
            ),
            methodology_panel(),
            # Table or empty state
            rx.cond(
                PortfolioState.all_companies.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("database", size=40, style={"color": _POWDER + "60"}),
                        rx.text("No companies loaded.", class_name="font-semibold", style={"color": _TEXT}),
                        rx.link(
                            "← Go to Data",
                            href="/data",
                            class_name="text-sm",
                            style={"color": _BLUE},
                        ),
                        spacing="2",
                        align="center",
                    ),
                    class_name="rounded-2xl p-16 w-full flex items-center justify-center",
                    style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                sort_header("Company", "company"),
                                rx.table.column_header_cell("Year", class_name="text-xs uppercase tracking-wider px-4 py-3", style={"color": _FAINT}),
                                sort_header("Sector",       "sector"),
                                sort_header("Health Score", "score"),
                                sort_header("ROE",          "roe"),
                                rx.table.column_header_cell("", class_name="px-4 py-3"),
                            ),
                            class_name="border-b",
                            style={"borderColor": _BORDER, "backgroundColor": _POWDER + "08"},
                        ),
                        rx.table.body(
                            rx.foreach(PortfolioState.filtered_companies, company_row),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                    class_name="rounded-2xl overflow-hidden w-full",
                    style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                ),
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
