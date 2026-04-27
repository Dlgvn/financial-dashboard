# MSE Analytica — Modeling Engine Implementation Plan
**Date:** 2026-03-16
**Status:** Ready to implement
**Priority:** MVP-critical (Piotroski + Beneish + Composite Score), Post-MVP (Black-Litterman + PMT)

---

## Context

The dashboard vision (`2026-03-05-dashboard-vision.md`) specifies three forensic models and a portfolio optimization engine. This plan provides the actual formulas, data field requirements, implementation design, and build order needed to code them.

**Current state:**
- Altman Z-Score: already implemented in `analysis/ratios.py`
- All other models: specified in vision, not yet implemented

---

## MVP Scope (Build before demo)

| Model | Purpose | Priority |
|-------|---------|----------|
| **Piotroski F-Score** | Financial strength (0–9) | MVP |
| **Beneish M-Score** | Earnings manipulation detection | MVP |
| **Composite Health Score** | Combined 0–100 company rating | MVP |
| Black-Litterman | Portfolio optimization | Post-MVP |
| PMT Risk Metrics | Downside risk (Sortino, CVaR, Max Drawdown) | Post-MVP |

---

## Model 1: Piotroski F-Score

**What it does:** Scores a company 0–9 based on 9 binary criteria across profitability, leverage, and operating efficiency. Score ≥ 7 = strong, ≤ 2 = weak.

### Data Requirements

All fields needed are already in the parsed JSON. Uses current year (`field`) and prior year (`field_prev`).

| Field | JSON Location |
|-------|--------------|
| `net_income` | `income_statement` |
| `total_assets`, `total_assets_prev` | `balance_sheet` |
| `operating_cash_flow` | `cash_flow` |
| `roa` (computed) | derived: net_income / avg_total_assets |
| `total_liabilities`, `total_liabilities_prev` | `balance_sheet` |
| `total_current_assets`, `total_current_assets_prev` | `balance_sheet` |
| `total_current_liabilities`, `total_current_liabilities_prev` | `balance_sheet` |
| `shares_outstanding`, `shares_outstanding_prev` | `balance_sheet` (may be missing — handle gracefully) |
| `gross_profit`, `gross_profit_prev` | `income_statement` |
| `revenue`, `revenue_prev` | `income_statement` |
| `total_equity`, `total_equity_prev` | `balance_sheet` (or derived: total_assets - total_liabilities) |

### The 9 Criteria (1 point each)

**Group A — Profitability (4 criteria)**

| # | Criterion | Formula | Pass if |
|---|-----------|---------|---------|
| F1 | ROA positive | `net_income / avg(total_assets, total_assets_prev)` | > 0 |
| F2 | Operating cash flow positive | `operating_cash_flow` | > 0 |
| F3 | ROA improving | `roa_current - roa_prev` | > 0 |
| F4 | Accruals (cash > earnings) | `operating_cash_flow / total_assets > roa` | True |

**Group B — Leverage & Liquidity (3 criteria)**

| # | Criterion | Formula | Pass if |
|---|-----------|---------|---------|
| F5 | Lower long-term debt ratio | `(long_term_loans / total_assets) vs prev year` | Ratio decreased |
| F6 | Higher current ratio | `current_assets / current_liabilities` | Improved YoY |
| F7 | No share dilution | `shares_outstanding` | Not increased vs prev year (1 if data unavailable — conservative pass) |

**Group C — Operating Efficiency (2 criteria)**

| # | Criterion | Formula | Pass if |
|---|-----------|---------|---------|
| F8 | Gross margin improving | `gross_profit / revenue` | Margin improved YoY |
| F9 | Asset turnover improving | `revenue / avg_total_assets` | Ratio improved YoY |

### Output

```python
{
    "f_score": 7,           # 0–9 total
    "criteria": {
        "f1_roa_positive": True,
        "f2_ocf_positive": True,
        "f3_roa_improving": False,
        "f4_accruals": True,
        "f5_leverage_down": True,
        "f6_liquidity_up": True,
        "f7_no_dilution": None,    # None = data unavailable
        "f8_gross_margin_up": True,
        "f9_asset_turnover_up": True,
    },
    "interpretation": "Strong (≥7)",   # Strong / Neutral / Weak
    "note": "F7 skipped — shares_outstanding not in source data"
}
```

