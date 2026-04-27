# MSE Analytica MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a working MVP in 7 days — Piotroski F-Score, Beneish M-Score, Composite Health Score, dark-themed screener, company analysis, and portfolio pages.

**Architecture:** Extend the existing Reflex app from a single upload page to a 4-page app (Upload → Screener → Company Analysis → Portfolio). All scoring models live in `analysis/ratios.py`. State is extended in `state.py` with analysis and portfolio substates. UI uses Tailwind v4 dark classes matching the UX design doc.

**Tech Stack:** Python 3.12, Reflex 0.8.26 + TailwindV4Plugin, existing ratio/parser/storage modules.

**Deadline:** 7 days. Follow tasks in order — each builds on the previous.

---

## Overview of 9 Tasks

| Task | What | Day |
|------|------|-----|
| 1 | Piotroski F-Score | 1 |
| 2 | Beneish M-Score | 1–2 |
| 3 | Composite Health Score | 2 |
| 4 | Extend state + wire all models | 2–3 |
| 5 | Dark theme + layout + sidebar | 3 |
| 6 | Screener page | 4 |
| 7 | Company analysis page | 5 |
| 8 | Portfolio state + page | 6 |
| 9 | Wire navigation + smoke test | 7 |

---

## Task 1: Piotroski F-Score

**Files:**
- Modify: `financial_dashboard/analysis/ratios.py` (append after `compute_ratios`)
- Modify: `financial_dashboard/analysis/labels.py` (append Piotroski labels)

### What it computes
9 binary criteria (1 = pass, 0 = fail, None = data unavailable).
Score = sum of non-None criteria. 7–9 = Strong, 3–6 = Neutral, 0–2 = Weak.

**Khan Bank / insurance caveat:** Missing `revenue`, `gross_profit`, `total_current_assets` → F7, F8, F9 will return None. Score is computed over available criteria only.

### Step 1: Add `compute_piotroski()` to `ratios.py`

Append this function at the end of `financial_dashboard/analysis/ratios.py` (before the `from .labels import` line):

```python
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
    roa = safe_div(net_income, ta)
    f1  = _flag(roa is not None and roa > 0)

    # ── F2: Operating cash flow positive ─────────────────────────────────────
    f2 = _flag(ocf is not None and ocf > 0)

    # ── F3: ROA improving year-over-year ─────────────────────────────────────
    roa_curr = safe_div(net_income, ta)
    roa_prev = safe_div(ni_prev, ta_prev)
    f3 = _flag(
        roa_curr is not None and roa_prev is not None and roa_curr > roa_prev
    )

    # ── F4: Accruals — cash earnings quality (OCF/TA > ROA) ──────────────────
    ocf_ta = safe_div(ocf, ta)
    f4 = _flag(
        ocf_ta is not None and roa_curr is not None and ocf_ta > roa_curr
    )

    # ── F5: Leverage decreased (total_liabilities / total_assets) ────────────
    lev      = safe_div(tl, ta)
    lev_prev = safe_div(tl_prev, ta_prev)
    f5 = _flag(
        lev is not None and lev_prev is not None and lev < lev_prev
    )

    # ── F6: Current ratio improved ────────────────────────────────────────────
    cr      = safe_div(ca, cl)
    cr_prev = safe_div(ca_prev, cl_prev)
    f6 = _flag(
        cr is not None and cr_prev is not None and cr > cr_prev
    )

    # ── F7: No share dilution — skip (shares_outstanding not in MSE data) ────
    f7 = None

    # ── F8: Gross margin improving ────────────────────────────────────────────
    gm      = safe_div(gp, rev)
    gm_prev = safe_div(gp_prev, rev_prev)
    f8 = _flag(
        gm is not None and gm_prev is not None and gm > gm_prev
    )

    # ── F9: Asset turnover improving (revenue / total_assets) ────────────────
    at      = safe_div(rev, ta)
    at_prev = safe_div(rev_prev, ta_prev)
    f9 = _flag(
        at is not None and at_prev is not None and at > at_prev
    )

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
```

### Step 2: Add Piotroski labels to `labels.py`

Append inside `RATIO_LABELS` (or add a new top-level dict at end of file):

```python
# ── Piotroski F-Score labels (ratios.py) ─────────────────────────────────────

PIOTROSKI_LABELS: dict[str, str] = {
    "f1_roa_positive":    "ROA Positive",
    "f2_ocf_positive":    "Operating Cash Flow Positive",
    "f3_roa_improving":   "ROA Improving YoY",
    "f4_accruals":        "Cash Earnings Quality (OCF > Net Income)",
    "f5_leverage_down":   "Leverage Decreased",
    "f6_liquidity_up":    "Current Ratio Improved",
    "f7_no_dilution":     "No Share Dilution",
    "f8_gross_margin_up": "Gross Margin Improving",
    "f9_asset_turnover_up": "Asset Turnover Improving",
}
```

### Step 3: Export from `__init__.py`

Add to the imports block in `financial_dashboard/analysis/__init__.py`:

```python
from .ratios import compute_piotroski
from .labels import PIOTROSKI_LABELS
```

### Step 4: Quick smoke test

