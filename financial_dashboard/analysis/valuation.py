"""Valuation ratio computation for MSE Analytica.

Subsector detection drives which metrics are computed and displayed:

  standard        — EV/EBIT, FCF Yield, P/E, P/BV
  commercial_bank — P/E, P/BV, P/TBV, P/PPOP, P/NII
  nbfi            — P/E, P/BV, P/PPOP, P/NII
  holding         — P/E, P/BV (as P/NAV), P/Inv Securities
  securities      — P/E, P/BV, P/Revenue
  insurance       — P/E, P/BV, P/NPE, P/UWP
"""


def _safe_div(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _detect_sector(parsed_data: dict) -> str:
    """Return one of: standard, commercial_bank, nbfi, holding, securities, insurance."""
    if parsed_data.get("insurance_balance_sheet") or parsed_data.get("insurance_income_statement"):
        return "insurance"

    if not (parsed_data.get("bank_balance_sheet") or parsed_data.get("bank_income_statement")):
        return "standard"

    bs  = parsed_data.get("bank_balance_sheet", {}) or {}
    inc = parsed_data.get("bank_income_statement", {}) or {}

    has_nii = inc.get("net_interest_income") is not None
    has_llp = inc.get("loan_loss_provision") is not None

    if has_nii or has_llp:
        return "commercial_bank" if bs.get("total_deposits") is not None else "nbfi"

    # No NII / LLP — distinguish holding vs securities by investment intensity
    inv_sec     = bs.get("investment_securities") or 0
    total_assets = bs.get("total_assets") or 1
    if inv_sec / total_assets > 0.05:
        return "holding"

    return "securities"


def compute_valuation_metrics(
    parsed_data: dict,
    shares_outstanding: int | None,
    last_close_price: float | None,
    reporting_unit_multiplier: int = 1,
) -> dict:
    """Compute valuation ratios.  Returned keys depend on detected sector.

    All sectors:
        sector, market_cap, pe, pbv

    standard only:
        ev, ev_ebitda, fcf_yield

    commercial_bank / nbfi:
        ptbv (bank only), p_ppop, p_nii

    holding:
        p_inv_sec   — Price / Investment Securities

    securities:
        p_revenue   — Price / Total Revenue

    insurance:
        p_npe       — Price / Net Premiums Earned
        p_uwp       — Price / Underwriting Profit
    """
    result = {
        "sector":    "standard",
        "market_cap": None,
        # Standard
        "ev":        None,
        "ev_ebitda": None,
        "fcf":       None,
        "fcf_yield": None,
        # Universal
        "pe":        None,
        "pbv":       None,
        # Bank / NBFI
        "ptbv":      None,
        "p_ppop":    None,
        "p_nii":     None,
        # Holding
        "p_inv_sec": None,
        # Securities
        "p_revenue": None,
        # Insurance
        "p_npe":     None,
        "p_uwp":     None,
    }

    if shares_outstanding is None or last_close_price is None:
        return result

    market_cap = shares_outstanding * last_close_price
    result["market_cap"] = market_cap

    sector = _detect_sector(parsed_data)
    result["sector"] = sector

    balance_sheet = (parsed_data.get("balance_sheet")
                     or parsed_data.get("bank_balance_sheet")
                     or parsed_data.get("insurance_balance_sheet")
                     or {})
    income_statement = (parsed_data.get("income_statement")
                        or parsed_data.get("bank_income_statement")
                        or parsed_data.get("insurance_income_statement")
                        or {})
    cash_flow = parsed_data.get("cash_flow", {}) or {}

    def _scale(v):
        return v * reporting_unit_multiplier if v is not None else None

    # ------------------------------------------------------------------
    # P/E — all sectors (positive net income only)
    # ------------------------------------------------------------------
    net_income = _scale(income_statement.get("net_income"))
    if net_income is not None and net_income > 0:
        result["pe"] = _safe_div(market_cap, net_income)

    # ------------------------------------------------------------------
    # P/BV — all sectors
    # Prefer derived equity when parsed total_equity captured only share
    # capital (< 1/5 of assets-minus-liabilities).
    # ------------------------------------------------------------------
    total_equity     = _scale(balance_sheet.get("total_equity"))
    total_assets     = _scale(balance_sheet.get("total_assets"))
    total_liabilities = _scale(balance_sheet.get("total_liabilities"))

    derived_equity = None
    if total_assets is not None and total_liabilities is not None:
        derived_equity = total_assets - total_liabilities

    if total_equity is None:
        equity_for_pbv = derived_equity
    elif derived_equity is not None and derived_equity > total_equity * 5:
        equity_for_pbv = derived_equity
    else:
        equity_for_pbv = total_equity

    if equity_for_pbv is not None and equity_for_pbv > 0:
        result["pbv"] = _safe_div(market_cap, equity_for_pbv)

    # ------------------------------------------------------------------
    # Standard: EV/EBIT, FCF Yield
    # ------------------------------------------------------------------
    if sector == "standard":
        short_term_loans = _scale(balance_sheet.get("short_term_loans"))
        long_term_loans  = _scale(balance_sheet.get("long_term_loans"))
        cash             = _scale(balance_sheet.get("cash_and_equivalents"))

        total_debt = (short_term_loans or 0) + (long_term_loans or 0)
        ev = market_cap + total_debt - (cash or 0)
        result["ev"] = ev

        profit_before_tax = _scale(income_statement.get("profit_before_tax"))
        financial_expense = _scale(income_statement.get("financial_expense"))

        ebit = None
        if profit_before_tax is not None and financial_expense is not None:
            ebit = profit_before_tax + financial_expense
        elif profit_before_tax is not None:
            ebit = profit_before_tax

        result["ev_ebitda"] = _safe_div(ev, ebit)

        ocf         = _scale(cash_flow.get("operating_cash_flow"))
        investing_cf = _scale(cash_flow.get("investing_cash_flow"))
        if ocf is not None:
            fcf = ocf + investing_cf if investing_cf is not None else ocf
            result["fcf"] = fcf
            result["fcf_yield"] = _safe_div(fcf, market_cap)

    # ------------------------------------------------------------------
    # Commercial bank: P/TBV, P/PPOP, P/NII
    # ------------------------------------------------------------------
    if sector == "commercial_bank":
        intangibles = _scale(balance_sheet.get("intangible_assets"))
        if equity_for_pbv is not None:
            tbv = equity_for_pbv - (intangibles or 0)
            if tbv > 0:
                result["ptbv"] = _safe_div(market_cap, tbv)

        llp = _scale(income_statement.get("loan_loss_provision"))
        if net_income is not None and llp is not None:
            ppop = net_income + llp
            if ppop > 0:
                result["p_ppop"] = _safe_div(market_cap, ppop)

        nii = _scale(income_statement.get("net_interest_income"))
        if nii is not None and nii > 0:
            result["p_nii"] = _safe_div(market_cap, nii)

    # ------------------------------------------------------------------
    # NBFI: P/PPOP, P/NII  (no P/TBV — intangibles negligible)
    # ------------------------------------------------------------------
    if sector == "nbfi":
        llp = _scale(income_statement.get("loan_loss_provision"))
        if net_income is not None and llp is not None:
            ppop = net_income + llp
            if ppop > 0:
                result["p_ppop"] = _safe_div(market_cap, ppop)

        nii = _scale(income_statement.get("net_interest_income"))
        if nii is not None and nii > 0:
            result["p_nii"] = _safe_div(market_cap, nii)

    # ------------------------------------------------------------------
    # Holding company: P/Inv Securities
    # P/BV is relabelled as P/NAV in the UI; no additional computation needed.
    # ------------------------------------------------------------------
    if sector == "holding":
        inv_sec = _scale(balance_sheet.get("investment_securities"))
        if inv_sec is not None and inv_sec > 0:
            result["p_inv_sec"] = _safe_div(market_cap, inv_sec)

    # ------------------------------------------------------------------
    # Securities / Broker-Dealer: P/Revenue
    # ------------------------------------------------------------------
    if sector == "securities":
        total_revenue = _scale(income_statement.get("total_revenue"))
        if total_revenue is not None and total_revenue > 0:
            result["p_revenue"] = _safe_div(market_cap, total_revenue)

    # ------------------------------------------------------------------
    # Insurance: P/NPE, P/UWP
    # ------------------------------------------------------------------
    if sector == "insurance":
        npe = _scale(income_statement.get("net_premiums_earned"))
        if npe is not None and npe > 0:
            result["p_npe"] = _safe_div(market_cap, npe)

        uwp = _scale(income_statement.get("insurance_operating_profit"))
        if uwp is not None and uwp > 0:
            result["p_uwp"] = _safe_div(market_cap, uwp)

    return result
