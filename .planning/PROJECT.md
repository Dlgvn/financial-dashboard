# MSE Analytica

## What This Is

MSE Analytica is a Mongolian-native portfolio and fundamental analysis platform for companies listed on the Mongolian Stock Exchange (MSE). Users upload raw Excel files from mse.mn, the platform auto-parses Mongolian-language financial statements, computes 26+ financial ratios plus three forensic models (Piotroski F-Score, Beneish M-Score, Altman Z-Score), scrapes historical price data for valuation metrics, and runs mean-variance portfolio optimization — covering the complete 6-step fundamental analysis workflow.

## Core Value

Upload an MSE Excel file and get a complete fundamental analysis — ratios, forensic scores, valuation, and portfolio optimization — in one place, in one click.

## Current State

**v1.1 MSE Analytica MVP — shipped 2026-04-01**

- 5 phases, 15 plans complete
- ~6,200 LOC Python across financial_dashboard/
- 7 demo companies pre-loaded (no upload required)
- Railway deployment infrastructure ready (Dockerfile, railway.toml) — pending live URL
- Capstone-quality README with full methodology documentation

## Requirements

### Validated

<!-- Shipped in v1.0 MVP -->
- ✓ Upload `.xls`/`.xlsx` MSE Excel files via drag-drop — v1.0
- ✓ Auto-parse Mongolian-language Balance Sheet, Income Statement, Cash Flow — v1.0
- ✓ Compute 26 financial ratios across 6 categories (standard companies) — v1.0
- ✓ Piotroski F-Score (9 criteria, F7 always N/A) — v1.0
- ✓ Beneish M-Score (8 indices, DEPI always N/A) — v1.0
- ✓ Altman Z-Score with zone classification — v1.0
- ✓ Composite Health Score 0–100 — v1.0
- ✓ Company screener page with health badge — v1.0
- ✓ Portfolio page: add/remove companies, equal weighting — v1.0
- ✓ Demo mode: 7 MSE companies pre-loaded — v1.0
- ✓ Dark OLED theme (Tailwind v4) — v1.0
- ✓ Bank ratio engine built (19 ratios) — v1.0
- ✓ Insurance ratio engine built (15+ ratios) — v1.0

<!-- Shipped in v1.1 -->
- ✓ **SCRP-01**: Historical price scraper (requests + BeautifulSoup4, old.mse.mn) — v1.1
- ✓ **SCRP-02**: Price history stored as JSON in data/prices/ — v1.1
- ✓ **SCRP-03**: 7 demo companies mapped to MSE company IDs — v1.1
- ✓ **SCRP-04**: Refresh Prices button with streaming UI feedback — v1.1
- ✓ **SECTOR-01**: sector field added to index.json for all 7 companies — v1.1
- ✓ **SECTOR-02**: Bank routing (Хаан банк → NIM, NPL, CAR, LDR) — v1.1
- ✓ **SECTOR-03**: Insurance routing (Мандал даатгал → Loss/Combined Ratio) — v1.1
- ✓ **COMP-01**: 26+ ratios organized by category on company detail — v1.1
- ✓ **COMP-02**: 5-tab company page (Ratios / Forensic / Valuation / DuPont / Red Flags) — v1.1
- ✓ **COMP-03**: DuPont ROE decomposition tab — v1.1
- ✓ **COMP-04**: Red Flags auto-detection (5+ patterns) — v1.1
- ✓ **COMP-05**: Composite health score gauge visualization — v1.1
- ✓ **COMP-06**: Radar chart for 6 health categories — v1.1
- ✓ **COMP-07**: Beneish M-Score bar chart with threshold line — v1.1
- ✓ **SCREEN-01**: Screener sector filter dropdown — v1.1
- ✓ **SCREEN-02**: Screener sortable columns — v1.1
- ✓ **VAL-01**: EV/EBITDA, FCF yield, P/E, P/BV on company page — v1.1
- ✓ **VAL-02**: Historical price line chart on company page — v1.1
- ✓ **VAL-03**: Manual shares outstanding input unlocks P/E and P/BV — v1.1
- ✓ **PORT-01**: Manual portfolio weights with auto-normalize — v1.1
- ✓ **PORT-02**: Sector breakdown donut chart — v1.1
- ✓ **PORT-03**: Covariance matrix from scraped price history — v1.1
- ✓ **PORT-04**: Mean-variance SLSQP optimization, optimal vs current weights — v1.1
- ✓ **PORT-05**: Sortino Ratio, Maximum Drawdown, CVaR (95%) — v1.1
- ✓ **PORT-06**: Efficient frontier scatter plot — v1.1
- ✓ **DEPLOY-01**: Railway deployment infrastructure ready (Dockerfile + railway.toml) — v1.1
- ✓ **DEPLOY-02**: 14 demo data files committed to git — v1.1
- ✓ **DOCS-01**: 10-section capstone README (screenshots pending live deploy) — v1.1
- ✓ **DOCS-02**: Inline WHY-comments on portfolio math, Beneish, header mappings — v1.1
- ✓ **DOCS-03**: No hardcoded secrets; .env gitignored — v1.1

