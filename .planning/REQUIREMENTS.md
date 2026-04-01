# Requirements — v1.1 Complete MSE Analytica

## Milestone Goal
Transform the working MVP into a rubric-excellent (95–100%), fully-deployed, production-quality platform covering the complete 6-step fundamental analysis workflow with scraped MSE historical price data.

---

## Active Requirements

### [A] Price Scraper

- [x] **SCRP-01**: System scrapes historical price data (Open/High/Low/Close/Volume/Date) from `old.mse.mn/en/company/{id}` using requests + BeautifulSoup4
- [x] **SCRP-02**: System stores price history as JSON in `data/prices/{company}.json` with date-indexed records
- [x] **SCRP-03**: System maintains a mapping of all 7 demo company names to their MSE company IDs (APU=90; others discovered)
- [x] **SCRP-04**: User can trigger "Refresh Prices" from the upload/home page UI; system shows loading state and success/error feedback

### [B] Valuation Metrics

- [x] **VAL-01**: User can view computed valuation metrics on the company page — EV/EBITDA and FCF yield (computable from existing data); P/E and P/BV shown if user provides shares outstanding
- [x] **VAL-02**: User can view a historical price line chart (Close price over time) on the company detail page
- [x] **VAL-03**: User can optionally input shares outstanding per company to unlock P/E and P/BV ratios (stored in company JSON)

### [C] Sector Routing

- [ ] **SECTOR-01**: System adds a `sector` field to each entry in `index.json` (Banking / Insurance / Manufacturing / Food / Textiles / Holding)
- [ ] **SECTOR-02**: System routes Khan Bank (Хаан банк) to `bank_ratios.py` — displaying NIM, NPL ratio, CAR, LDR, Cost-to-Income with correct benchmarks
- [ ] **SECTOR-03**: System routes Мандал даатгал to `insurance_ratios.py` — displaying Loss Ratio, Expense Ratio, Combined Ratio, Solvency Ratio with correct benchmarks

### [D] Company Detail Expansion

- [ ] **COMP-01**: User can view all 26+ computed ratios organized by category (Activity, Liquidity, Solvency, Profitability, Performance, Altman Z components)
- [ ] **COMP-02**: Company detail page has tabbed navigation: **Ratios | Forensic | Valuation | DuPont | Red Flags** — each tab renders its content without page reload
- [ ] **COMP-03**: DuPont tab shows ROE decomposition: ROE = Net Profit Margin × Asset Turnover × Equity Multiplier, with current and prior year comparison
- [ ] **COMP-04**: Red Flags tab auto-detects and displays at least 5 patterns (receivables growing faster than revenue; FCF diverging from net income; sudden leverage spike; M-Score above threshold; Current ratio deterioration) with plain-language explanations, not just flags
- [ ] **COMP-05**: Composite health score displayed as a gauge/arc visualization (0–100, color-coded green/amber/red)
- [ ] **COMP-06**: Radar chart visualizing the 6 health category scores (Profitability, Liquidity, Solvency, Activity, Altman Z, Piotroski) as axes
- [ ] **COMP-07**: Beneish M-Score indices displayed as a horizontal bar chart (not just a table), with the manipulation threshold line marked

### [E] Screener Improvements

- [ ] **SCREEN-01**: User can filter the screener by sector using a dropdown (All / Banking / Insurance / Manufacturing / Food / Textiles / Holding)
- [ ] **SCREEN-02**: User can sort the screener by any column (Health Score, F-Score, ROE, sector)

### [F] Portfolio — Optimization & Risk

- [x] **PORT-01**: User can manually input portfolio weights per holding (not just equal-weight auto-assignment); weights auto-normalize to 100%
- [x] **PORT-02**: Portfolio page shows sector breakdown as a donut/pie chart
- [x] **PORT-03**: System computes a return covariance matrix from scraped historical price data for portfolio companies
- [x] **PORT-04**: System runs mean-variance optimization and displays suggested optimal weights alongside current weights
- [x] **PORT-05**: Portfolio page shows PPMT risk metrics: Sortino Ratio, Maximum Drawdown, Conditional Value at Risk (CVaR at 95%)
- [x] **PORT-06**: Efficient frontier scatter plot shown on portfolio page — dots representing risk/return trade-offs with current portfolio highlighted

### [G] Deployment

- [x] **DEPLOY-01**: App deployed to Railway or Render with a stable public HTTPS URL accessible without login
- [x] **DEPLOY-02**: Demo data (7 companies' financial JSONs) bundled into deployment so app is immediately usable without uploading files

### [H] Documentation

- [x] **DOCS-01**: README contains: project description, live demo URL, at least 2 screenshots, feature list, technology stack, data sources with links, step-by-step local setup, known issues, future improvements, author
- [x] **DOCS-02**: Code has inline comments for non-obvious logic (scraper parsing, BL optimization math, Beneish formula, composite score weights)
- [x] **DOCS-03**: No API keys or secrets committed to repository; .env confirmed in .gitignore

---

## Future Requirements (Deferred)

- Black-Litterman user views UI (sliders for "Company X outperforms by Y%") — after mean-variance ships
- PDF investment report export — post-milestone
- Mongolian UI language toggle — future milestone
- Multi-year data support (CAGR across 3–5 years) — requires data pipeline change
- Scenario analysis sliders (stress testing) — post-MVP per vision doc
- Batch price scraping for all 180+ MSE companies — current scope: 7 demo companies

---

## Out of Scope

- SWOT analysis — qualitative, cannot be automated from financial data
- Management/strategy research — requires external qualitative sources
- Live/real-time price feeds — no MSE API exists
- User accounts / authentication — out of scope per vision doc
- Mobile-responsive layout — desktop-first per vision doc
- Non-MSE listed companies

---

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| SCRP-01 | Phase 1 | Complete |
| SCRP-02 | Phase 1 | Complete |
| SCRP-03 | Phase 1 | Complete |
| SCRP-04 | Phase 1 | Complete |
| SECTOR-01 | Phase 2 | Pending |
| SECTOR-02 | Phase 2 | Pending |
| SECTOR-03 | Phase 2 | Pending |
| COMP-01 | Phase 2 | Pending |
| COMP-02 | Phase 2 | Pending |
| COMP-03 | Phase 2 | Pending |
| COMP-04 | Phase 2 | Pending |
| COMP-05 | Phase 2 | Pending |
| COMP-06 | Phase 2 | Pending |
| COMP-07 | Phase 2 | Pending |
| SCREEN-01 | Phase 2 | Pending |
| SCREEN-02 | Phase 2 | Pending |
| VAL-01 | Phase 3 | Complete |
| VAL-02 | Phase 3 | Complete |
| VAL-03 | Phase 3 | Complete |
| PORT-01 | Phase 4 | Complete |
| PORT-02 | Phase 4 | Complete |
| PORT-03 | Phase 4 | Complete |
| PORT-04 | Phase 4 | Complete |
| PORT-05 | Phase 4 | Complete |
| PORT-06 | Phase 4 | Complete |
| DEPLOY-01 | Phase 5 | Complete |
| DEPLOY-02 | Phase 5 | Complete |
| DOCS-01 | Phase 5 | Complete |
| DOCS-02 | Phase 5 | Complete |
| DOCS-03 | Phase 5 | Complete |
