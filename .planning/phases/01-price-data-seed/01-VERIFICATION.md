---
phase: 01-price-data-seed
verified: 2026-03-25T12:45:00Z
status: human_needed
score: 7/8 must-haves verified
re_verification: true
  previous_status: gaps_found
  previous_score: 6/8
  gaps_closed:
    - "data/prices/ directory exists with 7 JSON files for demo companies — Gap 1 CLOSED"
    - "seed_prices.py supports --companies flag for targeted seeding"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Refresh Prices button end-to-end flow"
    expected: "Clicking Refresh Prices shows a spinner in the button, per-company rows appear one at a time in the log panel (green check icon for success, red X for error, with company name and record count). After completion, button re-enables and summary text shows (e.g. '7 updated, 0 failed')."
    why_human: "Requires running Reflex app with live WebSocket connection. Streaming yield behavior and Reflex reactivity cannot be tested programmatically without the full stack."
---

# Phase 01: Price Data Seed Verification Report

**Phase Goal:** Seed real OHLCV price data for demo companies from old.mse.mn so the dashboard has data to display.
**Verified:** 2026-03-25
**Status:** human_needed
**Re-verification:** Yes — after gap closure (Plan 03)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `scrape_company_prices(90, 'APU')` returns list of dicts with keys date, open, high, low, close, volume | VERIFIED | price_scraper.py confirmed; test_parse_price_table passes |
| 2 | `save_price_data` creates `data/prices/{company}.json` with company, mse_id, scraped_at, records fields | VERIFIED | All 7 live files confirmed to have these 4 top-level keys |
| 3 | `find_mse_id('APU')` returns 90; all 7 demo companies resolve correctly | VERIFIED | registry_loader.py; CLI confirmed 90; test_find_known_ids passes |
| 4 | seed_prices.py skips companies whose price file already exists (idempotent) | VERIFIED | --force flag present; SKIP logic at lines 60-63 confirmed |
| 5 | Per-company scrape errors are caught and logged without crashing the full seed run | VERIFIED | scripts/seed_prices.py try/except confirmed |
| 6 | `data/prices/{company}.json` exists for all 7 demo companies — price data available for any upload | VERIFIED | All 7 files present: APU 2811 records, Darhan 1946, Suu 2473, Mandal 1836, Monos 1679, Premium Nexus 1078, Khan Bank 717 |
| 7 | User sees a "Refresh Prices" button on the upload/home page | VERIFIED | financial_dashboard.py lines 95-101; button, on_click=UploadState.refresh_prices, disabled state all present |
| 8 | After scraping completes, per-company success/error feedback is visible in the UI | PARTIAL | Code fully wired (spinner, foreach log, summary text); runtime behavior requires human verification in running app |

