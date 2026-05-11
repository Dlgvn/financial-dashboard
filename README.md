# MSE Analytica

> Fundamental analysis platform for companies listed on the Mongolian Stock Exchange

The Mongolian Stock Exchange lists over 200 companies, yet investors have no dedicated tool for structured fundamental analysis — financial statements are published as raw Excel files with no standardised ratios, no scoring, and no cross-company comparison. MSE Analytica fills that gap: upload any MSE Excel filing and instantly get sector-aware ratio analysis, composite health scoring, forensic signals, and valuation multiples — all calibrated to the realities of the Mongolian market.

Built as a Capstone Project. Designed for Mongolian equity analysts and investors who need a structured, sector-aware workflow for evaluating MSE-listed companies.

---

## Features

### Multi-Sector Analysis Engine

The platform automatically detects the company's sector from the uploaded Excel file and routes it to the appropriate ratio engine:

| Sector | Engine | Key Metrics |
|--------|--------|-------------|
| **Standard** | `ratios.py` | ROA, ROE, margins, liquidity, solvency, activity, Altman Z, Piotroski, Beneish |
| **Banking** | `bank_ratios.py` | NIM, NPL Ratio, LDR, Coverage Ratio, Equity/Assets, Cost-to-Income (19 ratios) |
| **Insurance** | `insurance_ratios.py` | Loss Ratio, Combined Ratio, Solvency Ratio, Reserve Coverage (15 ratios) |
| **Finance / NBFI** | `finance_ratios.py` | Interest Spread, NPA Ratio, Provision Coverage, Asset Utilisation (20 ratios) |

Finance/NBFI subsectors (Securities, ББСБ Lending, Investment/Holding) are auto-classified via the 68-company registry.

### Company Detail Page — 5-Tab Layout

- **Overview**
  - Composite health gauge (radial bar) + radar breakdown chart
  - Key Metrics card: ROE, ROA, Net Margin, Gross Margin, Operating Margin, Debt/Equity, Current Ratio, Quick Ratio, Altman Z-Score
  - Risk Signals card alongside Key Metrics

- **Ratios**
  - Sector-aware ratio table with green / amber / red color coding against calibrated MSE benchmarks

- **Forensic**
  - Standard companies: Piotroski F-Score + Beneish M-Score
  - Banking / Insurance / Finance: 8-criterion sector forensic score + YoY bar chart

- **Valuation**
  - Subsector-specific card grids (cash flow metric on every grid):
    - Standard: EV/EBIT, FCF Yield, Free Cash Flow M₮, P/E, P/BV
    - Banking: P/E, P/BV, P/TBV, P/PPOP, P/NII, Op. Cash Flow M₮
    - NBFI: P/E, P/BV, P/PPOP, P/NII, Op. Cash Flow M₮
    - Holding: P/E, P/NAV, P/Inv Sec, Op. Cash Flow M₮
    - Securities: P/E, P/BV, P/Revenue, Op. Cash Flow M₮
    - Insurance: P/E, P/BV, P/NPE, P/UWP, Op. Cash Flow M₮
  - Historical OHLCV price chart with 1M / 6M / 1Y / All range toggle

- **DuPont**
  - 3-factor decomposition:
    - Standard / Insurance / Finance: Net Margin × Asset Turnover × Equity Multiplier
    - Banking: ROA × Equity Multiplier
  - Current vs. prior year comparison

- **Red Flags**
  - Rule-based flags appear instantly on page load
  - Replaced by Groq AI (Llama 3.3 70B) sector-aware flags with HIGH / MEDIUM / LOW / CLEAR severity badges

### Company Screener

Sortable, filterable table across all uploaded companies with an expandable Methodology & Validation panel. Columns: company name, year, sector, composite health badge, ROE. One-click "Add to Portfolio" per row. The methodology panel documents exact scoring weights per sector, universal adjustments (Beneish penalty, missing-data redistribution), and known limitations.

### Portfolio Manager

