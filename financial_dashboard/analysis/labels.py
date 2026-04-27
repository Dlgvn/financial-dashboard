"""Display metadata for all financial ratio engines.

Centralises three types of display data so UI components and the EDA
notebook can import from a single place instead of reaching into each
ratio module:

  RATIO_LABELS            — standard company ratios  (ratios.py)
  BANK_RATIO_LABELS       — bank-specific ratios      (bank_ratios.py)
  BANK_BENCHMARKS         — bank industry thresholds
  INSURANCE_RATIO_LABELS  — insurance-specific ratios (insurance_ratios.py)
  INSURANCE_BENCHMARKS    — insurance industry thresholds

Label format:  { key: (human_readable_name, unit_string) }
Benchmark format: { key: (threshold, direction, note) }
  direction "above" → good if value >= threshold
  direction "below" → good if value <= threshold
"""

# ── Standard company ratios (ratios.py) ──────────────────────────────────────

RATIO_LABELS: dict[str, tuple[str, str]] = {
    # Activity
    "total_asset_turnover":   ("Total Asset Turnover",        "times"),
    "fixed_asset_turnover":   ("Fixed Asset Turnover",        "times"),
    "inventory_turnover":     ("Inventory Turnover",          "times"),
    "days_inventory":         ("Days Inventory Outstanding",  "days"),
    "receivables_turnover":   ("Receivables Turnover",        "times"),
    "days_sales_outstanding": ("Days Sales Outstanding",      "days"),
    "payables_turnover":      ("Payables Turnover",           "times"),
    "days_payable_outstanding": ("Days Payable Outstanding",  "days"),
    "cash_conversion_cycle":  ("Cash Conversion Cycle",       "days"),
    # Liquidity
    "current_ratio":          ("Current Ratio",               "x"),
    "quick_ratio":            ("Quick Ratio",                 "x"),
    "cash_ratio":             ("Cash Ratio",                  "x"),
    "working_capital":        ("Working Capital",             "₮ thousands"),
    # Solvency
    "debt_to_equity":         ("Debt-to-Equity",              "x"),
    "debt_to_assets":         ("Debt-to-Assets",              "ratio"),
    "equity_ratio":           ("Equity Ratio",                "ratio"),
    "interest_coverage":      ("Interest Coverage",           "x"),
    # Profitability
    "gross_margin":           ("Gross Profit Margin",         "%"),
    "operating_margin":       ("Operating Margin",            "%"),
    "net_margin":             ("Net Profit Margin",           "%"),
    "roa":                    ("Return on Assets (ROA)",      "%"),
    "roe":                    ("Return on Equity (ROE)",      "%"),
    "ebit_margin":            ("EBIT Margin",                 "%"),
    # Performance
    "ocf_ratio":              ("Operating CF Ratio",          "x"),
    "cf_to_debt":             ("Cash Flow to Debt",           "x"),
    "reinvestment_ratio":     ("Reinvestment Ratio",          "x"),
    # Altman Z-Score components
    "x1_wc_ta":               ("X1: Working Capital / Total Assets",      "ratio"),
    "x2_re_ta":               ("X2: Retained Earnings / Total Assets",    "ratio"),
    "x3_ebit_ta":             ("X3: EBIT / Total Assets",                 "ratio"),
    "x4_eq_tl":               ("X4: Equity / Total Liabilities",          "ratio"),
    "x5_rev_ta":              ("X5: Revenue / Total Assets",              "ratio"),
    "z_score":                ("Altman Z-Score",                          "score"),
}

# ── Bank ratios (bank_ratios.py) ─────────────────────────────────────────────

