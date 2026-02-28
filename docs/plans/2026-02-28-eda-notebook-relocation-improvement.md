# EDA Notebook Relocation & Improvement Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move `financial-dashboard/notebooks/` to `Capstone Project/EDA Report/`, rewrite data ingestion to parse raw Excel files directly (bypassing the JSON pipeline), remove Z-score, and keep only 3 core ratios per category.

**Architecture:**
- The notebook shifts from reading pre-parsed `data/*.json` to loading raw `.xls/.xlsx` files from `Raw Data/` and calling `parse_excel_file()` inline.
- Ratio computation is inlined in the notebook itself using a trimmed engine (no Z-score; 3 ratios per category × 4 categories = 12 ratios total).
- The only external module import retained is `parse_excel_file` from `financial_dashboard.parser.excel_parser`.

**Tech Stack:** Python 3.12, xlrd, openpyxl, pandas, matplotlib, seaborn, pathlib

---

## Path Map (Before → After)

```
BEFORE:
  Capstone Project/
    financial-dashboard/
      notebooks/
        eda_report.ipynb        ← was here
      data/
        *.json                  ← old data source (website-generated, skip this)
      financial_dashboard/
        parser/excel_parser.py  ← still used
        analysis/ratios.py      ← no longer imported by notebook

AFTER:
  Capstone Project/
    EDA Report/
      eda_report.ipynb          ← moved here
    Raw Data/
      *.xls / *.xlsx            ← NEW data source (raw Excel files)
    financial-dashboard/
      financial_dashboard/
        parser/excel_parser.py  ← still imported for parsing
```

## Ratios to Keep (3 per category, Z-score removed)

| Category | Key | Label |
|----------|-----|-------|
| **Activity** | `total_asset_turnover` | Total Asset Turnover |
| | `inventory_turnover` | Inventory Turnover |
| | `days_sales_outstanding` | Days Sales Outstanding |
| **Liquidity** | `current_ratio` | Current Ratio |
| | `quick_ratio` | Quick Ratio |
| | `cash_ratio` | Cash Ratio |
| **Solvency** | `debt_to_equity` | Debt-to-Equity |
| | `debt_to_assets` | Debt-to-Assets |
| | `interest_coverage` | Interest Coverage |
| **Profitability** | `roa` | Return on Assets (ROA) |
| | `roe` | Return on Equity (ROE) |
| | `net_margin` | Net Profit Margin |

---

### Task 1: Move and Rename the Folder

**Step 1: Move the folder**

```bash
mv "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/financial-dashboard/notebooks" \
   "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/EDA Report"
```

**Step 2: Confirm the move succeeded**

```bash
ls "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/EDA Report/"
# Expected: eda_report.ipynb  .ipynb_checkpoints/
```

**Step 3: Remove old directory from git tracking**

```bash
cd "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/financial-dashboard"
git rm -r --cached notebooks/ 2>/dev/null || true
```

---

### Task 2: Rewrite `cell-02-setup` — Fix Paths + Import Parser

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-02-setup`

Replace the entire cell source with:

```python
import json
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

# ── Path setup ────────────────────────────────────────────────────────────────
# Notebook lives in:  Capstone Project/EDA Report/
# Raw Excel files in: Capstone Project/Raw Data/
# Parser module in:   Capstone Project/financial-dashboard/

_notebook_dir = Path.cwd()                                   # …/EDA Report
_capstone_dir = _notebook_dir.parent                         # …/Capstone Project
FINANCIAL_DASHBOARD = (_capstone_dir / "financial-dashboard").resolve()
RAW_DATA_DIR = (_capstone_dir / "Raw Data").resolve()

if not FINANCIAL_DASHBOARD.exists():
    raise FileNotFoundError(
        f"Could not find financial-dashboard at {FINANCIAL_DASHBOARD}\n"
        f"Make sure Jupyter is launched from inside 'EDA Report/'."
    )
if not RAW_DATA_DIR.exists():
    raise FileNotFoundError(
        f"Could not find Raw Data at {RAW_DATA_DIR}"
    )

sys.path.insert(0, str(FINANCIAL_DASHBOARD))
from financial_dashboard.parser.excel_parser import parse_excel_file  # noqa: E402

# ── Display settings ──────────────────────────────────────────────────────────
warnings.filterwarnings("ignore", category=FutureWarning)
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams.update({
    "figure.figsize": (12, 6),
    "figure.dpi": 100,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})

