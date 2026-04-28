"""Finance / NBFI company financial ratio computation engine.

Research basis
--------------
Finance and Non-Bank Financial Institutions (NBFIs) — lending companies (ББСБ),
securities firms, investment companies, holding companies — have a fundamentally
different financial structure from manufacturing or trading companies:

  Balance sheet
  ─────────────
  • Assets are predominantly FINANCIAL: loan portfolio, investment securities,
    receivables from financial operations.  Inventory and trade receivables are
    minimal or absent.
  • Liabilities are predominantly BORROWINGS: bank loans, bonds issued, commercial
    paper, lines of credit.  There are no trade payables to suppliers.

  Income statement
  ────────────────
  • Revenue concept: NBFIs earn INTEREST INCOME (from loans), FEE/COMMISSION INCOME
    (processing, brokerage), DIVIDEND INCOME, and RENTAL/OTHER INCOME.
    There is NO "revenue" and NO "cost of goods sold" in the manufacturing sense.
  • The equivalent of gross profit is NET INTEREST INCOME (NII):
      NII = Interest Income − Interest Expense (financial_expense)
  • Operating expenses are administrative and selling costs — not COGS.
  • Credit losses (loan loss provisions) are a unique cost specific to lending NBFIs.

  Key ratios that REPLACE standard metrics
  ─────────────────────────────────────────
  Standard metric              │  NBFI equivalent
  ─────────────────────────────┼──────────────────────────────────────────────
  Gross Profit Margin          │  Net Interest Margin (NIM)
  Asset Turnover               │  Asset Utilisation (Total Income / Assets)
  Inventory / DSO / DPO        │  Not applicable — replaced by loan quality metrics
  Current Ratio                │  Less meaningful; use Cash Ratio + D/E instead
  COGS-based ratios            │  Not applicable

Sources
-------
- CARE Ratings: "Ratios – Financial Sector" (2020)
- CARE Ratings: "Rating Methodology – NBFC" (Oct 2020)
- Sanjay Meena: "How to Analyze Banks and NBFCs" (sanjaymeena.io)
- BankBI: "7 Profitability Ratios for Microfinance" (bankbi.com)
- eLearnMarkets: "What to Look For in Banks and NBFCs" (elearnmarkets.com)
- IMF/World Bank NBFI supervision framework
- CFA Institute: Financial Analysis Techniques

Categories
──────────
  Profitability (6): NIM, Yield on Earning Assets, Cost of Funds, ROA, ROE, Net Margin
  Efficiency    (3): Cost-to-Income, Operating Expense Ratio, Non-Interest Income Ratio
  Leverage      (4): Debt-to-Equity (borrowings), Debt-to-Assets, Equity Ratio, Equity Multiplier
  Liquidity     (3): Cash Ratio, Operating CF Ratio, Loan-to-Asset Ratio
  Asset Quality (3): NPA Ratio, Receivables-to-Assets, Provision Coverage
"""

from .ratios import safe_div


# ── Income field helpers ──────────────────────────────────────────────────────

def _get_interest_income(inc: dict, suffix: str) -> float | None:
    """Primary income line for lending NBFIs."""
    return inc.get(f"interest_income{suffix}")


def _get_interest_expense(inc: dict, suffix: str) -> float | None:
    """Cost of funds.

    Standard IS format: financial_expense (sign may be negative — normalise).
    Bank/NBFI format:   interest_expense (always positive in bank IS).
    """
    val = inc.get(f"interest_expense{suffix}")
    if val is None:
        val = inc.get(f"financial_expense{suffix}")
    if val is None:
        return None
    return abs(val)


