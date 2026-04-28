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
    bs = (parsed_data.get("balance_sheet")
          or parsed_data.get("bank_balance_sheet")
          or parsed_data.get("insurance_balance_sheet")
          or {})
    inc = (parsed_data.get("income_statement")
           or parsed_data.get("bank_income_statement")
           or parsed_data.get("insurance_income_statement")
           or {})
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

        # Some companies report "цэвэр борлуулалт" (net_revenue) instead of "борлуулалтын орлого" (revenue).
        revenue = (inc.get(f"revenue{period_suffix}")
                   or inc.get(f"net_revenue{period_suffix}")
                   or inc.get(f"total_revenue{period_suffix}")
                   or inc.get(f"net_premiums_earned{period_suffix}")
                   or inc.get(f"gross_premiums_written{period_suffix}"))
        cogs = inc.get(f"cost_of_goods_sold{period_suffix}")
        gross_profit = inc.get(f"gross_profit{period_suffix}")
        net_income = inc.get(f"net_income{period_suffix}")
        profit_before_tax = inc.get(f"profit_before_tax{period_suffix}")
        income_tax = inc.get(f"income_tax_expense{period_suffix}")
        profit_after_tax = inc.get(f"profit_after_tax{period_suffix}")
        # Fallback: net_income may be 0.0 from a section-header parse artefact.
        # Use profit_after_tax or compute from profit_before_tax when available.
        if (net_income is None or net_income == 0) and profit_after_tax:
            net_income = profit_after_tax
        elif (net_income is None or net_income == 0) and profit_before_tax is not None and income_tax is not None:
            net_income = profit_before_tax - income_tax
        elif (net_income is None or net_income == 0) and profit_before_tax:
            net_income = profit_before_tax
        selling_expenses = inc.get(f"selling_expenses{period_suffix}")
        admin_expenses = inc.get(f"general_and_admin_expenses{period_suffix}")
        financial_expense = inc.get(f"financial_expense{period_suffix}")
        other_income = inc.get(f"other_income{period_suffix}")
        other_expenses = inc.get(f"other_expenses{period_suffix}")

        operating_cf = cf.get(f"operating_cash_flow{period_suffix}")
        investing_cf = cf.get(f"investing_cash_flow{period_suffix}")
        financing_cf = cf.get(f"financing_cash_flow{period_suffix}")

        # Derived values
        if (total_equity is None or total_equity == 0) and total_assets is not None and total_liabilities is not None:
            computed = total_assets - total_liabilities
            if total_equity is None or computed != 0:
                total_equity = computed
        elif total_equity is not None and total_assets is not None and total_liabilities is not None and total_assets > 0:
            # Override when parser captured a sub-line instead of the actual equity total.
            # Two cases:
            #   (1) Sign mismatch — parser clearly hit wrong row (e.g. Монложистикс: -212k vs +48.6M)
            #   (2) Parsed magnitude << derived magnitude — sub-line capture (e.g. Дархан нэхий:
            #       10.4M vs 66M; Мон-Ит: 266k vs 11M; Премиум нэксус: 318k vs 102.8M)
            # Do NOT override if parsed is larger in magnitude — that means accumulated losses or
            # comprehensive-income items are correctly included in parsed equity (УлсынИхДэлгүүр).
            derived = total_assets - total_liabilities
            if derived != 0:
                sign_mismatch = (total_equity >= 0) != (derived >= 0)
                sub_line_capture = (
                    abs(total_equity) < abs(derived) * 0.8
                    and abs(total_equity - derived) / total_assets > 0.05
                )
                if sign_mismatch or sub_line_capture:
                    total_equity = derived

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
    bs  = (parsed_data.get("balance_sheet")
           or parsed_data.get("bank_balance_sheet")
           or parsed_data.get("insurance_balance_sheet")
           or {})
    inc = (parsed_data.get("income_statement")
           or parsed_data.get("bank_income_statement")
           or parsed_data.get("insurance_income_statement")
           or {})
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
    # F4: Accruals quality — tests whether cash earnings (OCF/TA) exceed accrual earnings (ROA).
    # High accruals relative to cash earnings signal earnings quality risk (Sloan 1996, earnings persistence).
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
    # F7: Share dilution signal — always None. MSE Excel financial statements do not include shares
    # outstanding. Companies that issued new shares will not have this penalized in their F-Score.
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


