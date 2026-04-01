---
phase: 05-deployment-documentation
plan: 03
subsystem: documentation
tags: [inline-comments, secrets-audit, portfolio-optimization, beneish, piotroski, header-mapping]
dependency_graph:
  requires: []
  provides: [DOCS-02, DOCS-03]
  affects: [portfolio_optimization.py, ratios.py, header_mappings.py, excel_parser.py]
tech_stack:
  added: []
  patterns: [intent-explaining comments, WHY not WHAT comment style]
key_files:
  modified:
    - financial_dashboard/analysis/portfolio_optimization.py
    - financial_dashboard/analysis/ratios.py
    - financial_dashboard/parser/header_mappings.py
    - financial_dashboard/parser/excel_parser.py
decisions:
  - Comment style: explain WHY (formula source, statistical assumption, design decision) not what the code does
  - Secrets audit: clean — no hardcoded API keys or passwords in any Python file; .env confirmed in .gitignore
metrics:
  duration_seconds: 595
  completed_date: "2026-04-01T03:40:27Z"
  tasks_completed: 3
  files_modified: 4
requirements_satisfied: [DOCS-02, DOCS-03]
---

# Phase 05 Plan 03: Inline Comments and Secrets Audit Summary

**One-liner:** Intent-explaining inline comments added to 6 portfolio math targets, 8 Beneish/Piotroski/composite targets, and 5 Mongolian header-mapping architecture targets; secrets audit confirmed clean.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add inline comments to portfolio_optimization.py | 9df03b9 | financial_dashboard/analysis/portfolio_optimization.py |
| 2 | Add inline comments to ratios.py, header_mappings.py, excel_parser.py | d5aba7a | financial_dashboard/analysis/ratios.py, financial_dashboard/parser/header_mappings.py, financial_dashboard/parser/excel_parser.py |
| 3 | Secrets audit (DOCS-03) | (no commit — audit only, no changes needed) | .gitignore confirmed |

## What Was Built

### Task 1: portfolio_optimization.py — 6 comment targets

All 6 non-obvious math blocks annotated with WHY explanations:

1. **Log returns** (line ~78): explains log-normality assumption required for mean-variance optimization
2. **252-day annualization** (line ~171): explains 252 trading-day convention and i.i.d. scaling rules (linear for returns, √252 for volatility)
3. **CVaR at 95%** (line ~185): identifies it as Expected Shortfall = mean of tail below 5th percentile; notes historical simulation (no parametric distribution)
4. **SLSQP optimizer** (line ~228): explains why neg-Sharpe is minimized, what SLSQP is, why bounds enforce long-only constraint
5. **Monte Carlo frontier** (line ~291): distinguishes from parametric Markowitz sweep; notes sufficient for frontier shape visualization
6. **Fixed seed** (line ~283): explains determinism for stable page loads

### Task 2: ratios.py — 8 comment targets

All forensic model blocks annotated:

- **F4 accruals**: Sloan 1996 citation for earnings persistence signal
- **F7 always None**: MSE shares outstanding data limitation documented
- **DSRI**: Beneish 1999 citation; premature revenue recognition signal
- **GMI**: Declining margin as manipulation incentive; GMI > 1.0 interpretation
- **AQI**: Off-balance-sheet risk via non-current, non-PPE asset growth
- **DEPI always None**: MSE depreciation line item unavailability documented
- **M-Score coefficients**: Beneish 1999 probit regression; -4.84 intercept; -1.78 and -2.22 thresholds explained
- **Composite score weights**: Profitability 25%/Liquidity 20%/Solvency 20%/Activity 15%/Altman 10%/Piotroski 10%; Beneish penalty logic; available-data redistribution

### Task 2: header_mappings.py — 5 comment targets

Architecture rationale documented:

- **Module docstring**: 7-dictionary architecture — false match prevention between bank/insurance/standard terminology
- **normalize_header**: MSE file inconsistency problem (spacing, capitalization, trailing whitespace)
- **match_header sort**: Length-descending ordering — "урт хугацаат зээл" before "зээл" prevents generic field overwrite
- **Duplicate cash keys**: Three comma-space/conjunction variants across MSE company file versions
- **SHEET_TYPE_PATTERNS abbreviations**: сбд/одт/мгт decoded with full Mongolian names

### Task 2: excel_parser.py — 2 comment targets

Per D-13 requirement:

- **HEADERS_BY_TYPE dispatch site**: 7-dictionary false-match prevention rationale at the call site
- **_detect_sheet_type**: Pre-detection of framework type before mapping; 7-dictionary dispatch explanation

### Task 3: Secrets Audit Results

| Check | Result |
|-------|--------|
| `.env` in `.gitignore` | PASS — `.env` on line 1 of .gitignore |
| `ALPHA_VANTAGE_API_KEY` hardcoded | PASS — 0 matches |
| `password=` hardcoded | PASS — 0 matches |
| `DATABASE_URL=` hardcoded | PASS — 0 matches |
| `.env` file staged in git | PASS — not staged |
| `.env` file in `data/` | PASS — does not exist |

Railway deployment requires zero secrets. Only `API_URL` (public HTTPS URL) is set post-deploy in Railway dashboard — this is a public URL, not a secret.

## Verification

All files parse without syntax errors:
```
OK: financial_dashboard/analysis/portfolio_optimization.py
OK: financial_dashboard/analysis/ratios.py
OK: financial_dashboard/parser/header_mappings.py
```

Key comment markers confirmed present:
- `log-normality` in portfolio_optimization.py
- `252 trading` in portfolio_optimization.py
- `Expected Shortfall` in portfolio_optimization.py
- `SLSQP` in portfolio_optimization.py
- `Monte Carlo` in portfolio_optimization.py
- `deterministic` in portfolio_optimization.py (seed comment)
- `Beneish 1999` in ratios.py
- `Sloan 1996` in ratios.py
- `-1.78` in ratios.py (threshold comment)
- `profitability 25%` in ratios.py
- `entirely different` in header_mappings.py (architecture reason)
- `Longer patterns checked first` in header_mappings.py (sort reason)
- `7 separate` and `wrong field` in excel_parser.py (D-13 call site)

## Deviations from Plan

None — plan executed exactly as written.

The existing `header_mappings.py` module docstring was enhanced (not replaced) since it already partially covered matching behavior. The seven-dictionary architecture explanation and false-match rationale were added to the existing docstring. All other comments were added at the exact locations specified in the plan.

## Known Stubs

None — this plan added comments only. No data stubs introduced.

## Self-Check: PASSED

All key files confirmed present. Both task commits (9df03b9, d5aba7a) confirmed in git log.