print(f"Financial dashboard root : {FINANCIAL_DASHBOARD}")
print(f"Raw data directory       : {RAW_DATA_DIR}")

xls_files = sorted(RAW_DATA_DIR.glob("*.xls")) + sorted(RAW_DATA_DIR.glob("*.xlsx"))
print(f"\nFound {len(xls_files)} Excel files:")
for f in xls_files:
    print(f"  {f.name}")
```

---

### Task 3: Rewrite `cell-03-load` — Parse Raw Excel Files

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-03-load`

Replace source with:

```python
# Parse every raw Excel file found in Raw Data/
raw_data = {}
parse_errors = []

for fpath in xls_files:
    try:
        file_bytes = fpath.read_bytes()
        parsed = parse_excel_file(file_bytes, fpath.name)
        company = parsed["metadata"]["company"]
        sheets = parsed["metadata"]["sheets_parsed"]
        raw_data[company] = parsed
        print(f"  ✓  {fpath.name}  →  '{company}'  (sheets: {sheets})")
    except Exception as e:
        parse_errors.append((fpath.name, str(e)))
        print(f"  ✗  {fpath.name}  →  ERROR: {e}")

print(f"\nParsed successfully: {len(raw_data)} companies")
if parse_errors:
    print(f"Errors: {len(parse_errors)}")
    for name, err in parse_errors:
        print(f"  {name}: {err}")
```

---

### Task 4: Replace `cell-04-reshape` — Reshape Parsed Data to DataFrame

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-04-reshape`

Replace source with:

```python
# Reshape: one row per company-period with all financial fields as columns
rows = []
for company, data in raw_data.items():
    for period, suffix in [("current", ""), ("prev", "_prev")]:
        row = {"company": company, "period": period}
        for section in ["balance_sheet", "income_statement", "cash_flow"]:
            section_data = data.get(section, {})
            for key, value in section_data.items():
                if suffix == "":
                    if not key.endswith("_prev"):
                        row[key] = value
                else:
                    if key.endswith("_prev"):
                        row[key[:-5]] = value   # strip _prev
        rows.append(row)

df = pd.DataFrame(rows)

# Drop section-header columns (artifact from parsing)
section_cols = [c for c in df.columns if c.endswith("_section")]
df = df.drop(columns=section_cols, errors="ignore")

print(f"DataFrame shape: {df.shape}")
print(f"Companies ({len(df['company'].unique())}): {df['company'].unique().tolist()}")
print(f"Periods: {df['period'].unique().tolist()}")
df.head()
```

---

### Task 5: Replace Ratio Computation — Inline Slimmed Engine

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-10-ratios`

Replace source with a self-contained ratio engine (no Z-score, 3 ratios per category):