def compute_beneish(parsed_data: dict) -> dict:
    """Compute Beneish M-Score for earnings manipulation detection.

    Uses 8 financial indices. Requires two years of data.
    M-Score > -1.78  → possible manipulation
    M-Score < -2.22  → likely clean

    Returns:
        {
            "m_score": float | None,
            "interpretation": str,
            "threshold": float,
            "indices": { dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata },
            "missing_indices": [str],
            "reliable": bool,   # False if < 5 indices computable
        }
    """
    bs  = (parsed_data.get("balance_sheet")
           or parsed_data.get("bank_balance_sheet")
           or parsed_data.get("insurance_balance_sheet")
           or {})
    inc = (parsed_data.get("income_statement")
           or parsed_data.get("bank_income_statement")
           or parsed_data.get("insurance_income_statement")
           or {})
    cf  = parsed_data.get("cash_flow", {})

    # ── Extract current year fields ───────────────────────────────────────────
    ar     = bs.get("accounts_receivable")
    rev    = inc.get("revenue")
    gp     = inc.get("gross_profit")
    cogs   = inc.get("cost_of_goods_sold")
    ta     = bs.get("total_assets")
    ca     = bs.get("total_current_assets")
    ppe    = bs.get("fixed_assets")          # property, plant & equipment proxy
    dep    = None                            # depreciation not in MSE data
    sga    = None
    if inc.get("selling_expenses") or inc.get("general_and_admin_expenses"):
        parts = [inc.get("selling_expenses") or 0,
                 inc.get("general_and_admin_expenses") or 0]
        sga = sum(parts)
    ltd    = bs.get("long_term_loans")
    cl     = bs.get("total_current_liabilities")
    ni     = inc.get("net_income")
    ocf    = cf.get("operating_cash_flow")

    # Derive gross profit if missing
    if gp is None and rev is not None and cogs is not None:
        gp = rev - cogs

    # ── Extract previous year fields ──────────────────────────────────────────
    ar_p   = bs.get("accounts_receivable_prev")
    rev_p  = inc.get("revenue_prev")
    gp_p   = inc.get("gross_profit_prev")
    cogs_p = inc.get("cost_of_goods_sold_prev")
    ta_p   = bs.get("total_assets_prev")
    ca_p   = bs.get("total_current_assets_prev")
    ppe_p  = bs.get("fixed_assets_prev")
    sga_p  = None
    if inc.get("selling_expenses_prev") or inc.get("general_and_admin_expenses_prev"):
        parts = [inc.get("selling_expenses_prev") or 0,
                 inc.get("general_and_admin_expenses_prev") or 0]
        sga_p = sum(parts)
    ltd_p  = bs.get("long_term_loans_prev")
    cl_p   = bs.get("total_current_liabilities_prev")

    if gp_p is None and rev_p is not None and cogs_p is not None:
        gp_p = rev_p - cogs_p

    # ── Compute the 8 indices ─────────────────────────────────────────────────
    indices = {}
    missing = []

    # DSRI (Days Sales Receivables Index): rising AR relative to revenue suggests premature
    # revenue recognition — a common earnings manipulation technique (Beneish 1999).
    # DSRI: Days Sales Receivables Index = (AR_t/Rev_t) / (AR_p/Rev_p)
    dsri = safe_div(safe_div(ar, rev), safe_div(ar_p, rev_p))
    indices["dsri"] = dsri
    if dsri is None:
        missing.append("dsri")

    # GMI (Gross Margin Index): declining margin creates pressure and incentive to manipulate earnings.
    # GMI > 1.0 means margins deteriorated year-over-year.
    # GMI: Gross Margin Index = (GM_p/Rev_p) / (GM_t/Rev_t)  — prev/curr
    gm   = safe_div(gp, rev)
    gm_p = safe_div(gp_p, rev_p)
    gmi  = safe_div(gm_p, gm)
    indices["gmi"] = gmi
    if gmi is None:
        missing.append("gmi")

    # AQI (Asset Quality Index): growth in non-current, non-PPE assets proxies off-balance-sheet risk
    # and capitalization of future expenses as assets (a manipulation vehicle).
    # AQI: Asset Quality Index
    # = (1 - (CA_t + PPE_t)/TA_t) / (1 - (CA_p + PPE_p)/TA_p)
    def _aq(ca_v, ppe_v, ta_v):
        num = safe_div(ca_v, ta_v)
        num2 = safe_div(ppe_v, ta_v)
        if num is None or num2 is None:
            return None
        return 1 - num - num2

    aq   = _aq(ca, ppe, ta)
    aq_p = _aq(ca_p, ppe_p, ta_p)
    aqi  = safe_div(aq, aq_p)
    indices["aqi"] = aqi
    if aqi is None:
        missing.append("aqi")

    # SGI: Sales Growth Index = Rev_t / Rev_p
    sgi = safe_div(rev, rev_p)
    indices["sgi"] = sgi
    if sgi is None:
        missing.append("sgi")

    # DEPI (Depreciation Pattern Index): always None. MSE filings do not disclose depreciation
    # as a separate line item. This index cannot be computed for any MSE company.
    # DEPI: Depreciation Index — skipped, depreciation not in MSE data
    indices["depi"] = None
    missing.append("depi")

    # SGAI: SG&A Index = (SGA_t/Rev_t) / (SGA_p/Rev_p)
    sgai = safe_div(safe_div(sga, rev), safe_div(sga_p, rev_p))
    indices["sgai"] = sgai
    if sgai is None:
        missing.append("sgai")

    # LVGI: Leverage Index = ((LTD_t + CL_t)/TA_t) / ((LTD_p + CL_p)/TA_p)
    def _lev(ltd_v, cl_v, ta_v):
        if ltd_v is None and cl_v is None:
            return None
        num = (ltd_v or 0) + (cl_v or 0)
        return safe_div(num, ta_v)

    lv   = _lev(ltd, cl, ta)
    lv_p = _lev(ltd_p, cl_p, ta_p)
    lvgi = safe_div(lv, lv_p)
    indices["lvgi"] = lvgi
    if lvgi is None:
        missing.append("lvgi")

    # TATA: Total Accruals to Total Assets = (NI - OCF) / TA
    tata = safe_div(
        (ni - ocf) if (ni is not None and ocf is not None) else None,
        ta
    )
    indices["tata"] = tata
    if tata is None:
        missing.append("tata")

    # ── Compute M-Score ───────────────────────────────────────────────────────
    # M-Score formula: Beneish (1999) probit regression. Intercept -4.84.
    # Each coefficient is the log-odds contribution of that index to the probability of manipulation.
    # M > -1.78: possible manipulation. M > -2.22: likely clean (conservative threshold).
    # Weights: -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
    #          + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    available = 8 - len(missing)
    reliable  = available >= 5

    m_score = None
    if reliable:
        coeffs = {
            "dsri":  0.920,
            "gmi":   0.528,
            "aqi":   0.404,
            "sgi":   0.892,
            "depi":  0.115,
            "sgai": -0.172,
            "tata":  4.679,
            "lvgi": -0.327,
        }
        total = -4.84
        for key, coeff in coeffs.items():
            val = indices.get(key)
            if val is not None:
                total += coeff * val
            # Missing indices: excluded (partial score — noted in reliable flag)
        m_score = total

    if m_score is None:
        interpretation = "Insufficient data"
    elif m_score > -1.78:
        interpretation = "Possible manipulation"
    elif m_score < -2.22:
        interpretation = "Likely clean"
    else:
        interpretation = "Inconclusive (grey zone)"

    return {
        "m_score":         m_score,
        "interpretation":  interpretation,
        "threshold":       -1.78,
        "indices":         indices,
        "missing_indices": missing,
        "reliable":        reliable,
    }