### Implementation Location

- Add `compute_piotroski(parsed_data: dict) -> dict` to `financial_dashboard/analysis/ratios.py`
- Call it alongside `compute_ratios()` in state or wherever ratios are computed

---

## Model 2: Beneish M-Score

**What it does:** Uses 8 financial indices to detect whether earnings have likely been manipulated. M-Score > -1.78 suggests manipulation; < -2.22 suggests clean.

### Data Requirements

**Critical:** Beneish requires **two consecutive years** of data. Fields must have `_prev` counterparts.

| Field | Needed |
|-------|--------|
| `accounts_receivable`, `accounts_receivable_prev` | DSRI |
| `revenue`, `revenue_prev` | DSRI, SGI, SGAI |
| `gross_profit`, `gross_profit_prev` | GMI |
| `total_assets`, `total_assets_prev` | AQI, DEPI, TATA |
| `total_current_assets`, `total_current_assets_prev` | AQI |
| `property_plant_equipment`, `property_plant_equipment_prev` | AQI, DEPI |
| `depreciation`, `depreciation_prev` | DEPI |
| `sga_expense`, `sga_expense_prev` | SGAI (SG&A = selling, general & admin expense) |
| `total_liabilities`, `total_liabilities_prev` | LVGI |
| `total_current_liabilities`, `total_current_liabilities_prev` | LVGI |
| `long_term_debt`, `long_term_debt_prev` | LVGI |
| `net_income` | TATA |
| `operating_cash_flow` | TATA |

### The 8 Indices

| Index | Name | Formula |
|-------|------|---------|
| DSRI | Days Sales Receivables Index | `(AR_t / Rev_t) / (AR_{t-1} / Rev_{t-1})` |
| GMI | Gross Margin Index | `GM_{t-1} / GM_t` where GM = (Rev - COGS) / Rev |
| AQI | Asset Quality Index | `(1 - (CA_t + PPE_t) / TA_t) / (1 - (CA_{t-1} + PPE_{t-1}) / TA_{t-1})` |
| SGI | Sales Growth Index | `Rev_t / Rev_{t-1}` |
| DEPI | Depreciation Index | `(Dep_{t-1} / (Dep_{t-1} + PPE_{t-1})) / (Dep_t / (Dep_t + PPE_t))` |
| SGAI | SG&A Index | `(SGA_t / Rev_t) / (SGA_{t-1} / Rev_{t-1})` |
| LVGI | Leverage Index | `((LTD_t + CL_t) / TA_t) / ((LTD_{t-1} + CL_{t-1}) / TA_{t-1})` |
| TATA | Total Accruals to Total Assets | `(NI_t - CFO_t) / TA_t` |

### M-Score Formula

```
M-Score = -4.84 + 0.920×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
          + 0.115×DEPI − 0.172×SGAI + 4.679×TATA − 0.327×LVGI
```

### Output

```python
{
    "m_score": -2.45,
    "interpretation": "No manipulation likely",   # or "Possible manipulation"
    "threshold": -1.78,
    "indices": {
        "dsri": 1.12,
        "gmi": 0.98,
        "aqi": 1.05,
        "sgi": 1.18,
        "depi": 1.02,
        "sgai": 0.95,
        "lvgi": 0.88,
        "tata": -0.04,
    },
    "missing_fields": ["sga_expense"],    # fields that could not be computed
    "reliable": True    # False if >2 indices could not be computed
}
```

### Handling Missing Data

Some MSE companies (especially banks) will be missing fields like `sga_expense` or `depreciation`. Rules:
- If ≤ 2 indices are missing: compute M-Score with available indices, flag as partially reliable
- If > 2 indices missing: return `m_score = None`, flag as unreliable, show explanation in UI
- Banks: skip Beneish entirely — not designed for financial institutions

### Implementation Location

- Add `compute_beneish(parsed_data: dict) -> dict` to `financial_dashboard/analysis/ratios.py`