- Add/remove companies from any screener view; equal-weight rebalance on each add/remove
- Manual weight editing with proportional rebalance of remaining holdings
- Blended health score (weighted average across holdings)
- **Analysis tab** (requires ≥2 companies with price history):
  - Efficient frontier scatter (200 Monte Carlo portfolios)
  - Max-Sharpe SLSQP optimizer with current vs. optimal weight comparison
  - Min-Risk and Max-Return one-click weight application
  - Sortino Ratio, Maximum Drawdown
  - Sector allocation donut chart
  - Per-company return/volatility/Sharpe statistics table

---

## Scoring Models

### Composite Health Score (0–100)

Weighted blend of subscores derived from linear interpolation of raw ratios onto calibrated MSE ranges. Each sector uses its own composite function and weighting framework.

**Standard** (basis: MSE-calibrated benchmarks + Altman/Piotroski models)

| Component | Weight |
|-----------|--------|
| Profitability | 25% |
| Liquidity | 20% |
| Solvency | 20% |
| Activity | 15% |
| Altman Z | 10% |
| Piotroski | 10% |

Missing components redistribute weight proportionally. Beneish penalty: −10 pts when M-Score is reliable (≥5 indices computable) and above −1.78.

Labels: **≥80 Excellent** · **60–79 Good** · **40–59 Fair** · **<40 Weak**

---

**Banking** (basis: CAMELS framework — FDIC, IMF, World Bank)

| Component | Weight | Key Ratios |
|-----------|--------|------------|
| Capital Adequacy | 25% | Equity/Assets, Equity Multiplier |
| Asset Quality | 25% | NPL Ratio, Coverage Ratio, Loan Loss Reserve |
| Earnings | 20% | NIM, ROA, ROE, Cost-to-Income |
| Liquidity | 20% | LDR, Cash-to-Deposits, Loans-to-Assets |
| Efficiency | 10% | Cost-to-Income ratio |

Labels: **≥70 Healthy** · **40–69 Caution** · **<40 Distress**

---

**Insurance** (basis: IRIS screening, Solvency II, A.M. Best / S&P criteria, Mongolia FRC standards)

| Component | Weight | Key Ratios |
|-----------|--------|------------|
| Underwriting Quality | 30% | Combined Ratio, Loss Ratio, Expense Ratio |
| Solvency / Capital | 25% | Solvency Ratio, Leverage, Reserve Coverage |
| Profitability | 25% | ROA, ROE, Net Margin, Underwriting Margin |
| Liquidity | 20% | OCF Ratio, Cash-to-Liabilities, Investment Ratio |

Note: if underwriting data is unavailable, its weight redistributes to profitability.

Labels: **≥70 Healthy** · **40–69 Caution** · **<40 Distress**

---

**Finance / NBFI** (basis: CARE Ratings NBFC methodology, IMF FSAP NBFI indicators)

| Component | Weight | Key Ratios |
|-----------|--------|------------|
| Profitability | 30% | NIM, ROA, ROE, Net Margin, Interest Spread |
| Capital / Leverage | 25% | Debt/Equity, Equity Ratio |
| Efficiency | 25% | Cost-to-Income, Asset Utilisation |
| Liquidity | 20% | Cash Ratio, OCF Ratio, Loan-to-Assets |

Labels: **≥70 Healthy** · **40–69 Caution** · **<40 Distress**

### Piotroski F-Score

9 binary signals (0/1, max 9) measuring fundamental strength:

| Signal | Criterion |
|--------|-----------|
| F1 | ROA > 0 |
| F2 | OCF > 0 |
| F3 | ΔROA > 0 |
| F4 | OCF/TA > ROA (accruals quality) |
| F5 | ΔLeverage < 0 |
| F6 | ΔCurrent Ratio > 0 |
| F7 | No dilution — **always N/A** (shares not in MSE filings) |
| F8 | ΔGross Margin > 0 |
| F9 | ΔAsset Turnover > 0 |

Not applied to Banking/Insurance/Finance (replaced by sector forensic score).

### Beneish M-Score