```bash
cd "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/financial-dashboard"
source venv/bin/activate
python3 -c "
import json
from financial_dashboard.analysis.ratios import compute_piotroski
with open('data/АПУ_2025.json') as f:
    d = json.load(f)
r = compute_piotroski(d)
print(r)
"
```

Expected: dict with `f_score` between 0–9, `interpretation` one of Strong/Neutral/Weak.

### Step 5: Commit

```bash
git add financial_dashboard/analysis/ratios.py financial_dashboard/analysis/labels.py financial_dashboard/analysis/__init__.py
git commit -m "feat: add Piotroski F-Score (9 criteria, handles missing data)"
```

---

## Task 2: Beneish M-Score

**Files:**
- Modify: `financial_dashboard/analysis/ratios.py` (append after `compute_piotroski`)
- Modify: `financial_dashboard/analysis/__init__.py`

### What it computes
8 financial indices combined into a single M-Score via weighted formula.
M-Score > -1.78 → possible manipulation. M-Score < -2.22 → likely clean.

**Missing data handling:**
- `depreciation` not in MSE data → DEPI index returns None, excluded from score but flagged
- Banks → most indices return None → mark as `reliable: False`
- Score only computed if ≥ 5 of 8 indices are available

### Step 1: Add `compute_beneish()` to `ratios.py`

Append after `compute_piotroski`:

```python
def compute_beneish(parsed_data: dict) -> dict:
    """Compute Beneish M-Score for earnings manipulation detection.

    Uses 8 financial indices. Requires two years of data.
    M-Score > -1.78  → possible manipulation
    M-Score < -2.22  → likely clean

    Returns:
        {
            "m_score": float | None,
            "interpretation": str,
            "indices": { dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata },
            "missing_indices": [str],
            "reliable": bool,   # False if < 5 indices computable
        }
    """
    bs  = parsed_data.get("balance_sheet", {})
    inc = parsed_data.get("income_statement", {})
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

    # DSRI: Days Sales Receivables Index = (AR_t/Rev_t) / (AR_p/Rev_p)
    dsri = safe_div(safe_div(ar, rev), safe_div(ar_p, rev_p))
    indices["dsri"] = dsri
    if dsri is None:
        missing.append("dsri")

    # GMI: Gross Margin Index = (GM_p/Rev_p) / (GM_t/Rev_t)  — prev/curr
    gm   = safe_div(gp, rev)
    gm_p = safe_div(gp_p, rev_p)
    gmi  = safe_div(gm_p, gm)
    indices["gmi"] = gmi
    if gmi is None:
        missing.append("gmi")

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
```

### Step 2: Export from `__init__.py`

```python
from .ratios import compute_beneish
```

### Step 3: Smoke test

```bash
python3 -c "
import json
from financial_dashboard.analysis.ratios import compute_beneish
with open('data/АПУ_2025.json') as f:
    d = json.load(f)
r = compute_beneish(d)
print('M-Score:', r['m_score'])
print('Interpretation:', r['interpretation'])
print('Missing:', r['missing_indices'])
print('Reliable:', r['reliable'])
"
```

Expected: M-Score is a float, DEPI always in missing_indices (known gap), reliable=True for non-bank companies.

### Step 4: Commit

```bash
git add financial_dashboard/analysis/ratios.py financial_dashboard/analysis/__init__.py
git commit -m "feat: add Beneish M-Score (8 indices, graceful missing data)"
```

---

## Task 3: Composite Health Score

**Files:**
- Modify: `financial_dashboard/analysis/ratios.py` (append)
- Modify: `financial_dashboard/analysis/__init__.py`

### What it computes
Weighted 0–100 score aggregating all ratio categories + forensic models.
Requires pre-computed outputs from `compute_ratios()`, `compute_piotroski()`, `compute_beneish()`.

### Step 1: Add `compute_composite_score()` to `ratios.py`

