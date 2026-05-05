"""Company Health Analysis page — 6-tab layout with overview, sector-aware ratios, charts, DuPont, and red flags."""
import reflex as rx

from ..components.layout import page_layout
from ..state import AnalysisState, PortfolioState, UploadState

# ── Palette ───────────────────────────────────────────────────────────────────
_NAVY   = "#4361EE"
_BLUE   = "#6B9FFF"
_POWDER = "#B4C5E4"
_TEXT   = "#DDE2F2"
_MUTED  = "#8892A8"
_FAINT  = "#5A627A"
_CARD   = "#161B27"
_BORDER = "#2A3050"

# ── Helper components ─────────────────────────────────────────────────────────

def info_icon(tooltip_text: str) -> rx.Component:
    return rx.tooltip(
        rx.icon("info", size=13, class_name="cursor-help shrink-0", style={"color": _POWDER + "70"}),
        content=tooltip_text,
    )


def score_card(title: str, value: rx.Var, unit: str = "") -> rx.Component:
    return rx.box(
        rx.text(title, class_name="text-xs font-semibold uppercase tracking-wider mb-1", style={"color": _MUTED}),
        rx.hstack(
            rx.text(value, class_name="text-2xl font-bold", style={"color": _TEXT}),
            rx.text(unit, class_name="text-sm self-end mb-0.5", style={"color": _FAINT}),
            spacing="1",
            align="end",
        ),
        class_name="rounded-2xl p-5",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
    )


def _row_bg(color_key: str) -> rx.Var:
    c = AnalysisState.company_ratio_color_map[color_key]
    return rx.cond(
        AnalysisState.show_ratio_colors,
        rx.cond(
            c == "good",
            "border-b transition-colors bg-green-950/50",
            rx.cond(
                c == "bad",
                "border-b transition-colors bg-red-950/50",
                "border-b transition-colors bg-amber-950/30",
            ),
        ),
        "border-b transition-colors",
    )


def colored_ratio_row(
    label_en: str,
    label_mn: str,
    value: rx.Var,
    unit: str,
    color_key: str,
    tooltip: str = "",
) -> rx.Component:
    label_display = rx.cond(UploadState.lang == "EN", label_en, label_mn)
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(label_display, class_name="text-sm", style={"color": _TEXT}),
                info_icon(tooltip) if tooltip else rx.fragment(),
                spacing="1",
                align="center",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.text(value, class_name="text-sm font-mono font-semibold", style={"color": _BLUE}),
            class_name="py-2 px-4 text-right",
        ),
        rx.table.cell(
            rx.text(unit, class_name="text-xs", style={"color": _FAINT}),
            class_name="py-2 px-4",
        ),
        class_name=_row_bg(color_key),
        style={"borderColor": _BORDER},
    )


def ratio_row(label: str, value: rx.Var, unit: str = "", tooltip: str = "") -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.text(label, class_name="text-sm", style={"color": _TEXT}),
                info_icon(tooltip) if tooltip else rx.fragment(),
                spacing="1",
                align="center",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.text(value, class_name="text-sm font-mono font-semibold", style={"color": _BLUE}),
            class_name="py-2 px-4 text-right",
        ),
        rx.table.cell(
            rx.text(unit, class_name="text-xs", style={"color": _FAINT}),
            class_name="py-2 px-4",
        ),
        class_name="border-b",
        style={"borderColor": _BORDER},
    )


def ratio_category_card(title: str, tooltip: str, *rows) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(title, class_name="text-xs font-semibold uppercase tracking-wider", style={"color": _BLUE}),
            info_icon(tooltip),
            spacing="1",
            align="center",
            class_name="mb-3",
        ),
        rx.table.root(
            rx.table.body(*rows),
            variant="ghost",
            class_name="w-full",
        ),
        class_name="rounded-2xl p-5",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
    )


def piotroski_criterion(label: str, value: rx.Var, tooltip: str = "") -> rx.Component:
    return rx.hstack(
        rx.cond(
            value == 1,
            rx.icon("circle-check", size=16, class_name="text-green-400"),
            rx.cond(
                value == 0,
                rx.icon("circle-x", size=16, class_name="text-red-400"),
                rx.icon("circle-help", size=16, style={"color": _POWDER + "60"}),
            ),
        ),
        rx.text(label, class_name="text-sm flex-1", style={"color": _TEXT}),
        info_icon(tooltip) if tooltip else rx.fragment(),
        spacing="2",
        align="center",
        class_name="py-1",
    )


# ── Chart components ──────────────────────────────────────────────────────────

def health_gauge() -> rx.Component:
    s = AnalysisState
    return rx.box(
        rx.recharts.radial_bar_chart(
            rx.recharts.radial_bar(data_key="value", min_angle=15, background=True),
            data=s.company_gauge_data,
            start_angle=180,
            end_angle=0,
            inner_radius="55%",
            outer_radius="85%",
            width="100%",
            height=260,
        ),
        rx.text(s.company_score.to_string() + " / 100", class_name="text-2xl font-bold text-center -mt-12", style={"color": _TEXT}),
        rx.text(s.company_health_label, class_name="text-sm text-center mt-1", style={"color": _MUTED}),
        class_name="rounded-2xl p-5 flex flex-col items-center justify-center",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}", "minHeight": "320px"},
    )


def radar_chart_panel() -> rx.Component:
    s = AnalysisState
    return rx.box(
        rx.text("Health Category Breakdown", class_name="font-semibold mb-2", style={"color": _TEXT}),
        rx.recharts.radar_chart(
            rx.recharts.polar_grid(),
            rx.recharts.polar_angle_axis(data_key="category", tick={"fill": _MUTED, "fontSize": 12}),
            rx.recharts.radar(data_key="score", name="Health", fill=_BLUE, fill_opacity=0.2, stroke=_NAVY),
            data=s.company_radar_data,
            cx="50%",
            cy="50%",
            outer_radius="65%",
            width="100%",
            height=320,
        ),
        class_name="rounded-2xl p-5 flex flex-col",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}", "minHeight": "320px"},
    )


# ── Overview tab ──────────────────────────────────────────────────────────────

