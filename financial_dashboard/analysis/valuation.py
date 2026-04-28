"""Valuation ratio computation for MSE Analytica.

Computes 4 market-based valuation ratios:
  - EV/EBITDA
  - FCF Yield
  - P/E (Price-to-Earnings)
  - P/BV (Price-to-Book Value)
"""


def _safe_div(numerator, denominator):
    """Divide numerator by denominator safely.

    Returns None if denominator is None, zero, or numerator is None.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def compute_valuation_metrics(
    parsed_data: dict,
    shares_outstanding: int | None,
    last_close_price: float | None,
) -> dict:
    """Compute 4 valuation ratios from financial data, shares, and price.

    Args:
        parsed_data: The company's financial JSON dict containing balance_sheet,
                     income_statement, and cash_flow sub-dicts.
        shares_outstanding: Total shares outstanding (scraped or manually entered).
                            If None, all market-cap-dependent ratios return None.
        last_close_price: Most recent close price from price JSON records.
                          If None, all ratios return None.

    Returns:
        Dict with keys:
            ev_ebitda (float | None): Enterprise Value / EBITDA ratio
            fcf_yield (float | None): Free Cash Flow Yield (as decimal, e.g. 0.05 = 5%)
            pe (float | None): Price-to-Earnings ratio
            pbv (float | None): Price-to-Book Value ratio
            market_cap (float | None): Market capitalisation
            ev (float | None): Enterprise Value
    """
    result = {
        "ev_ebitda": None,
        "fcf_yield": None,
        "pe": None,
        "pbv": None,
        "market_cap": None,
        "ev": None,
    }

    # Market Cap is the foundation — all ratios require it
    if shares_outstanding is None or last_close_price is None:
        return result

    market_cap = shares_outstanding * last_close_price
    result["market_cap"] = market_cap

    # Extract financial sub-dicts — try sector-specific keys before standard ones
    balance_sheet = (parsed_data.get("balance_sheet")
                     or parsed_data.get("bank_balance_sheet")
                     or parsed_data.get("insurance_balance_sheet")
                     or {})
    income_statement = (parsed_data.get("income_statement")
                        or parsed_data.get("bank_income_statement")
                        or parsed_data.get("insurance_income_statement")
                        or {})
    cash_flow = parsed_data.get("cash_flow", {}) or {}

    # ------------------------------------------------------------------
    # EV/EBITDA (per D-03)
    # ------------------------------------------------------------------
    short_term_loans = balance_sheet.get("short_term_loans")
    long_term_loans = balance_sheet.get("long_term_loans")
    cash = balance_sheet.get("cash_and_equivalents")

    # Total debt: treat None as 0 for each component
    total_debt = (short_term_loans or 0) + (long_term_loans or 0)

    # EV = market_cap + total_debt - cash (cash treated as 0 if None)
    ev = market_cap + total_debt - (cash or 0)
    result["ev"] = ev

    # EBITDA approximation: EBIT = profit_before_tax + financial_expense
    # (no depreciation data available from MSE — same approach as ratios.py)
    profit_before_tax = income_statement.get("profit_before_tax")
    financial_expense = income_statement.get("financial_expense")

    ebitda = None
    if profit_before_tax is not None and financial_expense is not None:
        ebitda = profit_before_tax + financial_expense
    elif profit_before_tax is not None:
        ebitda = profit_before_tax

    result["ev_ebitda"] = _safe_div(ev, ebitda)

    # ------------------------------------------------------------------
    # FCF Yield (per D-02)
    # ------------------------------------------------------------------
    ocf = cash_flow.get("operating_cash_flow")
    capex = cash_flow.get("investing_cash_flow")  # typically negative

    if ocf is not None:
        if capex is not None:
            fcf = ocf - abs(capex)
        else:
            fcf = ocf
        result["fcf_yield"] = _safe_div(fcf, market_cap)

    # ------------------------------------------------------------------
    # P/E (per D-04)
    # ------------------------------------------------------------------
    net_income = income_statement.get("net_income")
    # P/E is only meaningful when net income is positive
    if net_income is not None and net_income > 0:
        result["pe"] = _safe_div(market_cap, net_income)

    # ------------------------------------------------------------------
    # P/BV (per D-04)
    # ------------------------------------------------------------------
    total_equity = balance_sheet.get("total_equity")
    if total_equity is None:
        # Derive from total_assets - total_liabilities if available
        total_assets = balance_sheet.get("total_assets")
        total_liabilities = balance_sheet.get("total_liabilities")
        if total_assets is not None and total_liabilities is not None:
            total_equity = total_assets - total_liabilities

    if total_equity is not None and total_equity > 0:
        result["pbv"] = _safe_div(market_cap, total_equity)

    return result