```python
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
        }
    """

    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v)) if v is not None else None

    def _interp(v, lo_v, hi_v, lo_s=0.0, hi_s=100.0):
        """Linear interpolation: map value range → score range."""
        if v is None:
            return None
        if hi_v == lo_v:
            return lo_s
        ratio = (v - lo_v) / (hi_v - lo_v)
        return _clamp(lo_s + ratio * (hi_s - lo_s))

    curr = ratios.get("current", {})

    # ── Sub-scores (each 0–100) ───────────────────────────────────────────────

    # Profitability
    roa = curr.get("profitability", {}).get("roa")
    roe = curr.get("profitability", {}).get("roe")
    npm = curr.get("profitability", {}).get("net_margin")
    prof_parts = list(filter(None, [
        _interp(roa,  0,    0.15, 0, 100),
        _interp(roe,  0,    0.25, 0, 100),
        _interp(npm, -0.05, 0.20, 0, 100),
    ]))
    prof_score = sum(prof_parts) / len(prof_parts) if prof_parts else None

    # Liquidity
    cr = curr.get("liquidity", {}).get("current_ratio")
    qr = curr.get("liquidity", {}).get("quick_ratio")
    cash_r = curr.get("liquidity", {}).get("cash_ratio")
    liq_parts = list(filter(None, [
        _interp(cr,     0, 3.0,  0, 100),
        _interp(qr,     0, 1.5,  0, 100),
        _interp(cash_r, 0, 0.5,  0, 100),
    ]))
    liq_score = sum(liq_parts) / len(liq_parts) if liq_parts else None

    # Solvency (inverted: lower debt = better)
    d2e = curr.get("solvency", {}).get("debt_to_equity")
    d2a = curr.get("solvency", {}).get("debt_to_assets")
    ic  = curr.get("solvency", {}).get("interest_coverage")
    solv_parts = list(filter(None, [
        _interp(d2e, 5, 0, 0, 100),   # inverted
        _interp(d2a, 1, 0, 0, 100),   # inverted
        _interp(ic,  0, 5, 0, 100),
    ]))
    solv_score = sum(solv_parts) / len(solv_parts) if solv_parts else None

    # Activity
    tat = curr.get("activity", {}).get("total_asset_turnover")
    dso = curr.get("activity", {}).get("days_sales_outstanding")
    it  = curr.get("activity", {}).get("inventory_turnover")
    act_parts = list(filter(None, [
        _interp(tat, 0, 2.0,  0, 100),
        _interp(dso, 180, 30, 0, 100),  # inverted (lower DSO = better)
        _interp(it,  0, 20,   0, 100),
    ]))
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

    # ── Weighted aggregate ────────────────────────────────────────────────────
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
        raw_score = weighted_sum / total_weight * 100 / 100

    # ── Beneish penalty ───────────────────────────────────────────────────────
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
        "score":     final_score,
        "label":     label,
        "color":     color,
        "breakdown": breakdown,
        "beneish_penalty": penalty,
    }
```

### Step 2: Export from `__init__.py`

```python
from .ratios import compute_composite_score
```

### Step 3: Smoke test — run all 3 models together

```bash
python3 -c "
import json
from financial_dashboard.analysis.ratios import compute_ratios, compute_piotroski, compute_beneish, compute_composite_score
with open('data/АПУ_2025.json') as f:
    d = json.load(f)
r  = compute_ratios(d)
p  = compute_piotroski(d)
b  = compute_beneish(d)
cs = compute_composite_score(r, p, b)
print('Composite score:', cs['score'], '-', cs['label'])
print('Breakdown:', cs['breakdown'])
print('Beneish penalty:', cs['beneish_penalty'])
"
```

Expected: score 0–100, label one of Healthy/Caution/Distress.

### Step 4: Commit

```bash
git add financial_dashboard/analysis/ratios.py financial_dashboard/analysis/__init__.py
git commit -m "feat: add Composite Health Score (0-100, weighted, Beneish penalty)"
```

---

## Task 4: Extend State — Wire All Models

**Files:**
- Modify: `financial_dashboard/state.py`

### What changes
Add two new state classes in `state.py`:
1. `AnalysisState(UploadState)` — loads a company and computes all scores
2. `PortfolioState(AnalysisState)` — manages portfolio holdings

### Step 1: Add `AnalysisState` and `PortfolioState` to `state.py`

Append at the end of `financial_dashboard/state.py`:

