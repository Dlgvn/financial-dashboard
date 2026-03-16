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
    """A single row inside a ratios table."""
    return rx.table.row(
        rx.table.cell(
            rx.text(label, class_name="text-slate-300 text-sm"),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.text(
                rx.cond(value != None, value.to_string(), "N/A"),  # noqa: E711
                class_name="text-slate-100 text-sm font-mono",
            ),
            class_name="py-2 px-4 text-right",
        ),
        rx.table.cell(
            rx.text(unit, class_name="text-slate-500 text-xs"),
            class_name="py-2 px-4",
        ),
        class_name="border-b border-slate-800/50",
    )


def piotroski_criterion(label: str, value: rx.Var) -> rx.Component:
    """A single Piotroski criterion with pass/fail icon."""
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
    comp = AnalysisState.company_composite
    piots = AnalysisState.company_piotroski
    ben = AnalysisState.company_beneish
    curr_r = AnalysisState.company_ratios

    return page_layout(
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
                    AnalysisState.selected_company_name,
                    size="7",
                    class_name="text-slate-100",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=14),
                    rx.text("Add to Portfolio"),
                    on_click=PortfolioState.add_to_portfolio(
                        AnalysisState.selected_company_name,
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
                score_card("Health Score", comp["score"], "/100"),
                score_card("Piotroski F-Score", piots["f_score"], "/ 9"),
                score_card("M-Score", ben["m_score"], ""),
                score_card("M-Score Result", ben["interpretation"], ""),
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
                            ratio_row(
                                "ROA",
                                curr_r["current"]["profitability"]["roa"],
                                "%",
                            ),
                            ratio_row(
                                "ROE",
                                curr_r["current"]["profitability"]["roe"],
                                "%",
                            ),
                            ratio_row(
                                "Net Margin",
                                curr_r["current"]["profitability"]["net_margin"],
                                "%",
                            ),
                            ratio_row(
                                "Current Ratio",
                                curr_r["current"]["liquidity"]["current_ratio"],
                                "x",
                            ),
                            ratio_row(
                                "Quick Ratio",
                                curr_r["current"]["liquidity"]["quick_ratio"],
                                "x",
                            ),
                            ratio_row(
                                "Debt/Equity",
                                curr_r["current"]["solvency"]["debt_to_equity"],
                                "x",
                            ),
                            ratio_row(
                                "Interest Cov.",
                                curr_r["current"]["solvency"]["interest_coverage"],
                                "x",
                            ),
                            ratio_row(
                                "Asset Turnover",
                                curr_r["current"]["activity"]["total_asset_turnover"],
                                "x",
                            ),
                            ratio_row(
                                "Altman Z-Score",
                                curr_r["current"]["z_score"]["z_score"],
                                "",
                            ),
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
                    # Piotroski criteria
                    rx.text(
                        "Piotroski F-Score Criteria",
                        class_name=(
                            "text-slate-400 text-xs uppercase tracking-wider mb-2 mt-3"
                        ),
                    ),
                    rx.vstack(
                        piotroski_criterion(
                            "ROA Positive",
                            piots["criteria"]["f1_roa_positive"],
                        ),
                        piotroski_criterion(
                            "Operating CF Positive",
                            piots["criteria"]["f2_ocf_positive"],
                        ),
                        piotroski_criterion(
                            "ROA Improving",
                            piots["criteria"]["f3_roa_improving"],
                        ),
                        piotroski_criterion(
                            "Cash Earnings Quality",
                            piots["criteria"]["f4_accruals"],
                        ),
                        piotroski_criterion(
                            "Leverage Decreased",
                            piots["criteria"]["f5_leverage_down"],
                        ),
                        piotroski_criterion(
                            "Liquidity Improved",
                            piots["criteria"]["f6_liquidity_up"],
                        ),
                        piotroski_criterion(
                            "Gross Margin Improving",
                            piots["criteria"]["f8_gross_margin_up"],
                        ),
                        piotroski_criterion(
                            "Asset Turnover Improving",
                            piots["criteria"]["f9_asset_turnover_up"],
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.separator(class_name="border-slate-700 my-3"),
                    # Beneish indices
                    rx.text(
                        "Beneish M-Score Indices",
                        class_name=(
                            "text-slate-400 text-xs uppercase tracking-wider mb-2"
                        ),
                    ),
                    rx.table.root(
                        rx.table.body(
                            ratio_row(
                                "DSRI (Receivables)",
                                ben["indices"]["dsri"],
                                "",
                            ),
                            ratio_row(
                                "GMI (Gross Margin)",
                                ben["indices"]["gmi"],
                                "",
                            ),
                            ratio_row(
                                "AQI (Asset Quality)",
                                ben["indices"]["aqi"],
                                "",
                            ),
                            ratio_row(
                                "SGI (Sales Growth)",
                                ben["indices"]["sgi"],
                                "",
                            ),
                            ratio_row(
                                "SGAI (SG&A)",
                                ben["indices"]["sgai"],
                                "",
                            ),
                            ratio_row(
                                "LVGI (Leverage)",
                                ben["indices"]["lvgi"],
                                "",
                            ),
                            ratio_row(
                                "TATA (Accruals)",
                                ben["indices"]["tata"],
                                "",
                            ),
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
    )
