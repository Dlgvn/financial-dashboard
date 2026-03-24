# MSE Analytica

## What This Is

MSE Analytica is a Mongolian-native portfolio and fundamental analysis platform for companies listed on the Mongolian Stock Exchange (MSE). Users upload raw Excel files from mse.mn, the platform auto-parses Mongolian-language financial statements, computes 26+ financial ratios plus three forensic models, scrapes historical price data for valuation metrics, and runs mean-variance portfolio optimization — covering the complete 6-step fundamental analysis workflow.

## Core Value

Upload an MSE Excel file and get a complete fundamental analysis — ratios, forensic scores, valuation, and portfolio optimization — in one place, in one click.

## Current Milestone: v1.1 — Complete MSE Analytica

**Goal:** Transform the working MVP into a rubric-excellent (95–100%), fully-deployed, production-quality platform covering the complete 6-step fundamental analysis workflow.

**Target features:**
- [A] Historical price scraper (requests + BeautifulSoup4, old.mse.mn/en/company/{id})
- [B] Valuation metrics: P/E, P/BV, P/S, FCF yield, EV/EBITDA + price chart
- [C] Sector routing: wire bank & insurance ratio engines already built
- [D] Company detail expansion: all 26+ ratios, tabs, DuPont, Red Flags, charts
- [E] Screener: sector filter + valuation ratio filters
- [F] Portfolio: mean-variance optimization, PPMT metrics, manual weights, efficient frontier
- [G] Deployment: Railway or Render, stable HTTPS URL
- [H] Documentation: comprehensive README, screenshots, data sources cited

## Requirements

### Validated

<!-- Shipped in MVP (v1.0) — confirmed working -->

- [x] Upload `.xls`/`.xlsx` MSE Excel files via drag-drop
- [x] Auto-parse Mongolian-language Balance Sheet, Income Statement, Cash Flow
- [x] Compute 26 financial ratios across 6 categories (standard companies)
- [x] Piotroski F-Score (9 criteria, F7 always N/A — no shares outstanding in MSE data)
- [x] Beneish M-Score (8 indices, DEPI always N/A — no depreciation in MSE data)
- [x] Altman Z-Score with zone classification
- [x] Composite Health Score 0–100 with Healthy/Caution/Distress labels
- [x] Company screener page with health badge
- [x] Company detail page (9 of 26 ratios shown)
- [x] Portfolio page: add/remove companies, equal weighting, blended health score
- [x] Demo mode: 7 MSE companies pre-loaded
- [x] Dark OLED theme (Tailwind v4, bg-slate-950)
- [x] Bank ratio engine built (19 ratios) — NOT yet wired
- [x] Insurance ratio engine built (15+ ratios) — NOT yet wired

### Active

<!-- v1.1 — building toward these -->

- [ ] **SCRP-01**: System scrapes historical price data (Open/High/Low/Close/Volume/Date) from old.mse.mn/en/company/{id}
- [ ] **SCRP-02**: System stores price history as JSON in data/prices/{company}.json
- [ ] **SCRP-03**: System maps all 7 demo companies to their MSE company IDs
- [ ] **SCRP-04**: User can trigger price refresh from the UI
- [ ] **VAL-01**: User can view P/E, P/BV, P/S, FCF yield, EV/EBITDA on company page
- [ ] **VAL-02**: User can view historical price line chart on company page
- [ ] **SECTOR-01**: System detects company sector (banking/insurance/standard) from metadata
- [ ] **SECTOR-02**: Khan Bank loads bank ratio engine (NIM, NPL, CAR, LDR, Cost-to-Income)
- [ ] **SECTOR-03**: Мандал даатгал loads insurance ratio engine (Loss Ratio, Combined Ratio, Solvency)
- [ ] **COMP-01**: User can view all 26+ computed ratios (currently only 9 shown)
- [ ] **COMP-02**: Company page has tabs: Ratios | Forensic | Valuation | DuPont | Red Flags
- [ ] **COMP-03**: DuPont ROE decomposition shown (Margin × Asset Turnover × Equity Multiplier)
- [ ] **COMP-04**: Red Flag detector auto-flags 5+ patterns with plain-language explanations
- [ ] **COMP-05**: Health score gauge/arc visualization on company page
- [ ] **COMP-06**: Radar chart showing 6 category health axes
- [ ] **COMP-07**: Beneish M-Score horizontal bar chart
- [ ] **SCREEN-01**: User can filter screener by sector
- [ ] **SCREEN-02**: User can filter screener by valuation ratio (P/E, FCF yield)
- [ ] **PORT-01**: User can input manual portfolio weights (beyond equal-weight)
- [ ] **PORT-02**: Portfolio shows sector breakdown donut chart
- [ ] **PORT-03**: System computes covariance matrix from scraped price history
- [ ] **PORT-04**: System runs mean-variance optimization to suggest optimal weights
- [ ] **PORT-05**: Portfolio shows PPMT risk metrics: Sortino ratio, Max Drawdown, CVaR
- [ ] **PORT-06**: Efficient frontier scatter plot shown in portfolio page
- [ ] **DEPLOY-01**: App deployed to Railway or Render with stable public HTTPS URL
- [ ] **DEPLOY-02**: Demo data accessible on deployment without manual setup
- [ ] **DOCS-01**: README covers what/why/how-to-run, at least 2 screenshots, data sources, setup, known issues
- [ ] **DOCS-02**: All data sources cited (MSE website for financials and price data)

