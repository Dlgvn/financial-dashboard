"""Financial ratio computation engine.

Computes ~25 financial ratios organized into categories:
Activity (9), Liquidity (4), Solvency (4), Profitability (6),
Performance (3), and Altman Z-Score.
"""


def safe_div(a, b):
    """Safe division — returns None if b is 0 or either operand is None."""
    if a is None or b is None:
        return None
    try:
        if b == 0:
            return None
        return a / b
    except (TypeError, ZeroDivisionError):
        return None


def _get(data, section, key, suffix=""):
    """Safely get a value from nested parsed data."""
    sec = data.get(section, {})
    return sec.get(key + suffix)


def _avg(val_curr, val_prev):
    """Average of current and previous period values."""
    if val_curr is None or val_prev is None:
        return None
    return (val_curr + val_prev) / 2


def compute_ratios(parsed_data: dict) -> dict:
    """Compute financial ratios from one company's parsed JSON data.

    Args:
        parsed_data: Full parsed JSON dict with keys:
            metadata, balance_sheet, income_statement, cash_flow

    Returns:
        Dict with structure:
        {
            "company": str,
            "current": { category: { ratio_name: value, ... }, ... },
            "prev": { category: { ratio_name: value, ... }, ... },
        }
    """
    bs = parsed_data.get("balance_sheet", {})
    inc = parsed_data.get("income_statement", {})
    cf = parsed_data.get("cash_flow", {})
    company = parsed_data.get("metadata", {}).get("company", "Unknown")

    result = {
        "company": company,
        "current": {},
        "prev": {},
    }

    for period_suffix, period_key in [("", "current"), ("_prev", "prev")]:
        # --- Extract values for this period ---
        total_assets = bs.get(f"total_assets{period_suffix}")
        total_liabilities = bs.get(f"total_liabilities{period_suffix}")
        total_equity = bs.get(f"total_equity{period_suffix}")
        total_current_assets = bs.get(f"total_current_assets{period_suffix}")
        total_current_liabilities = bs.get(f"total_current_liabilities{period_suffix}")
        total_non_current_liabilities = bs.get(f"total_non_current_liabilities{period_suffix}")

        cash = bs.get(f"cash_and_equivalents{period_suffix}")
        inventory = bs.get(f"inventory{period_suffix}")
        accounts_receivable = bs.get(f"accounts_receivable{period_suffix}")
        accounts_payable = bs.get(f"accounts_payable{period_suffix}")
        fixed_assets = bs.get(f"fixed_assets{period_suffix}")
        intangible_assets = bs.get(f"intangible_assets{period_suffix}")
        retained_earnings = bs.get(f"retained_earnings{period_suffix}")
        additional_paid_in_capital = bs.get(f"additional_paid_in_capital{period_suffix}")

        short_term_loans = bs.get(f"short_term_loans{period_suffix}")
        long_term_loans = bs.get(f"long_term_loans{period_suffix}")

        revenue = inc.get(f"revenue{period_suffix}")
        cogs = inc.get(f"cost_of_goods_sold{period_suffix}")
        gross_profit = inc.get(f"gross_profit{period_suffix}")
        net_income = inc.get(f"net_income{period_suffix}")
        profit_before_tax = inc.get(f"profit_before_tax{period_suffix}")
        income_tax = inc.get(f"income_tax_expense{period_suffix}")
        selling_expenses = inc.get(f"selling_expenses{period_suffix}")
        admin_expenses = inc.get(f"general_and_admin_expenses{period_suffix}")
        financial_expense = inc.get(f"financial_expense{period_suffix}")
        other_income = inc.get(f"other_income{period_suffix}")
        other_expenses = inc.get(f"other_expenses{period_suffix}")

        operating_cf = cf.get(f"operating_cash_flow{period_suffix}")
        investing_cf = cf.get(f"investing_cash_flow{period_suffix}")
        financing_cf = cf.get(f"financing_cash_flow{period_suffix}")

        # Derived values
        if total_equity is None and total_assets is not None and total_liabilities is not None:
            total_equity = total_assets - total_liabilities

        working_capital = None
        if total_current_assets is not None and total_current_liabilities is not None:
            working_capital = total_current_assets - total_current_liabilities

        total_debt = None
        if short_term_loans is not None and long_term_loans is not None:
            total_debt = short_term_loans + long_term_loans
        elif short_term_loans is not None:
            total_debt = short_term_loans
        elif long_term_loans is not None:
            total_debt = long_term_loans

        operating_expenses = None
        if selling_expenses is not None and admin_expenses is not None:
            operating_expenses = selling_expenses + admin_expenses

        # EBIT approximation: profit_before_tax + financial_expense
        ebit = None
        if profit_before_tax is not None and financial_expense is not None:
            ebit = profit_before_tax + financial_expense
        elif profit_before_tax is not None:
            ebit = profit_before_tax

        # EBITDA approximation (no depreciation data, so EBIT is used as proxy)
        ebitda = ebit

        # ============================================================
        # ACTIVITY RATIOS (9)
        # ============================================================
        activity = {}

        # 1. Total Asset Turnover = Revenue / Total Assets
        activity["total_asset_turnover"] = safe_div(revenue, total_assets)

        # 2. Fixed Asset Turnover = Revenue / Fixed Assets
        activity["fixed_asset_turnover"] = safe_div(revenue, fixed_assets)

        # 3. Inventory Turnover = COGS / Inventory
        activity["inventory_turnover"] = safe_div(cogs, inventory)

        # 4. Days Inventory Outstanding = 365 / Inventory Turnover
        activity["days_inventory"] = safe_div(365, activity.get("inventory_turnover"))

        # 5. Receivables Turnover = Revenue / Accounts Receivable
        activity["receivables_turnover"] = safe_div(revenue, accounts_receivable)

        # 6. Days Sales Outstanding = 365 / Receivables Turnover
        activity["days_sales_outstanding"] = safe_div(365, activity.get("receivables_turnover"))

        # 7. Payables Turnover = COGS / Accounts Payable
        activity["payables_turnover"] = safe_div(cogs, accounts_payable)

        # 8. Days Payable Outstanding = 365 / Payables Turnover
        activity["days_payable_outstanding"] = safe_div(365, activity.get("payables_turnover"))

        # 9. Cash Conversion Cycle = DIO + DSO - DPO
        dio = activity.get("days_inventory")
        dso = activity.get("days_sales_outstanding")
        dpo = activity.get("days_payable_outstanding")
        if dio is not None and dso is not None and dpo is not None:
            activity["cash_conversion_cycle"] = dio + dso - dpo
        else:
            activity["cash_conversion_cycle"] = None

        # ============================================================
        # LIQUIDITY RATIOS (4)
        # ============================================================
        liquidity = {}

        # 1. Current Ratio = Current Assets / Current Liabilities
        liquidity["current_ratio"] = safe_div(total_current_assets, total_current_liabilities)

        # 2. Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        if total_current_assets is not None and inventory is not None:
            liquidity["quick_ratio"] = safe_div(
                total_current_assets - inventory, total_current_liabilities
            )
        else:
            liquidity["quick_ratio"] = None

        # 3. Cash Ratio = Cash / Current Liabilities
        liquidity["cash_ratio"] = safe_div(cash, total_current_liabilities)

        # 4. Working Capital Ratio (same as current ratio, but store absolute WC)
        liquidity["working_capital"] = working_capital

        # ============================================================
        # SOLVENCY RATIOS (4)
        # ============================================================
        solvency = {}

        # 1. Debt-to-Equity = Total Liabilities / Total Equity
        solvency["debt_to_equity"] = safe_div(total_liabilities, total_equity)

        # 2. Debt-to-Assets = Total Liabilities / Total Assets
        solvency["debt_to_assets"] = safe_div(total_liabilities, total_assets)

        # 3. Equity Ratio = Total Equity / Total Assets
        solvency["equity_ratio"] = safe_div(total_equity, total_assets)

        # 4. Interest Coverage = EBIT / Financial Expense
        solvency["interest_coverage"] = safe_div(ebit, financial_expense)

        # ============================================================
        # PROFITABILITY RATIOS (6)
        # ============================================================
        profitability = {}

        # 1. Gross Profit Margin = Gross Profit / Revenue
        profitability["gross_margin"] = safe_div(gross_profit, revenue)

        # 2. Operating Margin = EBIT / Revenue
        profitability["operating_margin"] = safe_div(ebit, revenue)

        # 3. Net Profit Margin = Net Income / Revenue
        profitability["net_margin"] = safe_div(net_income, revenue)

        # 4. ROA = Net Income / Total Assets
        profitability["roa"] = safe_div(net_income, total_assets)

        # 5. ROE = Net Income / Total Equity
        profitability["roe"] = safe_div(net_income, total_equity)

        # 6. EBIT Margin = EBIT / Revenue
        profitability["ebit_margin"] = safe_div(ebit, revenue)

        # ============================================================
        # PERFORMANCE RATIOS (3)
        # ============================================================
        performance = {}

        # 1. Operating Cash Flow Ratio = Operating CF / Current Liabilities
        performance["ocf_ratio"] = safe_div(operating_cf, total_current_liabilities)

        # 2. Cash Flow to Debt = Operating CF / Total Liabilities
        performance["cf_to_debt"] = safe_div(operating_cf, total_liabilities)

        # 3. Reinvestment Ratio = Investing CF / Operating CF (how much is reinvested)
        performance["reinvestment_ratio"] = safe_div(investing_cf, operating_cf)

        # ============================================================
        # ALTMAN Z-SCORE (manufacturing variant)
        # ============================================================
        # Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        # X1 = Working Capital / Total Assets
        # X2 = Retained Earnings / Total Assets
        # X3 = EBIT / Total Assets
        # X4 = Equity / Total Liabilities
        # X5 = Revenue / Total Assets
        z_score_val = None
        x1 = safe_div(working_capital, total_assets)
        x2 = safe_div(retained_earnings, total_assets)
        x3 = safe_div(ebit, total_assets)
        x4 = safe_div(total_equity, total_liabilities)
        x5 = safe_div(revenue, total_assets)

        if all(v is not None for v in [x1, x2, x3, x4, x5]):
            z_score_val = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

        z_score = {
            "x1_wc_ta": x1,
            "x2_re_ta": x2,
            "x3_ebit_ta": x3,
            "x4_eq_tl": x4,
            "x5_rev_ta": x5,
            "z_score": z_score_val,
        }

        result[period_key] = {
            "activity": activity,
            "liquidity": liquidity,
            "solvency": solvency,
            "profitability": profitability,
            "performance": performance,
            "z_score": z_score,
        }

    return result


