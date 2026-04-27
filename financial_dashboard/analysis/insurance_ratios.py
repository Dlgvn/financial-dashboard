"""Insurance company financial ratio computation engine.

Insurance companies have a fundamentally different financial structure from
manufacturing or banking companies. They collect premiums upfront, invest
the float, and pay claims later. Their core metrics revolve around:

  - Underwriting profitability (Loss Ratio, Combined Ratio)
  - Investment performance (Investment Yield)
  - Capital adequacy / solvency (Solvency Ratio)
  - Reserve adequacy (Reserve Coverage)

Categories:
  Underwriting (3): Loss Ratio, Expense Ratio, Combined Ratio
  Profitability  (4): ROA, ROE, Net Margin, Investment Income Ratio
  Solvency       (3): Solvency Ratio, Leverage Ratio, Equity to Assets
  Liquidity      (3): Operating CF Ratio, Investment Ratio, Cash to Liabilities
  Growth         (2): Premium Growth, Revenue Growth

NOTE: Many insurance-specific ratios (Loss Ratio, Combined Ratio) require
claims and premium fields that are only captured when the XLS file uses
recognizable Mongolian insurance-specific headers. If those fields are
missing, the ratio returns None and is listed in `missing_fields`.
"""

from .ratios import safe_div


def _get_cash(bs: dict, cf: dict, suffix: str) -> float | None:
    """Get cash — prefer balance sheet, fall back to cash_ending in cash flow.

    Мандал's balance sheet maps cash_and_equivalents to 0.0 (parser issue),
    while the real cash value lives in cash_ending of the cash flow statement.
    """
    cash = bs.get(f"cash_and_equivalents{suffix}")
    if cash is None or cash == 0.0:
        # Fall back to cash_ending (end-of-period cash from cash flow)
        fallback = cf.get(f"cash_ending{suffix}")
        if fallback:
            return fallback
    return cash


def _get_premiums(inc: dict, bs: dict, suffix: str) -> float | None:
    """Get best available premium figure.

    Priority:
      1. net_premiums_earned  (most accurate for ratio computation)
      2. gross_premiums_written (before reinsurance cession)
      3. total_revenue as proxy (when no insurance-specific mapping exists)
    """
    return (
        inc.get(f"net_premiums_earned{suffix}")
        or inc.get(f"gross_premiums_written{suffix}")
        or inc.get(f"total_revenue{suffix}")
    )


def _get_claims(inc: dict, suffix: str) -> float | None:
    """Get best available claims figure.

    Priority:
      1. claims_incurred (direct field)
      2. claims_paid
      3. Derived: total_revenue - all_known_expenses - profit_before_tax
         This works when the income statement has total_revenue and
         admin/selling/financial expenses but no explicit claims line.
    """
    direct = inc.get(f"claims_incurred{suffix}") or inc.get(f"claims_paid{suffix}")
    if direct is not None:
        return direct

    # Derive claims as the residual: revenue - expenses - profit = claims
    revenue = inc.get(f"total_revenue{suffix}")
    pbt = inc.get(f"profit_before_tax{suffix}")
    if revenue is None or pbt is None:
        return None

    known_expenses = sum(
        v for v in [
            inc.get(f"general_and_admin_expenses{suffix}"),
            inc.get(f"selling_expenses{suffix}"),
            inc.get(f"financial_expense{suffix}"),
            inc.get(f"other_expenses{suffix}"),
        ]
        if v is not None
    )
    other_inc = inc.get(f"other_income{suffix}") or 0
    derived = revenue - known_expenses + other_inc - pbt
    return derived if derived > 0 else None


def _get_investments(bs: dict, suffix: str) -> float | None:
    """Get total invested assets."""
    investments = bs.get(f"investments{suffix}")
    if investments:
        return investments
    # Sum components if total not mapped
    components = [
        bs.get(f"investment_securities{suffix}"),
        bs.get(f"bonds{suffix}"),
        bs.get(f"equity_investments{suffix}"),
        bs.get(f"term_deposits{suffix}"),
        # Fallback: other_financial_assets is often where MSE parser puts investments
        bs.get(f"other_financial_assets{suffix}"),
    ]
    available = [v for v in components if v is not None and v > 0]
    return sum(available) if available else None