BANK_RATIO_LABELS: dict[str, tuple[str, str]] = {
    # Profitability
    "nim":                     ("Net Interest Margin (NIM)",   "%"),
    "roa":                     ("Return on Assets (ROA)",      "%"),
    "roe":                     ("Return on Equity (ROE)",      "%"),
    "net_margin":              ("Net Profit Margin",           "%"),
    "interest_income_ratio":   ("Interest Income Ratio",       "%"),
    # Capital Adequacy
    "equity_multiplier":       ("Equity Multiplier",           "x"),
    "equity_to_assets":        ("Equity to Assets",            "ratio"),
    # Asset Quality
    "npl_ratio":               ("NPL Ratio",                   "%"),
    "coverage_ratio":          ("Coverage Ratio",              "x"),
    "loan_loss_reserve_ratio": ("Loan Loss Reserve Ratio",     "%"),
    "provision_to_loans":      ("Provision to Loans",          "%"),
    # Liquidity
    "ldr":                     ("Loan-to-Deposit Ratio (LDR)", "%"),
    "cash_to_deposits":        ("Cash to Deposits",            "%"),
    "loans_to_assets":         ("Loans to Total Assets",       "%"),
    "securities_to_assets":    ("Securities to Total Assets",  "%"),
    # Efficiency
    "cost_to_income":          ("Cost-to-Income Ratio",        "%"),
    "fee_income_ratio":        ("Non-Interest Income Ratio",   "%"),
}

BANK_BENCHMARKS: dict[str, tuple[float, str, str]] = {
    "nim":            (0.03, "above", "Target: >3%"),
    "roa":            (0.01, "above", "Target: >1%"),
    "roe":            (0.10, "above", "Target: >10%"),
    "npl_ratio":      (0.03, "below", "Target: <3%"),
    "coverage_ratio": (1.00, "above", "Target: >100%"),
    "ldr":            (0.90, "below", "Target: <90%"),
    "cost_to_income": (0.55, "below", "Target: <55%"),
}

# ── Insurance ratios (insurance_ratios.py) ────────────────────────────────────

INSURANCE_RATIO_LABELS: dict[str, tuple[str, str]] = {
    # Underwriting
    "loss_ratio":              ("Loss Ratio",                  "%"),
    "expense_ratio":           ("Expense Ratio",               "%"),
    "combined_ratio":          ("Combined Ratio",              "%"),
    # Profitability
    "roa":                     ("Return on Assets (ROA)",      "%"),
    "roe":                     ("Return on Equity (ROE)",      "%"),
    "net_margin":              ("Net Profit Margin",           "%"),
    "investment_income_ratio": ("Investment Income Ratio",     "%"),
    "underwriting_margin":     ("Underwriting Profit Margin",  "%"),
    # Solvency
    "solvency_ratio":          ("Solvency Ratio",              "%"),
    "leverage_ratio":          ("Leverage Ratio",              "x"),
    "equity_to_liabilities":   ("Equity to Liabilities",       "ratio"),
    "reserve_coverage":        ("Reserve Coverage Ratio",      "x"),
    # Liquidity
    "ocf_ratio":               ("Operating Cash Flow Ratio",   "x"),
    "investment_ratio":        ("Investment Ratio",            "%"),
    "cash_to_liabilities":     ("Cash to Liabilities",         "%"),
    "unearned_premium_ratio":  ("Unearned Premium Ratio",      "%"),
    # Growth
    "premium_growth":          ("Premium Growth (YoY)",        "%"),
    "revenue_growth":          ("Revenue Growth (YoY)",        "%"),
}

INSURANCE_BENCHMARKS: dict[str, tuple[float, str, str]] = {
    "loss_ratio":       (0.70, "below", "Target: <70%. >85% signals underwriting problems"),
    "expense_ratio":    (0.30, "below", "Target: <30%"),
    "combined_ratio":   (1.00, "below", "Target: <100%. >100% = underwriting loss"),
    "roa":              (0.03, "above", "Target: >3% for insurance"),
    "roe":              (0.12, "above", "Target: >12%"),
    "solvency_ratio":   (0.20, "above", "Mongolia FRC minimum: ~20%"),
    "leverage_ratio":   (4.00, "below", "Target: <4x for non-life insurers"),
    "reserve_coverage": (1.00, "above", "Target: >1x (reserves cover one year of premiums)"),
    "investment_ratio": (0.40, "above", "Target: >40% of assets productively invested"),
}