```python
# ── Inline ratio engine (no external import needed) ───────────────────────────
def safe_div(a, b):
    if a is None or b is None:
        return None
    try:
        return None if b == 0 else a / b
    except (TypeError, ZeroDivisionError):
        return None


def compute_ratios(parsed_data: dict) -> dict:
    """Compute 3 ratios per category (Activity, Liquidity, Solvency, Profitability)."""
    bs  = parsed_data.get("balance_sheet", {})
    inc = parsed_data.get("income_statement", {})
    cf  = parsed_data.get("cash_flow", {})
    company = parsed_data.get("metadata", {}).get("company", "Unknown")

    result = {"company": company, "current": {}, "prev": {}}

    for suffix, period_key in [("", "current"), ("_prev", "prev")]:
        g = lambda key: bs.get(f"{key}{suffix}") or inc.get(f"{key}{suffix}") or cf.get(f"{key}{suffix}")

        total_assets            = g("total_assets")
        total_liabilities       = g("total_liabilities")
        total_equity            = g("total_equity")
        total_current_assets    = g("total_current_assets")
        total_current_liabilities = g("total_current_liabilities")
        cash                    = g("cash_and_equivalents")
        inventory               = g("inventory")
        accounts_receivable     = g("accounts_receivable")
        short_term_loans        = bs.get(f"short_term_loans{suffix}")
        long_term_loans         = bs.get(f"long_term_loans{suffix}")
        revenue                 = inc.get(f"revenue{suffix}")
        cogs                    = inc.get(f"cost_of_goods_sold{suffix}")
        net_income              = inc.get(f"net_income{suffix}")
        profit_before_tax       = inc.get(f"profit_before_tax{suffix}")
        financial_expense       = inc.get(f"financial_expense{suffix}")

        # Derived
        if total_equity is None and total_assets and total_liabilities:
            total_equity = total_assets - total_liabilities
        ebit = (profit_before_tax + financial_expense) if (profit_before_tax and financial_expense) else profit_before_tax

        # ── Activity ────────────────────────────────────
        rec_turnover = safe_div(revenue, accounts_receivable)
        activity = {
            "total_asset_turnover":   safe_div(revenue, total_assets),
            "inventory_turnover":     safe_div(cogs, inventory),
            "days_sales_outstanding": safe_div(365, rec_turnover),
        }

        # ── Liquidity ───────────────────────────────────
        quick = safe_div((total_current_assets - inventory) if (total_current_assets and inventory) else None,
                         total_current_liabilities)
        liquidity = {
            "current_ratio": safe_div(total_current_assets, total_current_liabilities),
            "quick_ratio":   quick,
            "cash_ratio":    safe_div(cash, total_current_liabilities),
        }

        # ── Solvency ────────────────────────────────────
        solvency = {
            "debt_to_equity":   safe_div(total_liabilities, total_equity),
            "debt_to_assets":   safe_div(total_liabilities, total_assets),
            "interest_coverage": safe_div(ebit, financial_expense),
        }

        # ── Profitability ───────────────────────────────
        profitability = {
            "roa":        safe_div(net_income, total_assets),
            "roe":        safe_div(net_income, total_equity),
            "net_margin": safe_div(net_income, revenue),
        }

        result[period_key] = {
            "activity":      activity,
            "liquidity":     liquidity,
            "solvency":      solvency,
            "profitability": profitability,
        }

    return result


# Human-readable labels  (key → (label, unit))
RATIO_LABELS = {
    "total_asset_turnover":   ("Total Asset Turnover",    "times"),
    "inventory_turnover":     ("Inventory Turnover",       "times"),
    "days_sales_outstanding": ("Days Sales Outstanding",   "days"),
    "current_ratio":          ("Current Ratio",            "x"),
    "quick_ratio":            ("Quick Ratio",              "x"),
    "cash_ratio":             ("Cash Ratio",               "x"),
    "debt_to_equity":         ("Debt-to-Equity",           "x"),
    "debt_to_assets":         ("Debt-to-Assets",           "ratio"),
    "interest_coverage":      ("Interest Coverage",        "x"),
    "roa":                    ("Return on Assets (ROA)",   "%"),
    "roe":                    ("Return on Equity (ROE)",   "%"),
    "net_margin":             ("Net Profit Margin",        "%"),
}

# ── Run computation ────────────────────────────────────────────────────────────
all_ratios = {company: compute_ratios(data) for company, data in raw_data.items()}

categories = ["activity", "liquidity", "solvency", "profitability"]
print(f"Computed {len(RATIO_LABELS)} ratios (3 per category) for {len(all_ratios)} companies")
```

---

### Task 6: Update the Ratio Display Table (`cell-11-ratio-table`)

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-10-ratios` (the display cell immediately after)

The existing `cell-11-ratio-table` code references `categories` which no longer includes `z_score` or `performance` — it will work as-is **if** the loop variable `categories` is updated. Verify the loop in that cell reads:

```python
categories = ["activity", "liquidity", "solvency", "profitability"]
```

If it still contains `"performance"` or `"z_score"`, remove those two entries.

---

### Task 7: Update Chart 5 (`cell-16-chart5`) — Remove Z-score from ratio comparison

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-16-chart5`

Change the `key_ratios` dict to only use the 4 kept categories:

```python
key_ratios = {
    "profitability": ["roa", "roe", "net_margin"],
    "liquidity":     ["current_ratio", "quick_ratio", "cash_ratio"],
    "solvency":      ["debt_to_equity", "debt_to_assets", "interest_coverage"],
    "activity":      ["total_asset_turnover", "inventory_turnover", "days_sales_outstanding"],
}
fig, axes = plt.subplots(1, 4, figsize=(22, 6))   # 4 panels now
```

---