```python
import json
from pathlib import Path

from .analysis.ratios import (
    compute_ratios,
    compute_piotroski,
    compute_beneish,
    compute_composite_score,
)
from .analysis.bank_ratios import compute_bank_ratios
from .analysis.insurance_ratios import compute_insurance_ratios
from .storage.json_store import DATA_DIR


def _load_all_companies() -> list[dict]:
    """Load all parsed company JSONs and compute scores for each."""
    index_path = Path(DATA_DIR) / "index.json"
    if not index_path.exists():
        return []
    with open(index_path) as f:
        index = json.load(f)

    results = []
    for entry in index.get("files", []):
        try:
            fp = Path(DATA_DIR) / entry["filename"]
            with open(fp) as f:
                data = json.load(f)

            ratios    = compute_ratios(data)
            piotroski = compute_piotroski(data)
            beneish   = compute_beneish(data)
            composite = compute_composite_score(ratios, piotroski, beneish)

            results.append({
                "filename":  entry["filename"],
                "company":   entry["company"],
                "year":      entry["year"],
                "sector":    entry.get("sector", ""),
                "score":     composite["score"],
                "label":     composite["label"],
                "color":     composite["color"],
                "z_score":   ratios["current"].get("z_score", {}).get("z_score"),
                "roe":       ratios["current"].get("profitability", {}).get("roe"),
                "f_score":   piotroski["f_score"],
                "m_score":   beneish["m_score"],
            })
        except Exception:
            continue
    return results


class AnalysisState(UploadState):
    """State for company screener and individual company analysis."""

    # Screener
    all_companies: list[dict] = []
    screener_filter: str = "All"     # sector filter value

    # Company detail
    selected_company_name: str = ""
    company_ratios:    dict = {}
    company_piotroski: dict = {}
    company_beneish:   dict = {}
    company_composite: dict = {}

    @rx.event
    def load_screener(self):
        """Load all companies with computed scores for screener page."""
        self.all_companies = _load_all_companies()

    @rx.event
    def load_company(self, company_name: str):
        """Load and compute full analysis for one company."""
        self.selected_company_name = company_name
        index_path = Path(DATA_DIR) / "index.json"
        if not index_path.exists():
            return
        with open(index_path) as f:
            index = json.load(f)

        filename = next(
            (e["filename"] for e in index.get("files", [])
             if e["company"] == company_name),
            None
        )
        if not filename:
            return

        fp = Path(DATA_DIR) / filename
        with open(fp) as f:
            data = json.load(f)

        self.company_ratios    = compute_ratios(data)
        self.company_piotroski = compute_piotroski(data)
        self.company_beneish   = compute_beneish(data)
        self.company_composite = compute_composite_score(
            self.company_ratios, self.company_piotroski, self.company_beneish
        )

    @rx.var
    def filtered_companies(self) -> list[dict]:
        if self.screener_filter == "All":
            return self.all_companies
        return [
            c for c in self.all_companies
            if c.get("sector") == self.screener_filter
        ]


class PortfolioState(AnalysisState):
    """State for portfolio management (Step 4)."""

    # List of { company, filename, weight, score, label, color }
    holdings: list[dict] = []

    @rx.event
    def add_to_portfolio(self, company: str):
        """Add a company to portfolio with equal weight."""
        if any(h["company"] == company for h in self.holdings):
            return  # already in portfolio
        entry = next(
            (c for c in self.all_companies if c["company"] == company),
            None
        )
        if not entry:
            return
        n = len(self.holdings) + 1
        # Rebalance to equal weights
        new_weight = round(1 / n, 4)
        holdings = [
            {**h, "weight": new_weight}
            for h in self.holdings
        ]
        holdings.append({
            "company":  entry["company"],
            "filename": entry["filename"],
            "weight":   new_weight,
            "score":    entry["score"],
            "label":    entry["label"],
            "color":    entry["color"],
        })
        self.holdings = holdings

    @rx.event
    def remove_from_portfolio(self, company: str):
        """Remove a company and rebalance weights."""
        holdings = [h for h in self.holdings if h["company"] != company]
        n = len(holdings)
        if n > 0:
            new_weight = round(1 / n, 4)
            holdings = [{**h, "weight": new_weight} for h in holdings]
        self.holdings = holdings

    @rx.var
    def portfolio_health(self) -> int:
        """Blended health score across portfolio (weighted average)."""
        if not self.holdings:
            return 0
        total = sum(h["score"] * h["weight"] for h in self.holdings)
        return int(total)

    @rx.var
    def in_portfolio(self) -> list[str]:
        """List of company names currently in portfolio."""
        return [h["company"] for h in self.holdings]
```

### Step 2: Also add `DATA_DIR` export to `json_store.py`

Check if `DATA_DIR` is already exported in `financial_dashboard/storage/json_store.py`. If not, find the data directory path definition and make sure it's accessible as a module-level constant named `DATA_DIR`.

```bash
grep -n "DATA_DIR\|data_dir\|DATA_PATH" financial_dashboard/storage/json_store.py
```

If the path is defined differently, update the import in state.py accordingly.

### Step 3: Smoke test state loads

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
# Just test the helper function directly
from financial_dashboard.state import _load_all_companies
companies = _load_all_companies()
print(f'Loaded {len(companies)} companies')
for c in companies:
    print(f'  {c[\"company\"]}: score={c[\"score\"]} ({c[\"label\"]})')
"
```

Expected: 7 companies listed, each with a numeric score and label.

### Step 4: Commit

```bash
git add financial_dashboard/state.py financial_dashboard/storage/json_store.py
git commit -m "feat: add AnalysisState and PortfolioState with full model wiring"
```

---

## Task 5: Dark Theme + Layout + Sidebar

**Files:**
- Modify: `rxconfig.py`
- Create: `financial_dashboard/components/sidebar.py`
- Create: `financial_dashboard/components/layout.py`

### Step 1: Enable dark theme in `rxconfig.py`

Replace the existing `rxconfig.py` with:

```python
import reflex as rx

config = rx.Config(
    app_name="financial_dashboard",
    plugins=[
        rx.plugins.TailwindV4Plugin(),
    ],
)
```

### Step 2: Create `financial_dashboard/components/sidebar.py`

```python
"""Navigation sidebar — 4-step workflow navigation."""
import reflex as rx


def nav_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, size="2", weight="medium"),
            spacing="2",
            align="center",
        ),
        href=href,
        class_name=(
            "flex items-center gap-2 px-3 py-2 rounded-md text-slate-400 "
            "hover:text-green-400 hover:bg-slate-800 transition-colors duration-150 "
            "w-full text-sm"
        ),
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Logo / title
            rx.box(
                rx.text(
                    "MSE",
                    class_name="text-green-400 font-bold text-lg tracking-tight",
                ),
                rx.text(
                    "Analytica",
                    class_name="text-slate-200 font-bold text-lg tracking-tight",
                ),
                class_name="flex gap-1 items-baseline px-3 py-4",
            ),
            rx.separator(class_name="border-slate-700 w-full"),
            # Navigation links
            rx.vstack(
                nav_link("Upload",   "/",          "upload"),
                nav_link("Screener", "/screener",  "search"),
                nav_link("Portfolio","/portfolio", "briefcase"),
                spacing="1",
                width="100%",
                padding_x="2",
                padding_y="3",
            ),
            spacing="0",
            width="100%",
            align="start",
        ),
        class_name=(
            "fixed left-0 top-0 h-full w-52 bg-slate-900 "
            "border-r border-slate-700 flex flex-col z-10"
        ),
    )