def compute_composite_score(
    ratios: dict,
    piotroski: dict,
    beneish: dict,
) -> dict:
    """Compute Composite Health Score (0–100) from all models.

    Args:
        ratios:     Output of compute_ratios()
        piotroski:  Output of compute_piotroski()
        beneish:    Output of compute_beneish()

    Returns:
        {
            "score": int,           # 0–100
            "label": str,           # Healthy | Caution | Distress
            "color": str,           # green | amber | red  (for UI)
            "breakdown": { category: sub_score },
            "beneish_penalty": int,
        }
    """

    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v)) if v is not None else None

    def _interp(v, lo_v, hi_v, lo_s=0.0, hi_s=100.0):
        """Linear interpolation: map value range -> score range."""
        if v is None:
            return None
        if hi_v == lo_v:
            return lo_s
        ratio = (v - lo_v) / (hi_v - lo_v)
        return _clamp(lo_s + ratio * (hi_s - lo_s))

    curr = ratios.get("current", {})

    # -- Sub-scores (each 0-100) -----------------------------------------------

    # Profitability
    roa = curr.get("profitability", {}).get("roa")
    roe = curr.get("profitability", {}).get("roe")
    npm = curr.get("profitability", {}).get("net_margin")
    prof_parts = [x for x in [
        _interp(roa,  0,    0.15, 0, 100),
        _interp(roe,  0,    0.25, 0, 100),
        _interp(npm, -0.05, 0.20, 0, 100),
    ] if x is not None]
    prof_score = sum(prof_parts) / len(prof_parts) if prof_parts else None

    # Liquidity
    cr = curr.get("liquidity", {}).get("current_ratio")
    qr = curr.get("liquidity", {}).get("quick_ratio")
    cash_r = curr.get("liquidity", {}).get("cash_ratio")
    liq_parts = [x for x in [
        _interp(cr,     0, 3.0,  0, 100),
        _interp(qr,     0, 1.5,  0, 100),
        _interp(cash_r, 0, 0.5,  0, 100),
    ] if x is not None]
    liq_score = sum(liq_parts) / len(liq_parts) if liq_parts else None

    # Solvency (inverted: lower debt = better)
    d2e = curr.get("solvency", {}).get("debt_to_equity")
    d2a = curr.get("solvency", {}).get("debt_to_assets")
    ic  = curr.get("solvency", {}).get("interest_coverage")
    solv_parts = [x for x in [
        _interp(d2e, 5, 0, 0, 100),   # inverted
        _interp(d2a, 1, 0, 0, 100),   # inverted
        _interp(ic,  0, 5, 0, 100),
    ] if x is not None]
    solv_score = sum(solv_parts) / len(solv_parts) if solv_parts else None

    # Activity
    tat = curr.get("activity", {}).get("total_asset_turnover")
    dso = curr.get("activity", {}).get("days_sales_outstanding")
    it  = curr.get("activity", {}).get("inventory_turnover")
    act_parts = [x for x in [
        _interp(tat, 0, 2.0,  0, 100),
        _interp(dso, 180, 30, 0, 100),  # inverted (lower DSO = better)
        _interp(it,  0, 20,   0, 100),
    ] if x is not None]
    act_score = sum(act_parts) / len(act_parts) if act_parts else None

    # Altman Z-Score
    z = curr.get("z_score", {}).get("z_score")
    if z is None:
        z_score_sub = None
    elif z >= 2.99:
        z_score_sub = _interp(z, 2.99, 5.0, 70, 100)
    elif z >= 1.81:
        z_score_sub = _interp(z, 1.81, 2.99, 30, 70)
    else:
        z_score_sub = _interp(z, 0, 1.81, 0, 30)

    # Piotroski F-Score
    f  = piotroski.get("f_score")
    mx = piotroski.get("max_score") or 9
    piotr_score = _clamp((f / mx) * 100) if f is not None and mx > 0 else None

    # -- Weighted aggregate ----------------------------------------------------
    # Composite Health Score weights: profitability 25%, liquidity 20%, solvency 20%, activity 15%,
    # Altman Z 10%, Piotroski 10% (total 100%). Beneish penalty (-10 pts) applied post-aggregation
    # when M-Score is reliable (>=5 indices) and above -1.78 manipulation threshold.
    # Available-data normalization: if a component has no data, its weight is redistributed
    # proportionally to components that do have data.
    weights = {
        "profitability": (prof_score, 0.25),
        "liquidity":     (liq_score,  0.20),
        "solvency":      (solv_score, 0.20),
        "activity":      (act_score,  0.15),
        "altman":        (z_score_sub, 0.10),
        "piotroski":     (piotr_score, 0.10),
    }

    total_weight = 0.0
    weighted_sum = 0.0
    breakdown    = {}

    for cat, (score, w) in weights.items():
        breakdown[cat] = round(score, 1) if score is not None else None
        if score is not None:
            weighted_sum += score * w
            total_weight += w

    if total_weight == 0:
        raw_score = 0
    else:
        # Re-normalise weights for available components
        raw_score = weighted_sum / total_weight

    # -- Beneish penalty -------------------------------------------------------
    m = beneish.get("m_score")
    penalty = -10 if (m is not None and beneish.get("reliable") and m > -1.78) else 0

    final_score = int(_clamp(raw_score + penalty))

    if final_score >= 70:
        label, color = "Healthy",  "green"
    elif final_score >= 40:
        label, color = "Caution",  "amber"
    else:
        label, color = "Distress", "red"

    return {
        "score":           final_score,
        "label":           label,
        "color":           color,
        "breakdown":       breakdown,
        "beneish_penalty": penalty,
    }


