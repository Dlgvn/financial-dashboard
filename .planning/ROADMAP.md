# Roadmap — v1.1 Complete MSE Analytica

**Milestone:** v1.1 — Complete MSE Analytica
**Goal:** Transform the working MVP into a rubric-excellent (95-100%), fully-deployed, production-quality platform covering the complete 6-step fundamental analysis workflow.
**Total requirements:** 30
**Generated:** 2026-03-24

---

## Phases

- [ ] **Phase 1: Price Data Seed** — Scrape and store historical MSE price data for all 162 listed companies (Classification I, II, III) as a one-time data seed
- [ ] **Phase 2: Sector Routing, Company Detail & Screener** — Wire bank/insurance engines, expand company page to full ratios/tabs/charts, and add sector/valuation filters to screener
- [ ] **Phase 3: Valuation Metrics** — Compute and display valuation ratios and historical price chart on company page
- [ ] **Phase 4: Portfolio Optimization** — Add manual weights, risk metrics, mean-variance optimization, and efficient frontier
- [ ] **Phase 5: Deployment & Documentation** — Deploy to production, bundle demo data, write comprehensive README

---

## Phase Details

### Phase 1: Price Data Seed
**Goal**: Scrape and store historical price data for all 162 MSE-listed companies (Classification I, II, III) as a one-time data seed — so price data is already waiting for any company a user later uploads, with no missing-data gaps
**Depends on**: Nothing (first phase)
**Requirements**: SCRP-01, SCRP-02, SCRP-03, SCRP-04
**Success Criteria** (what must be TRUE):
  1. `data/company_registry.json` contains all 162 MSE companies with ticker, name, classification tier (I/II/III), and MSE company ID — built by scraping old.mse.mn/en/companies_info/1, /2, /3
  2. `data/prices/{ticker}.json` exists for all 162 companies with OHLCV + Date records (scraped from old.mse.mn/en/company/{id})
  3. When a user uploads any of the 7 demo company XLS files, the app immediately finds their price history in data/prices/ — no "price data unavailable" state
  4. Scraper handles failures gracefully: per-company errors are logged and skipped without crashing the full run; completed files are not re-scraped on retry
  5. All price files and company_registry.json are bundled into deployment alongside financial JSONs
**Plans:** 2 plans
Plans:
- [ ] 01-01-PLAN.md — Registry, scraper module, seed script, and tests
- [ ] 01-02-PLAN.md — Refresh Prices button UI with streaming feedback
**UI hint**: no — scraper runs as a one-time seed script; optional admin "Refresh All Prices" button in upload page

### Phase 2: Sector Routing, Company Detail & Screener
**Goal**: Company pages show full ratio coverage with sector-correct engines, tabbed navigation, forensic visualizations, and the screener supports sector and sorting filters
**Depends on**: Phase 1 (sector field in index.json needed by screener; price data not yet needed here but scraper lays groundwork)
**Requirements**: SECTOR-01, SECTOR-02, SECTOR-03, COMP-01, COMP-02, COMP-03, COMP-04, COMP-05, COMP-06, COMP-07, SCREEN-01, SCREEN-02
**Success Criteria** (what must be TRUE):
  1. Opening Khan Bank's company page shows bank-specific ratios (NIM, NPL, CAR, LDR, Cost-to-Income) instead of standard ratios
  2. Opening Мандал даатгал's company page shows insurance-specific ratios (Loss Ratio, Combined Ratio, Solvency Ratio) instead of standard ratios
  3. A standard company page shows all 26+ ratios organized by category across the Ratios tab, with DuPont decomposition, Red Flags, health gauge, radar chart, and Beneish bar chart each in their own tabs — all without a page reload
  4. The screener dropdown filters companies by sector (All / Banking / Insurance / Manufacturing / Food / Textiles / Holding) and the table updates immediately
  5. Clicking a column header in the screener (Health Score, F-Score, ROE, sector) sorts the table ascending/descending
**Plans**: TBD
**UI hint**: yes

