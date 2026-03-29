---
phase: 4
slug: portfolio-optimization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing in project) |
| **Config file** | none — pytest discovers `tests/` automatically |
| **Quick run command** | `pytest tests/test_portfolio_optimization.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_portfolio_optimization.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-W0-01 | 01 | 0 | PORT-01..06 | unit stubs | `pytest tests/test_portfolio_optimization.py -x` | ❌ Wave 0 | ⬜ pending |
| 4-01-01 | 01 | 1 | PORT-01 | unit | `pytest tests/test_portfolio_optimization.py::test_weight_rebalance -x` | ❌ Wave 0 | ⬜ pending |
| 4-01-02 | 01 | 1 | PORT-02 | unit | `pytest tests/test_portfolio_optimization.py::test_sector_chart_data -x` | ❌ Wave 0 | ⬜ pending |
| 4-02-01 | 02 | 1 | PORT-03 | unit | `pytest tests/test_portfolio_optimization.py::test_covariance_matrix -x` | ❌ Wave 0 | ⬜ pending |
| 4-02-02 | 02 | 1 | PORT-04 | unit | `pytest tests/test_portfolio_optimization.py::test_optimization -x` | ❌ Wave 0 | ⬜ pending |
| 4-02-03 | 02 | 1 | PORT-05 | unit | `pytest tests/test_portfolio_optimization.py::test_risk_metrics -x` | ❌ Wave 0 | ⬜ pending |
| 4-02-04 | 02 | 1 | PORT-06 | unit | `pytest tests/test_portfolio_optimization.py::test_frontier_sampling -x` | ❌ Wave 0 | ⬜ pending |
| 4-03-01 | 03 | 2 | PORT-01 | manual | See manual verifications | — | ⬜ pending |
| 4-03-02 | 03 | 2 | PORT-02 | manual | See manual verifications | — | ⬜ pending |
| 4-04-01 | 04 | 2 | PORT-03..06 | manual | See manual verifications | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_portfolio_optimization.py` — covers PORT-01 through PORT-06 (stubs that fail until implementation)
- [ ] `tests/conftest.py` — extend existing `tmp_data_dir` fixture with a `sample_price_json` fixture returning mock price data (2 companies, 100 records each with `{date, open, high, low, close, volume}` string schema)

*Existing infrastructure: pytest already installed; conftest.py exists with tmp_data_dir fixture.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Weight input auto-normalizes to 100% | PORT-01 | Reflex UI interaction | Add 2 holdings, type weight for one, verify other updates automatically in browser |
| Sector donut chart renders | PORT-02 | Visual chart rendering | Add holdings with different sectors, verify donut chart appears on Analysis tab |
| Efficient frontier chart visible with current position highlighted | PORT-06 | Visual chart rendering | Add 2+ companies with price data, open Analysis tab, verify scatter plot with highlighted point |
| Optimization table displays current vs optimal weights | PORT-04 | Visual UI | Add 2+ companies with price data, verify optimization table on Analysis tab |
| Analysis tab placeholder shown with <2 holdings | PORT-03,04,05,06 | UI state | Clear holdings, verify placeholder message shown instead of charts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
