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
        other_fin_assets   = bs.get(f"other_financial_assets{period_suffix}")
        retained_earnings  = bs.get(f"retained_earnings{period_suffix}")
        # Bank-specific fields (present when parser maps them explicitly)
        total_loans        = bs.get(f"total_loans{period_suffix}")
        total_deposits     = bs.get(f"total_deposits{period_suffix}")
        loan_loss_reserves = bs.get(f"loan_loss_reserves{period_suffix}")
        non_performing_loans = bs.get(f"non_performing_loans{period_suffix}")
        investment_sec     = bs.get(f"investment_securities{period_suffix}") or other_fin_assets
        tier1_capital      = bs.get(f"tier1_capital{period_suffix}")
        tier2_capital      = bs.get(f"tier2_capital{period_suffix}")
        risk_weighted_assets = bs.get(f"risk_weighted_assets{period_suffix}")

        # Derive equity if missing
        if total_equity is None and total_assets is not None and total_liabilities is not None:
            total_equity = total_assets - total_liabilities

        # ── Income statement fields ───────────────────────────────────────
        net_income         = inc.get(f"net_income{period_suffix}")
        profit_before_tax  = inc.get(f"profit_before_tax{period_suffix}")
        income_tax         = inc.get(f"income_tax_expense{period_suffix}")
        other_income       = inc.get(f"other_income{period_suffix}")
        other_expenses     = inc.get(f"other_expenses{period_suffix}")
        # Bank-specific fields (present when parser maps them explicitly)
        interest_income    = inc.get(f"interest_income{period_suffix}")
        interest_expense   = inc.get(f"interest_expense{period_suffix}")
        net_interest_income = inc.get(f"net_interest_income{period_suffix}")
        fee_income         = inc.get(f"fee_income{period_suffix}")
        loan_loss_provision = inc.get(f"loan_loss_provision{period_suffix}")
        admin_expenses     = inc.get(f"admin_expenses{period_suffix}")
        operating_expenses = inc.get(f"operating_expenses{period_suffix}")
        total_revenue      = inc.get(f"total_revenue{period_suffix}")

        # ── Cash flow fields ──────────────────────────────────────────────
        cf = parsed_data.get("cash_flow", {})
        operating_cf = cf.get(f"operating_cash_flow{period_suffix}")

        # Derive net interest income if not directly available
        if net_interest_income is None and interest_income is not None and interest_expense is not None:
            net_interest_income = interest_income - interest_expense

        # Net banking income proxy: profit before tax minus secondary other_income + secondary other_expenses
        # This represents the core banking operations result before non-recurring items
        net_banking_income = None
        if profit_before_tax is not None:
            adj_other_income = other_income or 0
            adj_other_expenses = other_expenses or 0
            net_banking_income = profit_before_tax - adj_other_income + adj_other_expenses

        # Earning assets = total loans + investment securities (or proxy)
        earning_assets = None
        if total_loans is not None and investment_sec is not None:
            earning_assets = total_loans + investment_sec
        elif total_loans is not None:
            earning_assets = total_loans
        elif total_assets is not None:
            earning_assets = total_assets  # fallback: use total assets

        # Operating income for efficiency
        operating_income = None
        if net_interest_income is not None and fee_income is not None:
            operating_income = net_interest_income + fee_income
        elif net_interest_income is not None:
            operating_income = net_interest_income
        elif net_banking_income is not None:
            operating_income = net_banking_income

        # Total opex proxy
        total_opex = operating_expenses or admin_expenses or other_expenses

        # ── Profitability ─────────────────────────────────────────────────
        profitability = {}

        # 1. Net Interest Margin = Net Interest Income / Earning Assets
        #    Proxy when interest income not available: net banking income / total assets
        if net_interest_income is not None and earning_assets is not None:
            profitability["nim"] = safe_div(net_interest_income, earning_assets)
        elif net_banking_income is not None and total_assets is not None:
            profitability["nim"] = safe_div(net_banking_income, total_assets)
        else:
            profitability["nim"] = None

        # 2. ROA = Net Income / Total Assets
        profitability["roa"] = safe_div(net_income, total_assets)

        # 3. ROE = Net Income / Total Equity
        profitability["roe"] = safe_div(net_income, total_equity)

        # 4. Net Profit Margin = Net Income / Total Revenue (or net banking income proxy)
        profitability["net_margin"] = safe_div(
            net_income,
            total_revenue or operating_income or net_banking_income
        )

        # 5. Interest Income to Total Revenue (or operating income proxy)
        profitability["interest_income_ratio"] = safe_div(
            interest_income or net_interest_income or net_banking_income,
            total_revenue or operating_income or net_banking_income
        )

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

        # 2. Cash to Deposits (falls back to cash / total liabilities when deposits unavailable)
        liquidity["cash_to_deposits"] = safe_div(cash, total_deposits or total_liabilities)

        # 3. Loans to Total Assets (falls back to financial assets / total assets)
        liquidity["loans_to_assets"] = safe_div(total_loans or other_fin_assets, total_assets)

        # 4. Securities to Total Assets
        liquidity["securities_to_assets"] = safe_div(investment_sec, total_assets)

        # ── Efficiency ────────────────────────────────────────────────────
        efficiency = {}

        # 1. Cost-to-Income = Operating Expenses / Operating Income
        efficiency["cost_to_income"] = safe_div(total_opex, operating_income)

        # 2. Non-Interest Income / Operating Income
        efficiency["fee_income_ratio"] = safe_div(
            fee_income or other_income,
            operating_income or net_banking_income
        )

        result[period_key] = {
            "profitability": profitability,
            "capital_adequacy": capital,
            "asset_quality": asset_quality,
            "liquidity": liquidity,
            "efficiency": efficiency,
        }

    return result


from .labels import BANK_RATIO_LABELS, BANK_BENCHMARKS  # noqa: F401  (re-exported for convenience)
