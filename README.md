# MSE Financial Dashboard

A financial statement analysis tool for companies listed on the **Mongolian Stock Exchange (MSE)**. Parses XLS reports from [mse.mn](https://mse.mn), computes financial ratios, and provides exploratory data analysis through interactive visualizations.

## Features

- **Automated XLS Parsing** — Upload Mongolian-language financial statements; headers are auto-mapped to standardized English fields
- **Structured JSON Storage** — Each company's data stored as JSON with balance sheet, income statement, and cash flow sections
- **26 Financial Ratios** — Activity (9), Liquidity (4), Solvency (4), Profitability (6), Performance (3), Altman Z-Score
- **EDA Notebook** — Jupyter notebook with 7 chart types: box plots, bar charts, scatter plots, correlation heatmaps, radar charts, and more
- **Auto-Discovery** — Add a new company JSON to `data/` and re-run the notebook — no code changes needed

## Project Structure

```
financial-dashboard/
├── data/                          # Parsed company JSON files
│   ├── Хаан_банк_2025.json
│   ├── АПУ_2025.json
│   ├── "_Премиум_Нэксус_"_ХК_2025.json
│   └── index.json
├── notebooks/
│   └── eda_report.ipynb           # EDA report notebook
├── financial_dashboard/
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── ratios.py              # Ratio computation engine
│   ├── parser/
│   │   ├── excel_parser.py        # XLS → JSON parser
│   │   └── header_mappings.py     # Mongolian → English field mapping
│   ├── storage/
│   │   └── json_store.py          # JSON file storage
│   ├── components/                # Reflex UI components
│   └── financial_dashboard.py     # Main Reflex app
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
```

## Usage

### Run the EDA Notebook

```bash
jupyter lab
# Open notebooks/eda_report.ipynb → Run All Cells
```

### Run the Web Dashboard

```bash
reflex run
```

### Add a New Company

1. Download the XLS financial statement from [members.mse.mn](https://members.mse.mn)
2. Upload via the dashboard UI, or place the parsed JSON in `data/`
3. Re-run the notebook — it auto-discovers all `data/*.json` files

## Companies Analyzed

| Company | Sector | Notes |
|---------|--------|-------|
| Хаан банк (Khan Bank) | Banking | No revenue/COGS (bank structure) |
| АПУ (APU) | Manufacturing/Beverages | Full income statement |
| Премиум Нэксус ХК | Manufacturing/Holding | Full income statement |

## EDA Report Contents

| Section | Rubric Weight | Description |
|---------|--------------|-------------|
| Data Acquisition | 20% | Dynamic JSON loading, DataFrame reshaping, column descriptions |
| Data Quality | 20% | Missing values heatmap, duplicates, dtypes, outlier detection |
| Visualizations | 25% | 7 charts (box, bar, scatter, heatmap, grouped bar, trend, radar) |
| Insights | 20% | Key findings, sector patterns, hypotheses, limitations |
| Documentation | 10% | Methodology, reproducibility, data dictionary |

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
- **Reflex** — Web dashboard framework
- **pandas / matplotlib / seaborn** — Data analysis and visualization
- **openpyxl / xlrd** — Excel file parsing
- **Jupyter** — Interactive notebook environment