def compute_bank_composite_score(bank_ratios: dict) -> dict:
    """Composite health score (0–100) for banks using a CAMELS-inspired framework.

    Framework basis
    ---------------
    CAMELS (Capital adequacy, Asset quality, Management/Efficiency, Earnings,
    Liquidity, Sensitivity) is the global standard used by bank regulators (Fed,
    FDIC, IMF, World Bank).  Each pillar is scored 0–100 then weighted.

    Weights (sum to 1.0)
    --------------------
    Capital adequacy  25% — core buffer against insolvency
    Asset quality     25% — NPL and reserve coverage drive credit risk
    Earnings          20% — profitability: ROA, ROE, NIM
    Liquidity         20% — LDR and cash coverage
    Efficiency        10% — cost-to-income (management quality proxy)

    Sensitivity (market risk) is omitted — MSE-listed banks do not disclose
    interest-rate sensitivity or VaR data in their public filings.

    Benchmarks: IMF FSI thresholds, CARE Ratings "Banks" methodology (2020),
    Bank of Mongolia prudential norms, BIS Basel III capital standards.
    """

    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v)) if v is not None else None

    def _interp(v, lo_v, hi_v, lo_s=0.0, hi_s=100.0):
        if v is None or hi_v == lo_v:
            return None
        ratio = (v - lo_v) / (hi_v - lo_v)
        return _clamp(lo_s + ratio * (hi_s - lo_s))

    def _avg(parts):
        valid = [x for x in parts if x is not None]
        return sum(valid) / len(valid) if valid else None

    curr = bank_ratios.get("current", {})
    prof = curr.get("profitability", {})
    cap  = curr.get("capital_adequacy", {})
    aq   = curr.get("asset_quality", {})
    liq  = curr.get("liquidity", {})
    eff  = curr.get("efficiency", {})

    # ── Capital Adequacy (25%) ────────────────────────────────────────────────
    # equity_to_assets: BIS Basel III minimum 8%; >12% strong; >15% excellent
    # equity_multiplier: lower is safer; <8x excellent, 8-15x normal, >20x risky
    eq_to_assets     = cap.get("equity_to_assets")
    eq_multiplier    = cap.get("equity_multiplier")
    cap_score = _avg([
        _interp(eq_to_assets,  0.04, 0.15, 0, 100),
        _interp(eq_multiplier, 20,   6,    0, 100),   # inverted: lower multiplier = better
    ])

    # ── Asset Quality (25%) ──────────────────────────────────────────────────
    # npl_ratio: <2% excellent, 2-5% acceptable, >10% distress (BoM norms)
    # coverage_ratio: >150% excellent, 70-150% acceptable, <50% poor (Basel guidance)
    # loan_loss_reserve_ratio: <1% low risk, 1-3% moderate, >5% high (IMF FSI)
    npl      = aq.get("npl_ratio")
    coverage = aq.get("coverage_ratio")
    llr      = aq.get("loan_loss_reserve_ratio")
    aq_score = _avg([
        _interp(npl,      0.10, 0.00, 0, 100),   # inverted: lower NPL = better
        _interp(coverage, 0.50, 2.00, 0, 100),   # higher coverage = better
        _interp(llr,      0.05, 0.00, 0, 100),   # inverted: lower reserve ratio = cleaner book
    ])

    # ── Earnings (20%) ───────────────────────────────────────────────────────
    # ROA: <0.5% poor, 0.5-1% adequate, >1.5% excellent (IMF FSI / CARE Ratings)
    # ROE: <10% poor, 10-20% adequate, >25% excellent
    # NIM: <2% compressed, 2-4% adequate, >5% strong (varies by market)
    roa = prof.get("roa")
    roe = prof.get("roe")
    nim = prof.get("nim")
    earn_score = _avg([
        _interp(roa, 0,    0.020, 0, 100),
        _interp(roe, 0,    0.25,  0, 100),
        _interp(nim, 0,    0.08,  0, 100),   # Mongolian banks: typical 6-15%
    ])

    # ── Liquidity (20%) ──────────────────────────────────────────────────────
    # LDR (loan-to-deposit): <80% conservative, 80-100% normal, >120% stretched
    #   Score: inverted around 90% optimum — too low (idle) or too high (risky) both bad
    #   Simplified: penalise above 1.0, reward below 0.9
    # cash_to_deposits: >20% strong, 10-20% adequate, <5% tight
    ldr       = liq.get("ldr")
    cash_dep  = liq.get("cash_to_deposits")
    # LDR sweet-spot scoring: 60%-90% = full score, then decreasing
    ldr_score = None
    if ldr is not None:
        if ldr <= 0.90:
            ldr_score = _interp(ldr, 0.50, 0.90, 60, 100)
        else:
            ldr_score = _interp(ldr, 0.90, 1.30, 100, 0)
    liq_score = _avg([
        ldr_score,
        _interp(cash_dep, 0.02, 0.25, 0, 100),
    ])

    # ── Efficiency (10%) ─────────────────────────────────────────────────────
    # cost_to_income: <40% excellent, 40-60% adequate, >80% poor (CARE Ratings)
    cti = eff.get("cost_to_income")
    eff_score = _interp(cti, 0.80, 0.30, 0, 100)   # inverted

    # ── Weighted composite ────────────────────────────────────────────────────
    weights = {
        "capital":    (cap_score,  0.25),
        "asset_quality": (aq_score, 0.25),
        "earnings":   (earn_score, 0.20),
        "liquidity":  (liq_score,  0.20),
        "efficiency": (eff_score,  0.10),
    }

    total_weight = weighted_sum = 0.0
    breakdown = {}
    for cat, (score, w) in weights.items():
        breakdown[cat] = round(score, 1) if score is not None else None
        if score is not None:
            weighted_sum += score * w
            total_weight += w

    raw_score = weighted_sum / total_weight if total_weight > 0 else 0
    final_score = int(_clamp(raw_score))

    if final_score >= 70:
        label, color = "Healthy",  "green"
    elif final_score >= 40:
        label, color = "Caution",  "amber"
    else:
        label, color = "Distress", "red"

    return {
        "score":     final_score,
        "label":     label,
        "color":     color,
        "breakdown": breakdown,
        "beneish_penalty": 0,
    }