def _reconstruct_total_income(inc: dict, suffix: str) -> float | None:
    """Reconstruct total income from profit_before_tax + expenses.

    Used as a fallback when direct income component capture is incomplete
    (e.g. securities firms whose primary trading income line is not mapped
    by the parser).  Formula: total_income = profit_before_tax + Σ|expenses|.

    Returns None if profit_before_tax is unavailable or the result is <= 0.
    """
    pbt = inc.get(f"profit_before_tax{suffix}")
    if pbt is None:
        return None
    expense_keys = [
        f"selling_expenses{suffix}",
        f"general_and_admin_expenses{suffix}",
        f"financial_expense{suffix}",
        f"interest_expense{suffix}",
        f"operating_expenses{suffix}",
        f"other_expenses{suffix}",
        f"income_tax_expense{suffix}",
    ]
    total_expenses = sum(abs(inc[k]) for k in expense_keys if inc.get(k))
    reconstructed = pbt + total_expenses
    if reconstructed <= 0:
        return None
    # Guard: if reconstructed income is still < 10% of |net_income|, the IS is too
    # incomplete to produce meaningful margin ratios (e.g. near-zero-income company).
    ni = inc.get(f"net_income{suffix}")
    if ni is not None and reconstructed < abs(ni) * 0.10:
        return None
    return reconstructed


def _get_total_income(inc: dict, suffix: str) -> float | None:
    """Sum of all income sources — the NBFI equivalent of 'revenue'.

    Priority:
      1. Sum of positive income components (interest + fee + dividend + rental + other)
      2. Reconstructed from profit_before_tax + expenses (fallback for securities firms
         whose primary trading/commission income line is not captured by the parser)
    """
    # Explicit income components — include revenue/gross_profit because Finance companies
    # that use standard IS format (e.g. investment firms, holding companies) book their
    # primary income as "Борлуулалтын орлого" which maps to revenue/gross_profit.
    revenue_val = inc.get(f"revenue{suffix}") or inc.get(f"gross_profit{suffix}")
    fee_val     = inc.get(f"fee_income{suffix}")
    comm_val    = inc.get(f"commission_income{suffix}")

    # For securities firms, `revenue` = total operating income (broker fees + underwriting
    # + trading sub-items summed in the IS total row).  fee_income and commission_income
    # are sub-components already included in revenue — exclude them to avoid double-counting.
    # For lending NBFIs, revenue is None and fee/commission are standalone income lines.
    if revenue_val and revenue_val > 0:
        non_dupe_fee  = None
        non_dupe_comm = None
    else:
        non_dupe_fee  = fee_val
        non_dupe_comm = comm_val

    components = [
        revenue_val,
        inc.get(f"interest_income{suffix}"),
        non_dupe_fee,
        non_dupe_comm,
        inc.get(f"dividend_income{suffix}"),
        inc.get(f"rental_income{suffix}"),
        inc.get(f"other_income{suffix}"),
        inc.get(f"foreign_exchange_gain_loss{suffix}"),
        inc.get(f"trading_income{suffix}"),  # securities trading gains, valuation adj, other gains
    ]
    positive = [v for v in components if v is not None and v > 0]

    if not positive:
        return _reconstruct_total_income(inc, suffix)

    total = sum(positive)

    # Safety guard: discard if total captured income < |net_income|.
    # This indicates the parser only caught a fraction of actual income
    # (e.g. securities firms where trading gains are not mapped).
    # Fall back to profit_before_tax reconstruction in that case.
    ni = inc.get(f"net_income{suffix}")
    if ni is not None and total < abs(ni):
        return _reconstruct_total_income(inc, suffix)

    return total


def _get_non_interest_income(inc: dict, suffix: str) -> float | None:
    """Fee, dividend, rental, and other income (excluding pure interest)."""
    components = [
        inc.get(f"fee_income{suffix}"),
        inc.get(f"commission_income{suffix}"),
        inc.get(f"dividend_income{suffix}"),
        inc.get(f"rental_income{suffix}"),
        inc.get(f"other_income{suffix}"),
    ]
    positive = [v for v in components if v is not None and v > 0]
    return sum(positive) if positive else None


