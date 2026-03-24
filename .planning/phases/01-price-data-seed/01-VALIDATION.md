---
phase: 1
slug: price-data-seed
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Quick run command** | `pytest tests/test_scraper.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_scraper.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | SCRP-01 | unit | `pytest tests/test_scraper.py::test_company_registry -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | SCRP-02 | integration | `pytest tests/test_scraper.py::test_price_scrape -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 2 | SCRP-03 | integration | `pytest tests/test_scraper.py::test_refresh_button -x -q` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 2 | SCRP-04 | unit | `pytest tests/test_scraper.py::test_error_handling -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scraper.py` — stubs for SCRP-01 through SCRP-04
- [ ] `tests/conftest.py` — shared fixtures (mock HTTP responses, temp data dir)
- [ ] `pytest` install — `pip install pytest requests-mock`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All 161 price files exist after seed run | SCRP-02 | Requires live network access to old.mse.mn | Run `python scripts/seed_prices.py`, then `ls data/prices/ \| wc -l` should output 161 |
| Refresh button shows loading state and per-company feedback | SCRP-03 | Requires running Reflex app + browser | Start app, upload a company file, click Refresh Prices, observe UI feedback |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
