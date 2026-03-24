"""Company Health Analysis page — ratios, Piotroski, and Beneish display."""

import reflex as rx

from ..components.layout import page_layout
from ..state import AnalysisState, PortfolioState


def score_card(title: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single metric card with title, large value, and optional unit."""
    return rx.box(
        rx.text(
            title,
            class_name="text-slate-400 text-xs uppercase tracking-wider mb-1",
        ),
        rx.hstack(
            rx.text(value, class_name="text-2xl font-bold text-slate-100"),
            rx.text(unit, class_name="text-slate-500 text-sm self-end mb-1"),
            spacing="1",
            align="end",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
    )


def ratio_row(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single row inside a ratios table. value is a pre-formatted string."""
    return rx.table.row(
        rx.table.cell(
            rx.text(label, class_name="text-slate-300 text-sm"),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.text(value, class_name="text-slate-100 text-sm font-mono"),
            class_name="py-2 px-4 text-right",
        ),
        rx.table.cell(
            rx.text(unit, class_name="text-slate-500 text-xs"),
            class_name="py-2 px-4",
        ),
        class_name="border-b border-slate-800/50",
    )


def piotroski_criterion(label: str, value: rx.Var) -> rx.Component:
    """A single Piotroski criterion with pass/fail/unknown icon.
    value: 1 = pass, 0 = fail, -1 = N/A
    """
    return rx.hstack(
        rx.cond(
            value == 1,
            rx.icon("circle-check", size=16, class_name="text-green-400"),
            rx.cond(
                value == 0,
                rx.icon("circle-x", size=16, class_name="text-red-400"),
                rx.icon("circle-help", size=16, class_name="text-slate-500"),
            ),
        ),
        rx.text(label, class_name="text-slate-300 text-sm"),
        spacing="2",
        align="center",
        class_name="py-1",
    )


def company_page() -> rx.Component:
    """Full company analysis page."""
    s = AnalysisState

    return page_layout(
        rx.cond(
            s.selected_company_name == "",
            rx.box(
                rx.vstack(
                    rx.icon("bar-chart-2", size=40, class_name="text-slate-600"),
                    rx.text("No company selected.", class_name="text-slate-400"),
                    rx.link(
                        "← Back to Screener",
                        href="/screener",
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
            rx.vstack(
                # Back link
                rx.link(
                    rx.hstack(
                        rx.icon("arrow-left", size=14),
                        rx.text("Screener", size="2"),
                        spacing="1",
                        align="center",
                    ),
                    href="/screener",
                    class_name=(
                        "text-slate-400 hover:text-slate-200 text-sm "
                        "flex items-center gap-1 mb-2"
                    ),
                ),
                # Company header
                rx.hstack(
                    rx.heading(
                        s.selected_company_name,
                        size="7",
                        class_name="text-slate-100",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=14),
                        rx.text("Add to Portfolio"),
                        on_click=PortfolioState.add_to_portfolio(
                            s.selected_company_name,
                        ),
                        class_name=(
                            "flex items-center gap-2 px-4 py-2 rounded-lg "
                            "bg-green-600 hover:bg-green-500 text-white font-medium "
                            "transition-colors"
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                # Hero score cards row
                rx.grid(
                    score_card("Health Score", s.company_score.to_string(), "/100"),
                    score_card("Piotroski F-Score", s.company_f_score_display, ""),
                    score_card("M-Score", s.company_m_score_display, ""),
                    score_card("M-Score Result", s.company_m_interp, ""),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                # Ratios + Forensics side by side
                rx.grid(
                    # ----- Financial Ratios table -----
                    rx.box(
                        rx.text(
                            "Financial Ratios",
                            class_name="text-slate-200 font-semibold mb-3",
                        ),
                        rx.table.root(
                            rx.table.body(
                                ratio_row("ROA",            s.company_roa,           "%"),
                                ratio_row("ROE",            s.company_roe,           "%"),
                                ratio_row("Net Margin",     s.company_net_margin,    "%"),
                                ratio_row("Current Ratio",  s.company_current_ratio, "x"),
                                ratio_row("Quick Ratio",    s.company_quick_ratio,   "x"),
                                ratio_row("Debt/Equity",    s.company_debt_equity,   "x"),
                                ratio_row("Interest Cov.",  s.company_interest_cov,  "x"),
                                ratio_row("Asset Turnover", s.company_asset_turnover,"x"),
                                ratio_row("Altman Z-Score", s.company_z_score,       ""),
                            ),
                            variant="ghost",
                            class_name="w-full",
                        ),
                        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
                    ),
                    # ----- Forensic Analysis -----
                    rx.box(
                        rx.text(
                            "Forensic Analysis",
                            class_name="text-slate-200 font-semibold mb-3",
                        ),
                        rx.text(
                            "Piotroski F-Score Criteria",
                            class_name=(
                                "text-slate-400 text-xs uppercase tracking-wider mb-2 mt-3"
                            ),
                        ),
                        rx.vstack(
                            piotroski_criterion("ROA Positive",           s.company_f1),
                            piotroski_criterion("Operating CF Positive",  s.company_f2),
                            piotroski_criterion("ROA Improving",          s.company_f3),
                            piotroski_criterion("Cash Earnings Quality",  s.company_f4),
                            piotroski_criterion("Leverage Decreased",     s.company_f5),
                            piotroski_criterion("Liquidity Improved",     s.company_f6),
                            piotroski_criterion("Gross Margin Improving", s.company_f8),
                            piotroski_criterion("Asset Turnover Improving", s.company_f9),
                            spacing="0",
                            align="start",
                        ),
                        rx.separator(class_name="border-slate-700 my-3"),
                        rx.text(
                            "Beneish M-Score Indices",
                            class_name=(
                                "text-slate-400 text-xs uppercase tracking-wider mb-2"
                            ),
                        ),
                        rx.table.root(
                            rx.table.body(
                                ratio_row("DSRI (Receivables)", s.company_dsri,  ""),
                                ratio_row("GMI (Gross Margin)", s.company_gmi,   ""),
                                ratio_row("AQI (Asset Quality)",s.company_aqi,   ""),
                                ratio_row("SGI (Sales Growth)", s.company_sgi,   ""),
                                ratio_row("SGAI (SG&A)",        s.company_sgai,  ""),
                                ratio_row("LVGI (Leverage)",    s.company_lvgi,  ""),
                                ratio_row("TATA (Accruals)",    s.company_tata,  ""),
                            ),
                            variant="ghost",
                            class_name="w-full",
                        ),
                        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                spacing="5",
                width="100%",
                align="start",
            ),
        ),
    )