# ── Finance / NBFI ratios (finance_ratios.py) ────────────────────────────────

FINANCE_RATIO_LABELS: dict[str, tuple[str, str]] = {
    # Profitability
    "nim":                        ("Net Interest Margin (NIM)",       "%"),
    "yield_on_earning_assets":    ("Yield on Earning Assets",         "%"),
    "cost_of_funds":              ("Cost of Funds",                   "%"),
    "interest_spread":            ("Interest Spread",                 "%"),
    "roa":                        ("Return on Assets (ROA)",          "%"),
    "roe":                        ("Return on Equity (ROE)",          "%"),
    "net_margin":                 ("Net Profit Margin",               "%"),
    # Efficiency
    "cost_to_income":             ("Cost-to-Income Ratio",            "%"),
    "operating_expense_ratio":    ("Operating Expense Ratio",         "%"),
    "non_interest_income_ratio":  ("Non-Interest Income Ratio",       "%"),
    "asset_utilisation":          ("Asset Utilisation",               "x"),
    # Leverage & Capital
    "debt_to_equity":             ("Debt-to-Equity (Borrowings)",     "x"),
    "debt_to_assets":             ("Debt-to-Assets (Borrowings)",     "ratio"),
    "equity_ratio":               ("Equity Ratio",                    "ratio"),
    "equity_multiplier":          ("Equity Multiplier",               "x"),
    # Liquidity
    "cash_ratio":                 ("Cash Ratio",                      "x"),
    "ocf_ratio":                  ("Operating CF Ratio",              "x"),
    "loan_to_assets":             ("Loan-to-Asset Ratio",             "ratio"),
    # Asset Quality
    "npa_ratio":                  ("NPA Ratio",                       "%"),
    "receivables_to_assets":      ("Receivables-to-Assets",           "ratio"),
    "provision_coverage":         ("Provision Coverage Ratio",        "x"),
}

FINANCE_BENCHMARKS: dict[str, tuple[float, str, str]] = {
    "nim":                     (0.04,  "above", "Target: >4%. Microfinance typically 6–15%"),
    "interest_spread":         (0.03,  "above", "Target: >3% positive spread"),
    "roa":                     (0.013, "above", "Target: >1.3% good; >1.6% excellent (CARE Ratings)"),
    "roe":                     (0.15,  "above", "Target: >15% good; >20% excellent"),
    "cost_to_income":          (0.50,  "below", "Target: <50% good; <40% excellent (CARE Ratings)"),
    "debt_to_equity":          (6.0,   "below", "Target: <6x for NBFIs (regulatory guidance)"),
    "equity_ratio":            (0.10,  "above", "Target: >10% equity buffer"),
    "npa_ratio":               (0.05,  "below", "Target: <2% excellent; <5% acceptable"),
    "provision_coverage":      (0.70,  "above", "Target: >70% (regulatory minimum in most markets)"),
    "loan_to_assets":          (0.60,  "above", "Target: >60% for mature lending NBFIs"),
}

# ── Piotroski F-Score labels ─────────────────────────────────────────────────

PIOTROSKI_LABELS: dict[str, str] = {
    "f1_roa_positive":      "ROA Positive",
    "f2_ocf_positive":      "Operating Cash Flow Positive",
    "f3_roa_improving":     "ROA Improving YoY",
    "f4_accruals":          "Cash Earnings Quality (OCF/Assets > ROA)",
    "f5_leverage_down":     "Leverage Decreased",
    "f6_liquidity_up":      "Current Ratio Improved",
    "f7_no_dilution":       "No Share Dilution",
    "f8_gross_margin_up":   "Gross Margin Improving",
    "f9_asset_turnover_up": "Asset Turnover Improving",
}