```

### Step 3: Create `financial_dashboard/components/layout.py`

```python
"""Base page layout wrapping all pages with sidebar + content area."""
import reflex as rx
from .sidebar import sidebar


def page_layout(*children) -> rx.Component:
    """Wrap page content with dark background and sidebar."""
    return rx.box(
        sidebar(),
        rx.box(
            *children,
            class_name="ml-52 min-h-screen bg-slate-950 text-slate-100 p-8",
        ),
        class_name="flex min-h-screen bg-slate-950",
    )
```

### Step 4: Commit

```bash
git add rxconfig.py financial_dashboard/components/sidebar.py financial_dashboard/components/layout.py
git commit -m "feat: dark theme layout with sidebar navigation"
```

---

## Task 6: Screener Page

**Files:**
- Create: `financial_dashboard/pages/screener.py`
- Modify: `financial_dashboard/financial_dashboard.py` (register route)

### Step 1: Create `financial_dashboard/pages/` directory with `__init__.py`

```bash
mkdir -p financial_dashboard/pages
touch financial_dashboard/pages/__init__.py
```

### Step 2: Create `financial_dashboard/pages/screener.py`

```python
"""Step 2 — Screener: browse all uploaded companies."""
import reflex as rx
from ..components.layout import page_layout
from ..state import AnalysisState


def health_badge(score: int, label: str, color: str) -> rx.Component:
    color_map = {
        "green": "bg-green-500/20 text-green-400 border-green-500/30",
        "amber": "bg-amber-500/20 text-amber-400 border-amber-500/30",
        "red":   "bg-red-500/20   text-red-400   border-red-500/30",
    }
    css = color_map.get(color, color_map["amber"])
    return rx.box(
        rx.hstack(
            rx.text(score, weight="bold", size="3"),
            rx.text(label, size="2"),
            spacing="1",
            align="center",
        ),
        class_name=f"px-3 py-1 rounded-full border text-sm font-medium {css}",
    )


def company_row(company: dict) -> rx.Component:
    return rx.tr(
        rx.td(
            rx.link(
                company["company"],
                href=rx.cond(
                    company["company"] != "",
                    "/company/" + company["company"],
                    "#",
                ),
                class_name="text-green-400 hover:text-green-300 font-medium",
            ),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.text(company["year"], class_name="text-slate-400 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.td(
            health_badge(company["score"], company["label"], company["color"]),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.text(
                rx.cond(
                    company["f_score"] != None,
                    company["f_score"].to_string() + " / 9",
                    "N/A",
                ),
                class_name="text-slate-300 text-sm",
            ),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.text(
                rx.cond(
                    company["roe"] != None,
                    (company["roe"] * 100).to_string() + "%",
                    "N/A",
                ),
                class_name="text-slate-300 text-sm",
            ),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.button(
                rx.icon("plus", size=14),
                rx.text("Add", size="1"),
                on_click=AnalysisState.add_to_portfolio(company["company"]),  # type: ignore
                class_name=(
                    "flex items-center gap-1 px-3 py-1 rounded "
                    "bg-slate-700 hover:bg-green-600 text-slate-200 "
                    "hover:text-white text-xs transition-colors"
                ),
                size="1",
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b border-slate-800 hover:bg-slate-900/50 transition-colors",
    )


def screener_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Company Screener", size="6", class_name="text-slate-100"),
                rx.text(
                    AnalysisState.all_companies.length().to_string() + " companies",
                    class_name="text-slate-500 text-sm self-end",
                ),
                justify="between",
                width="100%",
                align="end",
            ),
            # Table
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                "Company",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Year",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Health Score",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "F-Score",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "ROE",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "",
                                class_name="px-4 py-3",
                            ),
                        ),
                        class_name="bg-slate-900/50",
                    ),
                    rx.table.body(
                        rx.foreach(
                            AnalysisState.all_companies,
                            company_row,
                        ),
                    ),
                    class_name="w-full",
                    variant="ghost",
                ),
                class_name="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden w-full",
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
```

### Step 3: Register route in `financial_dashboard.py`

Add to the existing `financial_dashboard/financial_dashboard.py`:

```python
from .pages.screener import screener_page
from .state import AnalysisState

# Add after the existing app.add_page line:
app.add_page(screener_page, route="/screener", on_load=AnalysisState.load_screener)
```

### Step 4: Smoke test

```bash
cd "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/financial-dashboard"
source venv/bin/activate
reflex run
```

Navigate to `http://localhost:3000/screener`. Expected: dark table listing companies with health badges.

### Step 5: Commit

```bash
git add financial_dashboard/pages/ financial_dashboard/financial_dashboard.py
git commit -m "feat: screener page with health badges and portfolio add button"
```

---

## Task 7: Company Analysis Page

**Files:**
- Create: `financial_dashboard/pages/company.py`
- Modify: `financial_dashboard/financial_dashboard.py`