def compute_insurance_ratios(parsed_data: dict) -> dict:
    """Compute insurance-specific financial ratios from parsed JSON data.

    Args:
        parsed_data: Full parsed dict. May contain keys:
            metadata, balance_sheet OR insurance_balance_sheet,
            income_statement OR insurance_income_statement, cash_flow

    Returns:
        Dict with structure:
        {
            "company": str,
            "is_insurance": True,
            "current": { category: { ratio_name: value, ... }, ... },
            "prev":    { category: { ratio_name: value, ... }, ... },
            "missing_fields": [str, ...],   # fields needed but not in data
            "data_quality": "full" | "partial" | "minimal",
        }
    """
    # Support both insurance-specific and generic sheet keys
    bs  = parsed_data.get("insurance_balance_sheet") or parsed_data.get("balance_sheet", {})
    inc = parsed_data.get("insurance_income_statement") or parsed_data.get("income_statement", {})
    cf  = parsed_data.get("cash_flow", {})
    company = parsed_data.get("metadata", {}).get("company", "Unknown")

    result = {
        "company": company,
        "is_insurance": True,
        "current": {},
        "prev": {},
        "missing_fields": [],
        "data_quality": "minimal",
    }

    for period_suffix, period_key in [("", "current"), ("_prev", "prev")]:

        # ── Extract balance sheet fields ──────────────────────────────────────
        total_assets        = bs.get(f"total_assets{period_suffix}")
        total_liabilities   = bs.get(f"total_liabilities{period_suffix}")
        total_equity        = bs.get(f"total_equity{period_suffix}")
        retained_earnings   = bs.get(f"retained_earnings{period_suffix}")
        cash                = _get_cash(bs, cf, period_suffix)
        insurance_reserves  = bs.get(f"insurance_reserves{period_suffix}")
        unearned_premiums   = (
            bs.get(f"unearned_premium_reserve{period_suffix}")
            or bs.get(f"unearned_revenue{period_suffix}")  # fallback: generic field
        )
        claim_reserves      = (
            bs.get(f"claim_reserves{period_suffix}")
            or insurance_reserves
            or unearned_premiums  # proxy: unearned premiums = future obligations
        )
        premium_receivables = (
            bs.get(f"premium_receivables{period_suffix}")
            or bs.get(f"other_receivables{period_suffix}")
        )
        reinsurance_recv    = bs.get(f"reinsurance_receivables{period_suffix}")
        investments         = _get_investments(bs, period_suffix)

        # Derive equity if missing
        if total_equity is None and total_assets is not None and total_liabilities is not None:
            total_equity = total_assets - total_liabilities

        # ── Extract income statement fields ───────────────────────────────────
        net_income          = inc.get(f"net_income{period_suffix}")
        profit_before_tax   = inc.get(f"profit_before_tax{period_suffix}")
        total_revenue       = inc.get(f"total_revenue{period_suffix}")
        premiums            = _get_premiums(inc, bs, period_suffix)
        claims              = _get_claims(inc, period_suffix)
        # other_income is NOT a valid proxy for investment_income — it includes non-recurring items
        # unrelated to investment returns. Return None when no real investment income line is mapped.
        investment_income   = (
            inc.get(f"investment_income{period_suffix}")
            or inc.get(f"interest_income{period_suffix}")
        )
        commission_expense  = (
            inc.get(f"commission_expense{period_suffix}")
            or inc.get(f"acquisition_costs{period_suffix}")
        )
        admin_expenses      = (
            inc.get(f"admin_expenses{period_suffix}")
            or inc.get(f"general_and_admin_expenses{period_suffix}")
        )
        selling_expenses    = inc.get(f"selling_expenses{period_suffix}")
        change_in_reserves  = inc.get(f"change_in_reserves{period_suffix}")

        # Total underwriting expenses = commissions + admin + selling
        underwriting_expenses = None
        expense_parts = [
            v for v in [commission_expense, admin_expenses, selling_expenses]
            if v is not None
        ]
        if expense_parts:
            underwriting_expenses = sum(expense_parts)

        # ── Cash flow ─────────────────────────────────────────────────────────
        operating_cf = cf.get(f"operating_cash_flow{period_suffix}")

        # ── Track missing critical fields ─────────────────────────────────────
        if period_key == "current":
            if claims is None:
                result["missing_fields"].append("claims_incurred")
            if inc.get("net_premiums_earned") is None and inc.get("gross_premiums_written") is None:
                result["missing_fields"].append("premiums_written_or_earned")
            if investment_income is None:
                result["missing_fields"].append("investment_income")
            if claim_reserves is None:
                result["missing_fields"].append("claim_reserves")

        # ══════════════════════════════════════════════════════════════════════
        # UNDERWRITING RATIOS (core insurance metrics)
        # ══════════════════════════════════════════════════════════════════════
        underwriting = {}

        # 1. Loss Ratio = Claims Incurred / Net Premiums Earned
        #    < 60%: excellent, 60–70%: good, 70–85%: moderate, >85%: poor
        #    > 100%: underwriting loss (claims exceed premiums)
        underwriting["loss_ratio"] = safe_div(claims, premiums)

        # 2. Expense Ratio = Underwriting Expenses / Net Premiums Earned
        #    Target: < 30%. Includes commissions, admin, acquisition costs.
        underwriting["expense_ratio"] = safe_div(underwriting_expenses, premiums)

        # 3. Combined Ratio = Loss Ratio + Expense Ratio
        #    THE most important insurance metric.
        #    < 100%: underwriting profit (company earns from insurance itself)
        #    > 100%: underwriting loss (company relies on investment income)
        lr = underwriting["loss_ratio"]
        er = underwriting["expense_ratio"]
        if lr is not None and er is not None:
            underwriting["combined_ratio"] = lr + er
        else:
            underwriting["combined_ratio"] = None

        # ══════════════════════════════════════════════════════════════════════
        # PROFITABILITY RATIOS
        # ══════════════════════════════════════════════════════════════════════
        profitability = {}

        # 1. ROA = Net Income / Total Assets
        profitability["roa"] = safe_div(net_income, total_assets)

        # 2. ROE = Net Income / Total Equity
        profitability["roe"] = safe_div(net_income, total_equity)

        # 3. Net Profit Margin = Net Income / Total Revenue
        profitability["net_margin"] = safe_div(net_income, total_revenue or premiums)

        # 4. Investment Income Ratio = Investment Income / Total Revenue
        #    High ratio = company heavily depends on investment returns, not underwriting
        profitability["investment_income_ratio"] = safe_div(
            investment_income, total_revenue or premiums
        )

        # 5. Underwriting Profit Margin
        #    = (Premiums - Claims - Underwriting Expenses) / Premiums
        if premiums and claims is not None and underwriting_expenses is not None:
            underwriting_profit = premiums - claims - underwriting_expenses
            profitability["underwriting_margin"] = safe_div(underwriting_profit, premiums)
        else:
            profitability["underwriting_margin"] = None

        # ══════════════════════════════════════════════════════════════════════
        # SOLVENCY RATIOS (insurance regulatory focus)
        # ══════════════════════════════════════════════════════════════════════
        solvency = {}

        # 1. Solvency Ratio = Total Equity / Total Assets
        #    Insurance regulators require this to be sufficiently high.
        #    Target: > 20% (Mongolia Financial Regulatory Commission standard)
        solvency["solvency_ratio"] = safe_div(total_equity, total_assets)

        # 2. Leverage Ratio = Total Liabilities / Total Equity
        #    Lower = more financially stable
        solvency["leverage_ratio"] = safe_div(total_liabilities, total_equity)

        # 3. Equity to Liabilities
        solvency["equity_to_liabilities"] = safe_div(total_equity, total_liabilities)

        # 4. Reserve Coverage = Claim Reserves / Net Premiums Earned
        #    Measures if the company has enough reserves for outstanding claims
        solvency["reserve_coverage"] = safe_div(claim_reserves, premiums)

        # ══════════════════════════════════════════════════════════════════════
        # LIQUIDITY RATIOS
        # ══════════════════════════════════════════════════════════════════════
        liquidity = {}

        # 1. Operating Cash Flow Ratio = Operating CF / Total Liabilities
        liquidity["ocf_ratio"] = safe_div(operating_cf, total_liabilities)

        # 2. Investment Ratio = Investments / Total Assets
        #    Insurance companies invest the premium float — this shows how much
        liquidity["investment_ratio"] = safe_div(investments, total_assets)

        # 3. Cash to Liabilities
        liquidity["cash_to_liabilities"] = safe_div(cash, total_liabilities)

        # 4. Unearned Premium Ratio = Unearned Premiums / Total Revenue
        #    Shows what portion of revenue is still "owed" in future coverage
        liquidity["unearned_premium_ratio"] = safe_div(unearned_premiums, total_revenue or premiums)

        # ══════════════════════════════════════════════════════════════════════
        # GROWTH METRICS (requires both periods)
        # ══════════════════════════════════════════════════════════════════════
        # Growth ratios are computed after both periods in a post-processing step
        # below. Stored as None here, filled in after the loop.
        growth = {
            "premium_growth": None,
            "revenue_growth": None,
        }

        result[period_key] = {
            "underwriting":  underwriting,
            "profitability": profitability,
            "solvency":      solvency,
            "liquidity":     liquidity,
            "growth":        growth,
        }

    # ── Post-loop: compute YoY growth rates ──────────────────────────────────
    curr_premiums = _get_premiums(
        parsed_data.get("insurance_income_statement") or parsed_data.get("income_statement", {}),
        bs, ""
    )
    prev_premiums = _get_premiums(
        parsed_data.get("insurance_income_statement") or parsed_data.get("income_statement", {}),
        bs, "_prev"
    )
    curr_revenue = (
        parsed_data.get("insurance_income_statement", {}).get("total_revenue")
        or parsed_data.get("income_statement", {}).get("total_revenue")
    )
    prev_revenue = (
        parsed_data.get("insurance_income_statement", {}).get("total_revenue_prev")
        or parsed_data.get("income_statement", {}).get("total_revenue_prev")
    )

    if curr_premiums and prev_premiums and prev_premiums != 0:
        growth_val = (curr_premiums - prev_premiums) / abs(prev_premiums)
        result["current"]["growth"]["premium_growth"] = growth_val
        result["prev"]["growth"]["premium_growth"] = None  # growth is always for current vs prev

    if curr_revenue and prev_revenue and prev_revenue != 0:
        revenue_growth = (curr_revenue - prev_revenue) / abs(prev_revenue)
        result["current"]["growth"]["revenue_growth"] = revenue_growth

    # ── Data quality assessment ───────────────────────────────────────────────
    missing_count = len(result["missing_fields"])
    if missing_count == 0:
        result["data_quality"] = "full"
    elif missing_count <= 2:
        result["data_quality"] = "partial"
    else:
        result["data_quality"] = "minimal"

    return result


from .labels import INSURANCE_RATIO_LABELS, INSURANCE_BENCHMARKS  # noqa: F401  (re-exported for convenience)
