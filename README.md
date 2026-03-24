# MSE Analytica

A financial health analysis platform for companies listed on the **Mongolian Stock Exchange (MSE)**. Parses XLS reports from [members.mse.mn](https://members.mse.mn), computes forensic and fundamental scores, and surfaces insights through an interactive dark-themed web dashboard.

## Features

- **Automated XLS Parsing** — Upload Mongolian-language financial statements; headers are auto-mapped to standardized English fields
- **Structured JSON Storage** — Each company's data stored as JSON with balance sheet, income statement, and cash flow sections
- **26 Financial Ratios** — Profitability, Liquidity, Solvency, Activity, and Altman Z-Score
- **Piotroski F-Score** — 9-point rule-based fundamental strength signal (scored over available criteria)
- **Beneish M-Score** — Forensic fraud detection via 8 accounting indices (threshold: −1.78)
- **Composite Health Score (0–100)** — Weighted blend: profitability 25%, liquidity 20%, solvency 20%, activity 15%, Altman 10%, Piotroski 10%; −10 Beneish penalty if M > −1.78
- **Company Screener** — Browse all companies with health badges, F-Score, and ROE at a glance
- **Company Detail Page** — Full ratio table, Piotroski checklist, and Beneish indices
- **Portfolio Manager** — Add companies, equal-weight rebalancing, blended health score
- **EDA Notebook** — Jupyter notebook with 7 chart types for exploratory analysis

## Demo

```bash
./venv/bin/reflex run
# Open http://localhost:3000
# Click "Load 7 MSE Companies" to instantly load all pre-parsed companies
```

## Project Structure

```
financial-dashboard/
├── data/                          # Parsed company JSON files + index.json
├── docs/plans/                    # Design and implementation plans
├── notebooks/
│   └── eda_report.ipynb           # EDA report notebook
├── financial_dashboard/
│   ├── analysis/
│   │   ├── ratios.py              # Ratio, Piotroski, Beneish, Composite computation
│   │   └── labels.py             # Display labels for ratios and criteria
│   ├── parser/
│   │   ├── excel_parser.py        # XLS → JSON parser
│   │   └── header_mappings.py     # Mongolian → English field mapping
│   ├── storage/
│   │   └── json_store.py          # JSON file storage
│   ├── components/
│   │   ├── layout.py              # Dark sidebar layout wrapper
│   │   ├── sidebar.py             # Navigation sidebar
│   │   ├── upload_zone.py         # File upload component
│   │   └── file_list.py           # Uploaded files table
│   ├── pages/
│   │   ├── screener.py            # Company screener page
│   │   ├── company.py             # Individual company analysis page
│   │   └── portfolio.py           # Portfolio management page
│   ├── state.py                   # Reflex state (Upload, Analysis, Portfolio)
│   └── financial_dashboard.py     # App entry point + routes
├── requirements.txt
└── README.md
```

## Setup

```bash
# Clone the repository
git clone https://github.com/dlgvn/financial-dashboard.git
cd financial-dashboard

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
reflex run
```

## Routes

| Route | Description |
|-------|-------------|
| `/` | Upload page — upload XLS or use demo shortcut |
| `/screener` | Company screener with health scores and methodology panel |
| `/company/[company]` | Individual company analysis |
| `/portfolio` | Portfolio manager with blended health score |

## Companies Analyzed (2025)

| Company | Sector | Health Score |
|---------|--------|-------------|
| АПУ (APU) | Manufacturing / Beverages | 71 — Healthy |
| Хаан банк (Khan Bank) | Banking | 36 — Distress |
| Мандал даатгал | Insurance | ~50 — Caution |
| Сүү | Dairy / Food | ~48 — Caution |
| Моносхүнс | Food Processing | ~44 — Caution |
| Дархан нэхий | Textiles | ~46 — Caution |
| Премиум Нэксус ХК | Holding / Manufacturing | ~48 — Caution |

## Scoring Models

### Piotroski F-Score (0–9)
Nine binary criteria across profitability (F1–F4), leverage/liquidity (F5–F6), and efficiency (F8–F9). Scored over non-None criteria only. Interpretation: ≥7 Strong, 4–6 Neutral, ≤3 Weak.

### Beneish M-Score
Eight indices (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA). M > −1.78 flags potential manipulation. DEPI is always N/A in MSE filings (no separate depreciation disclosure). Reliable if ≥5 indices available.

### Composite Health Score (0–100)
| Component | Weight |
|-----------|--------|
| Profitability ratios | 25% |
| Liquidity ratios | 20% |
| Solvency ratios | 20% |
| Activity ratios | 15% |
| Altman Z-Score | 10% |
| Piotroski F-Score | 10% |
| Beneish penalty (if M > −1.78) | −10 pts |

Labels: ≥60 Healthy (green), 40–59 Caution (amber), <40 Distress (red).

## Known Limitations

- Dataset: 7 MSE companies, 1–2 years of historical data
- DEPI index always N/A — MSE filings don't disclose depreciation separately
- No market price data — P/E ratio and market cap ratios out of scope
- Banking sector (Khan Bank) uses different financial structure; some ratios not applicable

## Data Format

All monetary values are in **₮ thousands** (Mongolian Tugrik). Each JSON file follows:

```json
{
  "metadata": { "company": "...", "year": "2025" },
  "balance_sheet": { "total_assets": 123.45, "total_assets_prev": 100.0 },
  "income_statement": { "revenue": 500.0, "revenue_prev": 450.0 },
  "cash_flow": { "operating_cash_flow": 80.0, "operating_cash_flow_prev": 70.0 }
}
```

## Tech Stack

- **Python 3.12**
- **Reflex 0.8.26** — Web dashboard framework
- **pandas / matplotlib / seaborn** — Data analysis and visualization
- **openpyxl / xlrd** — Excel file parsing
- **Jupyter** — Interactive notebook environment
