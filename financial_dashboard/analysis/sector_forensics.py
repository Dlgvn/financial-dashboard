"""Sector-specific forensic scoring for Banking, Insurance, and Finance companies.

Replaces Piotroski F-Score + Beneish M-Score (designed for manufacturing) with
rule-based criteria derived from sector-appropriate ratios and YoY trends.

Each compute function returns:
{
    "score":      int,            # criteria passed
    "max_score":  int,            # applicable criteria
    "criteria":   list[dict],     # [{label, pass (1/0/-1), explanation}]
    "chart_data": list[dict],     # [{metric, change, fill}] for YoY bar chart
}
"""


def _pass(condition: bool) -> int:
    return 1 if condition else 0


def _pct(v: float | None) -> str:
    return f"{v * 100:.2f}%" if v is not None else "N/A"


def _x(v: float | None) -> str:
    return f"{v:.2f}x" if v is not None else "N/A"


def _yoy_bar(metric: str, curr: float | None, prev: float | None, lower_is_better: bool = False) -> dict | None:
    """Build a YoY change bar chart entry. Returns None if data is missing."""
    if curr is None or prev is None or prev == 0:
        return None
    change = (curr - prev) / abs(prev)
    good = change < 0 if lower_is_better else change > 0
    return {
        "metric": metric,
        "change": round(change * 100, 2),
        "fill": "#4ade80" if good else "#f87171",
    }


# ── Banking ───────────────────────────────────────────────────────────────────

def compute_bank_forensic(bank_result: dict) -> dict:
    """8-point forensic scoring for banking companies."""
    curr = bank_result.get("current", {})
    prev = bank_result.get("prev", {})

    cp = curr.get("profitability", {})
    pp = prev.get("profitability", {})
    ca = curr.get("asset_quality", {})
    pa = prev.get("asset_quality", {})
    cl = curr.get("liquidity", {})
    ce = curr.get("efficiency", {})
    pe = prev.get("efficiency", {})
    ck = curr.get("capital_adequacy", {})
    pk = prev.get("capital_adequacy", {})

    criteria = []
    score = 0
    max_score = 0

    # B1: ROA Positive
    roa = cp.get("roa")
    if roa is not None:
        max_score += 1
        p = _pass(roa > 0)
        score += p
        criteria.append({"label": "ROA Positive", "pass": p, "explanation": f"ROA: {_pct(roa)}"})
    else:
        criteria.append({"label": "ROA Positive", "pass": -1, "explanation": "Data unavailable"})

    # B2: ROA Improving YoY
    prev_roa = pp.get("roa")
    if roa is not None and prev_roa is not None:
        max_score += 1
        p = _pass(roa > prev_roa)
        score += p
        criteria.append({"label": "ROA Improving YoY", "pass": p,
                         "explanation": f"{_pct(prev_roa)} → {_pct(roa)}"})
    else:
        criteria.append({"label": "ROA Improving YoY", "pass": -1, "explanation": "No prior-year data"})

    # B3: NPL Ratio Decreasing (lower is better)
    npl = ca.get("npl_ratio")
    prev_npl = pa.get("npl_ratio")
    if npl is not None and prev_npl is not None:
        max_score += 1
        p = _pass(npl < prev_npl)
        score += p
        criteria.append({"label": "NPL Ratio Decreasing", "pass": p,
                         "explanation": f"{_pct(prev_npl)} → {_pct(npl)}"})
    elif npl is not None:
        criteria.append({"label": "NPL Ratio Decreasing", "pass": -1, "explanation": "No prior-year NPL data"})
    else:
        criteria.append({"label": "NPL Ratio Decreasing", "pass": -1, "explanation": "NPL data unavailable"})

    # B4: Coverage Ratio ≥ 1.0x
    cov = ca.get("coverage_ratio")
    if cov is not None:
        max_score += 1
        p = _pass(cov >= 1.0)
        score += p
        criteria.append({"label": "Coverage Ratio ≥ 1.0x", "pass": p,
                         "explanation": f"Coverage: {_x(cov)}"})
    else:
        criteria.append({"label": "Coverage Ratio ≥ 1.0x", "pass": -1, "explanation": "NPL / reserve data unavailable"})

    # B5: Loan-to-Deposit Ratio ≤ 90%
    ldr = cl.get("ldr")
    if ldr is not None:
        max_score += 1
        p = _pass(ldr <= 0.90)
        score += p
        criteria.append({"label": "Loan-to-Deposit ≤ 90%", "pass": p,
                         "explanation": f"LDR: {_pct(ldr)}"})
    else:
        criteria.append({"label": "Loan-to-Deposit ≤ 90%", "pass": -1, "explanation": "Deposit data unavailable"})

    # B6: Cost-to-Income Improving (lower is better)
    cti = ce.get("cost_to_income")
    prev_cti = pe.get("cost_to_income")
    if cti is not None and prev_cti is not None:
        max_score += 1
        p = _pass(cti < prev_cti)
        score += p
        criteria.append({"label": "Cost-to-Income Improving", "pass": p,
                         "explanation": f"{_pct(prev_cti)} → {_pct(cti)}"})
    else:
        criteria.append({"label": "Cost-to-Income Improving", "pass": -1, "explanation": "No prior-year data"})

    # B7: NIM Stable or Improving
    nim = cp.get("nim")
    prev_nim = pp.get("nim")
    if nim is not None and prev_nim is not None:
        max_score += 1
        p = _pass(nim >= prev_nim)
        score += p
        criteria.append({"label": "NIM Stable or Improving", "pass": p,
                         "explanation": f"{_pct(prev_nim)} → {_pct(nim)}"})
    else:
        criteria.append({"label": "NIM Stable or Improving", "pass": -1, "explanation": "Interest income data unavailable"})

    # B8: Equity-to-Assets Increasing (capital strengthening)
    e2a = ck.get("equity_to_assets")
    prev_e2a = pk.get("equity_to_assets")
    if e2a is not None and prev_e2a is not None:
        max_score += 1
        p = _pass(e2a > prev_e2a)
        score += p
        criteria.append({"label": "Equity-to-Assets Improving", "pass": p,
                         "explanation": f"{_pct(prev_e2a)} → {_pct(e2a)}"})
    elif e2a is not None:
        criteria.append({"label": "Equity-to-Assets Improving", "pass": -1, "explanation": "No prior-year data"})
    else:
        criteria.append({"label": "Equity-to-Assets Improving", "pass": -1, "explanation": "Data unavailable"})

    # YoY change chart
    chart_data = [
        _yoy_bar("ROA", roa, pp.get("roa")),
        _yoy_bar("NIM", nim, pp.get("nim")),
        _yoy_bar("NPL Ratio", npl, pa.get("npl_ratio"), lower_is_better=True),
        _yoy_bar("Cost-to-Income", cti, pe.get("cost_to_income"), lower_is_better=True),
        _yoy_bar("Equity/Assets", e2a, pk.get("equity_to_assets")),
    ]
    chart_data = [d for d in chart_data if d is not None]

    return {"score": score, "max_score": max_score, "criteria": criteria, "chart_data": chart_data}