### Task 8: Update Chart 7 Radar (`cell-18-chart7`) — Remove Z-score metrics

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-18-chart7`

Update `radar_metrics` to use only kept ratios:

```python
radar_metrics = {
    "ROA":            ("profitability", "roa"),
    "ROE":            ("profitability", "roe"),
    "Net Margin":     ("profitability", "net_margin"),
    "Current Ratio":  ("liquidity",     "current_ratio"),
    "Debt/Assets":    ("solvency",      "debt_to_assets"),
}
```

The normalization and inversion for `"Debt/Assets"` stays the same (lower = better → invert).

---

### Task 9: Update Insights Cell (`cell-19-insights`) — Remove Z-score block

**File:** `EDA Report/eda_report.ipynb` — cell id `cell-19-insights`

Remove the Z-score section from the printed output:

```python
# DELETE these lines:
z = curr["z_score"]["z_score"]
if z:
    zone = "Safe (>2.99)" if z > 2.99 else "Grey (1.81-2.99)" if z > 1.81 else "Distress (<1.81)"
    print(f"  Z-Score: {z:.2f} → {zone}")
else:
    print(f"  Z-Score: N/A (missing inputs)")
```

Also remove the `z_score` key from `curr` lookups — the category no longer exists.

---

### Task 10: Update Markdown Docs

**Cells:** `cell-01-title`, `cell-20-findings`, `cell-21-documentation`

**`cell-01-title`** — complete the company table:
```markdown
| Company | Sector | Ticker |
|---------|--------|--------|
| Хаан банк (Khan Bank) | Banking | KHAN |
| Премиум Нэксус ХК | Manufacturing/Holding | CUMN |
| АПУ | Manufacturing/Beverages | APU |
| Мандал даатгал | Insurance | MNDL |
| Дархан нэхий ХК | Manufacturing/Textiles | DKHN |
| Моносхүнс | Food & Beverage | MNKH |
| Сүү | Food & Beverage | SUU |
```

**`cell-20-findings`** — update Limitations:
- Change "Only 3 companies" → "7 companies across 4 sectors"
- Remove the Z-score hypothesis H3

**`cell-21-documentation`** — update reproducibility instructions:
```bash
# 3. Launch Jupyter from the EDA Report folder
cd "Capstone Project/EDA Report"
jupyter lab
# Open eda_report.ipynb → Run All Cells
# Note: Raw Excel files are read directly from ../Raw Data/
```

Also update the Data Pipeline section to describe the new flow:
```
1. Raw XLS/XLSX files placed in  Capstone Project/Raw Data/
2. Notebook calls parse_excel_file() on each file at runtime
3. Parsed dicts flow directly into DataFrame reshape + ratio computation
```

---

### Task 11: Verify Notebook Runs End-to-End

**Step 1: Execute via nbconvert**

```bash
cd "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/EDA Report"
jupyter nbconvert --to notebook --execute eda_report.ipynb \
  --output eda_report_verified.ipynb 2>&1 | tail -30
```

Expected: `Writing ... notebook` with no `Error` or `Traceback` lines.

**Step 2: Check output**

```bash
ls -lh "eda_report_verified.ipynb"
# If file >100KB → success; clean up:
rm eda_report_verified.ipynb
```

**Step 3: Common failure modes**

| Error | Fix |
|-------|-----|
| `FileNotFoundError: financial-dashboard` | Jupyter started from wrong directory — launch from `EDA Report/` |
| `ModuleNotFoundError: financial_dashboard` | `FINANCIAL_DASHBOARD` path wrong — check Task 2 |
| `ValueError: No recognizable sheets` | Raw Excel file has non-standard sheet names — check parser logs |
| `KeyError: z_score` | Leftover z_score reference — check Tasks 7–9 |

---

### Task 12: Commit

```bash
cd "/Users/dlgvnbyr/Documents/Hicheel/Capstone Project/financial-dashboard"
git add -A
git commit -m "feat: EDA notebook — raw Excel ingestion, slim ratios (3/category), no Z-score

- Moved notebooks/ to Capstone Project/EDA Report/
- Data source: raw .xls/.xlsx from Raw Data/ via parse_excel_file()
- Removed dependency on pre-parsed data/*.json files
- Inlined ratio engine: 3 ratios × 4 categories = 12 ratios
- Removed Altman Z-Score and performance category
- Updated all charts, radar, and markdown docs accordingly"
```
