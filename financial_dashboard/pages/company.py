"""Company Health Analysis page — 5-tab layout with sector-aware ratios, charts, DuPont, and red flags."""

import reflex as rx

from ..components.layout import page_layout
from ..state import AnalysisState, PortfolioState


# ── Helper components (reused across tabs) ───────────────────────────────────


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


def ratio_category_card(title: str, *rows) -> rx.Component:
    """A category card with heading and a ratios table."""
    return rx.box(
        rx.text(title, class_name="text-slate-300 text-xs uppercase tracking-wider mb-2 font-semibold"),
        rx.table.root(
            rx.table.body(*rows),
            variant="ghost",
            class_name="w-full",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
    )


# ── Chart components ──────────────────────────────────────────────────────────


def health_gauge() -> rx.Component:
    """Semicircle arc gauge showing overall health score."""
    s = AnalysisState
    return rx.box(
        rx.recharts.radial_bar_chart(
            rx.recharts.radial_bar(
                data_key="value",
                min_angle=15,
                background=True,
            ),
            data=s.company_gauge_data,
            start_angle=180,
            end_angle=0,
            inner_radius="60%",
            outer_radius="90%",
            width=280,
            height=160,
        ),
        rx.text(
            s.company_score.to_string() + " / 100",
            class_name="text-slate-100 text-xl font-bold text-center -mt-4",
        ),
        rx.text(
            s.company_health_label,
            class_name="text-slate-400 text-sm text-center",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 flex flex-col items-center",
    )


def radar_chart_panel() -> rx.Component:
    """Radar chart showing health breakdown by category."""
    s = AnalysisState
    return rx.box(
        rx.text("Health Category Breakdown", class_name="text-slate-200 font-semibold mb-3"),
        rx.recharts.radar_chart(
            rx.recharts.polar_grid(),
            rx.recharts.polar_angle_axis(data_key="category"),
            rx.recharts.radar(
                data_key="score",
                name="Health",
                fill="#22c55e",
                fill_opacity=0.3,
                stroke="#22c55e",
            ),
            data=s.company_radar_data,
            width=300,
            height=300,
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 flex flex-col items-center",
    )


# ── Tab content components ────────────────────────────────────────────────────


def _standard_ratios_content() -> rx.Component:
    """All 26 standard ratios in 6 category cards."""
    s = AnalysisState
    return rx.grid(
        # Profitability (6)
        ratio_category_card(
            "Profitability",
            ratio_row("Return on Assets (ROA)",  s.company_roa,              "%"),
            ratio_row("Return on Equity (ROE)",  s.company_roe,              "%"),
            ratio_row("Net Profit Margin",        s.company_net_margin,       "%"),
            ratio_row("Gross Profit Margin",      s.company_gross_margin,     "%"),
            ratio_row("Operating Margin",         s.company_operating_margin, "%"),
            ratio_row("EBIT Margin",              s.company_ebit_margin,      "%"),
        ),
        # Liquidity (4)
        ratio_category_card(
            "Liquidity",
            ratio_row("Current Ratio",   s.company_current_ratio,   "x"),
            ratio_row("Quick Ratio",     s.company_quick_ratio,     "x"),
            ratio_row("Cash Ratio",      s.company_cash_ratio,      "x"),
            ratio_row("Working Capital", s.company_working_capital, "₮ thousands"),
        ),
        # Solvency (4)
        ratio_category_card(
            "Solvency",
            ratio_row("Debt-to-Equity",   s.company_debt_equity,   "x"),
            ratio_row("Debt-to-Assets",   s.company_debt_to_assets, "ratio"),
            ratio_row("Equity Ratio",     s.company_equity_ratio,  "ratio"),
            ratio_row("Interest Coverage",s.company_interest_cov,  "x"),
        ),
        # Activity (9)
        ratio_category_card(
            "Activity",
            ratio_row("Total Asset Turnover",     s.company_asset_turnover,           "times"),
            ratio_row("Fixed Asset Turnover",     s.company_fixed_asset_turnover,     "times"),
            ratio_row("Inventory Turnover",       s.company_inventory_turnover,       "times"),
            ratio_row("Days Inventory Outstanding", s.company_days_inventory,         "days"),
            ratio_row("Receivables Turnover",     s.company_receivables_turnover,     "times"),
            ratio_row("Days Sales Outstanding",   s.company_days_sales_outstanding,   "days"),
            ratio_row("Payables Turnover",        s.company_payables_turnover,        "times"),
            ratio_row("Days Payable Outstanding", s.company_days_payable_outstanding, "days"),
            ratio_row("Cash Conversion Cycle",    s.company_cash_conversion_cycle,    "days"),
        ),
        # Performance (3)
        ratio_category_card(
            "Performance",
            ratio_row("Operating CF Ratio",  s.company_ocf_ratio,          "x"),
            ratio_row("Cash Flow to Debt",   s.company_cf_to_debt,         "x"),
            ratio_row("Reinvestment Ratio",  s.company_reinvestment_ratio, "x"),
        ),
        # Altman Z-Score (6)
        ratio_category_card(
            "Altman Z-Score",
            ratio_row("Altman Z-Score",                     s.company_z_score, "score"),
            ratio_row("X1: Working Capital / Total Assets", s.company_z_x1,    "ratio"),
            ratio_row("X2: Retained Earnings / Total Assets", s.company_z_x2,  "ratio"),
            ratio_row("X3: EBIT / Total Assets",            s.company_z_x3,    "ratio"),
            ratio_row("X4: Equity / Total Liabilities",     s.company_z_x4,    "ratio"),
            ratio_row("X5: Revenue / Total Assets",         s.company_z_x5,    "ratio"),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _bank_ratios_content() -> rx.Component:
    """Bank-specific ratios in 5 category sections."""
    s = AnalysisState
    return rx.grid(
        # Profitability
        ratio_category_card(
            "Profitability",
            ratio_row("Net Interest Margin (NIM)",   s.company_bank_nim,                  "%"),
            ratio_row("Return on Assets (ROA)",      s.company_bank_roa,                  "%"),
            ratio_row("Return on Equity (ROE)",      s.company_bank_roe,                  "%"),
            ratio_row("Net Profit Margin",           s.company_bank_net_margin,           "%"),
            ratio_row("Interest Income Ratio",       s.company_bank_interest_income_ratio,"%"),
        ),
        # Capital Adequacy
        ratio_category_card(
            "Capital Adequacy",
            ratio_row("Equity Multiplier",            s.company_bank_equity_multiplier,  "x"),
            ratio_row("Equity to Assets",             s.company_bank_equity_to_assets,   "ratio"),
        ),
        # Asset Quality
        ratio_category_card(
            "Asset Quality",
            ratio_row("NPL Ratio",               s.company_bank_npl_ratio,             "%"),
            ratio_row("Coverage Ratio",          s.company_bank_coverage_ratio,        "x"),
            ratio_row("Loan Loss Reserve Ratio", s.company_bank_loan_loss_reserve_ratio,"%"),
            ratio_row("Provision to Loans",      s.company_bank_provision_to_loans,    "%"),
        ),
        # Liquidity
        ratio_category_card(
            "Liquidity",
            ratio_row("Loan-to-Deposit Ratio (LDR)", s.company_bank_ldr,                "%"),
            ratio_row("Cash to Deposits",            s.company_bank_cash_to_deposits,   "%"),
            ratio_row("Loans to Total Assets",       s.company_bank_loans_to_assets,    "%"),
            ratio_row("Securities to Total Assets",  s.company_bank_securities_to_assets,"%"),
        ),
        # Efficiency
        ratio_category_card(
            "Efficiency",
            ratio_row("Cost-to-Income Ratio",      s.company_bank_cost_to_income,  "%"),
            ratio_row("Non-Interest Income Ratio", s.company_bank_fee_income_ratio, "%"),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _insurance_ratios_content() -> rx.Component:
    """Insurance-specific ratios in 5 category sections."""
    s = AnalysisState
    return rx.grid(
        # Underwriting
        ratio_category_card(
            "Underwriting",
            ratio_row("Loss Ratio",     s.company_ins_loss_ratio,     "%"),
            ratio_row("Expense Ratio",  s.company_ins_expense_ratio,  "%"),
            ratio_row("Combined Ratio", s.company_ins_combined_ratio, "%"),
        ),
        # Profitability
        ratio_category_card(
            "Profitability",
            ratio_row("Return on Assets (ROA)",       s.company_ins_roa,                   "%"),
            ratio_row("Return on Equity (ROE)",       s.company_ins_roe,                   "%"),
            ratio_row("Net Profit Margin",            s.company_ins_net_margin,            "%"),
            ratio_row("Investment Income Ratio",      s.company_ins_investment_income_ratio,"%"),
            ratio_row("Underwriting Profit Margin",   s.company_ins_underwriting_margin,   "%"),
        ),
        # Solvency
        ratio_category_card(
            "Solvency",
            ratio_row("Solvency Ratio",       s.company_ins_solvency_ratio,        "%"),
            ratio_row("Leverage Ratio",       s.company_ins_leverage_ratio,        "x"),
            ratio_row("Equity to Liabilities",s.company_ins_equity_to_liabilities, "ratio"),
            ratio_row("Reserve Coverage Ratio",s.company_ins_reserve_coverage,     "x"),
        ),
        # Liquidity
        ratio_category_card(
            "Liquidity",
            ratio_row("Operating Cash Flow Ratio", s.company_ins_ocf_ratio,              "x"),
            ratio_row("Investment Ratio",          s.company_ins_investment_ratio,        "%"),
            ratio_row("Cash to Liabilities",       s.company_ins_cash_to_liabilities,    "%"),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _finance_ratios_content() -> rx.Component:
    """Finance / NBFI specific ratios in 5 category sections."""
    s = AnalysisState
    return rx.grid(
        # Profitability
        ratio_category_card(
            "Profitability",
            ratio_row("Net Interest Margin (NIM)",       s.company_fin_nim,                      "%"),
            ratio_row("Yield on Earning Assets",         s.company_fin_yield_on_earning_assets,   "%"),
            ratio_row("Cost of Funds",                   s.company_fin_cost_of_funds,             "%"),
            ratio_row("Interest Spread",                 s.company_fin_interest_spread,           "%"),
            ratio_row("Return on Assets (ROA)",          s.company_fin_roa,                       "%"),
            ratio_row("Return on Equity (ROE)",          s.company_fin_roe,                       "%"),
            ratio_row("Net Profit Margin",               s.company_fin_net_margin,                "%"),
        ),
        # Efficiency
        ratio_category_card(
            "Efficiency",
            ratio_row("Cost-to-Income Ratio",            s.company_fin_cost_to_income,            "%"),
            ratio_row("Operating Expense Ratio",         s.company_fin_operating_expense_ratio,   "%"),
            ratio_row("Non-Interest Income Ratio",       s.company_fin_non_interest_income_ratio, "%"),
            ratio_row("Asset Utilisation",               s.company_fin_asset_utilisation,         "%"),
        ),
        # Leverage
        ratio_category_card(
            "Leverage",
            ratio_row("Debt-to-Equity (Borrowings)",     s.company_fin_debt_to_equity,            "x"),
            ratio_row("Debt-to-Assets",                  s.company_fin_debt_to_assets,            "%"),
            ratio_row("Equity Ratio",                    s.company_fin_equity_ratio,              "%"),
            ratio_row("Equity Multiplier",               s.company_fin_equity_multiplier,         "x"),
        ),
        # Liquidity
        ratio_category_card(
            "Liquidity",
            ratio_row("Cash Ratio",                      s.company_fin_cash_ratio,                "%"),
            ratio_row("Operating Cash Flow Ratio",       s.company_fin_ocf_ratio,                 "x"),
            ratio_row("Loan-to-Assets",                  s.company_fin_loan_to_assets,            "%"),
        ),
        # Asset Quality
        ratio_category_card(
            "Asset Quality",
            ratio_row("NPA Ratio",                       s.company_fin_npa_ratio,                 "%"),
            ratio_row("Receivables-to-Assets",           s.company_fin_receivables_to_assets,     "%"),
            ratio_row("Provision Coverage",              s.company_fin_provision_coverage,        "x"),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def ratios_tab_content() -> rx.Component:
    """Full ratio display with sector branching (bank / insurance / finance / standard)."""
    s = AnalysisState
    return rx.cond(
        s.company_is_bank,
        _bank_ratios_content(),
        rx.cond(
            s.company_is_insurance,
            _insurance_ratios_content(),
            rx.cond(
                s.company_is_finance,
                _finance_ratios_content(),
                _standard_ratios_content(),
            ),
        ),
    )


def _sector_criterion_row(item: dict) -> rx.Component:
    """A single forensic criterion row for sector-specific scoring."""
    return rx.hstack(
        rx.cond(
            item["pass"] == 1,
            rx.icon("circle-check", size=16, class_name="text-green-400"),
            rx.cond(
                item["pass"] == 0,
                rx.icon("circle-x", size=16, class_name="text-red-400"),
                rx.icon("circle-help", size=16, class_name="text-slate-500"),
            ),
        ),
        rx.vstack(
            rx.text(item["label"], class_name="text-slate-300 text-sm"),
            rx.text(item["explanation"], class_name="text-slate-500 text-xs"),
            spacing="0",
            align="start",
        ),
        spacing="2",
        align="center",
        class_name="py-1",
    )


def _sector_forensic_panel() -> rx.Component:
    """Sector-specific forensic scoring panel for Banking / Insurance / Finance."""
    s = AnalysisState
    return rx.grid(
        # Left: criteria checklist
        rx.box(
            rx.hstack(
                rx.text("Sector Forensic Score", class_name="text-slate-200 font-semibold"),
                rx.spacer(),
                rx.text(
                    s.company_sector_forensic_score_display,
                    class_name="text-green-400 font-mono font-bold text-sm",
                ),
                width="100%",
                align="center",
                class_name="mb-3",
            ),
            rx.foreach(s.company_sector_forensic_criteria, _sector_criterion_row),
            class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
        ),
        # Right: YoY change bar chart
        rx.box(
            rx.text("Year-on-Year Key Ratio Changes (%)", class_name="text-slate-200 font-semibold mb-3"),
            rx.cond(
                s.company_sector_forensic_chart_data.length() == 0,
                rx.text(
                    "No prior-year data available for trend chart.",
                    class_name="text-slate-500 text-sm",
                ),
                rx.recharts.bar_chart(
                    rx.recharts.x_axis(type_="number", unit="%"),
                    rx.recharts.y_axis(data_key="metric", type_="category", width=120),
                    rx.recharts.bar(data_key="change", fill="#60a5fa"),
                    rx.recharts.reference_line(x=0, stroke="#64748b", stroke_dasharray="4 4"),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=s.company_sector_forensic_chart_data,
                    layout="vertical",
                    width="100%",
                    height=220,
                ),
            ),
            rx.text(
                "Green = improvement vs prior year. Red = deterioration. "
                "For ratios where lower is better (NPL, Cost-to-Income, Leverage), "
                "a negative change is shown as green.",
                class_name="text-slate-600 text-xs mt-3",
            ),
            class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def forensic_tab_content() -> rx.Component:
    """Piotroski F-Score criteria + Beneish M-Score horizontal bar chart and table."""
    s = AnalysisState
    return rx.cond(
        s.company_is_bank | s.company_is_insurance | s.company_is_finance,
        _sector_forensic_panel(),
        rx.grid(
        # Left: Piotroski criteria
        rx.box(
            rx.text(
                "Piotroski F-Score Criteria",
                class_name="text-slate-200 font-semibold mb-3",
            ),
            rx.vstack(
                piotroski_criterion("ROA Positive",                         s.company_f1),
                piotroski_criterion("Operating Cash Flow Positive",         s.company_f2),
                piotroski_criterion("ROA Improving YoY",                    s.company_f3),
                piotroski_criterion("Cash Earnings Quality (OCF/Assets > ROA)", s.company_f4),
                piotroski_criterion("Leverage Decreased",                   s.company_f5),
                piotroski_criterion("Current Ratio Improved",               s.company_f6),
                piotroski_criterion("Gross Margin Improving",               s.company_f8),
                piotroski_criterion("Asset Turnover Improving",             s.company_f9),
                spacing="0",
                align="start",
            ),
            class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
        ),
        # Right: Beneish M-Score chart + table
        rx.box(
            rx.text(
                "Beneish M-Score Indices",
                class_name="text-slate-200 font-semibold mb-3",
            ),
            rx.recharts.bar_chart(
                rx.recharts.x_axis(type_="number"),
                rx.recharts.y_axis(data_key="index", type_="category"),
                rx.recharts.bar(data_key="value", fill="#60a5fa"),
                rx.recharts.reference_line(x=1, stroke="#ef4444", stroke_dasharray="4 4"),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                data=s.company_beneish_chart_data,
                layout="vertical",
                width="100%",
                height=240,
            ),
            rx.separator(class_name="border-slate-700 my-3"),
            rx.table.root(
                rx.table.body(
                    ratio_row("DSRI (Receivables)", s.company_dsri, ""),
                    ratio_row("GMI (Gross Margin)", s.company_gmi,  ""),
                    ratio_row("AQI (Asset Quality)", s.company_aqi, ""),
                    ratio_row("SGI (Sales Growth)", s.company_sgi,  ""),
                    ratio_row("SGAI (SG&A)",         s.company_sgai,""),
                    ratio_row("LVGI (Leverage)",     s.company_lvgi,""),
                    ratio_row("TATA (Accruals)",     s.company_tata,""),
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
    )


def valuation_card(title: str, value: rx.Var, unit: str, has_shares: rx.Var) -> rx.Component:
    """A valuation ratio card with conditional rendering based on shares availability."""
    return rx.cond(
        has_shares,
        rx.box(
            rx.text(title, class_name="text-slate-400 text-xs uppercase tracking-wider mb-1"),
            rx.hstack(
                rx.text(value, class_name="text-2xl font-bold text-slate-100 font-mono"),
                rx.text(unit, class_name="text-slate-500 text-sm self-end mb-1"),
                spacing="1",
                align="end",
            ),
            class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
        ),
        rx.box(
            rx.text(title, class_name="text-slate-400 text-xs uppercase tracking-wider mb-1"),
            rx.hstack(
                rx.text("N/A", class_name="text-2xl font-bold text-slate-500 font-mono"),
                rx.box(
                    rx.icon("pencil", size=14, class_name="text-slate-500 hover:text-slate-300 cursor-pointer"),
                    on_click=AnalysisState.toggle_shares_input,
                ),
                spacing="2",
                align="center",
            ),
            rx.text("Enter shares outstanding to compute", class_name="text-slate-500 text-xs mt-1"),
            class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
        ),
    )


def shares_input_card() -> rx.Component:
    """Inline edit card for entering shares outstanding."""
    return rx.box(
        rx.text("Shares Outstanding", class_name="text-slate-400 text-xs uppercase tracking-wider mb-1"),
        rx.input(
            placeholder="e.g. 45,000,000",
            value=AnalysisState.company_shares_input_value,
            on_change=AnalysisState.set_shares_input_value,
            class_name="text-sm bg-slate-800 border-slate-700 text-slate-100 rounded px-2 py-1 w-full mb-2",
        ),
        rx.hstack(
            rx.text(
                "Save Shares",
                on_click=AnalysisState.save_shares_outstanding(AnalysisState.company_shares_input_value),
                class_name="text-xs text-green-400 hover:text-green-300 cursor-pointer",
            ),
            rx.text(
                "Discard changes",
                on_click=AnalysisState.toggle_shares_input,
                class_name="text-xs text-slate-500 hover:text-slate-400 ml-2 cursor-pointer",
            ),
            spacing="2",
        ),
        class_name="bg-slate-900 rounded-lg border border-green-800 p-4",
    )


def range_toggle() -> rx.Component:
    """Range toggle button group for chart date filtering."""
    s = AnalysisState
    ranges = ["1M", "6M", "1Y", "All"]
    return rx.hstack(
        *[
            rx.button(
                r,
                on_click=s.set_valuation_range(r),
                class_name=rx.cond(
                    s.valuation_range == r,
                    "px-3 py-2 rounded text-xs font-medium bg-slate-700 text-green-400 border border-slate-600",
                    "px-3 py-2 rounded text-xs font-medium bg-transparent text-slate-400 hover:text-slate-200 border border-transparent",
                ),
            )
            for r in ranges
        ],
        spacing="1",
    )


def price_chart_section() -> rx.Component:
    """Price history line chart and volume bar chart in a card container."""
    s = AnalysisState
    return rx.box(
        rx.hstack(
            rx.text("Price History", class_name="text-slate-200 font-bold"),
            rx.spacer(),
            range_toggle(),
            align="center",
            width="100%",
            class_name="mb-3",
        ),
        rx.text("Close Price (MNT)", class_name="text-slate-400 text-xs mb-2"),
        rx.recharts.line_chart(
            rx.recharts.line(data_key="close", stroke="#4ade80", dot=False, stroke_width=2),
            rx.recharts.x_axis(data_key="date", tick={"fontSize": 11, "fill": "#94a3b8"}),
            rx.recharts.y_axis(tick={"fontSize": 11, "fill": "#94a3b8"}, width=60),
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#1e293b"),
            rx.recharts.tooltip(content_style={"backgroundColor": "#1e293b", "border": "1px solid #334155"}),
            data=s.company_price_chart_data,
            width="100%",
            height=240,
        ),
        rx.text("Volume", class_name="text-slate-500 text-xs mt-2 mb-1"),
        rx.recharts.bar_chart(
            rx.recharts.bar(data_key="volume", fill="#60a5fa", opacity=0.7),
            rx.recharts.x_axis(data_key="date", tick=False),
            rx.recharts.y_axis(tick={"fontSize": 10, "fill": "#64748b"}, width=60),
            data=s.company_volume_chart_data,
            width="100%",
            height=80,
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 w-full",
    )


def valuation_tab_content() -> rx.Component:
    """Valuation tab: sector-aware ratio cards, shares input, price chart."""
    s = AnalysisState
    has_shares = s.company_shares_outstanding != ""

    standard_cards = rx.grid(
        valuation_card("EV / EBIT",  s.company_ev_ebitda, "x", has_shares),
        valuation_card("FCF Yield",  s.company_fcf_yield, "%", has_shares),
        valuation_card("P / E",      s.company_pe,        "x", has_shares),
        valuation_card("P / BV",     s.company_pbv,       "x", has_shares),
        columns="4", spacing="4", width="100%",
    )

    bank_cards = rx.grid(
        valuation_card("P / E",    s.company_pe,      "x", has_shares),
        valuation_card("P / BV",   s.company_pbv,     "x", has_shares),
        valuation_card("P / TBV",  s.company_ptbv,    "x", has_shares),
        valuation_card("P / PPOP", s.company_p_ppop,  "x", has_shares),
        valuation_card("P / NII",  s.company_p_nii,   "x", has_shares),
        columns="5", spacing="4", width="100%",
    )

    nbfi_cards = rx.grid(
        valuation_card("P / E",    s.company_pe,     "x", has_shares),
        valuation_card("P / BV",   s.company_pbv,    "x", has_shares),
        valuation_card("P / PPOP", s.company_p_ppop, "x", has_shares),
        valuation_card("P / NII",  s.company_p_nii,  "x", has_shares),
        columns="4", spacing="4", width="100%",
    )

    holding_cards = rx.grid(
        valuation_card("P / E",       s.company_pe,        "x", has_shares),
        valuation_card("P / NAV",     s.company_pbv,       "x", has_shares),
        valuation_card("P / Inv Sec", s.company_p_inv_sec, "x", has_shares),
        columns="3", spacing="4", width="100%",
    )

    securities_cards = rx.grid(
        valuation_card("P / E",       s.company_pe,        "x", has_shares),
        valuation_card("P / BV",      s.company_pbv,       "x", has_shares),
        valuation_card("P / Revenue", s.company_p_revenue, "x", has_shares),
        columns="3", spacing="4", width="100%",
    )

    insurance_cards = rx.grid(
        valuation_card("P / E",   s.company_pe,    "x", has_shares),
        valuation_card("P / BV",  s.company_pbv,   "x", has_shares),
        valuation_card("P / NPE", s.company_p_npe, "x", has_shares),
        valuation_card("P / UWP", s.company_p_uwp, "x", has_shares),
        columns="4", spacing="4", width="100%",
    )

    cards_row = rx.cond(
        s.company_valuation_sector == "commercial_bank",
        bank_cards,
        rx.cond(
            s.company_valuation_sector == "nbfi",
            nbfi_cards,
            rx.cond(
                s.company_valuation_sector == "holding",
                holding_cards,
                rx.cond(
                    s.company_valuation_sector == "securities",
                    securities_cards,
                    rx.cond(
                        s.company_valuation_sector == "insurance",
                        insurance_cards,
                        standard_cards,
                    ),
                ),
            ),
        ),
    )

    return rx.vstack(
        rx.cond(
            s.company_shares_input_open,
            shares_input_card(),
            cards_row,
        ),
        price_chart_section(),
        spacing="6",
        width="100%",
    )


def dupont_tab_content() -> rx.Component:
    """Sector-aware DuPont decomposition."""
    s = AnalysisState

    def dupont_row(
        year_label: str,
        factor1: rx.Var,
        factor2: rx.Var,
        eq_multiplier: rx.Var,
        roe: rx.Var,
    ) -> rx.Component:
        return rx.hstack(
            rx.box(
                rx.text(year_label, class_name="text-slate-400 text-xs uppercase tracking-wider mb-1"),
                class_name="w-24 flex-shrink-0",
            ),
            # Factor 1: Net Margin (standard/insurance) or ROA (bank/finance)
            rx.box(
                rx.text(s.company_dupont_factor1_label, class_name="text-slate-400 text-xs mb-1"),
                rx.text(factor1, class_name="text-slate-100 text-lg font-mono font-bold"),
                rx.text(s.company_dupont_factor1_unit, class_name="text-slate-500 text-xs"),
                class_name="flex flex-col items-center flex-1",
            ),
            rx.text("×", class_name="text-slate-500 text-xl font-bold px-1"),
            # Factor 2: conditionally shown (hidden for 2-factor bank/finance DuPont)
            rx.cond(
                s.company_dupont_show_factor2,
                rx.hstack(
                    rx.box(
                        rx.text(s.company_dupont_factor2_label, class_name="text-slate-400 text-xs mb-1"),
                        rx.text(factor2, class_name="text-slate-100 text-lg font-mono font-bold"),
                        rx.text(s.company_dupont_factor2_unit, class_name="text-slate-500 text-xs"),
                        class_name="flex flex-col items-center flex-1",
                    ),
                    rx.text("×", class_name="text-slate-500 text-xl font-bold px-1"),
                    spacing="2",
                    align="center",
                ),
                rx.box(),
            ),
            rx.box(
                rx.text("Equity Multiplier", class_name="text-slate-400 text-xs mb-1"),
                rx.text(eq_multiplier, class_name="text-slate-100 text-lg font-mono font-bold"),
                rx.text("x", class_name="text-slate-500 text-xs"),
                class_name="flex flex-col items-center flex-1",
            ),
            rx.text("=", class_name="text-green-400 text-xl font-bold px-1"),
            rx.box(
                rx.text("ROE", class_name="text-slate-400 text-xs mb-1"),
                rx.text(roe, class_name="text-green-400 text-lg font-mono font-bold"),
                rx.text("%", class_name="text-slate-500 text-xs"),
                class_name="flex flex-col items-center flex-1",
            ),
            spacing="2",
            align="center",
            width="100%",
            class_name="bg-slate-800/50 rounded-lg p-4",
        )

    return rx.box(
        rx.text("DuPont Decomposition", class_name="text-slate-200 font-semibold mb-2"),
        rx.text(
            s.company_dupont_formula_text,
            class_name="text-slate-400 text-sm mb-4 font-mono",
        ),
        rx.vstack(
            dupont_row(
                "Current Year",
                s.company_net_margin_dupont,
                s.company_asset_turnover_dupont,
                s.company_equity_multiplier_curr,
                s.company_roe_dupont,
            ),
            dupont_row(
                "Prior Year",
                s.company_net_margin_prev,
                s.company_asset_turnover_prev,
                s.company_equity_multiplier_prev,
                s.company_roe_prev,
            ),
            spacing="3",
            width="100%",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 w-full",
    )


def red_flag_item(flag: dict) -> rx.Component:
    """A single red flag card with severity-aware styling."""
    severity = flag["severity"]
    is_clear = flag["flag"] == "No Major Red Flags"
    is_high = severity == "high"
    is_medium = severity == "medium"

    icon_el = rx.cond(
        is_clear,
        rx.icon("circle-check", size=20, class_name="text-green-400 shrink-0"),
        rx.cond(
            is_high,
            rx.icon("octagon-alert", size=20, class_name="text-red-400 shrink-0"),
            rx.cond(
                is_medium,
                rx.icon("triangle-alert", size=20, class_name="text-amber-400 shrink-0"),
                rx.icon("info", size=20, class_name="text-blue-400 shrink-0"),
            ),
        ),
    )

    title_class = rx.cond(
        is_clear,
        "text-green-400 font-semibold text-sm",
        rx.cond(
            is_high,
            "text-red-400 font-semibold text-sm",
            rx.cond(
                is_medium,
                "text-amber-400 font-semibold text-sm",
                "text-blue-400 font-semibold text-sm",
            ),
        ),
    )

    severity_badge = rx.cond(
        is_clear,
        rx.badge("CLEAR", color_scheme="green", size="1"),
        rx.cond(
            is_high,
            rx.badge("HIGH", color_scheme="red", size="1"),
            rx.cond(
                is_medium,
                rx.badge("MEDIUM", color_scheme="yellow", size="1"),
                rx.badge("LOW", color_scheme="blue", size="1"),
            ),
        ),
    )

    border_class = rx.cond(
        is_clear,
        "bg-slate-900 border border-green-900 rounded-lg p-4",
        rx.cond(
            is_high,
            "bg-slate-900 border border-red-900 rounded-lg p-4",
            rx.cond(
                is_medium,
                "bg-slate-900 border border-amber-900 rounded-lg p-4",
                "bg-slate-900 border border-blue-900 rounded-lg p-4",
            ),
        ),
    )

    return rx.box(
        rx.hstack(
            icon_el,
            rx.vstack(
                rx.hstack(
                    rx.text(flag["flag"], class_name=title_class),
                    severity_badge,
                    spacing="2",
                    align="center",
                ),
                rx.text(flag["explanation"], class_name="text-slate-400 text-sm"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="start",
        ),
        class_name=border_class,
    )


def red_flags_tab_content() -> rx.Component:
    """Red flags tab with AI analysis and loading state."""
    return rx.vstack(
        rx.cond(
            AnalysisState.company_red_flags_loading,
            rx.vstack(
                rx.hstack(
                    rx.spinner(size="3", class_name="text-violet-400"),
                    rx.text("AI is analysing financial data...", class_name="text-slate-400 text-sm"),
                    spacing="3",
                    align="center",
                ),
                rx.text(
                    "Groq AI is cross-referencing ratios, forensic scores, DuPont decomposition, valuation multiples, and stock price context.",
                    class_name="text-slate-500 text-xs text-center",
                ),
                align="center",
                spacing="2",
                width="100%",
                class_name="py-6",
            ),
            rx.foreach(AnalysisState.company_red_flags, red_flag_item),
        ),
        rx.cond(
            ~AnalysisState.company_red_flags_loading,
            rx.hstack(
                rx.icon("sparkles", size=12, class_name="text-violet-400"),
                rx.text("Powered by Groq AI — llama-3.3-70b-versatile", class_name="text-slate-600 text-xs"),
                spacing="1",
                align="center",
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


# ── Main page ─────────────────────────────────────────────────────────────────


def company_page() -> rx.Component:
    """Full company analysis page with 5-tab layout."""
    s = AnalysisState

    return page_layout(
        rx.cond(
            s.selected_company_name == "",
            # Empty state
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
            # Company detail
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
                # Hero score cards row (4 cards)
                rx.grid(
                    score_card("Health Score",     s.company_score.to_string(), "/100"),
                    score_card(
                        rx.cond(
                            s.company_is_bank | s.company_is_insurance | s.company_is_finance,
                            "Sector Forensic Score",
                            "Piotroski F-Score",
                        ),
                        rx.cond(
                            s.company_is_bank | s.company_is_insurance | s.company_is_finance,
                            s.company_sector_forensic_score_display,
                            s.company_f_score_display,
                        ),
                        "",
                    ),
                    score_card("M-Score",          s.company_m_score_display,   ""),
                    score_card("M-Score Result",   s.company_m_interp,          ""),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                # Health gauge + Radar chart side by side
                rx.grid(
                    health_gauge(),
                    radar_chart_panel(),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                # 5-tab panel
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(
                            "Ratios",
                            value="ratios",
                            class_name="text-slate-400 data-[state=active]:text-green-400 data-[state=active]:border-b-2 data-[state=active]:border-green-400 px-4 py-2 text-sm font-medium",
                        ),
                        rx.tabs.trigger(
                            "Forensic",
                            value="forensic",
                            class_name="text-slate-400 data-[state=active]:text-green-400 data-[state=active]:border-b-2 data-[state=active]:border-green-400 px-4 py-2 text-sm font-medium",
                        ),
                        rx.tabs.trigger(
                            "Valuation",
                            value="valuation",
                            class_name="text-slate-400 data-[state=active]:text-green-400 data-[state=active]:border-b-2 data-[state=active]:border-green-400 px-4 py-2 text-sm font-medium",
                        ),
                        rx.tabs.trigger(
                            "DuPont",
                            value="dupont",
                            class_name="text-slate-400 data-[state=active]:text-green-400 data-[state=active]:border-b-2 data-[state=active]:border-green-400 px-4 py-2 text-sm font-medium",
                        ),
                        rx.tabs.trigger(
                            "Red Flags",
                            value="redflags",
                            class_name="text-slate-400 data-[state=active]:text-green-400 data-[state=active]:border-b-2 data-[state=active]:border-green-400 px-4 py-2 text-sm font-medium",
                        ),
                        class_name="border-b border-slate-800",
                    ),
                    rx.tabs.content(ratios_tab_content(),     value="ratios"),
                    rx.tabs.content(forensic_tab_content(),   value="forensic"),
                    rx.tabs.content(valuation_tab_content(),  value="valuation"),
                    rx.tabs.content(dupont_tab_content(),     value="dupont"),
                    rx.tabs.content(red_flags_tab_content(),  value="redflags"),
                    default_value="ratios",
                    width="100%",
                    class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
                ),
                spacing="5",
                width="100%",
                align="start",
            ),
        ),
    )