def compute_insurance_composite_score(ins_ratios: dict) -> dict:
    """Composite health score (0–100) for insurance companies.

    Framework basis
    ---------------
    Combines IRIS (Insurance Regulatory Information System) ratio screening,
    Solvency II capital adequacy concepts, and standard underwriting profitability
    metrics used by rating agencies (A.M. Best, S&P Insurance Criteria).

    Weights (sum to 1.0)
    --------------------
    Underwriting quality  30% — combined ratio drives insurance core business
    Solvency / capital    25% — solvency ratio and leverage (regulatory focus)
    Profitability         25% — ROA, ROE, net margin
    Liquidity             20% — cash and investment coverage

    Benchmarks: NAIC IRIS thresholds, A.M. Best criteria, Mongolia Financial
    Regulatory Commission (FRC) solvency standards (>20% equity/assets).
    """

    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v)) if v is not None else None

    def _interp(v, lo_v, hi_v, lo_s=0.0, hi_s=100.0):
        if v is None or hi_v == lo_v:
            return None
        ratio = (v - lo_v) / (hi_v - lo_v)
        return _clamp(lo_s + ratio * (hi_s - lo_s))

    def _avg(parts):
        valid = [x for x in parts if x is not None]
        return sum(valid) / len(valid) if valid else None

    curr = ins_ratios.get("current", {})
    uw   = curr.get("underwriting", {})
    prof = curr.get("profitability", {})
    solv = curr.get("solvency", {})
    liq  = curr.get("liquidity", {})

    # ── Underwriting Quality (30%) ────────────────────────────────────────────
    # combined_ratio: <90% excellent, 90-100% profitable, 100-110% marginal, >110% loss
    # loss_ratio: <55% excellent, 55-70% good, 70-85% moderate, >85% poor
    # expense_ratio: <25% excellent, 25-35% adequate, >40% poor
    combined = uw.get("combined_ratio")
    loss_r   = uw.get("loss_ratio")
    expense_r = uw.get("expense_ratio")
    # combined_ratio: 0.85 maps to 100, 1.10 maps to 0
    uw_score = _avg([
        _interp(combined,  1.15, 0.85, 0, 100),   # inverted
        _interp(loss_r,    0.90, 0.50, 0, 100),   # inverted
        _interp(expense_r, 0.45, 0.20, 0, 100),   # inverted
    ])
    # If combined_ratio is None but others available, use partial
    # If all underwriting data is absent (old format companies), fall back to profitability only
    if uw_score is None:
        uw_weight = 0.0
    else:
        uw_weight = 0.30

    # ── Solvency / Capital (25%) ──────────────────────────────────────────────
    # solvency_ratio (equity/assets): FRC minimum 20%; >30% strong; >40% excellent
    # leverage_ratio (liabilities/equity): <2x strong, 2-4x adequate, >6x risky
    solvency_r  = solv.get("solvency_ratio")
    leverage_r  = solv.get("leverage_ratio")
    reserve_cov = solv.get("reserve_coverage")
    solv_score = _avg([
        _interp(solvency_r,  0.10, 0.40, 0, 100),
        _interp(leverage_r,  6.0,  1.0,  0, 100),   # inverted
        _interp(reserve_cov, 0.0,  1.5,  0, 100),
    ])

    # ── Profitability (25%) ───────────────────────────────────────────────────
    # ROA: >3% excellent for insurers (lower asset base vs banks)
    # ROE: >15% good, >20% excellent
    # net_margin: >10% adequate, >20% good for insurance
    roa = prof.get("roa")
    roe = prof.get("roe")
    npm = prof.get("net_margin")
    prof_score = _avg([
        _interp(roa, -0.02, 0.05,  0, 100),
        _interp(roe, -0.05, 0.25,  0, 100),
        _interp(npm, -0.05, 0.25,  0, 100),
    ])

    # ── Liquidity (20%) ──────────────────────────────────────────────────────
    # investment_ratio (investments/assets): >60% adequate, >75% strong
    # cash_to_liabilities: >5% adequate, >15% strong
    # ocf_ratio: positive is good; >10% strong
    inv_r   = liq.get("investment_ratio")
    cash_l  = liq.get("cash_to_liabilities")
    ocf_r   = liq.get("ocf_ratio")
    liq_score = _avg([
        _interp(inv_r,  0.30, 0.80, 0, 100),
        _interp(cash_l, 0.00, 0.20, 0, 100),
        _interp(ocf_r, -0.05, 0.15, 0, 100),
    ])

    # ── Weighted composite ────────────────────────────────────────────────────
    # Redistribute underwriting weight to profitability when data unavailable
    remaining = 0.30 - uw_weight  # weight freed up from missing underwriting
    weights = {
        "underwriting": (uw_score,   uw_weight),
        "solvency":     (solv_score, 0.25),
        "profitability": (prof_score, 0.25 + remaining),
        "liquidity":    (liq_score,  0.20),
    }

    total_weight = weighted_sum = 0.0
    breakdown = {}
    for cat, (score, w) in weights.items():
        breakdown[cat] = round(score, 1) if score is not None else None
        if score is not None:
            weighted_sum += score * w
            total_weight += w

    raw_score = weighted_sum / total_weight if total_weight > 0 else 0
    final_score = int(_clamp(raw_score))

    if final_score >= 70:
        label, color = "Healthy",  "green"
    elif final_score >= 40:
        label, color = "Caution",  "amber"
    else:
        label, color = "Distress", "red"

    return {
        "score":     final_score,
        "label":     label,
        "color":     color,
        "breakdown": breakdown,
        "beneish_penalty": 0,
    }


