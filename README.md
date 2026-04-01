# MSE Analytica

> Fundamental analysis platform for companies listed on the Mongolian Stock Exchange

## Live Demo

**[Live app](https://your-app.up.railway.app)** ← _update this URL after Railway deployment_

Demo data for 7 MSE companies is pre-loaded — no file upload required.

## What It Does

Upload an MSE Excel financial statement and instantly get 26+ computed ratios, Piotroski F-Score, Beneish M-Score, Altman Z-Score, a composite health score, valuation metrics, and portfolio optimization with an efficient frontier — all in a single-page Reflex app. The platform targets the 6-step fundamental analysis workflow used in Mongolian equity research. Seven demo company datasets are pre-loaded on deployment.

## Features

- Automated Mongolian XLS parsing (7 statement mappings: standard BS/IS/CF, bank BS/IS, insurance BS/IS)
- 26+ financial ratios across 5 categories (Profitability, Liquidity, Solvency, Activity, Altman Z components)
- Piotroski F-Score (9 criteria; F7 dilution signal always N/A — no shares data in MSE Excel files)
- Beneish M-Score forensic fraud detection (8 indices; DEPI always N/A — no depreciation line in MSE filings)
- Altman Z-Score with Safe / Grey Zone / Distress classification
- Composite Health Score (0–100) with weighted subscore blend and Beneish penalty
- Company Screener with health badges, F-Score, and ROE columns
- Company Detail page: full ratio table, Piotroski checklist, Beneish bar chart, health gauge, radar chart
- Valuation tab: EV/EBITDA, FCF yield, historical price line chart; P/E and P/BV unlocked by manual shares input
- Portfolio Manager: manual weights, auto-normalize to 100%, sector donut chart
- Mean-variance optimization: max-Sharpe SLSQP optimizer, optimal vs. current weight comparison
- Risk metrics: Sortino Ratio, Maximum Drawdown, CVaR at 95%
- Efficient frontier scatter plot with current portfolio highlighted
- Historical price scraper for all 162 MSE-listed companies (data/prices/)

## Methodology

### Piotroski F-Score

9 binary signals (0 or 1 each, max score 9):

| Signal | Criterion | Direction |
|--------|-----------|-----------|
| F1 | ROA > 0 | Profitable |
| F2 | OCF > 0 | Cash-generating |
| F3 | ΔROA > 0 | Improving profitability |
| F4 | OCF/TA > ROA | Accruals quality — cash earnings exceed accrual earnings (Sloan 1996) |
| F5 | ΔLeverage < 0 | Less debt |
| F6 | ΔCurrent Ratio > 0 | Improved liquidity |
| F7 | No new share dilution | **Always N/A** — MSE Excel files do not contain shares outstanding |
| F8 | ΔGross Margin > 0 | Expanding margins |
| F9 | ΔAsset Turnover > 0 | Improving efficiency |

Score interpretation: **≥7 strong**, **4–6 neutral**, **≤3 weak**.

### Beneish M-Score

8 accounting manipulation indices (each is a ratio comparing current year to prior year):

| Index | Description |
|-------|-------------|
| DSRI | Days Sales Receivables Index — rising AR relative to revenue signals premature revenue recognition |
| GMI | Gross Margin Index — declining margin creates incentive to manipulate earnings |
| AQI | Asset Quality Index — growth in non-current, non-PPE assets proxies off-balance-sheet risk |
| SGI | Sales Growth Index — high sales growth companies face more earnings pressure |
| DEPI | Depreciation Index — **always N/A** (MSE filings do not disclose depreciation separately) |
| SGAI | SGA Expense Index — disproportionate SGA growth relative to sales |
| LVGI | Leverage Index — increasing leverage raises default risk and manipulation incentives |
| TATA | Total Accruals to Total Assets — high accruals relative to cash earnings |

M-Score formula (Beneish 1999 probit regression):

```
M = -4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI − 0.115·DEPI + 0.172·SGAI + 4.679·TATA − 0.327·LVGI
```

Threshold: **M > -1.78** indicates possible earnings manipulation. Conservative threshold: M > -2.22 suggests likely clean.

### Altman Z-Score

```
Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5
```

| Variable | Definition |
|----------|-----------|
| X1 | Working Capital / Total Assets |
| X2 | Retained Earnings / Total Assets |
| X3 | EBIT / Total Assets |
| X4 | Market Cap / Total Liabilities (or Book Equity if no market cap) |
| X5 | Revenue / Total Assets |

Zones: **Safe > 2.99** | **Grey Zone 1.23–2.99** | **Distress < 1.23**

### Composite Health Score

Weighted blend of 6 subscores (each 0–100), each derived from linear interpolation of raw ratio values onto calibrated MSE ranges:

| Component | Weight |
|-----------|--------|
| Profitability | 25% |
| Liquidity | 20% |
| Solvency | 20% |
| Activity | 15% |
| Altman Z | 10% |
| Piotroski | 10% |

If a component has insufficient data, its weight is redistributed proportionally among present components. Beneish penalty: **−10 points** applied when M-Score is both reliable (≥5 of 8 indices computable) and above the -1.78 manipulation threshold.

Score labels: ≥60 Healthy (green), 40–59 Caution (amber), <40 Distress (red).

### Mean-Variance Portfolio Optimization

Covariance matrix computed from log returns of scraped historical close prices (log returns used for time-additivity and log-normality assumption). Returns and volatility annualized using **252 trading days** (σ_annual = σ_daily × √252).

**Optimizer:** SLSQP (Sequential Least Squares Programming, `scipy.optimize.minimize`). Objective: maximize Sharpe ratio (minimize negative Sharpe). Constraints: weights sum to 1.0, all weights in [0, 1] (long-only). Equal-weight fallback used if optimizer fails to converge.

**Efficient frontier:** 200 random portfolios sampled using normalized random weights (Monte Carlo approximation — not a true Markowitz parametric sweep). Seed fixed at 42 for deterministic scatter across page loads.

**CVaR** (Conditional Value at Risk) at 95%: mean of portfolio returns below the 5th percentile — a tail-loss measure more conservative than VaR.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | Reflex 0.8.26 (Python + React) |
| Language | Python 3.12 |
| Optimization | scipy 1.11+ (SLSQP) |
| Numerics | numpy, pandas |
| Excel parsing | openpyxl, xlrd |
| Price scraping | requests, BeautifulSoup4 |
| Styling | Tailwind CSS v4 (via Reflex TailwindV4Plugin) |
| Charts | Recharts (via rx.recharts) |
| Deployment | Railway (Docker + Caddy reverse proxy) |

## Data Sources

- **Financial statements**: [MSE Members Portal](https://members.mse.mn) — XLS files for all listed companies
- **Historical prices**: [old.mse.mn](https://old.mse.mn/en/company/) — OHLCV data per company ID
- Demo data: 7 pre-parsed companies included in repository (financial JSONs + price JSONs)

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/{your-handle}/financial-dashboard.git
cd financial-dashboard

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app (demo data pre-loaded)
reflex run

# 5. Open in browser
# http://localhost:3000
```

The 7 demo companies load automatically — no file upload required. To add a new company, click "Upload" and select an MSE Excel financial statement (.xls or .xlsx).

## Known Issues / Limitations

- **Piotroski F7 always N/A**: MSE Excel financial statement files do not include shares outstanding. The dilution signal (F7) cannot be computed. Companies that issued new shares during the period will not have this penalized in their F-Score.
- **Beneish DEPI always N/A**: MSE financial filings do not disclose depreciation as a separate line item. The Depreciation Pattern Index cannot be computed.
- **P/E and P/BV require manual input**: Price-to-Earnings and Price-to-Book ratios are only displayed when shares outstanding is manually entered via the "Edit shares outstanding" field on the company detail page. This data is not available in MSE Excel files.
- **EBITDA uses EBIT proxy**: MSE filings do not include a depreciation line, so EV/EBITDA is computed using EBIT as the denominator (effectively EV/EBIT). Results are labeled accordingly in the UI.
- **Phase 2 features pending**: Sector routing (bank/insurance-specific ratio engines), tabbed company detail page, and screener filters are planned for Phase 2 but not yet implemented. The screener currently shows all companies with standard ratios.
- **Historical prices scope**: Price data is seeded for 7 demo companies. The 155 other MSE-listed companies have registry entries but no price history until the admin "Refresh Prices" function is run.

## Future Improvements

- Phase 2: Sector-specific ratio engines (bank NIM/NPL, insurance Loss Ratio/Combined Ratio)
- Phase 2: Tabbed company detail page (Ratios | Forensic | Valuation | DuPont | Red Flags)
- Phase 2: Screener filters by sector and sortable columns
- Phase 4: Black-Litterman optimization with user-specified views
- PDF export: one-click investment report generation
- Multi-year trend analysis (CAGR across 3–5 years)
- Mongolian language toggle

## Author

Written as a Capstone Project at [your institution]. Author: [Your Name].

---

Demo data is provided for educational and research purposes. No investment advice is implied.
