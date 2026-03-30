---
phase: 04-portfolio-optimization
plan: "01"
subsystem: portfolio-optimization
tags: [portfolio, optimization, risk-metrics, tdd, numpy, scipy]
dependency_graph:
  requires: []
  provides:
    - financial_dashboard/analysis/portfolio_optimization.py
  affects:
    - financial_dashboard/state.py (future wiring in plans 03/04)
tech_stack:
  added:
    - scipy.optimize.minimize (SLSQP method)
    - numpy log returns and covariance matrix
  patterns:
    - TDD (RED then GREEN)
    - Pure Python module with no Reflex dependencies
    - All chart-bound values returned as strings (list[dict[str,str]])
key_files:
  created:
    - financial_dashboard/analysis/portfolio_optimization.py
    - tests/test_portfolio_optimization.py
  modified:
    - tests/conftest.py
decisions:
  - All numeric values destined for Recharts state vars stored as strings per D-07 constraint
  - Sortino uses downside returns only (target=0); None if no negative returns
  - Max Drawdown from cumulative product peak-to-trough, expressed as negative float
  - CVaR 95% uses historical simulation (5th percentile average)
  - Optimization fallback to equal weights when SLSQP fails
  - PRICES_DIR defined as module-level constant for easy monkeypatching in tests
metrics:
  duration_minutes: 2
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_changed: 3
requirements_satisfied:
  - PORT-03
  - PORT-05
  - PORT-06
---

# Phase 04 Plan 01: Portfolio Optimization Module (TDD) Summary

**One-liner:** Pure-Python portfolio optimization module with 8 functions — log-return covariance, SLSQP max-Sharpe, Sortino/MaxDrawdown/CVaR, frontier sampling, weight rebalancing, sector breakdown — all 9 unit tests passing.

## What Was Built

`financial_dashboard/analysis/portfolio_optimization.py` — a standalone pure-Python module (no Reflex imports) implementing all the financial math needed for the portfolio analysis feature.

### 8 Exported Functions

| Function | Purpose |
|---|---|
| `load_price_returns` | Parse price JSONs, compute log returns per company |
| `align_returns` | Align multi-asset return arrays to equal length; return matrix |
| `compute_portfolio_returns` | Weighted portfolio return series (returns_matrix @ weights) |
| `compute_risk_metrics` | Sortino Ratio, Max Drawdown, CVaR 95% from daily returns |
| `mean_variance_optimize` | Max-Sharpe SLSQP optimization; fallback to equal weights |
| `sample_frontier` | 200 random portfolio samples tracing frontier shape |
| `rebalance_weights` | Proportional rebalance after manual weight edit |
| `compute_sector_breakdown` | Aggregate weights by sector for pie chart |

### Test Coverage

9 unit tests across all required behaviors:
- `test_weight_rebalance` — 2-asset rebalance to 80/20
- `test_weight_rebalance_zero_others` — 3-asset rebalance to 100/0/0
- `test_sector_chart_data` — Banking/Standard sector aggregation with correct colors
- `test_covariance_matrix` — load 2 mock companies, align returns, check matrix shape
- `test_optimization` — weights sum to ~100, all in bounds
- `test_risk_metrics` — sortino/max_drawdown/cvar_95 from normal returns
- `test_risk_metrics_insufficient` — all None for <10 observations
- `test_frontier_sampling` — 50 samples with string-typed risk/return keys
- `test_load_price_returns_missing_file` — skips nonexistent companies gracefully

## TDD Process

**RED:** Both test files committed with import that fails (module didn't exist yet).
**GREEN:** Module implemented; all 9 tests pass on first run.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — the module is fully functional pure math with no placeholder data or UI stubs.

## Self-Check: PASSED

All files exist and all commits verified:
- financial_dashboard/analysis/portfolio_optimization.py — FOUND
- tests/test_portfolio_optimization.py — FOUND
- tests/conftest.py — FOUND
- Commit 26c756f (test RED phase) — FOUND
- Commit b26f50d (feat GREEN phase) — FOUND