### Phase 3: Valuation Metrics
**Goal**: Users can view computed valuation ratios and a historical price chart on the company detail page
**Depends on**: Phase 1 (price data required for chart and market-based ratios), Phase 2 (Valuation tab exists in tabbed company page)
**Requirements**: VAL-01, VAL-02, VAL-03
**Success Criteria** (what must be TRUE):
  1. The Valuation tab on any company page shows EV/EBITDA and FCF yield computed from existing financial data
  2. A historical Close price line chart is visible on the Valuation tab with dates on the x-axis
  3. When a user enters shares outstanding for a company and saves it, P/E and P/BV appear in the Valuation tab immediately (no page reload required)
**Plans**: TBD
**UI hint**: yes

### Phase 4: Portfolio Optimization
**Goal**: The portfolio page supports manual weights, displays sector breakdown, and runs mean-variance optimization with risk metrics and an efficient frontier chart
**Depends on**: Phase 1 (price history needed for covariance matrix, optimization, and efficient frontier)
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05, PORT-06
**Success Criteria** (what must be TRUE):
  1. User can type custom weight percentages for each holding; weights auto-normalize to 100% as they are entered
  2. Portfolio page shows a donut chart of sector allocation that updates when holdings change
  3. After adding at least 2 companies with scraped price data, the page displays suggested optimal weights from mean-variance optimization alongside the current weights
  4. Portfolio page shows Sortino Ratio, Maximum Drawdown, and CVaR (95%) computed from historical price returns
  5. An efficient frontier scatter plot is visible on the portfolio page with the current portfolio position highlighted
**Plans**: TBD
**UI hint**: yes

### Phase 5: Deployment & Documentation
**Goal**: The app is publicly accessible via a stable HTTPS URL with demo data pre-loaded, and the repository has complete documentation
**Depends on**: Phase 2, Phase 3, Phase 4 (all features stable before deploy)
**Requirements**: DEPLOY-01, DEPLOY-02, DOCS-01, DOCS-02, DOCS-03
**Success Criteria** (what must be TRUE):
  1. Visiting the public HTTPS URL (Railway or Render) shows the MSE Analytica app with 7 demo companies loaded — no file upload required
  2. The README on GitHub shows a live demo URL, at least 2 screenshots, feature list, tech stack, data sources with links, local setup steps, and known issues
  3. Non-obvious code logic (scraper parsing, Beneish formula, composite score weights, optimization math) has inline comments explaining the intent
  4. No API keys or secrets are present in the repository; `.env` is confirmed in `.gitignore`
**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Price Scraper | 0/2 | Planning complete | - |
| 2. Sector Routing, Company Detail & Screener | 0/? | Not started | - |
| 3. Valuation Metrics | 0/? | Not started | - |
| 4. Portfolio Optimization | 0/? | Not started | - |
| 5. Deployment & Documentation | 0/? | Not started | - |

---

## Requirement Coverage

All 30 v1.1 requirements mapped.

| Requirement | Phase |
|-------------|-------|
| SCRP-01 | Phase 1 |
| SCRP-02 | Phase 1 |
| SCRP-03 | Phase 1 |
| SCRP-04 | Phase 1 |
| SECTOR-01 | Phase 2 |
| SECTOR-02 | Phase 2 |
| SECTOR-03 | Phase 2 |
| COMP-01 | Phase 2 |
| COMP-02 | Phase 2 |
| COMP-03 | Phase 2 |
| COMP-04 | Phase 2 |
| COMP-05 | Phase 2 |
| COMP-06 | Phase 2 |
| COMP-07 | Phase 2 |
| SCREEN-01 | Phase 2 |
| SCREEN-02 | Phase 2 |
| VAL-01 | Phase 3 |
| VAL-02 | Phase 3 |
| VAL-03 | Phase 3 |
| PORT-01 | Phase 4 |
| PORT-02 | Phase 4 |
| PORT-03 | Phase 4 |
| PORT-04 | Phase 4 |
| PORT-05 | Phase 4 |
| PORT-06 | Phase 4 |
| DEPLOY-01 | Phase 5 |
| DEPLOY-02 | Phase 5 |
| DOCS-01 | Phase 5 |
| DOCS-02 | Phase 5 |
| DOCS-03 | Phase 5 |