def compute_finance_composite_score(fin_ratios: dict) -> dict:
    """Composite health score (0–100) for Finance / NBFI companies.

    Framework basis
    ---------------
    Adapted CAMEL framework for NBFIs as recommended by CARE Ratings "Rating
    Methodology – NBFC" (Oct 2020), IMF NBFI supervision framework, and
    BankBI microfinance KPIs.  Weights reflect that NBFIs are primarily assessed
    on profitability and capital adequacy (no deposit insurance, higher leverage risk).

    Weights (sum to 1.0)
    --------------------
    Profitability   30% — NIM, ROA, ROE, net margin are the primary signals
    Capital/Leverage 25% — D/E, equity ratio (NBFIs leverage up to 6x normally)
    Efficiency      25% — cost-to-income and asset utilisation
    Liquidity       20% — cash ratio and loan-to-assets deployment

    Benchmarks: CARE Ratings NBFC methodology, Sanjay Meena NBFI analysis,
    BankBI microfinance benchmarks, IMF FSAP NBFI indicators.
    """

    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v)) if v is not None else None

    def _interp(v, lo_v, hi_v, lo_s=0.0, hi_s=100.0):
        if v is None or hi_v == lo_v:
            return None
        ratio = (v - lo_v) / (hi_v - lo_v)
        return _clamp(lo_s + ratio * (hi_s - lo_s))

    def _avg(parts):
        valid = [x for x in parts if x is not None]
        return sum(valid) / len(valid) if valid else None

    curr = fin_ratios.get("current", {})
    prof = curr.get("profitability", {})
    eff  = curr.get("efficiency", {})
    lev  = curr.get("leverage", {})
    liq  = curr.get("liquidity", {})

    # ── Profitability (30%) ───────────────────────────────────────────────────
    # NIM: >6% strong for microfinance/ББСБ; 2-4% for securities/investment firms
    #   Use a unified range covering both: 0 → 0, 10% → 100
    # ROA: >1.3% good, >1.6% excellent (CARE Ratings 2020)
    # ROE: >15% good, >20% excellent (CARE Ratings)
    # net_margin: >20% good for NBFIs
    nim = prof.get("nim")
    roa = prof.get("roa")
    roe = prof.get("roe")
    npm = prof.get("net_margin")
    prof_score = _avg([
        _interp(nim, 0,     0.12, 0, 100),
        _interp(roa, 0,     0.03, 0, 100),
        _interp(roe, 0,     0.25, 0, 100),
        _interp(npm, -0.10, 0.35, 0, 100),
    ])

    # ── Capital / Leverage (25%) ──────────────────────────────────────────────
    # debt_to_equity (borrowings-based): <3x strong, 3-6x normal, >8x stretched
    #   NBFIs operate at higher leverage than industrials — 6x is acceptable cap
    # equity_ratio: >15% strong, 10-15% adequate, <8% tight
    d2e      = lev.get("debt_to_equity")
    eq_ratio = lev.get("equity_ratio")
    cap_score = _avg([
        _interp(d2e,      8.0,  1.0,  0, 100),   # inverted: lower D/E = better
        _interp(eq_ratio, 0.05, 0.25, 0, 100),
    ])

    # ── Efficiency (25%) ─────────────────────────────────────────────────────
    # cost_to_income: <40% excellent, 40-60% adequate, >80% poor (CARE Ratings)
    # asset_utilisation (total_income/assets): >8% strong, 4-8% adequate, <2% poor
    cti     = eff.get("cost_to_income")
    asset_u = eff.get("asset_utilisation")
    eff_score = _avg([
        _interp(cti,     0.80, 0.25, 0, 100),   # inverted
        _interp(asset_u, 0.01, 0.12, 0, 100),
    ])

    # ── Liquidity (20%) ──────────────────────────────────────────────────────
    # cash_ratio (cash/liabilities): >5% adequate, >15% strong
    # loan_to_assets: >60% productive deployment; <30% underutilised
    cash_r     = liq.get("cash_ratio")
    loan_to_a  = liq.get("loan_to_assets")
    liq_score = _avg([
        _interp(cash_r,    0.00, 0.20, 0, 100),
        _interp(loan_to_a, 0.10, 0.80, 0, 100),
    ])

    # ── Weighted composite ────────────────────────────────────────────────────
    weights = {
        "profitability": (prof_score, 0.30),
        "capital":       (cap_score,  0.25),
        "efficiency":    (eff_score,  0.25),
        "liquidity":     (liq_score,  0.20),
    }

    total_weight = weighted_sum = 0.0
    breakdown = {}
    for cat, (score, w) in weights.items():
        breakdown[cat] = round(score, 1) if score is not None else None
        if score is not None:
            weighted_sum += score * w
            total_weight += w

    raw_score = weighted_sum / total_weight if total_weight > 0 else 0
    final_score = int(_clamp(raw_score))

    if final_score >= 70:
        label, color = "Healthy",  "green"
    elif final_score >= 40:
        label, color = "Caution",  "amber"
    else:
        label, color = "Distress", "red"

    return {
        "score":     final_score,
        "label":     label,
        "color":     color,
        "breakdown": breakdown,
        "beneish_penalty": 0,
    }


from .labels import RATIO_LABELS  # noqa: F401  (re-exported for convenience)