def compute_piotroski(parsed_data: dict) -> dict:
    """Compute Piotroski F-Score (0–9 financial strength indicator).

    Returns:
        {
            "f_score": int,
            "max_score": int,          # criteria with available data
            "criteria": { f1..f9: 0|1|None },
            "interpretation": "Strong"|"Neutral"|"Weak",
        }
    """
    bs  = parsed_data.get("balance_sheet", {})
    inc = parsed_data.get("income_statement", {})
    cf  = parsed_data.get("cash_flow", {})

    # ── Extract fields ────────────────────────────────────────────────────────
    net_income  = inc.get("net_income")
    ni_prev     = inc.get("net_income_prev")
    ta          = bs.get("total_assets")
    ta_prev     = bs.get("total_assets_prev")
    ocf         = cf.get("operating_cash_flow")
    tl          = bs.get("total_liabilities")
    tl_prev     = bs.get("total_liabilities_prev")
    ca          = bs.get("total_current_assets")
    ca_prev     = bs.get("total_current_assets_prev")
    cl          = bs.get("total_current_liabilities")
    cl_prev     = bs.get("total_current_liabilities_prev")
    rev         = inc.get("revenue")
    rev_prev    = inc.get("revenue_prev")
    gp          = inc.get("gross_profit")
    gp_prev     = inc.get("gross_profit_prev")

    # ── Helper ────────────────────────────────────────────────────────────────
    def _flag(condition) -> int | None:
        """Return 1/0 if condition evaluable, else None."""
        try:
            return 1 if condition else 0
        except TypeError:
            return None

    # ── F1: ROA positive (net_income / total_assets > 0) ─────────────────────
    roa_curr = safe_div(net_income, ta)
    f1 = None if roa_curr is None else _flag(roa_curr > 0)

    # ── F2: Operating cash flow positive ─────────────────────────────────────
    f2 = None if ocf is None else _flag(ocf > 0)

    # ── F3: ROA improving year-over-year ─────────────────────────────────────
    roa_prev = safe_div(ni_prev, ta_prev)
    f3 = None if (roa_curr is None or roa_prev is None) else _flag(roa_curr > roa_prev)

    # ── F4: Accruals — cash earnings quality (OCF/TA > ROA) ──────────────────
    ocf_ta = safe_div(ocf, ta)
    f4 = None if (ocf_ta is None or roa_curr is None) else _flag(ocf_ta > roa_curr)

    # ── F5: Leverage decreased (total_liabilities / total_assets) ────────────
    lev      = safe_div(tl, ta)
    lev_prev = safe_div(tl_prev, ta_prev)
    f5 = None if (lev is None or lev_prev is None) else _flag(lev < lev_prev)

    # ── F6: Current ratio improved ────────────────────────────────────────────
    cr      = safe_div(ca, cl)
    cr_prev = safe_div(ca_prev, cl_prev)
    f6 = None if (cr is None or cr_prev is None) else _flag(cr > cr_prev)

    # ── F7: No share dilution — skip (shares_outstanding not in MSE data) ────
    f7 = None

    # ── F8: Gross margin improving ────────────────────────────────────────────
    gm      = safe_div(gp, rev)
    gm_prev = safe_div(gp_prev, rev_prev)
    f8 = None if (gm is None or gm_prev is None) else _flag(gm > gm_prev)

    # ── F9: Asset turnover improving (revenue / total_assets) ────────────────
    at      = safe_div(rev, ta)
    at_prev = safe_div(rev_prev, ta_prev)
    f9 = None if (at is None or at_prev is None) else _flag(at > at_prev)

    criteria = {
        "f1_roa_positive":   f1,
        "f2_ocf_positive":   f2,
        "f3_roa_improving":  f3,
        "f4_accruals":       f4,
        "f5_leverage_down":  f5,
        "f6_liquidity_up":   f6,
        "f7_no_dilution":    f7,
        "f8_gross_margin_up": f8,
        "f9_asset_turnover_up": f9,
    }

    scored    = [v for v in criteria.values() if v is not None]
    f_score   = sum(scored)
    max_score = len(scored)

    if max_score == 0:
        interpretation = "Insufficient data"
    elif f_score >= 7:
        interpretation = "Strong"
    elif f_score <= 2:
        interpretation = "Weak"
    else:
        interpretation = "Neutral"

    return {
        "f_score":        f_score,
        "max_score":      max_score,
        "criteria":       criteria,
        "interpretation": interpretation,
    }


from .labels import RATIO_LABELS  # noqa: F401  (re-exported for convenience)
