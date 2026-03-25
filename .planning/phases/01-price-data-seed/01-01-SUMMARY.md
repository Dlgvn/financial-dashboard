---
phase: 01-price-data-seed
plan: "01"
subsystem: scraper
tags: [scraper, registry, price-data, requests, beautifulsoup4, seed-script]
dependency_graph:
  requires: []
  provides:
    - data/company_registry.json (161 MSE companies with mse_id, name, ticker, tier)
    - financial_dashboard/scraper/price_scraper.py (scrape_company_prices, save_price_data, price_file_exists)
    - financial_dashboard/scraper/registry_loader.py (find_mse_id, all_companies)
    - scripts/seed_prices.py (idempotent CLI seed script)
  affects:
    - Phase 3 (valuation charts — needs price data in data/prices/)
    - Phase 4 (portfolio covariance matrix — needs price data in data/prices/)
    - Phase 1 Plan 02 (Refresh Prices UI — imports from price_scraper and registry_loader)
tech_stack:
  added:
    - requests>=2.32.0 (HTTP GET to old.mse.mn)
    - beautifulsoup4>=4.12.0 (HTML table parsing)
  patterns:
    - Module-level lazy-load cache for registry (_registry global)
    - price_filename() sanitization strips quotes and unsafe chars
    - Normalization via remove-quotes + collapse-spaces + lowercase for name matching
key_files:
  created:
    - data/company_registry.json
    - financial_dashboard/scraper/__init__.py
    - financial_dashboard/scraper/price_scraper.py
    - financial_dashboard/scraper/registry_loader.py
    - scripts/seed_prices.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_price_scraper.py
    - tests/test_registry_loader.py
  modified:
    - requirements.txt (added requests>=2.32.0, beautifulsoup4>=4.12.0)
    - .gitignore (added !data/company_registry.json exception)
decisions:
  - "Registry name normalization removes ALL quote chars and collapses multiple spaces (not just leading/trailing strip) to handle index.json format '\" Премиум Нэксус \" ХК'"
  - "company_registry.json added as gitignore exception: it is project infrastructure, not user-uploaded data"
  - "Placeholder names Company_{mse_id} with ticker MSE{mse_id} for 154 non-demo companies — correct names added when companies are uploaded"
metrics:
  duration_minutes: 12
  completed: "2026-03-25"
  tasks_completed: 3
  tasks_total: 3
  files_created: 9
  files_modified: 2
---

# Phase 01 Plan 01: Registry, Scraper Module, Seed Script, and Tests Summary

**One-liner:** Company registry (161 MSE entries), requests+BeautifulSoup4 scraper with quote-normalized name lookup, and idempotent CLI seed script with --force flag.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create company registry and requirements | a49237d | data/company_registry.json, requirements.txt, .gitignore |
| 2 | Create scraper module, registry loader, and test infrastructure | 97c3d7f | financial_dashboard/scraper/*.py, tests/* |
| 3 | Create idempotent seed script | 038d286 | scripts/seed_prices.py |

## What Was Built

### Company Registry (data/company_registry.json)
161 MSE companies with four fields each: `name`, `mse_id`, `ticker`, `tier`.
- 7 demo companies: correct Mongolian names and confirmed MSE IDs
- 154 non-demo companies: `Company_{mse_id}` / `MSE{mse_id}` placeholders, assigned correct tier (I/II/III)
- Class I: 24 companies, Class II: 43 companies, Class III: 94 companies

### Price Scraper (financial_dashboard/scraper/price_scraper.py)
- `scrape_company_prices(mse_id, company_name)` — fetches `http://old.mse.mn/en/company/{mse_id}`, parses `trade_history_result` table, returns sorted OHLCV list
- `save_price_data(company_name, mse_id, records)` — writes to `data/prices/{name}.json` with company, mse_id, scraped_at, records fields
- `price_file_exists(company_name)` — idempotency check
- `price_filename(company_name)` — sanitizes for filesystem (strips quotes and unsafe chars)

### Registry Loader (financial_dashboard/scraper/registry_loader.py)
- `find_mse_id(company_name)` — normalizes both query and registry names (remove all quotes, collapse spaces, lowercase) so `'" Премиум Нэксус " ХК'` maps correctly to ID 557
- `all_companies()` — returns full 161-entry list
- Module-level lazy-load cache (`_registry`)

### Seed Script (scripts/seed_prices.py)
- Iterates all 161 companies; skips companies with existing price files by default
- `--force` flag to re-scrape all companies
- Per-company exceptions caught and logged; run never crashes
- 0.5s politeness delay between requests
- Summary log: `OK={n} SKIPPED={n} FAILED={n}`

### Test Suite (tests/)
9 unit tests, all passing, no live HTTP calls:
- `test_parse_price_table` — mocked HTTP, checks sort order and comma stripping
- `test_no_price_table_raises` — ValueError when no table present
- `test_save_and_exists` — file creation and structure verification
- `test_idempotency_check` — True/False for existing/non-existent files
- `test_price_filename_sanitization` — quote stripping
- `test_find_known_ids` — APU=90, Khan Bank=563
- `test_find_with_quotes_normalization` — `'" Премиум Нэксус " ХК'` → 557
- `test_find_unknown_raises` — KeyError for unknown names
- `test_all_companies` — returns 3 from sample registry

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed registry name normalization for embedded quotes**
- **Found during:** Task 2 (running tests)
- **Issue:** `_normalize()` used `strip().strip('"').strip()` which only removed leading/trailing quotes. The input `'" Премиум Нэксус " ХК'` has an interior quote after removing the leading `"`, producing `'премиум нэксус " хк'` vs registry entry `'премиум нэксус хк'`.
- **Fix:** Changed normalization to `name.replace('"', "").replace("'", "")` followed by `" ".join(result.split())` to collapse all spaces after quote removal.
- **Files modified:** financial_dashboard/scraper/registry_loader.py
- **Commit:** 97c3d7f (included in Task 2 commit)

**2. [Rule 2 - Missing] Added .gitignore exception for company_registry.json**
- **Found during:** Task 1 (git add attempt)
- **Issue:** `data/*.json` gitignore rule blocked tracking `company_registry.json`, which is project infrastructure (not user data).
- **Fix:** Added `!data/company_registry.json` exception to `.gitignore`.
- **Files modified:** .gitignore
- **Commit:** a49237d (included in Task 1 commit)

## Verification Results

All success criteria met:
- `pytest tests/test_price_scraper.py tests/test_registry_loader.py -x -q` — 9 passed
- `python scripts/seed_prices.py --help` — exits 0, shows --force flag
- `from financial_dashboard.scraper.price_scraper import scrape_company_prices, save_price_data, price_file_exists` — imports ok
- `len(all_companies())` — prints 161
- `find_mse_id('АПУ')` — prints 90

## Known Stubs

None. All code is fully wired for its intended purpose (CLI seed script + unit-tested module). The 154 placeholder company names in `company_registry.json` are documented as intentional — their correct Mongolian names will be populated when those companies are uploaded by users.

## Self-Check: PASSED