8 accounting manipulation indices. Formula (Beneish 1999):

```
M = -4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI
        − 0.115·DEPI + 0.172·SGAI + 4.679·TATA − 0.327·LVGI
```

Threshold: **M > −1.78** → possible manipulation. DEPI always N/A (no depreciation line in MSE filings). Not applied to Banking/Insurance/Finance.

### Altman Z-Score

```
Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5
```

Zones: **Safe > 2.99** · **Grey 1.23–2.99** · **Distress < 1.23**

### Sector Forensic Scores (Banking / Insurance / Finance)

8-criterion rule-based checklist using sector-appropriate ratios and YoY trends. Replaces Piotroski/Beneish which are designed for manufacturing companies.

**Banking (B1–B8):** ROA positive/improving, NPL decreasing, Coverage ≥1.0×, LDR ≤90%, Cost-to-Income improving, NIM stable, Equity/Assets improving.

**Insurance (I1–I8):** ROA positive/improving, Combined Ratio <100%/improving, Solvency ≥100%, Reserve Coverage ≥1.0×, Loss Ratio improving, OCF positive.

**Finance/NBFI (F1–F8):** ROA positive/improving, NIM stable, NPA decreasing, Cost-to-Income improving, Leverage not increasing, OCF positive, Provision Coverage ≥1.0×.

### Mean-Variance Portfolio Optimization

- Returns computed as log returns of adjusted closing prices
- Annualized using 252 trading days (σ_annual = σ_daily × √252)
- **Max-Sharpe:** SLSQP optimizer (scipy), long-only, weights sum to 1
- **Min-Risk:** minimum-variance portfolio
- **Max-Return:** concentrate in highest-returning asset
- **Efficient frontier:** 200 Monte Carlo random portfolios (seed=42)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | Reflex 0.8+ (Python + React) |
| Language | Python 3.12 |
| AI red flags | Groq API — Llama 3.3 70B Versatile |
| Optimization | SciPy SLSQP |
| Numerics | NumPy, Pandas |
| Excel parsing | openpyxl, xlrd |
| Price scraping | requests, BeautifulSoup4 |
| Styling | Tailwind CSS v4 |
| Charts | Recharts (via rx.recharts) |

---

## Data Sources

- **Financial statements:** [MSE Members Portal](https://members.mse.mn) — XLS/XLSX files for all listed companies
- **Historical prices:** [old.mse.mn](https://old.mse.mn/mn/company/) — OHLCV data per company ID
- **Company registry:** 68-company JSON with MSE IDs, sectors, subsectors, and name aliases

---

## Local Setup

```bash
git clone https://github.com/Dlgvn/financial-dashboard.git
cd financial-dashboard

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Optional: add Groq API key for AI red flags
echo "GROQ_API_KEY=your_key_here" > .env

reflex run
# → http://localhost:3000
```

Demo data for 7 MSE companies is pre-loaded — no file upload required. To add a new company, click **Upload** and select any MSE Excel financial statement (`.xls` or `.xlsx`).

---

## Known Limitations

| Limitation | Reason |
|-----------|--------|
| Piotroski F7 always N/A | MSE Excel filings do not include shares outstanding |
| Beneish DEPI always N/A | MSE filings do not disclose depreciation as a separate line |
| EV/EBITDA uses EBIT proxy | No depreciation line available; labeled as EV/EBIT in UI |
| FCF not shown for financial sectors | Investing CF is core business activity for banks/insurers/NBFIs; Op. Cash Flow shown instead |
| Valuation ratios require shares input | Shares outstanding must be entered manually on the company page if not scraped |
| Price history scope | Pre-loaded for 7 demo companies; run "Refresh Prices" to scrape remaining MSE companies |
| 1–2 years of data | MSE members portal typically provides only the most recent filing year |

---

## Project Structure

See [`docs/STRUCTURE.md`](docs/STRUCTURE.md) for a detailed breakdown of every module, state class, event handler, and data shape.

---

*Demo data is provided for educational and research purposes. No investment advice is implied.*