---

## Model 3: Composite Health Score (0–100)

**What it does:** Aggregates all ratio categories and forensic models into a single 0–100 score with a plain-language label (Healthy / Caution / Distress).

### Weighting Scheme

| Component | Weight | Source |
|-----------|--------|--------|
| Profitability (ROA, ROE, Net Margin) | 25% | ratios.py |
| Liquidity (Current, Quick, Cash ratio) | 20% | ratios.py |
| Solvency (Debt/Equity, Debt/Assets, Coverage) | 20% | ratios.py |
| Activity (Asset turnover, DSO, Inventory) | 15% | ratios.py |
| Altman Z-Score | 10% | ratios.py (already computed) |
| Piotroski F-Score | 10% | new |

Note: Beneish M-Score is a **penalty flag only** — it does not contribute positively. If M-Score > -1.78, subtract 10 points from the composite score.

### Scoring Per Component

Each ratio is normalized to a 0–100 sub-score using industry benchmarks:

**Profitability sub-score:**
- ROA: 0→0, 5%→50, 15%+→100 (linear interpolation, capped)
- ROE: 0→0, 10%→50, 25%+→100
- Net Margin: 0→0, 5%→50, 20%+→100
- Sub-score = average of the three

**Liquidity sub-score:**
- Current Ratio: <1→0, 1→40, 2→80, 3+→100
- Quick Ratio: <0.5→0, 1→60, 1.5+→100
- Cash Ratio: 0→20, 0.2→60, 0.5+→100
- Sub-score = average

**Solvency sub-score:**
- Debt/Equity: >5→0, 2→40, 1→70, 0.5→90, 0→100 (inverted: lower = better)
- Debt/Assets: >0.9→0, 0.6→40, 0.4→70, 0.2→90, 0→100 (inverted)
- Interest Coverage: <1→0, 1.5→40, 3→70, 5+→100
- Sub-score = average

**Activity sub-score:**
- Asset Turnover: 0→0, 0.5→40, 1→70, 2+→100
- DSO: >180→0, 90→40, 45→70, <30→100 (inverted: lower = better)
- Inventory Turnover: 0→0, 4→50, 10→80, 20+→100
- Sub-score = average

**Altman Z-Score sub-score:**
- <1.81 (Distress) → 0–30
- 1.81–2.99 (Grey) → 30–70
- >2.99 (Safe) → 70–100

**Piotroski F-Score sub-score:**
- F-Score / 9 × 100

### Output

```python
{
    "composite_score": 74,
    "label": "Healthy",          # Healthy (70-100), Caution (40-69), Distress (0-39)
    "color": "green",            # green / amber / red
    "breakdown": {
        "profitability": {"score": 65, "weight": 0.25, "contribution": 16.25},
        "liquidity":     {"score": 82, "weight": 0.20, "contribution": 16.40},
        "solvency":      {"score": 71, "weight": 0.20, "contribution": 14.20},
        "activity":      {"score": 58, "weight": 0.15, "contribution": 8.70},
        "altman":        {"score": 80, "weight": 0.10, "contribution": 8.00},
        "piotroski":     {"score": 78, "weight": 0.10, "contribution": 7.80},
    },
    "beneish_penalty": 0,        # 0 or -10
    "raw_weighted": 71.35,
    "final": 71
}
```

### Implementation Location

- Add `compute_composite_score(ratios: dict, piotroski: dict, altman: dict, beneish: dict) -> dict` to `financial_dashboard/analysis/ratios.py`
- This function receives pre-computed outputs from the other models

---

## Model 4: Black-Litterman Portfolio Optimization (Post-MVP)

**What it does:** Combines equilibrium market returns (from market cap weights) with user-expressed views about specific companies to produce optimal portfolio weights.

### Data Requirements (additional — not in current parser)

| Data | Source | Notes |
|------|--------|-------|
| Market capitalization per company | MSE website (manual input for MVP) | Used to compute equilibrium weights |
| Current stock price | MSE website (manual input) | For valuation ratios + BL weights |
| Risk-free rate | Mongolbank policy rate (~10%) | Hardcode initially |
| Historical return covariance | Requires multi-year price history | Simplify: use book value returns if price unavailable |