### Step 1: Create `financial_dashboard/pages/company.py`

```python
"""Step 3 — Company Health Analysis page."""
import reflex as rx
from ..components.layout import page_layout
from ..state import AnalysisState


def score_card(title: str, value, unit: str = "", color: str = "slate") -> rx.Component:
    color_map = {
        "green": "text-green-400",
        "amber": "text-amber-400",
        "red":   "text-red-400",
        "slate": "text-slate-100",
    }
    return rx.box(
        rx.text(title, class_name="text-slate-400 text-xs uppercase tracking-wider mb-1"),
        rx.hstack(
            rx.text(value, class_name=f"text-2xl font-bold {color_map.get(color, color_map['slate'])}"),
            rx.text(unit, class_name="text-slate-500 text-sm self-end mb-1"),
            spacing="1",
            align="end",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
    )


def ratio_row(label: str, value, unit: str = "") -> rx.Component:
    return rx.tr(
        rx.td(rx.text(label, class_name="text-slate-300 text-sm"), class_name="py-2 px-4"),
        rx.td(
            rx.text(
                rx.cond(value != None, value, "N/A"),
                class_name="text-slate-100 text-sm font-mono",
            ),
            class_name="py-2 px-4 text-right",
        ),
        rx.td(rx.text(unit, class_name="text-slate-500 text-xs"), class_name="py-2 px-4"),
        class_name="border-b border-slate-800/50",
    )


def piotroski_criterion(label: str, value) -> rx.Component:
    return rx.hstack(
        rx.cond(
            value == 1,
            rx.icon("circle-check", size=16, class_name="text-green-400"),
            rx.cond(
                value == 0,
                rx.icon("circle-x", size=16, class_name="text-red-400"),
                rx.icon("circle-help", size=16, class_name="text-slate-500"),
            ),
        ),
        rx.text(label, class_name="text-slate-300 text-sm"),
        spacing="2",
        align="center",
        class_name="py-1",
    )


def company_page() -> rx.Component:
    comp   = AnalysisState.company_composite
    piots  = AnalysisState.company_piotroski
    ben    = AnalysisState.company_beneish
    curr   = AnalysisState.company_ratios

    return page_layout(
        rx.vstack(
            # Back link
            rx.link(
                rx.hstack(
                    rx.icon("arrow-left", size=14),
                    rx.text("Screener", size="2"),
                    spacing="1",
                    align="center",
                ),
                href="/screener",
                class_name="text-slate-400 hover:text-slate-200 text-sm flex items-center gap-1 mb-2",
            ),
            # Company header
            rx.hstack(
                rx.heading(
                    AnalysisState.selected_company_name,
                    size="7",
                    class_name="text-slate-100",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=14),
                    rx.text("Add to Portfolio"),
                    on_click=AnalysisState.add_to_portfolio(AnalysisState.selected_company_name),
                    class_name=(
                        "flex items-center gap-2 px-4 py-2 rounded-lg "
                        "bg-green-600 hover:bg-green-500 text-white font-medium "
                        "transition-colors"
                    ),
                ),
                width="100%",
                align="center",
            ),
            # Hero score cards row
            rx.grid(
                score_card("Health Score",    comp["score"],         "/100",  comp["color"]),
                score_card("Piotroski",       piots["f_score"],      "/ " + piots["max_score"].to_string()),
                score_card("M-Score",         ben["m_score"],        "",      "slate"),
                score_card("Interpretation",  ben["interpretation"], "",      "slate"),
                columns="4",
                spacing="4",
                width="100%",
            ),
            # Ratios + Forensics side by side
            rx.grid(
                # Ratios table
                rx.box(
                    rx.text("Financial Ratios", class_name="text-slate-200 font-semibold mb-3"),
                    rx.table.root(
                        rx.table.body(
                            ratio_row("ROA",            curr["current"]["profitability"]["roa"],          "%"),
                            ratio_row("ROE",            curr["current"]["profitability"]["roe"],          "%"),
                            ratio_row("Net Margin",     curr["current"]["profitability"]["net_margin"],   "%"),
                            ratio_row("Current Ratio",  curr["current"]["liquidity"]["current_ratio"],    "x"),
                            ratio_row("Quick Ratio",    curr["current"]["liquidity"]["quick_ratio"],      "x"),
                            ratio_row("Debt/Equity",    curr["current"]["solvency"]["debt_to_equity"],    "x"),
                            ratio_row("Interest Cov.",  curr["current"]["solvency"]["interest_coverage"], "x"),
                            ratio_row("Asset Turnover", curr["current"]["activity"]["total_asset_turnover"], "x"),
                            ratio_row("Altman Z-Score", curr["current"]["z_score"]["z_score"],            ""),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
                ),
                # Forensic models
                rx.box(
                    rx.text("Forensic Analysis", class_name="text-slate-200 font-semibold mb-3"),
                    rx.text("Piotroski F-Score", class_name="text-slate-400 text-xs uppercase tracking-wider mb-2 mt-3"),
                    rx.vstack(
                        piotroski_criterion("ROA Positive",             piots["criteria"]["f1_roa_positive"]),
                        piotroski_criterion("Operating CF Positive",    piots["criteria"]["f2_ocf_positive"]),
                        piotroski_criterion("ROA Improving",            piots["criteria"]["f3_roa_improving"]),
                        piotroski_criterion("Cash Earnings Quality",    piots["criteria"]["f4_accruals"]),
                        piotroski_criterion("Leverage Decreased",       piots["criteria"]["f5_leverage_down"]),
                        piotroski_criterion("Liquidity Improved",       piots["criteria"]["f6_liquidity_up"]),
                        piotroski_criterion("Gross Margin Improving",   piots["criteria"]["f8_gross_margin_up"]),
                        piotroski_criterion("Asset Turnover Improving", piots["criteria"]["f9_asset_turnover_up"]),
                        spacing="0",
                        align="start",
                    ),
                    rx.separator(class_name="border-slate-700 my-3"),
                    rx.text("Beneish M-Score Indices", class_name="text-slate-400 text-xs uppercase tracking-wider mb-2"),
                    rx.table.root(
                        rx.table.body(
                            ratio_row("DSRI (Receivables)",  ben["indices"]["dsri"],  ""),
                            ratio_row("GMI (Gross Margin)",  ben["indices"]["gmi"],   ""),
                            ratio_row("AQI (Asset Quality)", ben["indices"]["aqi"],   ""),
                            ratio_row("SGI (Sales Growth)",  ben["indices"]["sgi"],   ""),
                            ratio_row("SGAI (SG&A)",         ben["indices"]["sgai"],  ""),
                            ratio_row("LVGI (Leverage)",     ben["indices"]["lvgi"],  ""),
                            ratio_row("TATA (Accruals)",     ben["indices"]["tata"],  ""),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
```