### Active

<!-- v1.2 candidates -->
- [ ] Railway live deploy: set API_URL env var, confirm 7 companies load at public URL
- [ ] README screenshots: 2+ screenshots embedded after Railway deploy
- [ ] Sector-specific screener filters (sector dropdown already built, ensure fully wired)

### Out of Scope

- Black-Litterman user views UI — after mean-variance proves stable
- PDF report export — post-milestone
- Language toggle (MN/EN) — future milestone
- SWOT analysis — qualitative, cannot be automated
- Management/strategy research — requires external sources
- Live/real-time price feeds — no MSE API exists
- User accounts / authentication — out of scope per vision doc
- Mobile-responsive layout — desktop-first

## Context

- **Framework:** Reflex 0.8.26 (Python → React, server-sent events)
- **Styling:** Tailwind CSS v4 via TailwindV4Plugin, dark OLED theme (bg-slate-950)
- **Storage:** Flat JSON files in data/ (partially gitignored); index.json is the manifest
- **Price data:** old.mse.mn/en/company/{id} — ~1,400–2,800 records/company
- **Parser:** 7 Mongolian→English header dictionaries in header_mappings.py
- **Analysis:** ratios.py, bank_ratios.py, insurance_ratios.py — all wired via sector routing
- **Portfolio:** scipy SLSQP optimizer, log returns, 252-day annualization, CVaR
- **Deployment:** Docker + Caddy reverse proxy, railway.toml, rxconfig.py reads API_URL from env

## Key Decisions

- **Scraper:** requests + BeautifulSoup4 — server-rendered HTML, no JS rendering needed
- **Portfolio optimization:** Mean-variance SLSQP (not Black-Litterman) for v1.1
- **Price storage:** data/prices/{company}.json alongside financial JSONs
- **Sector detection:** sector field in index.json, auto-detected from data patterns
- **Valuation without shares:** EV/EBITDA + FCF yield always shown; P/E/P/BV unlocked by manual input
- **Deployment:** Single Docker container — Caddy serves static frontend, proxies /_event/* to Reflex backend
- **Comments:** WHY-comments only (formula source, assumption, design decision) — not what the code does

## Constraints

- **Tech stack:** Reflex 0.8.26 — must stay
- **Python:** 3.12
- **Deployment:** Railway (Docker) — not Vercel/Streamlit Cloud
- **Data:** No live API; scraped historical prices only
- **Beneish DEPI:** Always N/A — MSE doesn't disclose depreciation separately
- **Piotroski F7:** Always N/A — MSE Excel files don't include shares outstanding

## Evolution

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check
3. Requirements audit (Active → Validated or Out of Scope)
4. Update Context with current state

---
*Last updated: 2026-04-01 after v1.1 milestone*
