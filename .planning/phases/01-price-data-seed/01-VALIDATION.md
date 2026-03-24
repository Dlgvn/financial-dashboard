---
phase: 1
slug: price-data-seed
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_price_scraper.py tests/test_registry_loader.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_price_scraper.py tests/test_registry_loader.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | SCRP-01, SCRP-03 | unit | `pytest tests/test_registry_loader.py -x -q` | Yes (Wave 0) | ⬜ pending |
| 1-01-02 | 01 | 1 | SCRP-01, SCRP-02 | unit | `pytest tests/test_price_scraper.py -x -q` | Yes (Wave 0) | ⬜ pending |
| 1-02-01 | 02 | 2 | SCRP-04 | unit | `pytest tests/test_price_state.py -x -q` | Yes (Wave 0) | ⬜ pending |
| 1-02-02 | 02 | 2 | SCRP-04 | integration | `python -c "from financial_dashboard.financial_dashboard import index; print('ok')"` | N/A | ⬜ pending |
| 1-02-03 | 02 | 2 | SCRP-04 | manual | Visual verification of Refresh Prices button | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_price_scraper.py` — tests for scrape_company_prices, save_price_data, price_file_exists, price_filename (created in Plan 01, Task 2)
- [x] `tests/test_registry_loader.py` — tests for find_mse_id, all_companies (created in Plan 01, Task 2)
- [x] `tests/test_price_state.py` — tests for UploadState price refresh state vars (created in Plan 02, Task 1)
- [x] `tests/conftest.py` — shared fixtures: tmp_data_dir, sample_registry, sample_html_with_prices, sample_html_no_table (created in Plan 01, Task 2)
- [x] `pytest` install — `pip install pytest requests beautifulsoup4`

---

## Test Function Reference

### tests/test_price_scraper.py (Plan 01, Task 2)
- `test_parse_price_table` — SCRP-01: Verifies HTML table parsing returns correct OHLCV dicts
- `test_no_price_table_raises` — SCRP-01: Verifies ValueError on missing table
- `test_save_and_exists` — SCRP-02: Verifies JSON file creation and price_file_exists
- `test_idempotency_check` — SCRP-02: Verifies idempotency via price_file_exists
- `test_price_filename_sanitization` — SCRP-02: Verifies filename sanitization

### tests/test_registry_loader.py (Plan 01, Task 2)
- `test_find_known_ids` — SCRP-03: Verifies find_mse_id returns correct IDs
- `test_find_with_quotes_normalization` — SCRP-03: Verifies quote-normalized lookup
- `test_find_unknown_raises` — SCRP-03: Verifies KeyError on unknown company
- `test_all_companies` — SCRP-03: Verifies all_companies returns full registry

### tests/test_price_state.py (Plan 02, Task 1)
- `test_state_vars_exist` — SCRP-04: Verifies UploadState has price refresh state vars
- `test_refresh_prices_method_exists` — SCRP-04: Verifies refresh_prices method exists

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All 161 price files exist after seed run | SCRP-02 | Requires live network access to old.mse.mn | Run `python scripts/seed_prices.py`, then `ls data/prices/ \| wc -l` should output 161 |
| Refresh button shows loading state and per-company feedback | SCRP-04 | Requires running Reflex app + browser | Start app, upload a company file, click Refresh Prices, observe UI feedback |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
