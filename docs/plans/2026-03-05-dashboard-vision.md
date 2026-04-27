# MSE Analytica — Product Vision
**Date:** 2026-03-05
**Status:** Vision (pre-implementation)

---

## What We're Building

**MSE Analytica** — a Mongolian-native portfolio and fundamental analysis platform for companies listed on the Mongolian Stock Exchange (MSE). Inspired by [PortfolioVisualizer](https://www.portfoliovisualizer.com/), it serves both retail investors making personal decisions and financial analysts doing professional due diligence.

The core innovation: users download raw Excel files from the MSE website, upload them here, and the platform handles everything — parsing Mongolian-language statements, computing 40+ financial ratios, running forensic scoring models, and optimizing portfolios using institutional-grade methods.

---

## The Problem

The MSE has 180+ listed companies that publish financial statements as Excel files — but this data is scattered, in Mongolian, and requires manual effort to interpret. Retail investors must download dozens of files, open them in Excel, and calculate by hand. No integrated analytical tool exists for the Mongolian market.

MSE Analytica solves this end-to-end: upload once, analyze everything.

---

## Target Users

| User | Needs |
|------|-------|
| **Retail investor** | Simple health scores, screening, plain-language insights, portfolio builder |
| **Financial analyst / student** | 40+ ratios, forensic models, Black-Litterman optimization, PDF export |

Simple view by default; professional depth available on demand.

---

## The 6-Step Workflow

The platform guides users through a complete investment analysis process:

```
[1. Upload] → [2. Screen & Select] → [3. Health Analysis] → [4. Add to Portfolio] → [5. Portfolio Construction] → [6. Scenario Analysis]
```

---

## Feature Specification by Step

### Step 1 — Upload Data
*"Bring your data in"*

- Drag-and-drop interface for Excel files downloaded from mse.mn
- Auto-parses Balance Sheet, Income Statement, Cash Flow worksheets
- Handles Mongolian-language headers via header mapping engine (already built)
- Confirms successful extraction with field-by-field preview
- Pre-loaded sample dataset: 5–10 major MSE companies (APU, Khan Bank, Talkh Chikher, Gobi, etc.)
- Fallback: standardized CSV template for manually entered data

---

### Step 2 — Screen & Select
*"Find the right investment"*

- Browse all uploaded companies with basic metadata (sector, reporting period)
- Filter by: Revenue CAGR, Operating Margin, Net Debt/EBITDA, ROE, Composite Health Score, Altman Z-Score
- Sector filter: Banking / Mining / Manufacturing / Energy / Retail / Other
- Composite Health Score badge per company: 0–100 gauge (Healthy / Caution / Distress)
- Save a filtered set as a Watchlist
- Peer group auto-assignment by sector

---

### Step 3 — Company Health Analysis
*"Understand the finances"*

Core of the platform. Full 40+ ratio engine plus three forensic models.

**Ratio Categories:**
| Category | Count | Key Metrics |
|----------|-------|-------------|
| Activity | 9 | Asset turnover, Receivables days, Inventory days, Working capital turnover |
| Liquidity | 5 | Current, Quick, Cash ratio, Defensive interval, Cash conversion cycle |
| Solvency | 4 | Debt/Equity, Debt/Assets, Financial leverage, Interest coverage |
| Profitability | 8 | Gross/Operating/Net margin, ROE, ROA, ROIC, Return on total capital |
| Valuation | 7 | P/E, P/CF, P/S, P/BV, EPS, Cash flow per share, EBT per share |
| Cash Flow / Performance | 6 | FCF conversion, Cash ROA, Cash ROE, Accruals ratio, CF-to-income |

**Composite Health Score (0–100):**
- Weighted aggregate across all ratio categories
- Displayed as a gauge visualization
- Category breakdown chart showing strengths/weaknesses by area
- Drill-down to individual metrics

**Forensic Scoring Models:**
| Model | Purpose | Detail |
|-------|---------|--------|
| **Altman Z-Score** | Bankruptcy prediction | Already implemented; displayed with zone indicator (Distress / Grey / Safe) |
| **Beneish M-Score** | Earnings manipulation detection | 8 indices (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA) |
| **Piotroski F-Score** | Financial strength | 9 criteria across profitability, leverage, and operating efficiency |

**DuPont Decomposition:**
- Break ROE = Profit Margin × Asset Turnover × Equity Multiplier
- Show which driver explains ROE changes year-over-year

**Red Flag Detector:**
- Auto-flag: receivables growing faster than revenue, FCF diverging from net income, sudden leverage spikes, M-Score above manipulation threshold
- Plain-language explanation per flag

**Banking-Specific Module** (Khan Bank and other financial institutions):
- Net Interest Margin (NIM), Non-Performing Loan ratio (NPL), Capital Adequacy Ratio (CAR), Loan-to-Deposit Ratio (LDR)
- Replaces standard profitability/activity metrics where not applicable

**Multi-Year Trends** (when historical data is available):
- YoY and CAGR for Revenue, EBITDA, Net Income, Total Assets, Debt
- Trend line charts across 3–5 years

---

### Step 4 — Add to Portfolio
*"Build your investment universe"*

- One-click "Add to Portfolio" from any company analysis
- Assign initial weight (or auto-equal weight)
- Portfolio summary: list of holdings, weights, sector breakdown pie chart
- Blended health score across portfolio
- Edit/remove holdings at any time

---

### Step 5 — Portfolio Construction
*"Optimize the allocation"*

**Black-Litterman Model:**
- Calculate implied equilibrium returns from market capitalization weights
- User expresses views: "Company X will outperform by 5% over 12 months"
- System generates posterior return estimates and optimal allocations
- Produces more intuitive, diversified portfolios vs. naive mean-variance optimization

**Post-Modern Portfolio Theory (PMT) Risk Metrics:**
- Sortino Ratio (downside deviation, not total volatility)
- Maximum Drawdown
- Conditional Value at Risk (CVaR)
- Downside deviation vs. standard deviation comparison

**Portfolio Visualizations:**
- Efficient frontier scatter: risk-return plot with portfolio dot
- Sector concentration chart
- Blended weighted ratios across holdings
- Comparison: Black-Litterman optimal weights vs. current weights ("recommended trades")

**Mongolian Macro Context:**
- MNT inflation toggle: real vs. nominal figures
- FX sensitivity: MNT/USD impact on debt-heavy companies
- Commodity price overlay: gold/coal/copper vs. mining company revenues

---

### Step 6 — Scenario Analysis
*"Test your assumptions"*

- View sliders: adjust confidence levels on expressed views in real-time
- Portfolio allocation updates live as views change
- Stress test: "What if revenue drops 20%?" — see impact on ratios and health score
- Side-by-side: current allocation vs. optimized allocation
- Export final portfolio as PDF report (Mongolian and/or English)
- Investment thesis template: Bull case / Bear case / Key risks / Target valuation

---

## Mongolian-Specific Context (Cross-Cutting)

| Context | Implementation |
|---------|---------------|
| MNT inflation | Real vs. nominal toggle on all monetary values |
| Commodity prices | Gold/coal/copper overlay for mining sector companies |
| China exposure | Dependency flag on company profiles |
| FX risk | MNT/USD sensitivity on solvency metrics |
| MSE data source | XLS ingestion from mse.mn (parser already built) |
| Language | Mongolian UI with English toggle |

---

## Data Architecture

### Current State
- 3 companies (Khan Bank, APU, Premium Nexus)
- 1 year of data (2025)
- 26 ratios in `ratios.py`

### Target State
- 20–30 MSE-listed companies (180+ potential)
- 3–5 years of historical data per company (for CAGR, trends)
- Market price data for valuation ratios (manual input or MSE source)
- Macro data: MNT/USD rate, CPI, commodity prices

---

## Tech Stack

| Layer | Current | Addition |
|-------|---------|----------|
| Framework | Reflex (Python) | No change |
| Data | JSON files | Multi-year versioning |
| Ratios | 26 in `ratios.py` | Expand to 40+ (Beneish, Piotroski, valuation, banking) |
| Portfolio models | None | Black-Litterman, PMT metrics |
| Visualization | Jupyter/matplotlib | Reflex-native interactive charts |
| Export | None | PDF report generation |
| Data ingestion | XLS parser | Batch processing support |

---

## Success Criteria

1. User uploads an MSE Excel file and sees parsed ratios in under 60 seconds
2. All three forensic models (Altman Z, Beneish M, Piotroski F) compute correctly and are cross-validated against manual calculations
3. Black-Litterman produces stable, diversified allocations when user inputs views
4. A retail investor understands company health without knowing financial jargon
5. An analyst can export a formatted investment report as PDF
6. Banking companies use sector-appropriate metrics automatically

---

## Out of Scope

- Real-time price feeds / live market data
- Automated trading or brokerage integration
- Mobile app (desktop-first)
- User accounts / authentication
- Automated news scraping
- Non-MSE listed companies

---

## Phased Build Order

Aligned with proposal timeline (16 weeks):

| Phase | Weeks | Focus |
|-------|-------|-------|
| **Phase 1** | 1–3 | Upload system + XLS parser (already underway) |
| **Phase 2** | 4–5 | EDA report + data standardization for 5–10 companies |
| **Phase 3** | 6–8 | MVP: 10 key ratios working end-to-end |
| **Phase 4** | 9–11 | Full 40+ ratio engine + forensic models (Beneish M, Piotroski F) + composite score |
| **Phase 5** | 12–14 | Portfolio module: Black-Litterman + PMT metrics + scenario analysis |
| **Phase 6** | 15–16 | Polish, PDF export, Mongolian UI, sample dataset, deployment |
