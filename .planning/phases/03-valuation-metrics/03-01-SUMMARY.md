---
phase: 03-valuation-metrics
plan: 01
subsystem: valuation-backend
tags: [valuation, scraper, state, computation]
dependency_graph:
  requires:
    - "financial_dashboard/analysis/ratios.py (EBITDA approximation pattern)"
    - "financial_dashboard/scraper/price_scraper.py (price JSON format)"
    - "data/prices/{company}.json (price data)"
  provides:
    - "financial_dashboard/analysis/valuation.py — compute_valuation_metrics()"
    - "financial_dashboard/scraper/price_scraper.py — scrape_shares_outstanding()"
    - "financial_dashboard/state.py — 10 valuation state vars + 4 event handlers"
  affects:
    - "financial_dashboard/state.py — load_company() now calls _load_valuation_data()"
    - "financial_dashboard/scraper/price_scraper.py — scrape_company_prices() now returns tuple"
tech_stack:
  added: []
  patterns:
    - "_safe_div() helper for None-safe ratio computation"
    - "YYYY-MM-DD string comparison for date range filtering"
    - "shares_outstanding_override in financial JSON for manual override"
key_files:
  created:
    - financial_dashboard/analysis/valuation.py
  modified:
    - financial_dashboard/scraper/price_scraper.py
    - financial_dashboard/state.py
decisions:
  - "FCF = OCF - abs(investing_cash_flow): investing CF is negative for outflows, abs() gives capex"
  - "P/E only computed when net_income > 0 (negative earnings P/E is misleading)"
  - "Scraped shares_outstanding stored at top-level of price JSON (not in records)"
  - "Manual shares override stored as shares_outstanding_override in financial JSON"
  - "EBITDA = EBIT = profit_before_tax + financial_expense (consistent with ratios.py proxy)"
metrics:
  duration: "~20 minutes"
  completed: "2026-03-26"
  tasks: 2
  files: 3
requirements: [VAL-01, VAL-02, VAL-03]
---

# Phase 3 Plan 1: Valuation Backend Summary

Valuation computation engine with EV/EBITDA, FCF Yield, P/E, P/BV plus scraper shares extraction and full state wiring.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Extend scraper + create valuation module | e7a13ff | price_scraper.py, valuation.py, state.py |
| 2 | Add valuation state vars and event handlers | 33f49e0 | state.py |

## What Was Built

### financial_dashboard/analysis/valuation.py (new)

Single public function `compute_valuation_metrics(parsed_data, shares_outstanding, last_close_price)` returns:
- `market_cap`: shares × last_close_price
- `ev`: market_cap + total_debt - cash
- `ev_ebitda`: EV / EBITDA (EBITDA = EBIT = profit_before_tax + financial_expense)
- `fcf_yield`: (OCF - |investing_CF|) / market_cap
- `pe`: market_cap / net_income (only when net_income > 0)
- `pbv`: market_cap / total_equity (falls back to total_assets - total_liabilities)

All ratios return None when shares_outstanding is None (no market cap computable). Uses `_safe_div()` helper for None/zero-safe division.

### financial_dashboard/scraper/price_scraper.py (extended)

- `scrape_shares_outstanding(soup)` — extracts total shares from MSE company page table rows, falls back to text search; returns `int | None`
- `scrape_company_prices()` — now returns `tuple[list[dict], int | None]`; no extra HTTP request
- `save_price_data()` — now accepts `shares_outstanding: int | None = None`; persists to price JSON top-level when provided

### financial_dashboard/state.py (extended)

**10 new state vars on AnalysisState:**
- Display: `company_ev_ebitda`, `company_fcf_yield`, `company_pe`, `company_pbv`, `company_shares_outstanding`
- Input UI: `company_shares_input_open`, `company_shares_input_value`
- Charts: `company_price_chart_data`, `company_volume_chart_data` (both `list[dict[str, str]]`)
- Range: `valuation_range` (default "1Y")

**Private helpers:**
- `_load_valuation_data(company_name)` — loads price JSON, resolves effective shares (manual override > scraped), calls `compute_valuation_metrics`, formats results, slices chart data
- `_slice_price_records(records)` — filters records by `valuation_range` (1M=30d, 6M=180d, 1Y=365d, All=no cutoff)

**4 new event handlers:**
- `set_valuation_range(range_value)` — updates range and re-slices chart data from price JSON
- `toggle_shares_input()` — toggles input form open/close
- `set_shares_input_value(value)` — setter for input field
- `save_shares_outstanding(value)` — parses int, writes `shares_outstanding_override` to financial JSON, recomputes valuation

**load_company integration:** `_load_valuation_data()` called at end of `load_company()` so valuation data loads automatically when a company page opens.

## Deviations from Plan

None — plan executed exactly as written. The only clarification was using `source venv/bin/activate` for verification commands since reflex is venv-installed.

## Known Stubs

None. All state vars are wired to real computation:
- `company_ev_ebitda` through `company_pbv` populated from `compute_valuation_metrics()`
- `company_price_chart_data` / `company_volume_chart_data` populated from real price JSON records
- `company_shares_outstanding` populated from scraped or manually overridden value

The only scenario where values show "N/A" is when no price file exists for the company (legitimate empty state, not a stub).

## Self-Check: PASSED