# ── Insurance ─────────────────────────────────────────────────────────────────

def compute_insurance_forensic(ins_result: dict) -> dict:
    """8-point forensic scoring for insurance companies."""
    curr = ins_result.get("current", {})
    prev = ins_result.get("prev", {})

    cp = curr.get("profitability", {})
    pp = prev.get("profitability", {})
    cu = curr.get("underwriting", {})
    pu = prev.get("underwriting", {})
    cs = curr.get("solvency", {})
    ps = prev.get("solvency", {})
    cl = curr.get("liquidity", {})

    criteria = []
    score = 0
    max_score = 0

    # I1: ROA Positive
    roa = cp.get("roa")
    if roa is not None:
        max_score += 1
        p = _pass(roa > 0)
        score += p
        criteria.append({"label": "ROA Positive", "pass": p, "explanation": f"ROA: {_pct(roa)}"})
    else:
        criteria.append({"label": "ROA Positive", "pass": -1, "explanation": "Data unavailable"})

    # I2: ROA Improving YoY
    prev_roa = pp.get("roa")
    if roa is not None and prev_roa is not None:
        max_score += 1
        p = _pass(roa > prev_roa)
        score += p
        criteria.append({"label": "ROA Improving YoY", "pass": p,
                         "explanation": f"{_pct(prev_roa)} → {_pct(roa)}"})
    else:
        criteria.append({"label": "ROA Improving YoY", "pass": -1, "explanation": "No prior-year data"})

    # I3: Combined Ratio < 100% (profitable underwriting)
    cr = cu.get("combined_ratio")
    if cr is not None:
        max_score += 1
        p = _pass(cr < 1.0)
        score += p
        criteria.append({"label": "Combined Ratio < 100%", "pass": p,
                         "explanation": f"Combined: {_pct(cr)}"})
    else:
        criteria.append({"label": "Combined Ratio < 100%", "pass": -1, "explanation": "Claims / premium data unavailable"})

    # I4: Combined Ratio Improving (lower is better)
    prev_cr = pu.get("combined_ratio")
    if cr is not None and prev_cr is not None:
        max_score += 1
        p = _pass(cr < prev_cr)
        score += p
        criteria.append({"label": "Combined Ratio Improving", "pass": p,
                         "explanation": f"{_pct(prev_cr)} → {_pct(cr)}"})
    else:
        criteria.append({"label": "Combined Ratio Improving", "pass": -1, "explanation": "No prior-year data"})

    # I5: Solvency Ratio ≥ 1.0 (100%)
    solv = cs.get("solvency_ratio")
    if solv is not None:
        max_score += 1
        p = _pass(solv >= 1.0)
        score += p
        criteria.append({"label": "Solvency Ratio ≥ 100%", "pass": p,
                         "explanation": f"Solvency: {_pct(solv)}"})
    else:
        criteria.append({"label": "Solvency Ratio ≥ 100%", "pass": -1, "explanation": "Solvency data unavailable"})

    # I6: Reserve Coverage ≥ 1.0x
    res = cs.get("reserve_coverage")
    if res is not None:
        max_score += 1
        p = _pass(res >= 1.0)
        score += p
        criteria.append({"label": "Reserve Coverage ≥ 1.0x", "pass": p,
                         "explanation": f"Reserve Coverage: {_x(res)}"})
    else:
        criteria.append({"label": "Reserve Coverage ≥ 1.0x", "pass": -1, "explanation": "Reserve data unavailable"})

    # I7: Loss Ratio Improving (lower is better)
    lr = cu.get("loss_ratio")
    prev_lr = pu.get("loss_ratio")
    if lr is not None and prev_lr is not None:
        max_score += 1
        p = _pass(lr < prev_lr)
        score += p
        criteria.append({"label": "Loss Ratio Improving", "pass": p,
                         "explanation": f"{_pct(prev_lr)} → {_pct(lr)}"})
    else:
        criteria.append({"label": "Loss Ratio Improving", "pass": -1, "explanation": "No prior-year data"})

    # I8: Operating Cash Flow Positive
    ocf = cl.get("ocf_ratio")
    if ocf is not None:
        max_score += 1
        p = _pass(ocf > 0)
        score += p
        criteria.append({"label": "Operating Cash Flow Positive", "pass": p,
                         "explanation": f"OCF Ratio: {_x(ocf)}"})
    else:
        criteria.append({"label": "Operating Cash Flow Positive", "pass": -1, "explanation": "Cash flow data unavailable"})

    # YoY change chart
    chart_data = [
        _yoy_bar("ROA", roa, pp.get("roa")),
        _yoy_bar("Combined Ratio", cr, pu.get("combined_ratio"), lower_is_better=True),
        _yoy_bar("Loss Ratio", lr, pu.get("loss_ratio"), lower_is_better=True),
        _yoy_bar("Solvency", solv, ps.get("solvency_ratio")),
        _yoy_bar("Reserve Coverage", res, ps.get("reserve_coverage")),
    ]
    chart_data = [d for d in chart_data if d is not None]

    return {"score": score, "max_score": max_score, "criteria": criteria, "chart_data": chart_data}