**Score:** 7/8 truths verified (0 failed, 1 partial/human-needed)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/company_registry.json` | 161 MSE companies with name, mse_id, ticker, tier | VERIFIED | 161 entries confirmed |
| `financial_dashboard/scraper/price_scraper.py` | scrape_company_prices, save_price_data, price_file_exists, price_filename | VERIFIED | All 4 functions present; 5 unit tests pass |
| `financial_dashboard/scraper/registry_loader.py` | find_mse_id, all_companies with quote-normalized lookup | VERIFIED | Normalization and lazy-load cache confirmed; 4 tests pass |
| `scripts/seed_prices.py` | Idempotent CLI seed with --force and --companies flags | VERIFIED | `--companies` flag added in Plan 03; `--help` shows both flags; run_seed() accepts target_names |
| `data/prices/` | 7 price JSON files for demo companies | VERIFIED | Directory exists; all 7 files present with real OHLCV records |
| `data/prices/АПУ.json` | APU price history | VERIFIED | 2811 records, mse_id=90, all OHLCV keys present |
| `data/prices/Хаан банк.json` | Khan Bank price history | VERIFIED | 717 records, mse_id=563, all OHLCV keys present |
| `financial_dashboard/state.py` | is_refreshing_prices, price_refresh_log, price_refresh_summary, refresh_prices handler | VERIFIED | All 3 state vars and handler present; scraper imports wired |
| `financial_dashboard/financial_dashboard.py` | Refresh Prices button in index page | VERIFIED | Button, spinner (rx.cond), foreach log, summary text all confirmed |
| `tests/test_price_scraper.py` | 5 unit tests for scraper functions | VERIFIED | 9 tests pass (combined with registry); 0.12s |
| `tests/test_registry_loader.py` | 4 unit tests for registry lookup | VERIFIED | Included in 9 passed above |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `scripts/seed_prices.py` | `financial_dashboard/scraper/price_scraper.py` | `from financial_dashboard.scraper.price_scraper import` | WIRED | Confirmed line 29 |
| `scripts/seed_prices.py` | `data/prices/` | `save_price_data()` | WIRED | 7 files confirmed created by commit 5146ce2 |
| `scripts/seed_prices.py` | target_names filtering | `--companies` argparse + set-based filter | WIRED | Lines 110-116 confirmed; help output shows flag |
| `financial_dashboard/state.py` | `financial_dashboard/scraper/price_scraper.py` | `from .scraper.price_scraper import scrape_company_prices, save_price_data` | WIRED | Confirmed |
| `financial_dashboard/financial_dashboard.py` | `financial_dashboard/state.py` | `UploadState.refresh_prices` on_click | WIRED | Lines 95-101 confirmed |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `data/prices/АПУ.json` | records (2811 OHLCV dicts) | HTTP scrape of old.mse.mn/en/company/90 via price_scraper.py | Yes — verified 2811 records with date/open/high/low/close/volume | FLOWING |
| `data/prices/Хаан банк.json` | records (717 OHLCV dicts) | HTTP scrape of old.mse.mn/en/company/563 | Yes — verified 717 records | FLOWING |
| `financial_dashboard/financial_dashboard.py` (price log) | `UploadState.price_refresh_log` | refresh_prices() in state.py — appends per-company dicts during live scrape | Yes (conditional on Refresh Prices click) | FLOWING (requires running app) |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| data/prices/ has 7 files | `ls data/prices/ \| wc -l` | 7 | PASS |
| seed_prices.py --help shows --companies | `python scripts/seed_prices.py --help` | Shows `--companies COMPANIES` with description | PASS |
| All 7 price files have valid OHLCV structure | `python -c "import json,os; ..."` | ALL 7 DEMO COMPANIES VERIFIED | PASS |
| Scraper/registry tests pass | `pytest tests/test_price_scraper.py tests/test_registry_loader.py -x -q` | 9 passed in 0.12s | PASS |
| price_file_exists('АПУ') returns True | `python -c "from financial_dashboard.scraper.price_scraper import price_file_exists; print(price_file_exists('АПУ'))"` | True | PASS |
| Commit 5146ce2 exists in git history | `git show --stat 5146ce2` | Confirmed: feat(01-03) commit with 7 price files + seed_prices.py | PASS |
| Refresh Prices button end-to-end | Requires running Reflex app | N/A | SKIP (human needed) |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCRP-01 | 01-01-PLAN.md | System scrapes historical OHLCV data from old.mse.mn using requests + BeautifulSoup4 | SATISFIED | price_scraper.py confirmed; 5 unit tests pass |
| SCRP-02 | 01-01-PLAN.md, 01-03-PLAN.md | System stores price history as JSON in `data/prices/{company}.json` | SATISFIED | 7 files present with correct structure: company, mse_id, scraped_at, records |
| SCRP-03 | 01-01-PLAN.md, 01-03-PLAN.md | System maintains mapping of all 7 demo company names to MSE IDs | SATISFIED | All 7 files have correct mse_ids; find_mse_id() resolves all demo names; 4 registry tests pass |
| SCRP-04 | 01-02-PLAN.md | User can trigger Refresh Prices from upload/home page; system shows loading state and feedback | SATISFIED (code) / HUMAN-NEEDED (runtime) | Button, spinner, foreach log, summary text all wired; runtime requires human verification |

**Orphaned requirements:** None.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | No TODO/FIXME/placeholder comments found in phase 1 files | — | — |

No code anti-patterns detected. The price JSON files contain real scraped data (not stubs).

---

### Human Verification Required

#### 1. Refresh Prices Button — End-to-End UI Flow

**Test:** Start the Reflex app (`reflex run`), open http://localhost:3000, click "Load 7 MSE Companies" (demo mode), scroll to the "Price Data" section, click "Refresh Prices".
**Expected:** Button disables and shows spinner during operation. Per-company result rows appear one at a time (green check icon for success, red X for error, with company name and record count). After completion, button re-enables and summary text shows (e.g. "7 updated, 0 failed"). Because `data/prices/` files already exist from the seed run, all 7 should be skipped (idempotency) — the UI should show 0 updated, 7 skipped.
**Why human:** Requires running Reflex app with live WebSocket connection. Streaming yield behavior and Reflex reactivity cannot be tested programmatically without the full stack.

---

## Re-Verification: Gap Closure Summary

**Previous status:** gaps_found (6/8)
**Current status:** human_needed (7/8)

### Gaps Closed

| Gap | Closed By | Evidence |
|-----|-----------|---------|
| Gap 1: `data/prices/` does not exist (SCRP-02 partial) | Plan 03 — `python scripts/seed_prices.py --companies "..."` executed | `ls data/prices/` shows 7 files; all have real OHLCV records |
| seed_prices.py lacked --companies flag | Plan 03 — `--companies` argparse flag added to seed_prices.py | `--help` output confirms; lines 110-116 wired |

### Gaps Remaining

None — the only remaining item is the pre-existing human-verification checkpoint for the Refresh Prices UI flow (Truth 8 / SCRP-04 runtime). This was already documented as human-needed in the initial verification and no code regression was introduced.

### Regressions

None — 9 scraper/registry tests still pass; seed_prices.py is backwards-compatible (--companies is optional; default behavior is all companies).

---

## Gaps Summary

No automated gaps remain. The single outstanding item (Truth 8, SCRP-04 runtime UI behavior) requires a human to start the Reflex app and click Refresh Prices to confirm the streaming feedback renders correctly. This is a verification checkpoint, not a code defect — the implementation is fully wired.

The core phase goal is achieved: real OHLCV price data for all 7 demo companies exists in `data/prices/`, the scraper module is tested, and the UI has a working Refresh Prices button.

---

_Verified: 2026-03-25_
_Verifier: Claude (gsd-verifier)_