### Out of Scope

<!-- Explicit exclusions with reasoning -->

- Black-Litterman user views UI — add after simpler optimization ships and proves stable
- PDF report export — post-milestone, not required for rubric excellence
- Language toggle (MN/EN) — English-only for now; Mongolian UI is a future milestone
- SWOT analysis — qualitative, cannot be automated from financial data
- Management/strategy research (Steps 2 & 4 of PPTX framework) — requires external sources
- Live/real-time price feeds — no MSE API exists; historical scraping is the approach
- User accounts / authentication — out of scope per vision doc
- Mobile-responsive layout — desktop-first per vision doc

## Context

- **Framework:** Reflex 0.8.26 (Python → React, server-sent events state sync)
- **Styling:** Tailwind CSS v4 via TailwindV4Plugin, dark OLED theme (bg-slate-950)
- **Storage:** Flat JSON files in data/ (gitignored); index.json is the manifest
- **Price data source:** old.mse.mn/en/company/{id} — server-rendered HTML, ~1,400 records/company, columns: High/Low/Open/Close/Volume/Date
- **Company IDs confirmed:** APU = 90; others to be discovered and mapped
- **Parser:** 7 Mongolian→English header dictionaries, 333-line excel_parser.py
- **Analysis:** ratios.py (719 lines, 26 ratios), bank_ratios.py (181 lines, 19 ratios), insurance_ratios.py (335 lines, 15+ ratios) — bank/insurance NOT YET wired
- **State:** UploadState → AnalysisState → PortfolioState inheritance chain in state.py
- **Rubric weights:** Functionality 30%, Deployment 20%, UX 20%, Code Quality 15%, Documentation 15%
- **Demo companies (7):** АПУ (Manufacturing), Хаан банк (Banking), Мандал даатгал (Insurance), Сүү (Dairy), Моносхүнс (Food), Дархан нэхий ХК (Textiles), Премиум Нэксус ХК (Holding)

## Constraints

- **Tech stack:** Reflex 0.8.26 — must stay; no framework change
- **Python:** 3.12
- **Deployment:** Must support Python web server (Railway or Render — NOT Vercel/Streamlit Cloud)
- **Data:** No live API; scraped historical prices only
- **Shares outstanding:** Not in MSE Excel files — needed for P/E; require manual input field or skip P/E
- **Beneish DEPI:** Always N/A (MSE doesn't disclose depreciation separately) — document as known limitation

## Key Decisions

- **Scraper:** requests + BeautifulSoup4 (server-rendered HTML, no JS rendering needed based on page structure)
- **Portfolio optimization:** Simple mean-variance (not Black-Litterman views UI) for v1.1 — keep stable, BL views as future improvement
- **Price storage:** data/prices/{company}.json alongside financial data JSONs
- **Sector detection:** Add `sector` field to index.json entries manually for the 7 demo companies
- **Valuation without shares outstanding:** Show EV/EBITDA and FCF yield (computable from existing data); add optional manual "shares outstanding" input to unlock P/E and P/BV

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-24 — Milestone v1.1 started*