def overview_tab_content() -> rx.Component:
    s = AnalysisState
    return rx.vstack(
        rx.grid(
            health_gauge(),
            radar_chart_panel(),
            columns="2",
            spacing="4",
            width="100%",
        ),
        rx.grid(
            # Key metrics
            rx.box(
                rx.hstack(
                    rx.text("Key Metrics", class_name="font-semibold text-sm", style={"color": _TEXT}),
                    info_icon("Snapshot of the most important financial ratios for a quick health check."),
                    spacing="1",
                    align="center",
                    class_name="mb-4",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("ROE", class_name="text-xs font-semibold w-40", style={"color": _MUTED}),
                        rx.text(s.company_roe, class_name="text-sm font-mono font-bold", style={"color": _BLUE}),
                        rx.text("%", class_name="text-xs", style={"color": _FAINT}),
                        spacing="2", align="center", class_name="py-2 border-b", style={"borderColor": _BORDER},
                    ),
                    rx.hstack(
                        rx.text("ROA", class_name="text-xs font-semibold w-40", style={"color": _MUTED}),
                        rx.text(s.company_roa, class_name="text-sm font-mono font-bold", style={"color": _BLUE}),
                        rx.text("%", class_name="text-xs", style={"color": _FAINT}),
                        spacing="2", align="center", class_name="py-2 border-b", style={"borderColor": _BORDER},
                    ),
                    rx.hstack(
                        rx.text("Net Margin", class_name="text-xs font-semibold w-40", style={"color": _MUTED}),
                        rx.text(s.company_net_margin, class_name="text-sm font-mono font-bold", style={"color": _BLUE}),
                        rx.text("%", class_name="text-xs", style={"color": _FAINT}),
                        spacing="2", align="center", class_name="py-2 border-b", style={"borderColor": _BORDER},
                    ),
                    rx.hstack(
                        rx.text("Debt / Equity", class_name="text-xs font-semibold w-40", style={"color": _MUTED}),
                        rx.text(s.company_debt_equity, class_name="text-sm font-mono font-bold", style={"color": _BLUE}),
                        rx.text("x", class_name="text-xs", style={"color": _FAINT}),
                        spacing="2", align="center", class_name="py-2 border-b", style={"borderColor": _BORDER},
                    ),
                    rx.hstack(
                        rx.text("Current Ratio", class_name="text-xs font-semibold w-40", style={"color": _MUTED}),
                        rx.text(s.company_current_ratio, class_name="text-sm font-mono font-bold", style={"color": _BLUE}),
                        rx.text("x", class_name="text-xs", style={"color": _FAINT}),
                        spacing="2", align="center", class_name="py-2 border-b", style={"borderColor": _BORDER},
                    ),
                    rx.hstack(
                        rx.text("Altman Z-Score", class_name="text-xs font-semibold w-40", style={"color": _MUTED}),
                        rx.text(s.company_z_score, class_name="text-sm font-mono font-bold", style={"color": _BLUE}),
                        spacing="2", align="center", class_name="py-2",
                    ),
                    spacing="0",
                    width="100%",
                ),
                class_name="rounded-2xl p-5 self-start",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            # Risk signals
            rx.box(
                rx.hstack(
                    rx.text("Risk Signals", class_name="font-semibold text-sm", style={"color": _TEXT}),
                    info_icon("Top risk signals identified by the AI analysis engine. Go to the Red Flags tab for full detail."),
                    spacing="1",
                    align="center",
                    class_name="mb-4",
                ),
                rx.cond(
                    s.company_red_flags_loading,
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("AI analysing...", class_name="text-xs", style={"color": _FAINT}),
                        spacing="2",
                        align="center",
                        class_name="py-4",
                    ),
                    rx.vstack(
                        rx.foreach(
                            s.company_red_flags,
                            lambda flag: rx.box(
                                rx.hstack(
                                    rx.cond(
                                        flag["severity"] == "high",
                                        rx.icon("octagon-alert", size=16, class_name="text-red-400 shrink-0"),
                                        rx.cond(
                                            flag["severity"] == "medium",
                                            rx.icon("triangle-alert", size=16, class_name="text-amber-400 shrink-0"),
                                            rx.cond(
                                                flag["severity"] == "clear",
                                                rx.icon("circle-check", size=16, class_name="text-green-400 shrink-0"),
                                                rx.icon("info", size=16, class_name="text-blue-400 shrink-0"),
                                            ),
                                        ),
                                    ),
                                    rx.vstack(
                                        rx.text(flag["flag"], class_name="text-sm font-semibold", style={"color": _TEXT}),
                                        rx.text(flag["explanation"], class_name="text-xs", style={"color": _MUTED}),
                                        spacing="0",
                                        align="start",
                                    ),
                                    spacing="2",
                                    align="start",
                                ),
                                class_name="py-2 border-b",
                                style={"borderColor": _BORDER},
                            ),
                        ),
                        spacing="0",
                        width="100%",
                    ),
                ),
                class_name="rounded-2xl p-5",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


# ── Ratios tab ────────────────────────────────────────────────────────────────

def _standard_ratios_content() -> rx.Component:
    s = AnalysisState
    return rx.grid(
        ratio_category_card(
            "Profitability",
            "How much profit the company generates relative to its revenue and assets.",
            colored_ratio_row("Return on Assets (ROA)",  "Нийт хөрөнгийн өгөөж",     s.company_roa,              "%",    "roa",              "ROA = Net Income / Total Assets. Good: >5%. Measures how efficiently assets generate profit."),
            colored_ratio_row("Return on Equity (ROE)",  "Өмчийн өгөөж",              s.company_roe,              "%",    "roe",              "ROE = Net Income / Equity. Good: >10%. Shows return to shareholders."),
            colored_ratio_row("Net Profit Margin",       "Цэвэр ашгийн маржин",       s.company_net_margin,       "%",    "net_margin",       "Net Margin = Net Income / Revenue. Good: >5%. Higher means more profit per unit of revenue."),
            colored_ratio_row("Gross Profit Margin",     "Нийт ашгийн маржин",        s.company_gross_margin,     "%",    "gross_margin",     "Gross Margin = Gross Profit / Revenue. Good: >20%. Measures production efficiency."),
            colored_ratio_row("Operating Margin",        "Үйл ажиллагааны маржин",    s.company_operating_margin, "%",    "operating_margin", "Operating Margin = EBIT / Revenue. Good: >10%. Core business profitability before interest & taxes."),
            colored_ratio_row("EBIT Margin",             "EBIT маржин",               s.company_ebit_margin,      "%",    "ebit_margin",      "EBIT Margin = EBIT / Revenue. Similar to operating margin; used for cross-sector comparison."),
        ),
        ratio_category_card(
            "Liquidity",
            "Can the company pay its short-term debts? Higher ratios = more cash buffer.",
            colored_ratio_row("Current Ratio",   "Поточ харьцаа",  s.company_current_ratio,   "x",            "current_ratio", "Current Ratio = Current Assets / Current Liabilities. Good: >1.5. Below 1.0 means potential cash crunch."),
            colored_ratio_row("Quick Ratio",     "Хурдан харьцаа", s.company_quick_ratio,     "x",            "quick_ratio",   "Quick Ratio = (Cash + Receivables) / Current Liabilities. Good: >1.0. Excludes inventory."),
            colored_ratio_row("Cash Ratio",      "Мөнгөн харьцаа", s.company_cash_ratio,      "x",            "cash_ratio",    "Cash Ratio = Cash / Current Liabilities. Most conservative liquidity measure. Good: >0.5."),
            ratio_row("Working Capital", s.company_working_capital, "₮ thousands",             "Working Capital = Current Assets − Current Liabilities. Positive = can cover short-term obligations."),
        ),
        ratio_category_card(
            "Solvency",
            "How much debt does the company carry? Lower D/E and higher interest coverage = safer.",
            colored_ratio_row("Debt-to-Equity",    "Өр/Өмч харьцаа",    s.company_debt_equity,    "x",     "debt_equity",    "D/E = Total Debt / Equity. Good: <1.0. High D/E increases financial risk."),
            colored_ratio_row("Debt-to-Assets",    "Өр/Хөрөнгө харьцаа", s.company_debt_to_assets, "ratio", "debt_to_assets", "Debt-to-Assets = Total Debt / Total Assets. Good: <0.4. Shows what fraction of assets is debt-financed."),
            colored_ratio_row("Equity Ratio",      "Өмчийн харьцаа",    s.company_equity_ratio,   "ratio", "equity_ratio",   "Equity Ratio = Equity / Total Assets. Good: >0.4. Inverse of leverage."),
            colored_ratio_row("Interest Coverage", "Хүүний бүрхэц",     s.company_interest_cov,   "x",     "interest_cov",   "Interest Coverage = EBIT / Interest Expense. Good: >3x. Below 1x means can't cover interest."),
        ),
        ratio_category_card(
            "Activity",
            "How efficiently does the company use its assets to generate revenue?",
            colored_ratio_row("Total Asset Turnover",       "Нийт хөрөнгийн эргэлт",    s.company_asset_turnover,           "times", "asset_turnover",           "Asset Turnover = Revenue / Total Assets. Good: >1.0. Higher = more revenue per unit of asset."),
            ratio_row("Fixed Asset Turnover",               s.company_fixed_asset_turnover,     "times", "Fixed Asset Turnover = Revenue / Fixed Assets. Measures how well fixed assets generate revenue."),
            ratio_row("Inventory Turnover",                 s.company_inventory_turnover,       "times", "Inventory Turnover = COGS / Inventory. Higher = faster inventory cycle."),
            ratio_row("Days Inventory Outstanding",         s.company_days_inventory,           "days",  "DIO = 365 / Inventory Turnover. Fewer days = faster inventory conversion."),
            ratio_row("Days Sales Outstanding",             s.company_days_sales_outstanding,   "days",  "DSO = Receivables / (Revenue / 365). Fewer days = faster cash collection."),
            ratio_row("Days Payable Outstanding",           s.company_days_payable_outstanding, "days",  "DPO = Payables / (COGS / 365). More days = better use of supplier credit."),
            ratio_row("Cash Conversion Cycle",              s.company_cash_conversion_cycle,    "days",  "CCC = DIO + DSO − DPO. Shorter = more efficient cash flow."),
        ),
        ratio_category_card(
            "Performance",
            "How well does the company convert earnings into cash?",
            colored_ratio_row("Operating CF Ratio", "Үйл ажиллагааны мөнгөн урсгал", s.company_ocf_ratio,          "x", "ocf_ratio",   "OCF Ratio = Operating Cash Flow / Current Liabilities. Good: >0.1. Shows cash generation quality."),
            colored_ratio_row("Cash Flow to Debt",  "Мөнгөн урсгал / Өр",            s.company_cf_to_debt,         "x", "cf_to_debt",  "CF-to-Debt = Operating Cash Flow / Total Debt. Good: >0.2. Higher = faster debt repayment capacity."),
            ratio_row("Reinvestment Ratio",                                            s.company_reinvestment_ratio, "x",               "Reinvestment Ratio = Capex / Operating CF. Shows how much cash is reinvested in the business."),
        ),
        ratio_category_card(
            "Altman Z-Score",
            "Bankruptcy prediction model. Z > 2.99 = Safe zone. 1.81–2.99 = Grey zone. < 1.81 = Distress zone.",
            colored_ratio_row("Altman Z-Score",                      "Альтман Z-оноо",   s.company_z_score, "score", "z_score", "Z > 2.99: Safe. 1.81–2.99: Grey zone. < 1.81: Financial distress likely. Validated on emerging markets."),
            ratio_row("X1: Working Capital / Total Assets",          s.company_z_x1,    "ratio", "X1 captures short-term liquidity relative to total assets. Positive is healthy."),
            ratio_row("X2: Retained Earnings / Total Assets",        s.company_z_x2,    "ratio", "X2 measures accumulated profitability. Higher = company has reinvested profits over time."),
            ratio_row("X3: EBIT / Total Assets",                     s.company_z_x3,    "ratio", "X3 measures operating return on assets. Key driver of the Z-Score."),
            ratio_row("X4: Equity / Total Liabilities",              s.company_z_x4,    "ratio", "X4 is the inverse leverage ratio. How much equity cushion protects creditors."),
            ratio_row("X5: Revenue / Total Assets",                  s.company_z_x5,    "ratio", "X5 is asset turnover. Measures how actively assets are being used."),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _bank_ratios_content() -> rx.Component:
    s = AnalysisState
    return rx.grid(
        ratio_category_card(
            "Profitability",
            "Key earnings metrics for a bank. NIM is the primary profitability driver.",
            colored_ratio_row("Net Interest Margin (NIM)",   "Цэвэр хүүний маржин",    s.company_bank_nim,                   "%", "bank_nim",                   "NIM = Net Interest Income / Earning Assets. Good: >4%. Core banking spread between loan and deposit rates."),
            colored_ratio_row("Return on Assets (ROA)",      "Нийт хөрөнгийн өгөөж",   s.company_bank_roa,                   "%", "bank_roa",                   "Bank ROA. Good: >1.5%. Banks operate with high leverage so ROA thresholds are lower than standard."),
            colored_ratio_row("Return on Equity (ROE)",      "Өмчийн өгөөж",            s.company_bank_roe,                   "%", "bank_roe",                   "Bank ROE. Good: >10%. Return generated for shareholders."),
            colored_ratio_row("Net Profit Margin",           "Цэвэр ашгийн маржин",    s.company_bank_net_margin,            "%", "bank_net_margin",            "Net Margin for banking income. Good: >15%."),
            colored_ratio_row("Interest Income Ratio",       "Хүүний орлогын харьцаа", s.company_bank_interest_income_ratio, "%", "bank_interest_income_ratio", "Interest income as share of total income. Good: >60%. Core revenue composition check."),
        ),
        ratio_category_card(
            "Capital Adequacy",
            "Capital buffer protecting depositors. Higher equity-to-assets = safer bank.",
            colored_ratio_row("Equity to Assets",    "Өмч/Хөрөнгө",       s.company_bank_equity_to_assets,  "ratio", "bank_equity_to_assets",  "Equity-to-Assets. Good: >12%. Inverse of leverage; Basel III-aligned capital cushion."),
            ratio_row("Equity Multiplier",           s.company_bank_equity_multiplier,  "x",     "Equity Multiplier = Total Assets / Equity. Lower = less leveraged bank."),
        ),
        ratio_category_card(
            "Asset Quality",
            "Loan book health. Lower NPL and higher coverage = better asset quality.",
            colored_ratio_row("NPL Ratio",               "МЗЗ харьцаа",          s.company_bank_npl_ratio,              "%", "bank_npl_ratio",         "NPL Ratio = Non-Performing Loans / Total Loans. Good: <3%. High NPL signals credit risk."),
            colored_ratio_row("Coverage Ratio",          "Бүрхэцийн харьцаа",   s.company_bank_coverage_ratio,         "x", "bank_coverage_ratio",    "Coverage = Loan Loss Reserves / NPLs. Good: >1.5x. Shows provisioning adequacy."),
            ratio_row("Loan Loss Reserve Ratio",         s.company_bank_loan_loss_reserve_ratio, "%", "Loan Loss Reserves / Total Loans. Higher = more conservative provisioning."),
            ratio_row("Provision to Loans",              s.company_bank_provision_to_loans,      "%", "New provisions as % of total loans. Rising trend signals deteriorating loan quality."),
        ),
        ratio_category_card(
            "Liquidity",
            "Can the bank fund withdrawals and meet obligations? LDR is the key watch ratio.",
            colored_ratio_row("Loan-to-Deposit (LDR)",   "Зээл/Хадгаламж",    s.company_bank_ldr,                "%", "bank_ldr",  "LDR = Loans / Deposits. Good: <80%. Above 90% means reliance on wholesale funding."),
            ratio_row("Cash to Deposits",                s.company_bank_cash_to_deposits,    "%", "Cash held as % of deposits. Higher = more liquid but less earning."),
            ratio_row("Loans to Total Assets",           s.company_bank_loans_to_assets,     "%", "Loan concentration in the asset base. High = more credit risk exposure."),
            ratio_row("Securities to Total Assets",      s.company_bank_securities_to_assets, "%", "Investment securities as % of assets. Higher = more liquidity buffer."),
        ),
        ratio_category_card(
            "Efficiency",
            "How much does it cost the bank to generate each unit of income?",
            colored_ratio_row("Cost-to-Income",          "Зардал/Орлого",     s.company_bank_cost_to_income,   "%", "bank_cost_to_income", "Cost-to-Income = Operating Expenses / Operating Income. Good: <50%. Lower = more efficient bank."),
            ratio_row("Non-Interest Income Ratio",       s.company_bank_fee_income_ratio, "%", "Fee and commission income as share of total income. Diversification of revenue sources."),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _insurance_ratios_content() -> rx.Component:
    s = AnalysisState
    return rx.grid(
        ratio_category_card(
            "Underwriting",
            "Core insurance profitability. Combined ratio < 100% means underwriting profit.",
            colored_ratio_row("Loss Ratio",     "Нөхөн төлбөрийн харьцаа", s.company_ins_loss_ratio,     "%", "ins_loss_ratio",     "Loss Ratio = Claims Paid / Premiums Earned. Good: <60%. Shows claims cost efficiency."),
            colored_ratio_row("Expense Ratio",  "Зардлын харьцаа",          s.company_ins_expense_ratio,  "%", "ins_expense_ratio",  "Expense Ratio = Underwriting Expenses / Premiums. Good: <25%. Operating cost efficiency."),
            colored_ratio_row("Combined Ratio", "Нийлмэл харьцаа",          s.company_ins_combined_ratio, "%", "ins_combined_ratio", "Combined Ratio = Loss + Expense Ratio. Good: <95%. Above 100% means underwriting loss."),
        ),
        ratio_category_card(
            "Profitability",
            "Overall earnings performance including investment returns.",
            colored_ratio_row("Return on Assets (ROA)",       "Нийт хөрөнгийн өгөөж",    s.company_ins_roa,                   "%", "ins_roa",        "Insurance ROA. Good: >3%. Lower than standard due to regulated reserve requirements."),
            colored_ratio_row("Return on Equity (ROE)",       "Өмчийн өгөөж",             s.company_ins_roe,                   "%", "ins_roe",        "ROE for insurers. Good: >10%."),
            colored_ratio_row("Net Profit Margin",            "Цэвэр ашгийн маржин",     s.company_ins_net_margin,            "%", "ins_net_margin", "Net Margin. Good: >10% for insurers."),
            ratio_row("Investment Income Ratio",              s.company_ins_investment_income_ratio, "%", "Investment income as % of total income. Diversification beyond underwriting."),
            ratio_row("Underwriting Profit Margin",           s.company_ins_underwriting_margin,     "%", "Underwriting Profit / Premiums. Positive means profitable before investment income."),
        ),
        ratio_category_card(
            "Solvency",
            "Can the insurer cover all claims? Solvency ratio must stay above 100%.",
            colored_ratio_row("Solvency Ratio",         "Төлбөрийн чадварын харьцаа", s.company_ins_solvency_ratio,        "%",    "ins_solvency_ratio",   "Solvency Ratio = Equity / Technical Reserves. Good: >150%. Regulator minimum is 100%."),
            colored_ratio_row("Reserve Coverage",       "Нөөцийн бүрхэц",             s.company_ins_reserve_coverage,      "x",    "ins_reserve_coverage", "Reserve Coverage = Reserves / Claims. Good: >1.5x. Shows adequacy of claim reserves."),
            ratio_row("Leverage Ratio",                 s.company_ins_leverage_ratio,        "x",    "Liabilities / Equity. Insurance-specific leverage measure."),
            ratio_row("Equity to Liabilities",          s.company_ins_equity_to_liabilities, "ratio","Equity as % of liabilities. Higher = more solvent."),
        ),
        ratio_category_card(
            "Liquidity",
            "Can the insurer pay claims quickly if needed?",
            colored_ratio_row("Operating Cash Flow Ratio", "Үйл ажиллагааны мөнгөн урсгал", s.company_ins_ocf_ratio,          "x",  "ins_ocf_ratio", "OCF / Current Liabilities. Good: >0.1. Measures ability to pay claims from operations."),
            ratio_row("Investment Ratio",                  s.company_ins_investment_ratio,   "%",   "Investments / Total Assets. Higher = stronger long-term reserve backing."),
            ratio_row("Cash to Liabilities",               s.company_ins_cash_to_liabilities, "%",  "Immediate liquidity ratio. Higher = can meet sudden large claims."),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _finance_ratios_content() -> rx.Component:
    s = AnalysisState
    return rx.grid(
        ratio_category_card(
            "Profitability",
            "Core earnings metrics for non-bank financial institutions (NBFI, securities firms, holding companies).",
            colored_ratio_row("Net Interest Margin (NIM)",       "Цэвэр хүүний маржин",        s.company_fin_nim,                      "%", "fin_nim",        "NIM = Net Interest Income / Earning Assets. Good: >4%. Key spread between lending and borrowing rates."),
            ratio_row("Yield on Earning Assets",                 s.company_fin_yield_on_earning_assets,   "%", "Average interest rate earned on loans and investments."),
            ratio_row("Cost of Funds",                           s.company_fin_cost_of_funds,             "%", "Average cost of borrowed funds. Lower = cheaper funding base."),
            ratio_row("Interest Spread",                         s.company_fin_interest_spread,           "%", "Yield on Assets − Cost of Funds. Wider spread = more profitable core business."),
            colored_ratio_row("Return on Assets (ROA)",          "Нийт хөрөнгийн өгөөж",       s.company_fin_roa,                       "%", "fin_roa",        "Finance sector ROA. Good: >2%. Lower than standard due to leverage."),
            colored_ratio_row("Return on Equity (ROE)",          "Өмчийн өгөөж",                s.company_fin_roe,                       "%", "fin_roe",        "ROE for finance/NBFI. Good: >10%."),
            colored_ratio_row("Net Profit Margin",               "Цэвэр ашгийн маржин",        s.company_fin_net_margin,                "%", "fin_net_margin", "Net Margin. Good: >10% for finance firms."),
        ),
        ratio_category_card(
            "Efficiency",
            "How much does it cost to generate each unit of income?",
            colored_ratio_row("Cost-to-Income Ratio",            "Зардал/Орлого",               s.company_fin_cost_to_income,            "%", "fin_cost_to_income", "Good: <50%. Operating expenses vs total income. Lower = more efficient."),
            ratio_row("Operating Expense Ratio",                 s.company_fin_operating_expense_ratio,   "%", "Operating expenses as % of total assets."),
            ratio_row("Non-Interest Income Ratio",               s.company_fin_non_interest_income_ratio, "%", "Fee/commission income as share of total. Revenue diversification."),
            ratio_row("Asset Utilisation",                       s.company_fin_asset_utilisation,         "%", "Total Income / Total Assets. Higher = more productive asset base."),
        ),
        ratio_category_card(
            "Leverage",
            "How much debt does the NBFI carry relative to its equity and assets?",
            colored_ratio_row("Debt-to-Equity (Borrowings)",     "Зээл/Өмч харьцаа",            s.company_fin_debt_to_equity,            "x", "fin_debt_to_equity", "D/E = Total Borrowings / Equity. Good: <3x for NBFIs (higher tolerance than standard)."),
            ratio_row("Debt-to-Assets",                          s.company_fin_debt_to_assets,            "%", "Borrowings / Total Assets. Measures leverage concentration."),
            colored_ratio_row("Equity Ratio",                    "Өмчийн харьцаа",              s.company_fin_equity_ratio,              "%", "fin_equity_ratio",   "Equity / Total Assets. Good: >15% for NBFIs. Capital buffer."),
            ratio_row("Equity Multiplier",                       s.company_fin_equity_multiplier,         "x", "Assets / Equity. Financial leverage multiplier."),
        ),
        ratio_category_card(
            "Liquidity",
            "Can the NBFI meet its funding obligations on short notice?",
            ratio_row("Cash Ratio",                              s.company_fin_cash_ratio,                "%", "Cash and equivalents as % of assets."),
            colored_ratio_row("Operating Cash Flow Ratio",       "Үйл ажиллагааны мөнгөн урсгал", s.company_fin_ocf_ratio,               "x", "fin_ocf_ratio",  "OCF / Current Liabilities. Good: >0.1. Operational cash generation quality."),
            ratio_row("Loan-to-Assets",                          s.company_fin_loan_to_assets,            "%", "Loan portfolio as share of total assets. High = concentrated credit exposure."),
        ),
        ratio_category_card(
            "Asset Quality",
            "Quality of the loan or receivables portfolio. Lower NPA and higher provision coverage = safer.",
            colored_ratio_row("NPA Ratio",                       "Хэвийн бус актив",            s.company_fin_npa_ratio,                 "%", "fin_npa_ratio",          "Non-Performing Assets / Total Assets. Good: <3%. High NPA signals deteriorating portfolio."),
            ratio_row("Receivables-to-Assets",                   s.company_fin_receivables_to_assets,     "%", "Receivables concentration in asset base."),
            colored_ratio_row("Provision Coverage",              "Нөөцийн бүрхэц",              s.company_fin_provision_coverage,        "x", "fin_provision_coverage", "Provisions / NPAs. Good: >1.0x. Shows how well NPAs are provisioned for."),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def ratios_tab_content() -> rx.Component:
    s = AnalysisState
    toggle_btn = rx.hstack(
        rx.button(
            rx.icon("palette", size=13),
            rx.text(rx.cond(s.show_ratio_colors, "Colors ON", "Colors OFF"), size="1"),
            on_click=s.toggle_ratio_colors,
            class_name="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer",
            style=rx.cond(
                s.show_ratio_colors,
                {"backgroundColor": _NAVY + "25", "color": _BLUE, "borderColor": _NAVY + "50"},
                {"backgroundColor": _CARD, "color": _FAINT, "borderColor": _BORDER},
            ),
        ),
        rx.text("Row colors relative to standard benchmarks", class_name="text-xs", style={"color": _FAINT}),
        spacing="2",
        align="center",
        class_name="mb-4",
    )
    return rx.vstack(
        toggle_btn,
        rx.cond(
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
        ),
        spacing="0",
        width="100%",
    )


# ── Forensic tab ──────────────────────────────────────────────────────────────

def _sector_criterion_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.cond(
            item["pass"] == 1,
            rx.icon("circle-check", size=16, class_name="text-green-400"),
            rx.cond(
                item["pass"] == 0,
                rx.icon("circle-x", size=16, class_name="text-red-400"),
                rx.icon("circle-help", size=16, style={"color": _POWDER + "60"}),
            ),
        ),
        rx.vstack(
            rx.text(item["label"], class_name="text-sm", style={"color": _TEXT}),
            rx.text(item["explanation"], class_name="text-xs", style={"color": _MUTED}),
            spacing="0",
            align="start",
        ),
        spacing="2",
        align="center",
        class_name="py-1.5 border-b",
        style={"borderColor": _BORDER},
    )


def _sector_forensic_panel() -> rx.Component:
    s = AnalysisState
    return rx.grid(
        rx.box(
            rx.hstack(
                rx.text("Sector Forensic Score", class_name="font-semibold text-sm", style={"color": _TEXT}),
                rx.spacer(),
                rx.text(s.company_sector_forensic_score_display, class_name="font-mono font-bold text-sm", style={"color": _NAVY}),
                width="100%",
                align="center",
                class_name="mb-4",
            ),
            rx.foreach(s.company_sector_forensic_criteria, _sector_criterion_row),
            class_name="rounded-2xl p-5",
            style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
        ),
        rx.box(
            rx.text("Year-on-Year Key Ratio Changes (%)", class_name="font-semibold text-sm mb-3", style={"color": _TEXT}),
            rx.cond(
                s.company_sector_forensic_chart_data.length() == 0,
                rx.text("No prior-year data available.", class_name="text-sm", style={"color": _MUTED}),
                rx.recharts.bar_chart(
                    rx.recharts.x_axis(type_="number", unit="%", tick={"fill": _FAINT, "fontSize": 11}),
                    rx.recharts.y_axis(data_key="metric", type_="category", width=130, tick={"fill": _MUTED, "fontSize": 10}),
                    rx.recharts.bar(data_key="change", fill=_BLUE),
                    rx.recharts.reference_line(x=0, stroke=_POWDER + "60", stroke_dasharray="4 4"),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke=_BORDER),
                    rx.recharts.tooltip(),
                    data=s.company_sector_forensic_chart_data,
                    layout="vertical",
                    width="100%",
                    height=240,
                ),
            ),
            rx.text(
                "Green = improvement vs prior year. For ratios where lower is better (NPL, Cost-to-Income), a negative change is shown as green.",
                class_name="text-xs mt-3",
                style={"color": _FAINT},
            ),
            class_name="rounded-2xl p-5",
            style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def forensic_tab_content() -> rx.Component:
    s = AnalysisState
    return rx.cond(
        s.company_is_bank | s.company_is_insurance | s.company_is_finance,
        _sector_forensic_panel(),
        rx.grid(
            rx.box(
                rx.hstack(
                    rx.text("Piotroski F-Score Criteria", class_name="font-semibold text-sm", style={"color": _TEXT}),
                    info_icon("9-point scoring system. Each criterion scores 1 (pass) or 0 (fail). Total 7-9 = strong, 4-6 = moderate, 0-3 = weak fundamentals."),
                    spacing="1",
                    align="center",
                    class_name="mb-4",
                ),
                rx.vstack(
                    piotroski_criterion("ROA Positive",                              s.company_f1, "F1: ROA > 0 means the company earned a profit on its assets."),
                    piotroski_criterion("Operating Cash Flow Positive",              s.company_f2, "F2: Operating CF > 0 means real cash earnings, not just accounting profit."),
                    piotroski_criterion("ROA Improving YoY",                         s.company_f3, "F3: Rising ROA signals improving profitability trend."),
                    piotroski_criterion("Cash Earnings Quality (OCF/Assets > ROA)",  s.company_f4, "F4: Cash earnings > accrual earnings. Lower accruals = higher earnings quality."),
                    piotroski_criterion("Leverage Decreased",                        s.company_f5, "F5: Less long-term debt relative to assets = improving financial health."),
                    piotroski_criterion("Current Ratio Improved",                    s.company_f6, "F6: Higher current ratio than prior year = better short-term liquidity."),
                    piotroski_criterion("Gross Margin Improving",                    s.company_f8, "F8: Rising gross margin = pricing power or cost control improvement."),
                    piotroski_criterion("Asset Turnover Improving",                  s.company_f9, "F9: Higher asset turnover = assets being used more efficiently."),
                    spacing="0",
                    align="start",
                ),
                class_name="rounded-2xl p-5",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            rx.box(
                rx.hstack(
                    rx.text("Beneish M-Score Indices", class_name="font-semibold text-sm", style={"color": _TEXT}),
                    info_icon("Fraud detection model. M-Score < −1.78 = likely no manipulation. M-Score > −1.78 = possible earnings manipulation. The red dashed line at x=1 marks the manipulation zone."),
                    spacing="1",
                    align="center",
                    class_name="mb-3",
                ),
                rx.recharts.bar_chart(
                    rx.recharts.x_axis(type_="number", tick={"fill": _FAINT, "fontSize": 11}),
                    rx.recharts.y_axis(data_key="index", type_="category", tick={"fill": _MUTED, "fontSize": 10}),
                    rx.recharts.bar(data_key="value", fill=_BLUE),
                    rx.recharts.reference_line(x=1, stroke="#F87171", stroke_dasharray="4 4"),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke=_BORDER),
                    data=s.company_beneish_chart_data,
                    layout="vertical",
                    width="100%",
                    height=240,
                ),
                rx.separator(class_name="my-3", style={"borderColor": _BORDER}),
                rx.table.root(
                    rx.table.body(
                        ratio_row("DSRI — Receivables Index", s.company_dsri, "", "DSRI > 1 means receivables grew faster than sales. May signal revenue inflation."),
                        ratio_row("GMI — Gross Margin Index", s.company_gmi,  "", "GMI > 1 means gross margin deteriorated. Can signal competitive pressure."),
                        ratio_row("AQI — Asset Quality Index",s.company_aqi,  "", "AQI > 1 means more non-current assets vs last year. May signal off-balance-sheet risk."),
                        ratio_row("SGI — Sales Growth Index", s.company_sgi,  "", "SGI > 1 means sales grew. High growth alone isn't a flag, but combined with others it is."),
                        ratio_row("SGAI — SG&A Index",        s.company_sgai, "", "SGAI > 1 means selling & admin expenses grew faster than sales. Efficiency deterioration."),
                        ratio_row("LVGI — Leverage Index",    s.company_lvgi, "", "LVGI > 1 means leverage increased. Higher debt burden may create income manipulation incentives."),
                        ratio_row("TATA — Total Accruals",    s.company_tata, "", "High accruals (TATA > 0) relative to assets mean income is accrual-based, not cash-based. Red flag."),
                    ),
                    variant="ghost",
                    class_name="w-full",
                ),
                class_name="rounded-2xl p-5",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
    )


# ── Valuation tab ─────────────────────────────────────────────────────────────

def valuation_card(title: str, value: rx.Var, unit: str, has_shares: rx.Var, tooltip: str = "") -> rx.Component:
    return rx.cond(
        has_shares,
        rx.box(
            rx.hstack(
                rx.text(title, class_name="text-xs font-semibold uppercase tracking-wider", style={"color": _MUTED}),
                info_icon(tooltip) if tooltip else rx.fragment(),
                spacing="1",
                align="center",
                class_name="mb-1",
            ),
            rx.hstack(
                rx.text(value, class_name="text-2xl font-bold font-mono", style={"color": _BLUE}),
                rx.text(unit, class_name="text-sm self-end mb-0.5", style={"color": _FAINT}),
                spacing="1",
                align="end",
            ),
            class_name="rounded-2xl p-5",
            style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
        ),
        rx.box(
            rx.text(title, class_name="text-xs font-semibold uppercase tracking-wider mb-1", style={"color": _MUTED}),
            rx.hstack(
                rx.text("N/A", class_name="text-2xl font-bold font-mono", style={"color": _FAINT}),
                rx.box(
                    rx.icon("pencil", size=14, class_name="cursor-pointer", style={"color": _BLUE}),
                    on_click=AnalysisState.toggle_shares_input,
                ),
                spacing="2",
                align="center",
            ),
            rx.text("Enter shares outstanding to compute", class_name="text-xs mt-1", style={"color": _FAINT}),
            class_name="rounded-2xl p-5",
            style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
        ),
    )


def shares_input_card() -> rx.Component:
    return rx.box(
        rx.text("Shares Outstanding", class_name="text-xs font-semibold uppercase tracking-wider mb-1", style={"color": _MUTED}),
        rx.input(
            placeholder="e.g. 45,000,000",
            value=AnalysisState.company_shares_input_value,
            on_change=AnalysisState.set_shares_input_value,
            class_name="text-sm rounded-lg px-3 py-2 w-full mb-2 border",
            style={"borderColor": _NAVY + "60", "color": _TEXT, "backgroundColor": _CARD},
        ),
        rx.hstack(
            rx.text(
                "Save",
                on_click=AnalysisState.save_shares_outstanding(AnalysisState.company_shares_input_value),
                class_name="text-xs font-semibold cursor-pointer",
                style={"color": _NAVY},
            ),
            rx.text(
                "Cancel",
                on_click=AnalysisState.toggle_shares_input,
                class_name="text-xs cursor-pointer ml-2",
                style={"color": _FAINT},
            ),
            spacing="2",
        ),
        class_name="rounded-2xl p-5",
        style={"backgroundColor": _CARD, "border": f"1px solid {_NAVY}40"},
    )


def range_toggle() -> rx.Component:
    s = AnalysisState
    ranges = ["1M", "6M", "1Y", "All"]
    return rx.hstack(
        *[
            rx.button(
                r,
                on_click=s.set_valuation_range(r),
                class_name="px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer",
                style=rx.cond(
                    s.valuation_range == r,
                    {"backgroundColor": _NAVY, "color": "white", "borderColor": _NAVY},
                    {"backgroundColor": _CARD, "color": _MUTED, "borderColor": _BORDER},
                ),
            )
            for r in ranges
        ],
        spacing="1",
    )


def price_chart_section() -> rx.Component:
    s = AnalysisState
    return rx.box(
        rx.hstack(
            rx.text("Price History", class_name="font-bold text-sm", style={"color": _TEXT}),
            rx.spacer(),
            range_toggle(),
            align="center",
            width="100%",
            class_name="mb-3",
        ),
        rx.text("Close Price (MNT)", class_name="text-xs mb-2", style={"color": _FAINT}),
        rx.recharts.line_chart(
            rx.recharts.line(data_key="close", stroke=_BLUE, dot=False, stroke_width=2),
            rx.recharts.x_axis(data_key="date", tick={"fontSize": 11, "fill": _FAINT}),
            rx.recharts.y_axis(tick={"fontSize": 11, "fill": _FAINT}, width=60),
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke=_BORDER),
            rx.recharts.tooltip(),
            data=s.company_price_chart_data,
            width="100%",
            height=240,
        ),
        rx.text("Volume", class_name="text-xs mt-2 mb-1", style={"color": _FAINT}),
        rx.recharts.bar_chart(
            rx.recharts.bar(data_key="volume", fill=_BLUE, opacity=0.5),
            rx.recharts.x_axis(data_key="date", tick=False),
            rx.recharts.y_axis(tick={"fontSize": 10, "fill": _FAINT}, width=60),
            data=s.company_volume_chart_data,
            width="100%",
            height=80,
        ),
        class_name="rounded-2xl p-5 w-full",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
    )


def valuation_tab_content() -> rx.Component:
    s = AnalysisState
    has_shares = s.company_shares_outstanding != ""

    standard_cards = rx.grid(
        valuation_card("EV / EBIT",  s.company_ev_ebitda, "x", has_shares, "EV / EBIT approximation. Lower = cheaper relative to operating earnings."),
        valuation_card("FCF Yield",  s.company_fcf_yield, "%", has_shares, "Free Cash Flow / Market Cap. Higher = more cash generated per dollar of market value."),
        valuation_card("Free Cash Flow", s.company_fcf,   "M₮", has_shares, "Operating Cash Flow minus Capex (investing cash flow). Positive = cash generated after sustaining operations."),
        valuation_card("P / E",      s.company_pe,        "x", has_shares, "Price-to-Earnings. Market price relative to net profit. Lower = cheaper."),
        valuation_card("P / BV",     s.company_pbv,       "x", has_shares, "Price-to-Book Value. Market price relative to net assets. < 1 may indicate undervaluation."),
        columns="5", spacing="4", width="100%",
    )
    bank_cards = rx.grid(
        valuation_card("P / E",    s.company_pe,      "x",  has_shares, "Price-to-Earnings."),
        valuation_card("P / BV",   s.company_pbv,     "x",  has_shares, "Price-to-Book Value."),
        valuation_card("P / TBV",  s.company_ptbv,    "x",  has_shares, "Price-to-Tangible Book Value. Excludes intangibles. Key bank valuation metric."),
        valuation_card("P / PPOP", s.company_p_ppop,  "x",  has_shares, "Price-to-Pre-Provision Operating Profit. Shows core earnings power ex-credit cost."),
        valuation_card("P / NII",  s.company_p_nii,   "x",  has_shares, "Price-to-Net Interest Income. Core banking revenue multiple."),
        valuation_card("Op. Cash Flow", s.company_ocf, "M₮", has_shares, "Operating Cash Flow. Cash generated from core banking operations before investing and financing activities."),
        columns="6", spacing="4", width="100%",
    )
    nbfi_cards = rx.grid(
        valuation_card("P / E",    s.company_pe,     "x",  has_shares),
        valuation_card("P / BV",   s.company_pbv,    "x",  has_shares),
        valuation_card("P / PPOP", s.company_p_ppop, "x",  has_shares, "Price-to-Pre-Provision Operating Profit."),
        valuation_card("P / NII",  s.company_p_nii,  "x",  has_shares, "Price-to-Net Interest Income."),
        valuation_card("Op. Cash Flow", s.company_ocf, "M₮", has_shares, "Operating Cash Flow. Cash generated from core lending and financing operations."),
        columns="5", spacing="4", width="100%",
    )
    holding_cards = rx.grid(
        valuation_card("P / E",       s.company_pe,        "x",  has_shares),
        valuation_card("P / NAV",     s.company_pbv,       "x",  has_shares, "Price-to-Net Asset Value. Key metric for holding/investment companies."),
        valuation_card("P / Inv Sec", s.company_p_inv_sec, "x",  has_shares, "Price-to-Investment Securities. Compares market cap to investment portfolio."),
        valuation_card("Op. Cash Flow", s.company_ocf,     "M₮", has_shares, "Operating Cash Flow. Cash generated from portfolio and management operations."),
        columns="4", spacing="4", width="100%",
    )
    securities_cards = rx.grid(
        valuation_card("P / E",       s.company_pe,        "x",  has_shares),
        valuation_card("P / BV",      s.company_pbv,       "x",  has_shares),
        valuation_card("P / Revenue", s.company_p_revenue, "x",  has_shares, "Price-to-Revenue. Used for securities firms without stable earnings."),
        valuation_card("Op. Cash Flow", s.company_ocf,     "M₮", has_shares, "Operating Cash Flow. Cash generated from brokerage and advisory operations."),
        columns="4", spacing="4", width="100%",
    )
    insurance_cards = rx.grid(
        valuation_card("P / E",   s.company_pe,    "x",  has_shares),
        valuation_card("P / BV",  s.company_pbv,   "x",  has_shares),
        valuation_card("P / NPE", s.company_p_npe, "x",  has_shares, "Price-to-Net Premiums Earned. Core insurance revenue multiple."),
        valuation_card("P / UWP", s.company_p_uwp, "x",  has_shares, "Price-to-Underwriting Profit. Measures market value relative to core insurance profit."),
        valuation_card("Op. Cash Flow", s.company_ocf, "M₮", has_shares, "Operating Cash Flow. Cash from underwriting and claims operations before investing activities."),
        columns="5", spacing="4", width="100%",
    )

    cards_row = rx.cond(
        s.company_valuation_sector == "commercial_bank",
        bank_cards,
        rx.cond(s.company_valuation_sector == "nbfi",       nbfi_cards,
        rx.cond(s.company_valuation_sector == "holding",    holding_cards,
        rx.cond(s.company_valuation_sector == "securities", securities_cards,
        rx.cond(s.company_valuation_sector == "insurance",  insurance_cards,
        standard_cards)))),
    )

    return rx.vstack(
        rx.cond(s.company_shares_input_open, shares_input_card(), cards_row),
        price_chart_section(),
        spacing="6",
        width="100%",
    )


# ── DuPont tab ────────────────────────────────────────────────────────────────

def dupont_tab_content() -> rx.Component:
    s = AnalysisState

    def dupont_row(year_label, factor1, factor2, eq_multiplier, roe) -> rx.Component:
        return rx.hstack(
            rx.box(rx.text(year_label, class_name="text-xs font-semibold uppercase tracking-wider", style={"color": _MUTED}), class_name="w-28 shrink-0"),
            rx.box(
                rx.text(s.company_dupont_factor1_label, class_name="text-xs mb-1", style={"color": _MUTED}),
                rx.text(factor1, class_name="text-lg font-mono font-bold", style={"color": _BLUE}),
                rx.text(s.company_dupont_factor1_unit, class_name="text-xs", style={"color": _FAINT}),
                class_name="flex flex-col items-center flex-1",
            ),
            rx.text("×", class_name="text-xl font-bold px-1", style={"color": _FAINT}),
            rx.cond(
                s.company_dupont_show_factor2,
                rx.hstack(
                    rx.box(
                        rx.text(s.company_dupont_factor2_label, class_name="text-xs mb-1", style={"color": _MUTED}),
                        rx.text(factor2, class_name="text-lg font-mono font-bold", style={"color": _BLUE}),
                        rx.text(s.company_dupont_factor2_unit, class_name="text-xs", style={"color": _FAINT}),
                        class_name="flex flex-col items-center flex-1",
                    ),
                    rx.text("×", class_name="text-xl font-bold px-1", style={"color": _FAINT}),
                    spacing="2",
                    align="center",
                ),
                rx.box(),
            ),
            rx.box(
                rx.text("Equity Multiplier", class_name="text-xs mb-1", style={"color": _MUTED}),
                rx.text(eq_multiplier, class_name="text-lg font-mono font-bold", style={"color": _BLUE}),
                rx.text("x", class_name="text-xs", style={"color": _FAINT}),
                class_name="flex flex-col items-center flex-1",
            ),
            rx.text("=", class_name="text-xl font-bold px-1", style={"color": _NAVY}),
            rx.box(
                rx.text("ROE", class_name="text-xs mb-1", style={"color": _MUTED}),
                rx.text(roe, class_name="text-lg font-mono font-bold", style={"color": _NAVY}),
                rx.text("%", class_name="text-xs", style={"color": _FAINT}),
                class_name="flex flex-col items-center flex-1",
            ),
            spacing="2",
            align="center",
            width="100%",
            class_name="rounded-xl p-4",
            style={"backgroundColor": _POWDER + "08", "border": f"1px solid {_BORDER}"},
        )

    return rx.box(
        rx.hstack(
            rx.text("DuPont Decomposition", class_name="font-semibold text-sm", style={"color": _TEXT}),
            info_icon("DuPont breaks ROE into component drivers. A high ROE driven by high margin and turnover is healthier than one driven purely by leverage (equity multiplier)."),
            spacing="1",
            align="center",
            class_name="mb-2",
        ),
        rx.text(s.company_dupont_formula_text, class_name="text-sm mb-4 font-mono", style={"color": _MUTED}),
        rx.vstack(
            dupont_row("Current Year", s.company_net_margin_dupont,  s.company_asset_turnover_dupont, s.company_equity_multiplier_curr, s.company_roe_dupont),
            dupont_row("Prior Year",   s.company_net_margin_prev,    s.company_asset_turnover_prev,   s.company_equity_multiplier_prev,  s.company_roe_prev),
            spacing="3",
            width="100%",
        ),
        class_name="rounded-2xl p-5 w-full",
        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
    )


# ── Red Flags tab ─────────────────────────────────────────────────────────────

def red_flag_item(flag: dict) -> rx.Component:
    is_clear  = flag["flag"] == "No Major Red Flags"
    is_high   = flag["severity"] == "high"
    is_medium = flag["severity"] == "medium"

    icon_el = rx.cond(
        is_clear,
        rx.icon("circle-check", size=20, class_name="text-green-400 shrink-0"),
        rx.cond(is_high,
            rx.icon("octagon-alert", size=20, class_name="text-red-400 shrink-0"),
            rx.cond(is_medium,
                rx.icon("triangle-alert", size=20, class_name="text-amber-400 shrink-0"),
                rx.icon("info", size=20, class_name="text-blue-400 shrink-0"),
            ),
        ),
    )
    title_color = rx.cond(is_clear, "#4ADE80", rx.cond(is_high, "#F87171", rx.cond(is_medium, "#FCD34D", "#60A5FA")))
    border_color = rx.cond(is_clear, "#166534", rx.cond(is_high, "#991B1B", rx.cond(is_medium, "#92400E", "#1E40AF")))
    badge = rx.cond(
        is_clear,   rx.badge("CLEAR",  color_scheme="green",  size="1"),
        rx.cond(is_high,   rx.badge("HIGH",   color_scheme="red",    size="1"),
        rx.cond(is_medium, rx.badge("MEDIUM", color_scheme="yellow", size="1"),
                           rx.badge("LOW",    color_scheme="blue",   size="1"))),
    )

    return rx.box(
        rx.hstack(
            icon_el,
            rx.vstack(
                rx.hstack(
                    rx.text(flag["flag"], class_name="text-sm font-semibold", style={"color": title_color}),
                    badge,
                    spacing="2",
                    align="center",
                ),
                rx.text(flag["explanation"], class_name="text-sm", style={"color": _MUTED}),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="start",
        ),
        class_name="rounded-2xl p-4",
        style={"backgroundColor": _CARD, "border": "1px solid", "borderColor": border_color},
    )


def red_flags_tab_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AnalysisState.company_red_flags_loading,
            rx.vstack(
                rx.hstack(
                    rx.spinner(size="3", style={"color": _NAVY}),
                    rx.text("AI is analysing financial data...", class_name="text-sm", style={"color": _MUTED}),
                    spacing="3",
                    align="center",
                ),
                rx.text(
                    "Groq AI is cross-referencing ratios, forensic scores, DuPont decomposition, valuation multiples, and price context.",
                    class_name="text-xs text-center",
                    style={"color": _FAINT},
                ),
                align="center",
                spacing="2",
                width="100%",
                class_name="py-8",
            ),
            rx.foreach(AnalysisState.company_red_flags, red_flag_item),
        ),
        rx.cond(
            ~AnalysisState.company_red_flags_loading,
            rx.hstack(
                rx.icon("sparkles", size=12, style={"color": _BLUE}),
                rx.text("Powered by Groq AI — llama-3.3-70b-versatile", class_name="text-xs", style={"color": _FAINT}),
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
    s = AnalysisState

    def tab_trigger(label: str, value: str) -> rx.Component:
        return rx.tabs.trigger(
            label,
            value=value,
            class_name="px-4 py-2.5 text-sm font-medium transition-colors",
            style={"color": _MUTED},
        )

    return page_layout(
        rx.cond(
            s.selected_company_name == "",
            rx.box(
                rx.vstack(
                    rx.icon("bar-chart-2", size=40, style={"color": _POWDER + "50"}),
                    rx.text("No company selected.", class_name="font-semibold", style={"color": _TEXT}),
                    rx.link("← Back to Screener", href="/screener", class_name="text-sm", style={"color": _BLUE}),
                    spacing="2",
                    align="center",
                ),
                class_name="rounded-2xl p-16 w-full flex items-center justify-center",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
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
                    class_name="text-sm flex items-center gap-1 mb-2",
                    style={"color": _MUTED},
                ),
                # Company header
                rx.hstack(
                    rx.heading(s.selected_company_name, size="8", class_name="font-bold", style={"color": _TEXT}),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=14),
                        rx.text("Add to Portfolio"),
                        on_click=PortfolioState.add_to_portfolio(s.selected_company_name),
                        class_name="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white transition-colors cursor-pointer",
                        style={"backgroundColor": _NAVY},
                    ),
                    width="100%",
                    align="center",
                ),
                # Hero score cards
                rx.grid(
                    score_card("Health Score", s.company_score.to_string(), "/100"),
                    score_card(
                        rx.cond(s.company_is_bank | s.company_is_insurance | s.company_is_finance, "Sector Forensic Score", "Piotroski F-Score"),
                        rx.cond(s.company_is_bank | s.company_is_insurance | s.company_is_finance, s.company_sector_forensic_score_display, s.company_f_score_display),
                        "",
                    ),
                    score_card("M-Score",       s.company_m_score_display, ""),
                    score_card("M-Score Result", s.company_m_interp,       ""),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                # 6-tab panel
                rx.tabs.root(
                    rx.tabs.list(
                        tab_trigger("Overview",  "overview"),
                        tab_trigger("Ratios",    "ratios"),
                        tab_trigger("Forensic",  "forensic"),
                        tab_trigger("Valuation", "valuation"),
                        tab_trigger("DuPont",    "dupont"),
                        tab_trigger("Red Flags", "redflags"),
                        class_name="border-b",
                        style={"borderColor": _BORDER},
                    ),
                    rx.tabs.content(overview_tab_content(),    value="overview",   class_name="pt-5"),
                    rx.tabs.content(ratios_tab_content(),      value="ratios",     class_name="pt-5"),
                    rx.tabs.content(forensic_tab_content(),    value="forensic",   class_name="pt-5"),
                    rx.tabs.content(valuation_tab_content(),   value="valuation",  class_name="pt-5"),
                    rx.tabs.content(dupont_tab_content(),      value="dupont",     class_name="pt-5"),
                    rx.tabs.content(red_flags_tab_content(),   value="redflags",   class_name="pt-5"),
                    default_value="overview",
                    width="100%",
                    class_name="rounded-2xl px-5 pb-5",
                    style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                ),
                spacing="5",
                width="100%",
                align="start",
            ),
        ),
    )