def _get_operating_expenses(inc: dict, suffix: str) -> float | None:
    """Admin + selling expenses as total operating cost.

    Standard IS: general_and_admin_expenses + selling_expenses.
    Bank/NBFI IS: operating_expenses (хүүгийн бус зардал) is the direct aggregate.
    """
    # Try direct aggregate first (bank IS format)
    direct = inc.get(f"operating_expenses{suffix}")
    if direct is not None and direct != 0:
        return abs(direct)
    # Fall back to component sum (standard IS format).
    # Some companies store expenses as negative values (sign-flipped from Excel),
    # so use abs() to normalise before summing.
    admin = inc.get(f"general_and_admin_expenses{suffix}")
    if admin is None:
        admin = inc.get(f"admin_expenses{suffix}")
    selling = inc.get(f"selling_expenses{suffix}")
    parts = [abs(v) for v in [admin, selling] if v is not None and v != 0]
    if parts:
        return sum(parts)
    # Derive operating expenses as residual: total_income − profit_before_tax.
    # Applies to firms (e.g. Тандэм Инвэст) where all direct expense fields are
    # 0/None in the parsed data but PBT and total income are both available.
    pbt = inc.get(f"profit_before_tax{suffix}")
    total_inc = _get_total_income(inc, suffix)
    if pbt is not None and total_inc is not None and total_inc > 0:
        derived = total_inc - pbt
        return derived if derived > 0 else None
    return None


def _get_total_borrowings(bs: dict, suffix: str) -> float | None:
    """Total interest-bearing debt (short + long term loans).

    For NBFIs this is the primary liability — they borrow to lend.
    Bank IS format: other_funding (БУСАД ЭХ ҮҮСВЭР) covers bonds + bank loans.
    Standard BS format: short_term_loans + long_term_loans.
    Falls back to total_liabilities if nothing else is available.
    """
    # Bank/NBFI format: other_funding = bonds + borrowings aggregate
    of = bs.get(f"other_funding{suffix}")
    if of is not None and of > 0:
        return of
    # Explicit bank borrowings + bonds issued (investment/securities firms)
    bb = bs.get(f"bank_borrowings{suffix}")
    bi = bs.get(f"bonds_issued{suffix}")
    if bb is not None or bi is not None:
        return (bb or 0) + (bi or 0)
    # Standard format: explicit short + long term loans
    stl = bs.get(f"short_term_loans{suffix}")
    ltl = bs.get(f"long_term_loans{suffix}")
    if stl is not None or ltl is not None:
        return (stl or 0) + (ltl or 0)
    # Last resort: total_liabilities (accurate when liabilities are primarily debt,
    # which holds for most Finance/NBFI companies that lack detailed liability breakdown)
    return bs.get(f"total_liabilities{suffix}")


def _get_loan_portfolio(bs: dict, suffix: str) -> float | None:
    """Proxy for loan portfolio / earning assets from balance sheet.

    Priority:
      1. total_loans / net_loans — direct from bank BS format (ЗЭЭЛ ЦЭВРЭЭР)
      2. loan_portfolio — explicit bank BS field
      3. accounts_receivable / other_receivables / other_financial_assets — standard BS proxy
    """
    # Bank BS format: explicit loan totals
    for key in (f"total_loans{suffix}", f"net_loans{suffix}", f"loan_portfolio{suffix}"):
        val = bs.get(key)
        if val is not None and val > 0:
            return val
    # Securities/investment firm proxy: investment_securities is the primary earning asset
    # for broker-dealers and investment companies (analogous to loan portfolio for lenders).
    # Checked BEFORE receivables so Бидисек's 28B securities portfolio isn't overridden
    # by the smaller other_receivables (3B) entry.  Banks reach this point only when
    # total_loans is 0; they also carry investment_securities, so this still works.
    inv_sec = bs.get(f"investment_securities{suffix}")
    if inv_sec is not None and inv_sec > 0:
        oth_fin = bs.get(f"other_financial_assets{suffix}") or 0
        return inv_sec + (oth_fin if oth_fin > 0 else 0)

    # Standard BS proxy: largest financial receivable (lending NBFIs without explicit loan fields)
    candidates = [
        bs.get(f"accounts_receivable{suffix}"),
        bs.get(f"other_receivables{suffix}"),
        bs.get(f"other_financial_assets{suffix}"),
        bs.get(f"long_term_investments{suffix}"),
    ]
    valid = [v for v in candidates if v is not None and v > 0]
    return max(valid) if valid else None


