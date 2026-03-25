"""Bank financial ratio computation engine.

Computes bank-specific ratios organized into categories:
  Profitability (5): NIM, ROA, ROE, Net Margin, Cost-to-Income
  Capital Adequacy (4): CAR, Tier1 Ratio, Equity Multiplier, Equity/Assets
  Asset Quality (4): NPL Ratio, Coverage Ratio, Loan Loss Reserve Ratio, Net Charge-off Ratio
  Liquidity (4): LDR, Cash-to-Deposits, LCR, Loans-to-Assets
  Efficiency (2): Cost-to-Income, Non-Interest Income Ratio
"""

from .ratios import safe_div


def compute_bank_ratios(parsed_data: dict) -> dict:
    """Compute bank-specific financial ratios from parsed JSON data.

    Args:
        parsed_data: Full parsed dict. May contain keys:
            metadata, balance_sheet OR bank_balance_sheet,
            income_statement OR bank_income_statement, cash_flow

    Returns:
        Dict with structure:
        {
            "company": str,
            "is_bank": True,
            "current": { category: { ratio_name: value, ... }, ... },
            "prev": { category: { ratio_name: value, ... }, ... },
        }
    """
    # Support both regular sheet keys and bank-specific sheet keys
    bs = parsed_data.get("bank_balance_sheet") or parsed_data.get("balance_sheet", {})
    inc = parsed_data.get("bank_income_statement") or parsed_data.get("income_statement", {})
    company = parsed_data.get("metadata", {}).get("company", "Unknown")

    result = {
        "company": company,
        "is_bank": True,
        "current": {},
        "prev": {},
    }

    for period_suffix, period_key in [("", "current"), ("_prev", "prev")]:

        # ── Balance sheet fields ──────────────────────────────────────────
        total_assets       = bs.get(f"total_assets{period_suffix}")
        total_liabilities  = bs.get(f"total_liabilities{period_suffix}")
        total_equity       = bs.get(f"total_equity{period_suffix}")
        cash               = bs.get(f"cash_and_equivalents{period_suffix}")
        total_loans        = bs.get(f"total_loans{period_suffix}")
        total_deposits     = bs.get(f"total_deposits{period_suffix}")
        loan_loss_reserves = bs.get(f"loan_loss_reserves{period_suffix}")
        non_performing_loans = bs.get(f"non_performing_loans{period_suffix}")
        investment_sec     = bs.get(f"investment_securities{period_suffix}")
        tier1_capital      = bs.get(f"tier1_capital{period_suffix}")
        tier2_capital      = bs.get(f"tier2_capital{period_suffix}")
        risk_weighted_assets = bs.get(f"risk_weighted_assets{period_suffix}")
        retained_earnings  = bs.get(f"retained_earnings{period_suffix}")

        # Derive equity if missing
        if total_equity is None and total_assets is not None and total_liabilities is not None:
            total_equity = total_assets - total_liabilities

        # ── Income statement fields ───────────────────────────────────────
        interest_income    = inc.get(f"interest_income{period_suffix}")
        interest_expense   = inc.get(f"interest_expense{period_suffix}")
        net_interest_income = inc.get(f"net_interest_income{period_suffix}")
        fee_income         = inc.get(f"fee_income{period_suffix}")
        fee_expense        = inc.get(f"fee_expense{period_suffix}")
        loan_loss_provision = inc.get(f"loan_loss_provision{period_suffix}")
        admin_expenses     = inc.get(f"admin_expenses{period_suffix}")
        operating_expenses = inc.get(f"operating_expenses{period_suffix}")
        net_income         = inc.get(f"net_income{period_suffix}")
        total_revenue      = inc.get(f"total_revenue{period_suffix}")

        # Derive net interest income if not directly available
        if net_interest_income is None and interest_income is not None and interest_expense is not None:
            net_interest_income = interest_income - interest_expense

        # Earning assets = total loans + investment securities (proxy)
        earning_assets = None
        if total_loans is not None and investment_sec is not None:
            earning_assets = total_loans + investment_sec
        elif total_loans is not None:
            earning_assets = total_loans

        # Operating income for efficiency = net interest income + fee income + other
        operating_income = None
        if net_interest_income is not None and fee_income is not None:
            operating_income = net_interest_income + fee_income
        elif net_interest_income is not None:
            operating_income = net_interest_income

        # Total opex proxy
        total_opex = operating_expenses or admin_expenses

        # ── Profitability ─────────────────────────────────────────────────
        profitability = {}

        # 1. Net Interest Margin = Net Interest Income / Earning Assets
        profitability["nim"] = safe_div(net_interest_income, earning_assets)

        # 2. ROA = Net Income / Total Assets
        profitability["roa"] = safe_div(net_income, total_assets)

        # 3. ROE = Net Income / Total Equity
        profitability["roe"] = safe_div(net_income, total_equity)

        # 4. Net Profit Margin = Net Income / Total Revenue
        profitability["net_margin"] = safe_div(net_income, total_revenue or operating_income)

        # 5. Interest Income to Total Revenue
        profitability["interest_income_ratio"] = safe_div(interest_income, total_revenue or operating_income)

        # ── Capital Adequacy ──────────────────────────────────────────────
        capital = {}

        # 1. CAR = (Tier1 + Tier2) / Risk-Weighted Assets
        if tier1_capital is not None and tier2_capital is not None and risk_weighted_assets is not None:
            capital["car"] = safe_div(tier1_capital + tier2_capital, risk_weighted_assets)
        else:
            capital["car"] = None

        # 2. Tier 1 Capital Ratio
        capital["tier1_ratio"] = safe_div(tier1_capital, risk_weighted_assets)

        # 3. Equity Multiplier = Total Assets / Total Equity
        capital["equity_multiplier"] = safe_div(total_assets, total_equity)

        # 4. Equity to Assets
        capital["equity_to_assets"] = safe_div(total_equity, total_assets)

        # ── Asset Quality ─────────────────────────────────────────────────
        asset_quality = {}

        # 1. NPL Ratio = Non-Performing Loans / Total Loans
        asset_quality["npl_ratio"] = safe_div(non_performing_loans, total_loans)

        # 2. Coverage Ratio = Loan Loss Reserves / Non-Performing Loans
        asset_quality["coverage_ratio"] = safe_div(loan_loss_reserves, non_performing_loans)

        # 3. Loan Loss Reserve Ratio = Loan Loss Reserves / Total Loans
        asset_quality["loan_loss_reserve_ratio"] = safe_div(loan_loss_reserves, total_loans)

        # 4. Provision to Loans = Loan Loss Provision (expense) / Total Loans
        asset_quality["provision_to_loans"] = safe_div(loan_loss_provision, total_loans)

        # ── Liquidity ─────────────────────────────────────────────────────
        liquidity = {}

        # 1. Loan-to-Deposit Ratio (LDR)
        liquidity["ldr"] = safe_div(total_loans, total_deposits)

        # 2. Cash to Deposits
        liquidity["cash_to_deposits"] = safe_div(cash, total_deposits)

        # 3. Loans to Total Assets
        liquidity["loans_to_assets"] = safe_div(total_loans, total_assets)

        # 4. Securities to Total Assets
        liquidity["securities_to_assets"] = safe_div(investment_sec, total_assets)

        # ── Efficiency ────────────────────────────────────────────────────
        efficiency = {}

        # 1. Cost-to-Income = Operating Expenses / Operating Income
        efficiency["cost_to_income"] = safe_div(total_opex, operating_income)

        # 2. Non-Interest Income Ratio = Fee Income / Operating Income
        efficiency["fee_income_ratio"] = safe_div(fee_income, operating_income)

        result[period_key] = {
            "profitability": profitability,
            "capital_adequacy": capital,
            "asset_quality": asset_quality,
            "liquidity": liquidity,
            "efficiency": efficiency,
        }

    return result


from .labels import BANK_RATIO_LABELS, BANK_BENCHMARKS  # noqa: F401  (re-exported for convenience)