### Step 2: Register dynamic route in `financial_dashboard.py`

```python
from .pages.company import company_page

# Dynamic route — company name comes from URL
app.add_page(
    company_page,
    route="/company/[company]",
    on_load=AnalysisState.load_company(AnalysisState.router.page.params.get("company", "")),
)
```

**Note on dynamic route loading in Reflex 0.8.x:** The `on_load` pattern for dynamic routes needs the param. If the above doesn't work, use this alternative in `AnalysisState`:

```python
@rx.event
def on_load_company(self):
    """Called on page load — reads company from URL params."""
    company = self.router.page.params.get("company", "")
    if company:
        self.load_company(company)
```

And register as: `on_load=AnalysisState.on_load_company`

### Step 3: Commit

```bash
git add financial_dashboard/pages/company.py financial_dashboard/financial_dashboard.py
git commit -m "feat: company analysis page with ratios, Piotroski, and Beneish display"
```

---

## Task 8: Portfolio Page

**Files:**
- Create: `financial_dashboard/pages/portfolio.py`
- Modify: `financial_dashboard/financial_dashboard.py`

### Step 1: Create `financial_dashboard/pages/portfolio.py`

```python
"""Step 4 — Portfolio: manage holdings and view blended health."""
import reflex as rx
from ..components.layout import page_layout
from ..state import PortfolioState


def holding_row(holding: dict) -> rx.Component:
    color_map = {
        "green": "text-green-400",
        "amber": "text-amber-400",
        "red":   "text-red-400",
    }
    return rx.tr(
        rx.td(
            rx.link(
                holding["company"],
                href="/company/" + holding["company"],
                class_name="text-green-400 hover:text-green-300 font-medium",
            ),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.text(
                (holding["weight"] * 100).to_string() + "%",
                class_name="text-slate-300 text-sm font-mono",
            ),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.text(
                holding["score"].to_string(),
                class_name=f"font-bold {color_map.get(holding['color'], 'text-slate-300')}",
            ),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.text(holding["label"], class_name="text-slate-400 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.td(
            rx.button(
                rx.icon("trash-2", size=14),
                on_click=PortfolioState.remove_from_portfolio(holding["company"]),
                class_name=(
                    "p-1 rounded text-slate-500 hover:text-red-400 "
                    "hover:bg-red-500/10 transition-colors"
                ),
                variant="ghost",
                size="1",
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b border-slate-800 hover:bg-slate-900/50 transition-colors",
    )


def portfolio_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Portfolio", size="6", class_name="text-slate-100"),
                rx.spacer(),
                # Blended health score
                rx.cond(
                    PortfolioState.holdings.length() > 0,
                    rx.box(
                        rx.text("Blended Health", class_name="text-slate-400 text-xs uppercase tracking-wider"),
                        rx.text(
                            PortfolioState.portfolio_health.to_string(),
                            class_name="text-2xl font-bold text-green-400",
                        ),
                        class_name="bg-slate-900 rounded-lg border border-slate-800 px-5 py-3 text-center",
                    ),
                    rx.box(),
                ),
                width="100%",
                align="center",
            ),
            # Empty state
            rx.cond(
                PortfolioState.holdings.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("briefcase", size=40, class_name="text-slate-600"),
                        rx.text(
                            "No companies in portfolio yet.",
                            class_name="text-slate-400",
                        ),
                        rx.text(
                            "Go to the Screener and click + Add on any company.",
                            class_name="text-slate-500 text-sm",
                        ),
                        rx.link(
                            "Go to Screener →",
                            href="/screener",
                            class_name="text-green-400 hover:text-green-300 text-sm mt-2",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    class_name=(
                        "bg-slate-900 rounded-lg border border-slate-800 "
                        "p-16 w-full flex items-center justify-center"
                    ),
                ),
                # Holdings table
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Company",      class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("Weight",       class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("Health Score", class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("Label",        class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("",             class_name="px-4 py-3"),
                            ),
                            class_name="bg-slate-900/50",
                        ),
                        rx.table.body(
                            rx.foreach(PortfolioState.holdings, holding_row),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden w-full",
                ),
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
```

