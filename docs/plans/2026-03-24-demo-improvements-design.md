# Demo Improvements Design
**Date:** 2026-03-24
**Goal:** Align MSE Analytica MVP demo with Checkpoint 3 rubric (Core Functionality, Quality of Results, Live Demo)

---

## Problem

Three demo risks identified:
1. **Reliability (A)** — runtime crashes on None values give grader a bad impression
2. **Quality evidence (B)** — no validation shown; grader will ask "how do you know scores are correct?"
3. **Upload awkwardness (C)** — live file upload is slow and risky in a 5-minute demo

## Approach

**Screener as demo hub** — keep all existing routes, add three targeted improvements without introducing new routes or pages.

---

## Section 1: Load Demo Data Button

**Where:** Upload page (`financial_dashboard/financial_dashboard.py` index function)

**What:**
- Add a "Load 7 MSE Companies" green button as co-equal CTA alongside the upload zone
- Calls new `UploadState.load_demo_data()` event
- Event reads all 7 JSON files from `data/` (same logic as `_load_all_companies()`), populates screener state, redirects to `/screener` via `rx.redirect`
- No file upload, no parsing delay — instant redirect

**Why:** Eliminates the riskiest part of the demo (live upload) while keeping upload available for the "real use case" story.

---

## Section 2: Methodology & Quality Panel

**Where:** Screener page (`financial_dashboard/pages/screener.py`), above the company table

**What:**
- `rx.accordion` with single item "Methodology & Validation" (collapsed by default)
- Inside: 3-column grid with:

  **Models Used**
  - Piotroski F-Score: 9-point rule-based fundamental strength signal
  - Beneish M-Score: forensic fraud detection via 8 accounting ratios
  - Altman Z-Score: bankruptcy prediction, validated on emerging markets
  - Composite 0–100: weighted blend for single actionable health number

  **Quality Evidence**
  - Small table: Company | Criterion | Result | Verified
  - 3 manually spot-checked rows (user fills verified column from annual reports)

  **Known Limitations**
  - Dataset: 7 companies, 1–2 years of data
  - DEPI index always N/A (no depreciation data in MSE filings)
  - No market price data (no P/E, market cap ratios)

**Why:** Grader sees quality evidence and technical justification at the highest-traffic page without extra navigation. Addresses rubric criteria: Technical Approach (25%) and Quality of Results (15%).

---

## Section 3: Graceful Empty States

**Where:** All 4 pages

**What:**
- **Company page** — show "No company loaded" placeholder if `selected_company_name` is empty
- **Screener page** — show "Click Load Demo Data to begin" prompt if `all_companies` is empty
- **Portfolio page** — audit remaining `ObjectItemOperation` fields for None safety
- **State defaults** — verify all flat display vars default to `"—"` not `""` or `0` in ways that crash renders

**Why:** Any crash during a 5-minute demo costs significant points on Live Demo (20%). Graceful degradation shows systematic testing.

---

## Demo Flow After Changes

```
Upload page
  └── [Load 7 MSE Companies] ──► Screener
                                    ├── [Methodology & Validation accordion] (expand to show quality evidence)
                                    └── Company table
                                          └── Click company ──► Company detail page
                                                                    └── [Add to Portfolio] ──► Portfolio page
```

Total demo: ~4 minutes, clean linear flow, no file upload required.

---

## Files to Change

| File | Change |
|------|--------|
| `financial_dashboard/state.py` | Add `load_demo_data()` event to `UploadState` |
| `financial_dashboard/financial_dashboard.py` | Add demo button to `index()` |
| `financial_dashboard/pages/screener.py` | Add methodology accordion above company table; add empty state |
| `financial_dashboard/pages/company.py` | Add empty state guard |
| `financial_dashboard/pages/portfolio.py` | Audit None safety |
