---
phase: 01-price-data-seed
plan: "03"
subsystem: scraper
tags: [price-data, seed, mse, ohlcv, cli]
dependency_graph:
  requires: [01-01, 01-02]
  provides: [data/prices/*.json, --companies CLI flag]
  affects: [Phase 3 valuation charts, Phase 4 portfolio optimization]
tech_stack:
  added: []
  patterns: [argparse --companies flag, targeted seed with set-based filtering]
key_files:
  created:
    - data/prices/АПУ.json
    - data/prices/Дархан нэхий ХК.json
    - data/prices/Сүү.json
    - data/prices/Мандал даатгал.json
    - data/prices/Моносхүнс.json
    - data/prices/Премиум Нэксус ХК.json
    - data/prices/Хаан банк.json
  modified:
    - scripts/seed_prices.py
decisions:
  - Added --companies CLI flag to seed_prices.py for targeted per-company seeding (~17s for 7 companies vs ~80min for all 161)
  - run_seed() accepts optional target_names list; set-based filtering against registry names
metrics:
  duration: 17 minutes
  completed: 2026-03-25
  tasks_completed: 2
  files_created: 7
  files_modified: 1
requirements_closed: [SCRP-02, SCRP-03]
---

# Phase 01 Plan 03: Demo Price Seed Summary

**One-liner:** Seeded 7 demo companies with real OHLCV data from old.mse.mn (717–2811 records each) via new `--companies` CLI flag on seed_prices.py.

## What Was Built

Gap 1 from VERIFICATION.md is now closed. The `data/prices/` directory was empty because the seed script had never been executed against the demo companies. This plan:

1. Added `--companies` flag to `scripts/seed_prices.py` — accepts a comma-separated list of company names to seed instead of all 161 MSE companies.
2. Enhanced `run_seed()` with an optional `target_names` parameter and set-based filtering logic.
3. Ran the seeder against all 7 demo companies, producing real OHLCV data files.

## Seeded Companies

| Company | MSE ID | Records |
|---------|--------|---------|
| АПУ | 90 | 2811 |
| Дархан нэхий ХК | 71 | 1946 |
| Сүү | 135 | 2473 |
| Мандал даатгал | 547 | 1836 |
| Моносхүнс | 551 | 1679 |
| Премиум Нэксус ХК | 557 | 1078 |
| Хаан банк | 563 | 717 |

## Verification Results

- `ls data/prices/ | wc -l` → 7
- `python scripts/seed_prices.py --help` shows `--companies` flag
- `pytest tests/test_price_scraper.py tests/test_registry_loader.py -x -q` → 9 passed
- `price_file_exists('АПУ')` → True
- Re-running seeder with same companies → SKIPPED=2 (idempotency confirmed)
- All 7 JSON files have `company`, `mse_id`, `scraped_at`, `records` fields with date/open/high/low/close/volume keys

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add --companies flag and seed 7 demo companies | 5146ce2 | scripts/seed_prices.py, data/prices/*.json (7 files) |
| 2 | Verify all 7 demo price files and run tests | (verification only) | - |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all 7 price files contain real scraped OHLCV data from old.mse.mn.

## Self-Check: PASSED