### Step 2: Register route in `financial_dashboard.py`

```python
from .pages.portfolio import portfolio_page

app.add_page(portfolio_page, route="/portfolio")
```

### Step 3: Commit

```bash
git add financial_dashboard/pages/portfolio.py financial_dashboard/financial_dashboard.py
git commit -m "feat: portfolio page with holdings, equal weighting, blended health score"
```

---

## Task 9: Wire Navigation + Smoke Test

**Files:**
- Modify: `financial_dashboard/financial_dashboard.py` (refactor upload page to use layout)
- Modify: `financial_dashboard/components/sidebar.py` (if nav links need updating)

### Step 1: Refactor upload page to use dark layout

Update `financial_dashboard/financial_dashboard.py` so the `index()` function wraps its content with `page_layout()`:

```python
from .components.layout import page_layout
from .components.upload_zone import selected_files_list, upload_zone
from .components.file_list import file_list

def index() -> rx.Component:
    return page_layout(
        rx.vstack(
            rx.heading("Upload Financial Statements", size="6", class_name="text-slate-100"),
            rx.text(
                "Upload .xls or .xlsx files from members.mse.mn",
                class_name="text-slate-400 text-sm",
            ),
            rx.separator(class_name="border-slate-700"),
            upload_zone(),
            selected_files_list(),
            rx.cond(
                UploadState.is_uploading,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Parsing files...", size="2", class_name="text-slate-300"),
                    align="center", spacing="2",
                ),
            ),
            rx.cond(
                UploadState.success_message != "",
                rx.callout(
                    UploadState.success_message,
                    icon="check",
                    color_scheme="green",
                    width="100%",
                ),
            ),
            rx.cond(
                UploadState.parse_error != "",
                rx.callout(
                    UploadState.parse_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    width="100%",
                ),
            ),
            rx.separator(class_name="border-slate-700"),
            rx.text("Uploaded Companies", class_name="text-slate-200 font-semibold"),
            file_list(),
            spacing="4",
            width="100%",
        ),
    )
```

### Step 2: Final full smoke test

```bash
source venv/bin/activate
reflex run
```

**Check each route:**
- `http://localhost:3000/` — Upload page with dark sidebar
- `http://localhost:3000/screener` — Company list with health badges
- `http://localhost:3000/company/АПУ` — APU analysis with ratios and forensic scores
- `http://localhost:3000/portfolio` — Empty portfolio with add prompt

**Check flows:**
1. Screener → click company name → company analysis page loads
2. Company page → click "Add to Portfolio" → navigate to `/portfolio` → company appears
3. Portfolio → remove company → table updates
4. Upload new XLS → screener refreshes with new company

### Step 3: Fix any broken imports or state issues found during testing

Common issues in Reflex 0.8.x:
- State vars must be JSON-serializable (no raw `dict` with nested `dict` as var type — use `list[dict]` or simple scalars where possible)
- Dynamic route param access: use `self.router.page.params` inside event handlers
- `rx.foreach` only works with `list` state vars, not computed vars of complex types

### Step 4: Final commit

```bash
git add -A
git commit -m "feat: MVP complete — upload, screener, company analysis, portfolio with dark UI"
```

---

## Final File Structure After MVP

```
financial_dashboard/
├── analysis/
│   ├── ratios.py            ← + compute_piotroski, compute_beneish, compute_composite_score
│   ├── bank_ratios.py
│   ├── insurance_ratios.py
│   └── labels.py            ← + PIOTROSKI_LABELS
├── components/
│   ├── upload_zone.py
│   ├── file_list.py
│   ├── sidebar.py           ← NEW
│   └── layout.py            ← NEW
├── pages/
│   ├── __init__.py          ← NEW
│   ├── screener.py          ← NEW
│   ├── company.py           ← NEW
│   └── portfolio.py         ← NEW
├── parser/
├── storage/
├── state.py                 ← + AnalysisState, PortfolioState
└── financial_dashboard.py   ← + 3 new routes
```

---

## Day-by-Day Schedule

| Day | Tasks | Deliverable |
|-----|-------|-------------|
| 1   | Tasks 1–2 | Piotroski + Beneish working in Python |
| 2   | Task 3–4 | Composite score + full state wiring |
| 3   | Task 5 | Dark theme, sidebar, layout |
| 4   | Task 6 | Screener page live |
| 5   | Task 7 | Company analysis page live |
| 6   | Task 8 | Portfolio page live |
| 7   | Task 9 | Navigation wired, all flows tested |