# ── Main computation function ─────────────────────────────────────────────────

def compute_finance_ratios(parsed_data: dict) -> dict:
    """Compute Finance / NBFI specific financial ratios from parsed JSON data.

    Args:
        parsed_data: Full parsed dict. Expected keys:
            metadata, balance_sheet, income_statement, cash_flow

    Returns:
        {
            "company":      str,
            "is_finance":   True,
            "current":      { category: { ratio_name: value, ... }, ... },
            "prev":         { category: { ratio_name: value, ... }, ... },
            "missing_fields": [str, ...],
            "data_quality": "full" | "partial" | "minimal",
        }

    Ratio categories
    ─────────────────
    profitability:  nim, yield_on_earning_assets, cost_of_funds, interest_spread,
                    roa, roe, net_margin
    efficiency:     cost_to_income, operating_expense_ratio, non_interest_income_ratio,
                    asset_utilisation
    leverage:       debt_to_equity, debt_to_assets, equity_ratio, equity_multiplier
    liquidity:      cash_ratio, ocf_ratio, loan_to_assets
    asset_quality:  npa_ratio, receivables_to_assets, provision_coverage
    """
    bs  = (
        parsed_data.get("bank_balance_sheet")
        or parsed_data.get("securities_balance_sheet")
        or parsed_data.get("balance_sheet", {})
    )
    inc = (
        parsed_data.get("bank_income_statement")
        or parsed_data.get("securities_income_statement")
        or parsed_data.get("income_statement", {})
    )
    cf  = parsed_data.get("cash_flow", {})
    company = parsed_data.get("metadata", {}).get("company", "Unknown")

    result = {
        "company":        company,
        "is_finance":     True,
        "current":        {},
        "prev":           {},
        "missing_fields": [],
        "data_quality":   "minimal",
    }

    for period_suffix, period_key in [("", "current"), ("_prev", "prev")]:

        # ── Balance sheet extracts ────────────────────────────────────────────
        total_assets      = bs.get(f"total_assets{period_suffix}")
        total_liabilities = bs.get(f"total_liabilities{period_suffix}")
        total_equity      = bs.get(f"total_equity{period_suffix}")
        retained_earnings = bs.get(f"retained_earnings{period_suffix}")
        # Cash: vault cash + interbank placements. total_deposits is a customer
        # deposit liability in BANK_BALANCE_SHEET_HEADERS — must NOT be included here.
        _cash_vault_raw = bs.get(f"cash_and_equivalents{period_suffix}")
        _cash_ibk_raw   = bs.get(f"interbank_placements{period_suffix}")
        _cash_vault = _cash_vault_raw if _cash_vault_raw is not None else 0
        _cash_ibk   = _cash_ibk_raw   if _cash_ibk_raw   is not None else 0
        _cash_sum = _cash_vault + _cash_ibk
        cash = _cash_sum if (_cash_vault_raw is not None or _cash_ibk_raw is not None) else None
        total_borrowings  = _get_total_borrowings(bs, period_suffix)
        loan_portfolio    = _get_loan_portfolio(bs, period_suffix)

        # Derive equity from assets - liabilities when not directly available
        if (total_equity is None or total_equity == 0) and total_assets is not None and total_liabilities is not None:
            computed = total_assets - total_liabilities
            if total_equity is None or computed != 0:
                total_equity = computed
        elif total_equity is not None and total_assets is not None and total_liabilities is not None and total_assets > 0:
            derived = total_assets - total_liabilities
            if derived != 0:
                sign_mismatch = (total_equity >= 0) != (derived >= 0)
                sub_line_capture = (
                    abs(total_equity) < abs(derived) * 0.8
                    and abs(total_equity - derived) / total_assets > 0.05
                )
                if sign_mismatch or sub_line_capture:
                    total_equity = derived

        # For NBFIs, "earning assets" is the loan portfolio; fall back to total_assets
        earning_assets = loan_portfolio or total_assets

        # ── Income statement extracts ─────────────────────────────────────────
        interest_income    = _get_interest_income(inc, period_suffix)
        interest_expense   = _get_interest_expense(inc, period_suffix)
        total_income       = _get_total_income(inc, period_suffix)
        non_interest_income = _get_non_interest_income(inc, period_suffix)
        operating_expenses = _get_operating_expenses(inc, period_suffix)
        net_income         = inc.get(f"net_income{period_suffix}")
        profit_before_tax  = inc.get(f"profit_before_tax{period_suffix}")
        income_tax_expense = inc.get(f"income_tax_expense{period_suffix}")
        profit_after_tax   = inc.get(f"profit_after_tax{period_suffix}")
        # Fallback: net_income may be 0.0 from a section-header parse artefact.
        if (net_income is None or net_income == 0) and profit_after_tax:
            net_income = profit_after_tax
        elif (net_income is None or net_income == 0) and profit_before_tax is not None and income_tax_expense is not None:
            net_income = profit_before_tax - income_tax_expense
        elif (net_income is None or net_income == 0) and profit_before_tax:
            net_income = profit_before_tax

        # Net Interest Income (NBFI's equivalent of Gross Profit)
        nii = None
        if interest_income is not None and interest_expense is not None:
            nii = interest_income - interest_expense
        elif interest_income is not None:
            nii = interest_income  # no funding cost captured — use gross interest

        # ── Cash flow ─────────────────────────────────────────────────────────
        # Standard CF: operating_cash_flow; Bank/NBFI CF: operating_activities_section
        operating_cf = (
            cf.get(f"operating_cash_flow{period_suffix}")
            or cf.get(f"operating_activities_section{period_suffix}")
        )

        # ── Track missing critical fields ─────────────────────────────────────
        if period_key == "current":
            if interest_income is None:
                result["missing_fields"].append("interest_income")
            if total_income is None:
                result["missing_fields"].append("total_income")
            if total_borrowings is None:
                result["missing_fields"].append("total_borrowings")
            if loan_portfolio is None:
                result["missing_fields"].append("loan_portfolio")

        # ══════════════════════════════════════════════════════════════════════
        # PROFITABILITY RATIOS
        # ══════════════════════════════════════════════════════════════════════
        # These replace the standard gross/operating/net margin ratios which
        # are meaningless for NBFIs (no revenue / COGS structure).
        profitability = {}

        # 1. Net Interest Margin (NIM) — the NBFI equivalent of Gross Margin.
        #    Measures how much the NBFI earns on its lending/investing activities
        #    above its cost of funds, per unit of earning assets.
        #    Formula: (Interest Income - Interest Expense) / Earning Assets
        #    Benchmark: 2.75–4.25% for large NBFIs; 6–15% for microfinance (CARE Ratings 2020)
        profitability["nim"] = safe_div(nii, earning_assets)

        # 2. Yield on Earning Assets — average rate earned on loans/investments.
        #    Formula: Interest Income / Earning Assets
        #    High yield indicates riskier borrower mix or higher pricing power.
        profitability["yield_on_earning_assets"] = safe_div(interest_income, earning_assets)

        # 3. Cost of Funds — average rate paid on borrowings.
        #    Formula: Interest Expense / Total Borrowings (or Total Liabilities as fallback)
        #    Lower is better — reflects funding efficiency and credit quality of the NBFI itself.
        profitability["cost_of_funds"] = safe_div(
            interest_expense,
            total_borrowings or total_liabilities
        )

        # 4. Interest Spread — difference between yield earned and cost paid.
        #    Formula: Yield on Earning Assets − Cost of Funds
        #    Positive spread is fundamental to NBFI profitability.
        yea = profitability["yield_on_earning_assets"]
        cof = profitability["cost_of_funds"]
        profitability["interest_spread"] = (yea - cof) if (yea is not None and cof is not None) else None

        # 5. Return on Assets (ROA) — net income per unit of total assets.
        #    Formula: Net Income / Total Assets
        #    Benchmark: >1.3% good, >1.6% excellent (CARE Ratings, Sanjay Meena)
        profitability["roa"] = safe_div(net_income, total_assets)

        # 6. Return on Equity (ROE) — return earned on shareholder capital.
        #    Formula: Net Income / Total Equity
        #    Benchmark: >15% considered good for NBFIs; >20% excellent (CARE Ratings)
        profitability["roe"] = safe_div(net_income, total_equity)

        # 7. Net Profit Margin — net income as fraction of total income.
        #    Uses TOTAL INCOME (all income sources), not "revenue" — because
        #    NBFIs earn from multiple streams (interest + fees + dividends).
        #    Formula: Net Income / Total Income
        profitability["net_margin"] = safe_div(net_income, total_income)

        # ══════════════════════════════════════════════════════════════════════
        # EFFICIENCY RATIOS
        # ══════════════════════════════════════════════════════════════════════
        efficiency = {}

        # 1. Cost-to-Income Ratio — operating costs per unit of income generated.
        #    This is the primary efficiency metric for ALL financial companies.
        #    Formula: Operating Expenses / (NII + Non-Interest Income)
        #    Benchmark: <50% good, <40% excellent (CARE Ratings 2020)
        #    NOTE: lower is better — a high ratio means excessive cost structure.
        income_base = None
        if nii is not None and nii > 0 and non_interest_income is not None:
            income_base = nii + non_interest_income
        elif nii is not None and nii > 0:
            income_base = nii
        elif total_income is not None:
            income_base = total_income

        efficiency["cost_to_income"] = safe_div(operating_expenses, income_base)

        # 2. Operating Expense Ratio — operating costs relative to total assets.
        #    Formula: Operating Expenses / Total Assets
        #    Shows administrative burden per unit of deployed assets.
        efficiency["operating_expense_ratio"] = safe_div(operating_expenses, total_assets)

        # 3. Non-Interest Income Ratio — diversification of income sources.
        #    Formula: Non-Interest Income / Total Income
        #    Higher ratio means the NBFI is less dependent on spread income alone.
        efficiency["non_interest_income_ratio"] = safe_div(non_interest_income, total_income)

        # 4. Asset Utilisation — total income generated per unit of assets.
        #    This replaces the standard "Asset Turnover" ratio (Revenue / Assets),
        #    which cannot be applied to NBFIs because they have no product revenue.
        #    Formula: Total Income / Total Assets
        efficiency["asset_utilisation"] = safe_div(total_income, total_assets)

        # ══════════════════════════════════════════════════════════════════════
        # LEVERAGE & CAPITAL RATIOS
        # ══════════════════════════════════════════════════════════════════════
        # NBFIs are inherently leveraged (they borrow to lend). D/E of 3–7x is
        # normal; this is very different from manufacturing companies where >2x is
        # already considered high. Ratios use BORROWINGS (not total liabilities)
        # as the numerator — trade payables are not material for NBFIs.
        leverage = {}

        # 1. Debt-to-Equity (borrowings-based) — financial leverage from debt funding.
        #    Formula: Total Borrowings / Total Equity
        #    Benchmark: <6x for NBFIs (regulatory guidance in many markets)
        #    IMPORTANT: this uses borrowings only, not all liabilities, because
        #    total liabilities for an NBFI includes many non-debt items.
        leverage["debt_to_equity"] = safe_div(total_borrowings, total_equity)

        # 2. Debt-to-Assets (borrowings-based) — proportion of assets funded by debt.
        #    Formula: Total Borrowings / Total Assets
        leverage["debt_to_assets"] = safe_div(total_borrowings, total_assets)

        # 3. Equity Ratio — proportion of assets funded by equity (financial strength).
        #    Formula: Total Equity / Total Assets
        #    Benchmark: >10% provides reasonable buffer for NBFIs
        leverage["equity_ratio"] = safe_div(total_equity, total_assets)

        # 4. Equity Multiplier — financial leverage (total assets per unit of equity).
        #    Formula: Total Assets / Total Equity
        #    Inverse of equity ratio; shows how many assets are supported by 1 unit of equity.
        leverage["equity_multiplier"] = safe_div(total_assets, total_equity)

        # ══════════════════════════════════════════════════════════════════════
        # LIQUIDITY RATIOS
        # ══════════════════════════════════════════════════════════════════════
        # Current ratio and quick ratio are not meaningful for NBFIs because
        # their "current liabilities" are primarily short-term borrowings (not
        # trade obligations), and their "current assets" include the loan book
        # which is not truly liquid. Use cash-based and flow-based measures instead.
        liquidity = {}

        # 1. Cash Ratio — immediate liquidity relative to total liabilities.
        #    Formula: Cash & Equivalents / Total Liabilities
        #    For NBFIs, total liabilities (mostly borrowings) is the relevant denominator.
        liquidity["cash_ratio"] = safe_div(cash, total_liabilities)

        # 2. Operating Cash Flow Ratio — cash generated from operations vs liabilities.
        #    Formula: Operating Cash Flow / Total Liabilities
        liquidity["ocf_ratio"] = safe_div(operating_cf, total_liabilities)

        # 3. Loan-to-Asset Ratio — proportion of assets deployed as earning loans.
        #    Formula: Loan Portfolio / Total Assets
        #    Higher ratio = more productive deployment of assets into core business.
        #    Benchmark: >60% for mature lending NBFIs
        liquidity["loan_to_assets"] = safe_div(loan_portfolio, total_assets)

        # ══════════════════════════════════════════════════════════════════════
        # ASSET QUALITY RATIOS
        # ══════════════════════════════════════════════════════════════════════
        # These are unique to lending NBFIs and have no equivalent in standard
        # corporate financial analysis. MSE parsed data does not contain explicit
        # NPA fields for non-bank Finance companies (those are in bank_balance_sheet
        # only). These ratios will be None for most companies until the parser
        # is extended to capture NBFI-specific balance sheet fields.
        asset_quality = {}

        # 1. NPA Ratio — share of loan portfolio that is non-performing.
        #    Formula: Non-Performing Loans / Total Loan Portfolio
        #    Benchmark: <2% excellent, 2–5% moderate, >5% concerning
        npl = bs.get(f"non_performing_loans{period_suffix}")
        asset_quality["npa_ratio"] = safe_div(npl, loan_portfolio)

        # 2. Receivables-to-Assets — financial receivables as share of total assets.
        #    Proxy for the proportion of assets in lending/investment activities.
        #    Formula: Loan Portfolio (proxy) / Total Assets
        asset_quality["receivables_to_assets"] = safe_div(loan_portfolio, total_assets)

        # 3. Provision Coverage — loan loss reserves relative to non-performing loans.
        #    Formula: Loan Loss Reserves / Non-Performing Loans
        #    Benchmark: >70% (regulatory minimum in most markets)
        llr = bs.get(f"loan_loss_reserves{period_suffix}")
        asset_quality["provision_coverage"] = safe_div(llr, npl)

        result[period_key] = {
            "profitability": profitability,
            "efficiency":    efficiency,
            "leverage":      leverage,
            "liquidity":     liquidity,
            "asset_quality": asset_quality,
        }

    # ── Data quality assessment ───────────────────────────────────────────────
    missing_count = len(result["missing_fields"])
    if missing_count == 0:
        result["data_quality"] = "full"
    elif missing_count <= 2:
        result["data_quality"] = "partial"
    else:
        result["data_quality"] = "minimal"

    return result


from .labels import FINANCE_RATIO_LABELS, FINANCE_BENCHMARKS  # noqa: F401