# ── Finance / NBFI ────────────────────────────────────────────────────────────

def compute_finance_forensic(fin_result: dict) -> dict:
    """8-point forensic scoring for Finance / NBFI companies."""
    curr = fin_result.get("current", {})
    prev = fin_result.get("prev", {})

    cp = curr.get("profitability", {})
    pp = prev.get("profitability", {})
    ce = curr.get("efficiency", {})
    pe = prev.get("efficiency", {})
    cl = curr.get("leverage", {})
    pl = prev.get("leverage", {})
    cq = curr.get("asset_quality", {})
    pq = prev.get("asset_quality", {})
    cliq = curr.get("liquidity", {})

    criteria = []
    score = 0
    max_score = 0

    # F1: ROA Positive
    roa = cp.get("roa")
    if roa is not None:
        max_score += 1
        p = _pass(roa > 0)
        score += p
        criteria.append({"label": "ROA Positive", "pass": p, "explanation": f"ROA: {_pct(roa)}"})
    else:
        criteria.append({"label": "ROA Positive", "pass": -1, "explanation": "Data unavailable"})

    # F2: ROA Improving YoY
    prev_roa = pp.get("roa")
    if roa is not None and prev_roa is not None:
        max_score += 1
        p = _pass(roa > prev_roa)
        score += p
        criteria.append({"label": "ROA Improving YoY", "pass": p,
                         "explanation": f"{_pct(prev_roa)} → {_pct(roa)}"})
    else:
        criteria.append({"label": "ROA Improving YoY", "pass": -1, "explanation": "No prior-year data"})

    # F3: NIM Stable or Improving
    nim = cp.get("nim")
    prev_nim = pp.get("nim")
    if nim is not None and prev_nim is not None:
        max_score += 1
        p = _pass(nim >= prev_nim)
        score += p
        criteria.append({"label": "NIM Stable or Improving", "pass": p,
                         "explanation": f"{_pct(prev_nim)} → {_pct(nim)}"})
    else:
        criteria.append({"label": "NIM Stable or Improving", "pass": -1, "explanation": "Interest income data unavailable"})

    # F4: NPA Ratio Decreasing (lower is better)
    npa = cq.get("npa_ratio")
    prev_npa = pq.get("npa_ratio")
    if npa is not None and prev_npa is not None:
        max_score += 1
        p = _pass(npa < prev_npa)
        score += p
        criteria.append({"label": "NPA Ratio Decreasing", "pass": p,
                         "explanation": f"{_pct(prev_npa)} → {_pct(npa)}"})
    elif npa is not None:
        criteria.append({"label": "NPA Ratio Decreasing", "pass": -1, "explanation": "No prior-year data"})
    else:
        criteria.append({"label": "NPA Ratio Decreasing", "pass": -1, "explanation": "NPA data unavailable"})

    # F5: Cost-to-Income Improving (lower is better)
    cti = ce.get("cost_to_income")
    prev_cti = pe.get("cost_to_income")
    if cti is not None and prev_cti is not None:
        max_score += 1
        p = _pass(cti < prev_cti)
        score += p
        criteria.append({"label": "Cost-to-Income Improving", "pass": p,
                         "explanation": f"{_pct(prev_cti)} → {_pct(cti)}"})
    else:
        criteria.append({"label": "Cost-to-Income Improving", "pass": -1, "explanation": "No prior-year data"})

    # F6: Debt-to-Equity Not Increasing (leverage discipline)
    d2e = cl.get("debt_to_equity")
    prev_d2e = pl.get("debt_to_equity")
    if d2e is not None and prev_d2e is not None:
        max_score += 1
        p = _pass(d2e <= prev_d2e)
        score += p
        criteria.append({"label": "Leverage Not Increasing", "pass": p,
                         "explanation": f"D/E: {_x(prev_d2e)} → {_x(d2e)}"})
    else:
        criteria.append({"label": "Leverage Not Increasing", "pass": -1, "explanation": "No prior-year data"})

    # F7: Operating Cash Flow Positive
    ocf = cliq.get("ocf_ratio")
    if ocf is not None:
        max_score += 1
        p = _pass(ocf > 0)
        score += p
        criteria.append({"label": "Operating Cash Flow Positive", "pass": p,
                         "explanation": f"OCF Ratio: {_x(ocf)}"})
    else:
        criteria.append({"label": "Operating Cash Flow Positive", "pass": -1, "explanation": "Cash flow data unavailable"})

    # F8: Provision Coverage Adequate (≥ 1.0x)
    prov = cq.get("provision_coverage")
    if prov is not None:
        max_score += 1
        p = _pass(prov >= 1.0)
        score += p
        criteria.append({"label": "Provision Coverage ≥ 1.0x", "pass": p,
                         "explanation": f"Coverage: {_x(prov)}"})
    else:
        criteria.append({"label": "Provision Coverage ≥ 1.0x", "pass": -1, "explanation": "Provision data unavailable"})

    # YoY change chart
    chart_data = [
        _yoy_bar("ROA", roa, pp.get("roa")),
        _yoy_bar("NIM", nim, pp.get("nim")),
        _yoy_bar("NPA Ratio", npa, pq.get("npa_ratio"), lower_is_better=True),
        _yoy_bar("Cost-to-Income", cti, pe.get("cost_to_income"), lower_is_better=True),
        _yoy_bar("D/E Ratio", d2e, pl.get("debt_to_equity"), lower_is_better=True),
    ]
    chart_data = [d for d in chart_data if d is not None]

    return {"score": score, "max_score": max_score, "criteria": criteria, "chart_data": chart_data}