### Algorithm Steps

```
1. Compute market-cap weights (π) for portfolio companies
2. Set risk aversion parameter δ = 2.5 (standard)
3. Compute implied equilibrium excess returns: Π = δ × Σ × π
4. Encode user views as: P (view matrix) and Q (return expectations)
5. Set uncertainty scalar τ = 0.05
6. Compute posterior returns:
   μ_BL = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ × [(τΣ)⁻¹Π + P'Ω⁻¹Q]
7. Compute optimal weights via mean-variance optimization on μ_BL
8. Apply constraints: weights ≥ 0, sum = 1
```

**Simplified fallback** (if historical prices unavailable):
- Use equal-weight as equilibrium (π = 1/n)
- Estimate covariance from ratio volatility across companies
- Still produces meaningful view-adjusted weights

### Libraries

```
scipy.optimize (quadratic programming for portfolio weights)
numpy (matrix operations)
```

No additional pip install needed — both already in requirements.

### Implementation Location

- New file: `financial_dashboard/analysis/portfolio.py`
- Functions: `compute_equilibrium_returns()`, `encode_views()`, `black_litterman()`, `optimize_weights()`

---

## Model 5: Post-Modern Portfolio Theory Risk Metrics (Post-MVP)

**What it does:** Computes downside-focused risk metrics that are more relevant than standard deviation for asymmetric return distributions.

### Required Data

Historical returns per company (ideally monthly, at least annual). If only annual data available, use YoY change in book value per share.

### Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| **Downside Deviation** | `sqrt(mean(min(r - MAR, 0)²))` where MAR = 0% | Uses only negative returns |
| **Sortino Ratio** | `(portfolio_return - risk_free) / downside_deviation` | Higher = better risk-adjusted return |
| **Maximum Drawdown** | `max(peak - trough) / peak` over observation period | Worst historical loss |
| **CVaR (95%)** | Average of worst 5% return observations | Conditional Value at Risk |

### Implementation Location

- Add to `financial_dashboard/analysis/portfolio.py`
- Functions: `compute_sortino()`, `compute_max_drawdown()`, `compute_cvar()`

---

## Build Order

### Phase 1 — MVP (implement now)

```
Step 1: compute_piotroski()         → analysis/ratios.py
Step 2: compute_beneish()           → analysis/ratios.py
Step 3: compute_composite_score()   → analysis/ratios.py
Step 4: Wire all three into state.py (called after ratio computation)
Step 5: Display in UI:
        - Hero block: Composite score gauge + F-Score + M-Score badges
        - Forensic tab: Full criterion breakdowns
```

### Phase 2 — Post-MVP

```
Step 6: Create analysis/portfolio.py
Step 7: compute_equilibrium_returns() + black_litterman()
Step 8: compute_sortino() + compute_max_drawdown() + compute_cvar()
Step 9: Portfolio Construction page (Step 5 in UX design)
Step 10: Scenario analysis sliders (Step 6 in UX design)
```

---

## File Changes Summary

| File | Change |
|------|--------|
| `financial_dashboard/analysis/ratios.py` | Add `compute_piotroski()`, `compute_beneish()`, `compute_composite_score()` |
| `financial_dashboard/analysis/portfolio.py` | New file — Black-Litterman + PMT metrics (post-MVP) |
| `financial_dashboard/state.py` | Call new models after existing ratio computation |
| `financial_dashboard/components/` | New forensic display components |

---

## Validation Checklist

- [ ] Piotroski F-Score cross-validated against manual calculation for APU 2025
- [ ] Beneish M-Score cross-validated against manual calculation for APU 2025
- [ ] Composite score produces Healthy/Caution/Distress labels that match intuition
- [ ] Banks (Khan Bank) handled: Beneish skipped, Piotroski criteria adjusted for missing COGS/inventory
- [ ] Missing field cases tested: all models degrade gracefully (None values, not crashes)
- [ ] Black-Litterman produces diversified weights (not corner solutions) — post-MVP
