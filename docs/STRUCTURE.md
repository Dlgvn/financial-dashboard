# MSE Analytica — File Structure

## Project Layout

```
financial-dashboard/
├── financial_dashboard/
│   ├── financial_dashboard.py    ← App entry point + home page UI
│   ├── state.py                  ← All Reflex state classes
│   ├── parser/                   ← Excel parsing engine
│   ├── storage/                  ← JSON persistence
│   ├── scraper/                  ← Price scraping + registry
│   ├── analysis/                 ← Financial computation engines
│   ├── components/               ← Reusable UI components
│   └── pages/                    ← Page-level UI
└── data/
    ├── index.json                ← Master manifest
    ├── company_registry.json     ← 68-company registry
    ├── prices/                   ← {company}.json OHLCV files
    └── {Company}_{year}.json     ← Parsed financial data files
```

---

## `financial_dashboard.py` — App Entry Point

Registers 4 routes and defines the home page UI:

| Route | Page | On-load |
|---|---|---|
| `/` | `index()` | `PortfolioState.load_screener` |
| `/screener` | `screener_page` | `PortfolioState.load_screener` |
| `/company/[company]` | `company_page` | `AnalysisState.on_load_company` |
| `/portfolio` | `portfolio_page` | — |

> **Why `PortfolioState.load_screener` and not `AnalysisState.load_screener`:** Reflex substates own separate copies of inherited vars. Calling `AnalysisState.load_screener` populates only `AnalysisState.all_companies`; `PortfolioState.all_companies` (read by `add_to_portfolio`) stays empty, causing every "Add" button to silently no-op. Both the index and screener pages use `PortfolioState.*` for all screener-related state vars (`filtered_companies`, `screener_sort_col`, `screener_filter`, etc.).

**Home page sections:**
1. **Demo mode** — "Load 7 MSE Companies" → skips upload, loads pre-parsed data, redirects to `/screener`
2. **Upload zone** — drag-and-drop `.xls/.xlsx`
3. **Uploaded Companies** table — lists parsed files with delete buttons
4. **Price Data** — "Refresh Prices" button re-scrapes `old.mse.mn` for all uploaded companies; shows per-company status log

---

## `state.py` — State Classes

Three layered classes (each inherits the previous):

### `UploadState(rx.State)`

| Var | Type | Purpose |
|---|---|---|
| `is_uploading` | `bool` | Spinner during parse |
| `uploaded_files` | `list[dict]` | Table rows from index.json |
| `parse_error` / `success_message` | `str` | Feedback callouts |
| `is_refreshing_prices` | `bool` | Price refresh spinner |
| `price_refresh_log` | `list[dict]` | Per-company scrape result rows |
| `price_refresh_summary` | `str` | "N updated, M failed" |
| `selected_file` | `str` | Currently selected filename |

**Events:**
- `handle_upload(files)` → `parse_excel_file()` → `save_parsed_data()` → refresh list
- `on_load()` → reads index.json into `uploaded_files`
- `delete_file(filename)` → removes file + index entry
- `refresh_prices()` → for each company: `find_mse_id()` → `scrape_company_prices()` → `save_price_data()`

---

### `AnalysisState(UploadState)`

Holds ~80 flat display vars (pre-formatted strings) for the company detail page — necessary because Reflex reactive vars cannot be nested dicts rendered directly.

**Screener vars:** `all_companies`, `screener_filter`, `screener_sort_col`, `screener_sort_asc`

**Company display vars (by group):**

| Group | Key vars |
|---|---|
| Composite | `company_score`, `company_health_label`, `company_health_color` |
| Piotroski | `company_f_score_display`, `company_f1`–`company_f9` (int: 1/0/−1) — N/A for Banking/Insurance/Finance |
| Beneish | `company_m_score_display`, `company_dsri/gmi/aqi/sgi/sgai/lvgi/tata` — N/A for Banking/Insurance/Finance |
| Sector Forensic | `company_sector_forensic_criteria: list[dict]`, `company_sector_forensic_score_display: str`, `company_sector_forensic_chart_data: list[dict]` — populated only for Banking/Insurance/Finance |
| Standard ratios | `roa`, `roe`, `net_margin`, `current_ratio`, `quick_ratio`, `debt_equity`, `interest_cov`, `asset_turnover`, `z_score` + 18 extended |
| Bank-specific | 19 vars: `nim`, `car`, `npl_ratio`, `ldr`, `cost_to_income`, … |
| Insurance-specific | 15 vars: `loss_ratio`, `combined_ratio`, `solvency_ratio`, … |
| Finance-specific | 21 vars (`company_fin_*`): `nim`, `yield_on_earning_assets`, `cost_of_funds`, `interest_spread`, `roa`, `roe`, `net_margin`, `cost_to_income`, `operating_expense_ratio`, `non_interest_income_ratio`, `asset_utilisation`, `debt_to_equity`, `debt_to_assets`, `equity_ratio`, `equity_multiplier`, `cash_ratio`, `ocf_ratio`, `loan_to_assets`, `npa_ratio`, `receivables_to_assets`, `provision_coverage` |
| DuPont | `net_margin_dupont/prev`, `asset_turnover_dupont/prev`, `equity_multiplier_curr/prev`, `roe_dupont/prev` |
| Valuation | `company_valuation_sector`, `ev_ebitda`, `fcf` (M₮, standard only), `fcf_yield`, `ocf` (M₮, all sectors), `pe`, `pbv`, `shares_outstanding`, `ptbv`, `p_ppop`, `p_nii`, `p_npe`, `p_uwp`, `p_inv_sec`, `p_revenue` |
| Charts | `gauge_data`, `radar_data`, `beneish_chart_data`, `price_chart_data`, `volume_chart_data` |
| Red flags | `company_red_flags: list[dict]`, `company_red_flags_loading: bool` |

**Sector flags:** `company_is_bank: bool`, `company_is_insurance: bool`, `company_is_finance: bool` — control conditional tab rendering.

**Key events:**
- `load_company(name)` — async; full sector-aware analysis: detects Banking / Insurance / Finance / Standard → runs matching ratio engine → populates all flat vars → calls `_load_valuation_data()` → yields to flush UI → calls Groq AI for red flags upgrade
- `on_load_company()` — reads `[company]` URL param → returns `AnalysisState.load_company()`
- `load_screener()` → `_load_all_companies()` — processes all index.json entries with scores
- `set_valuation_range(range)` — re-slices price records for 1M/6M/1Y/All chart views
- `save_shares_outstanding(value)` — writes `shares_outstanding_override` into the company's financial JSON; recomputes valuation

**Computed var:** `filtered_companies` — sector filter + sort applied over `all_companies`

**Module-level helpers:**
- `_fmt(v, decimals)` — formats a float for display (`"N/A"` when None); used for ratio/multiplier values displayed with "x" or "ratio" units
- `_pct(v, decimals)` — multiplies by 100 then formats; used for all ratio values displayed with "%" unit (ROA, ROE, margins, NIM, LDR, Loss Ratio, etc.)
- `_load_all_companies()` — reads index.json, computes composite score per company for screener
- `_detect_sector_from_data(data)` — heuristic: checks for bank/insurance sheet keys in parsed dict
- `_detect_finance_subsector(name)` — classifies Finance companies into subsector; registry lookup (`find_sub_sector`) takes precedence over name-pattern heuristics
- `_compute_red_flags(ratios, beneish)` — rule-based fallback: returns list of flag dicts (DSRI spike, TATA, D/E jump, M-Score, current ratio drop); used as instant seed before AI response arrives

**Formatting contract:** all ratio engines return raw decimals (e.g. `0.12` for 12%). State assignments use `_pct` for "%" display vars and `_fmt` for "x"/"ratio" display vars. `_slice_price_records` casts `volume` to `int` before storing chart data. `_load_valuation_data` reads `index.json` once and reuses the loaded `fin_data` for both the shares-override check and valuation computation.

---

### `PortfolioState(AnalysisState)`

| Var | Purpose |
|---|---|
| `holdings` | `list[dict]` — each: `{company, weight, score, sector, …}` |
| `active_portfolio_tab` | `"holdings"` or `"analysis"` |
| `sector_chart_data` | Donut chart input |
| `frontier_data` | Efficient frontier scatter (200 samples) |
| `current_point_data` | Current portfolio point on frontier |
| `optimization_data` | Table: current % vs optimal % per company |
| `sortino_str / max_drawdown_str / cvar_str` | Risk metric display strings |
| `can_show_analysis` | Guard: requires ≥2 companies with price data |

**Events:**
- `add_to_portfolio(company)` — equal-weight rebalance on add; looks up `self.all_companies` (populated by `load_screener` on the same `PortfolioState` instance)
- `remove_from_portfolio(company)` — rebalances remaining
- `set_holding_weight(company, value)` — manual weight edit → `rebalance_weights()`
- `apply_optimal_weights()` — applies mean-variance optimal weights from `optimization_data`
- `on_tab_change(tab)` — triggers `_run_portfolio_analysis()` when switching to "analysis" tab

**Holdings dict keys:** `company`, `filename`, `url`, `weight` (float 0–1), `weight_str` (e.g. `"33.3%"`), `weight_pct` (e.g. `"33.3"`), `score`, `score_str`, `label`, `color`, `sector`.

**Computed vars:** `portfolio_health` (weighted avg score), `in_portfolio` (list of names)

---

## `parser/`

### `excel_parser.py` — Core Parser

Entry point: `parse_excel_file(file_bytes, filename, sector="") → dict`

**MSE file column layout:**

| Col | Index | Content |
|---|---|---|
| C | 2 | Mongolian header text |
| D | 3 | Previous year value |
| E | 4 | Current year value |

**Output shape:**
```python
{
  "metadata": {filename, company, year, parsed_at, sheets_parsed},
  "balance_sheet": {field: curr, field_prev: prev, ...},
  "income_statement": {...},
  "cash_flow": {...},
  # Banks get:  "bank_balance_sheet", "bank_income_statement"
  # Insurers get: "insurance_balance_sheet", "insurance_income_statement"
  # Finance/NBFIs: may produce either bank_* sheets or standard sheets
  #   depending on whether the company uses the banking IS format
}
```

**Sector routing:** `_SECTOR_SHEET_OVERRIDES` redirects standard sheet names (e.g. "баланс") to bank/insurance header dictionaries when sector is known. Prevents Mongolian terminology overlap between sectors.

**Flow:** `_parse_xlsx` (openpyxl) or `_parse_xls` (xlrd) → `_detect_sheet_type()` → select dict from `HEADERS_BY_TYPE` → `_parse_openpyxl_sheet()` / `_parse_xlrd_sheet()` → row scan on col C, values from cols D/E.

**Company name extraction:** Scans first 5 rows for `"Байгууллагын нэр: <name>"` pattern; always overrides filename-derived name.

---

### `header_mappings.py` — Mongolian → English Dictionaries

9 header dictionaries (one per statement type) + `SHEET_TYPE_PATTERNS` for tab-name detection:

1. `balance_sheet` — standard
2. `income_statement` — standard
3. `cash_flow`
4. `bank_balance_sheet`
5. `bank_income_statement` — also used by Finance/NBFI companies that follow the banking IS format; maps `admin_expenses` among others
6. `insurance_balance_sheet`
7. `insurance_income_statement`
8. `securities_balance_sheet` — FRC-format securities/investment companies; superset of `balance_sheet` with broker receivables, investment securities, and client account payables
9. `securities_income_statement` — FRC-format; covers fee/commission income, trading income, and OCI rows; handles Cyrillic/Latin homoglyph variants in header text

`match_header(cell_text, headers_dict)` — normalizes Mongolian text and matches to English key.

---

## `storage/json_store.py` — JSON Persistence

**Storage path:** `data/{Company}_{year}.json`

**`index.json` entry shape:**
```json
{
  "filename": "АПУ_2024.json",
  "company": "АПУ",
  "year": "2024",
  "sector": "Standard",
  "sheets_parsed": ["balance_sheet", "income_statement"],
  "parsed_at": "..."
}
```

**Functions:**
- `save_parsed_data(parsed_dict)` — writes `{company}_{year}.json`; calls `_detect_sector()` then `_update_index()`
- `load_index()` → `{"files": [...]}` or `{"files": []}` if missing
- `delete_parsed_file(filename)` — removes file + index entry
- `load_parsed_file(filename)` — reads by filename

**`_detect_sector(parsed_dict)`** — registry name lookup → filename mse_id fallback → sheet-key heuristic (bank/insurance keys present).

---

## `scraper/`

### `price_scraper.py` — OHLCV Scraper

**Source:** `https://old.mse.mn/mn/company/{mse_id}` (Mongolian page — contains shares outstanding)

- `scrape_company_prices(mse_id, company_name)` → `(records, shares_outstanding)` — parses `<table class="trade_history_result">`; columns: No/High/Low/Open/Close/Volume/Value/Date
- `scrape_shares_outstanding(soup)` — reads `#trade_chart > 2nd direct div > ul > li[7] > b` ("Нийт гаргасан хувьцаа")
- `save_price_data(company_name, mse_id, records, shares_outstanding)` → writes `data/prices/{company}.json`:
```json
{
  "company": "АПУ",
  "mse_id": 90,
  "scraped_at": "...",
  "shares_outstanding": 1234567,
  "records": [{"date": "...", "open": "...", "high": "...", "low": "...", "close": "...", "volume": "..."}]
}
```
- `price_filename(company_name)` — sanitizes Mongolian name for filesystem

---

### `registry_loader.py` — Company Registry

**Source:** `data/company_registry.json` (lazy-loaded, module-level cache)

| Function | Returns |
|---|---|
| `find_mse_id(name)` | `int` — raises `KeyError` if not found |
| `find_sector(name)` | `str \| None` — "Banking", "Insurance", "Finance", "Standard" |
| `find_sector_by_mse_id(id)` | `str \| None` |
| `find_sector_from_filename(filename)` | `str \| None` — extracts mse_id from filename first |
| `find_sub_sector(name)` | `str \| None` — e.g. "Securities", "ББСБ (Lending NBFI)", "Investment/Holding" |
| `find_sub_sector_by_mse_id(id)` | `str \| None` |
| `all_companies()` | `list[dict]` |

Name normalization: strips `"` `'`, collapses whitespace, lowercases. Checks `aliases` list per entry.

---

## `analysis/`

### `ratios.py` — Standard Ratio Engine

`compute_ratios(parsed_data)` → `{"company": str, "current": {...}, "prev": {...}}`

~25 ratios computed for both periods:

| Category | Ratios |
|---|---|
| Profitability | ROA, ROE, net margin, gross margin, operating margin, EBIT margin |
| Liquidity | current ratio, quick ratio, cash ratio, working capital |
| Solvency | debt/equity, debt/assets, equity ratio, interest coverage |
| Activity | asset turnover, fixed asset, inventory, DSO, DPO, cash conversion cycle (9 total) |
| Performance | OCF ratio, CF-to-debt, reinvestment ratio |
| Altman Z | X1–X5 components + Z-score |

Also exports:
- `compute_piotroski(data)` → `{f_score, max_score, criteria: {f1..f9}}`
- `compute_beneish(data)` → `{m_score, reliable, interpretation, indices: {dsri..tata}}`
- `compute_composite_score(ratios, piotroski, beneish)` → `{score: 0–100, label, color, breakdown}`

---

### `bank_ratios.py` — Banking Ratios

`compute_bank_ratios(parsed_data)` → `{"current": {...}, "prev": {...}}`

19 ratios across: Profitability (NIM, ROA, ROE, net margin, interest income ratio) · Capital Adequacy (equity multiplier, equity-to-assets) · Asset Quality (NPL ratio, coverage ratio, loan loss reserve, provision-to-loans) · Liquidity (LDR, cash-to-deposits, loans-to-assets, securities-to-assets) · Efficiency (cost-to-income, fee income ratio)

**`interest_income_ratio`** returns `None` (not 1.0) when neither `interest_income` nor `net_interest_income` is available — prevents the spurious 100% reading that occurred when `net_banking_income` was used as both numerator and denominator.

---

### `insurance_ratios.py` — Insurance Ratios

`compute_insurance_ratios(parsed_data)` → `{"current": {...}, "prev": {...}}`

15 ratios across: Underwriting (loss, expense, combined ratio) · Profitability (ROA, ROE, net margin, investment income, underwriting margin) · Solvency (solvency ratio, leverage ratio, equity-to-liabilities, reserve coverage) · Liquidity (OCF ratio, investment ratio, cash-to-liabilities)

**`reserve_coverage`** denominator priority: `claims_incurred` (most accurate) → `premiums` (fallback). Previously always used premiums, which understated coverage when claims < premiums.

---

### `finance_ratios.py` — Finance / NBFI Ratios

`compute_finance_ratios(parsed_data)` → `{"company": str, "is_finance": True, "current": {...}, "prev": {...}, "missing_fields": [...], "data_quality": str}`

20 ratios across 5 categories, designed for non-bank financial institutions (securities firms, leasing, BBSB/ББСБ, holding companies):

| Category | Ratios |
|---|---|
| Profitability | NIM, yield on earning assets, cost of funds, interest spread, ROA, ROE, net margin |
| Efficiency | cost-to-income, operating expense ratio, non-interest income ratio, asset utilisation |
| Leverage | debt-to-equity (borrowings), debt-to-assets, equity ratio, equity multiplier |
| Liquidity | cash ratio, OCF ratio, loan-to-assets |
| Asset Quality | NPA ratio, receivables-to-assets, provision coverage |

**Input routing:** reads `bank_balance_sheet` / `bank_income_statement` when present (companies using the banking IS format, e.g. securities firms), otherwise falls back to `balance_sheet` / `income_statement`.

**Key internal helpers:**
- `_get_total_income(inc, suffix)` — sums positive income components (interest + fee + commission + dividend + rental + other + revenue/gross_profit); falls back to `_reconstruct_total_income()` when the safety guard fires (captured income < |net_income|) or no positive components found
- `_reconstruct_total_income(inc, suffix)` — derives income from `profit_before_tax + Σ|expenses|`; used for securities firms whose primary trading/commission income line is not captured by the parser
- `_get_operating_expenses(inc, suffix)` — maps both `general_and_admin_expenses` (standard IS) and `admin_expenses` (bank IS format) to ensure Finance companies using either sheet type compute cost-to-income correctly

---

### `ai_red_flags.py` — Groq AI Red Flags Engine

`compute_red_flags_ai(company_name, sector, company_ratios, company_beneish, forensic_criteria, forensic_score_display, dupont_vars, valuation_vars, price_records)` → `list[dict]`

Calls Groq `llama-3.3-70b-versatile` with a sector-aware prompt that includes all computed data. Returns structured `{flag, explanation, severity}` flags. Falls back to `_rule_based_fallback()` (same logic as `_compute_red_flags`) on any error or missing API key.

**Severity levels:** `"high"` (red) · `"medium"` (amber) · `"low"` (blue) · `"clear"` (green)

**Sector contexts injected into prompt:**
- **Standard** — Beneish/Piotroski/DSRI/TATA/Z-Score/DuPont drivers
- **Banking** — NPL, Coverage, LDR, NIM, Equity/Assets, Cost-to-Income; Beneish explicitly excluded
- **Finance/NBFI** — NPA, Provision Coverage, D/E acceleration, Interest Spread, OCF; Beneish excluded
- **Insurance** — Combined Ratio, Loss Ratio, Solvency, Reserve Coverage, investment-income dependency; Beneish excluded

**Data fed to Groq:** current + prior period ratios · forensic score + criteria · DuPont formula and all 3 factors (curr/prev) · sector-appropriate valuation multiples · 52-week price range + 3-month return

**API key:** reads `GROQ_API_KEY` from environment; auto-loads from `.env` at module import if not already set.

---

### `sector_forensics.py` — Sector-Specific Forensic Scoring

Replaces Piotroski F-Score + Beneish M-Score (designed for manufacturing) with rule-based criteria derived from sector-appropriate ratios and YoY trends. Piotroski/Beneish are **suppressed** (shown as N/A) for Banking, Insurance, and Finance companies.

Each function returns: `{score, max_score, criteria: [{label, pass (1/0/−1), explanation}], chart_data: [{metric, change, fill}]}`

#### `compute_bank_forensic(bank_result)` — 8 criteria

| # | Criterion | Pass condition |
|---|---|---|
| B1 | ROA Positive | ROA > 0 |
| B2 | ROA Improving YoY | ROA(curr) > ROA(prev) |
| B3 | NPL Ratio Decreasing | NPL(curr) < NPL(prev) |
| B4 | Coverage Ratio ≥ 1.0x | loan_loss_reserves / non_performing_loans ≥ 1.0 |
| B5 | Loan-to-Deposit ≤ 90% | LDR ≤ 0.90 |
| B6 | Cost-to-Income Improving | CTI(curr) < CTI(prev) |
| B7 | NIM Stable or Improving | NIM(curr) ≥ NIM(prev) |
| B8 | Equity-to-Assets Improving | E/A(curr) > E/A(prev) |

YoY chart tracks: ROA, NIM, NPL Ratio, Cost-to-Income, Equity/Assets

#### `compute_insurance_forensic(ins_result)` — 8 criteria

| # | Criterion | Pass condition |
|---|---|---|
| I1 | ROA Positive | ROA > 0 |
| I2 | ROA Improving YoY | ROA(curr) > ROA(prev) |
| I3 | Combined Ratio < 100% | combined_ratio < 1.0 |
| I4 | Combined Ratio Improving | CR(curr) < CR(prev) |
| I5 | Solvency Ratio ≥ 100% | solvency_ratio ≥ 1.0 |
| I6 | Reserve Coverage ≥ 1.0x | reserve_coverage ≥ 1.0 |
| I7 | Loss Ratio Improving | LR(curr) < LR(prev) |
| I8 | Operating Cash Flow Positive | OCF ratio > 0 |

YoY chart tracks: ROA, Combined Ratio, Loss Ratio, Solvency, Reserve Coverage

#### `compute_finance_forensic(fin_result)` — 8 criteria

| # | Criterion | Pass condition |
|---|---|---|
| F1 | ROA Positive | ROA > 0 |
| F2 | ROA Improving YoY | ROA(curr) > ROA(prev) |
| F3 | NIM Stable or Improving | NIM(curr) ≥ NIM(prev) |
| F4 | NPA Ratio Decreasing | NPA(curr) < NPA(prev) |
| F5 | Cost-to-Income Improving | CTI(curr) < CTI(prev) |
| F6 | Leverage Not Increasing | D/E(curr) ≤ D/E(prev) |
| F7 | Operating Cash Flow Positive | OCF ratio > 0 |
| F8 | Provision Coverage ≥ 1.0x | provision_coverage ≥ 1.0 |

YoY chart tracks: ROA, NIM, NPA Ratio, Cost-to-Income, D/E Ratio

---

### `valuation.py` — Valuation Metrics

`compute_valuation_metrics(fin_data, shares, last_close, reporting_unit_multiplier=1)` → dict

Requires shares outstanding + last close price. Any metric with missing inputs returns `None`. Returns a `sector` key that drives UI card selection; `fcf_yield` is multiplied by 100 in `state.py` before display.

**Subsector detection** (`_detect_sector`) maps each company to one of 6 types based on balance sheet and income statement keys:

| Subsector | Detection rule | Metrics shown |
|-----------|---------------|---------------|
| `standard` | no `bank_*` or `insurance_*` keys | EV/EBIT, FCF Yield, Free Cash Flow M₮, P/E, P/BV |
| `commercial_bank` | has `net_interest_income` + `total_deposits` | P/E, P/BV, P/TBV, P/PPOP, P/NII, Op. Cash Flow M₮ |
| `nbfi` | has `net_interest_income`, no `total_deposits` | P/E, P/BV, P/PPOP, P/NII, Op. Cash Flow M₮ |
| `holding` | no NII/LLP; `investment_securities / total_assets > 5%` | P/E, P/NAV, P/Inv Securities, Op. Cash Flow M₮ |
| `securities` | no NII/LLP; minimal investment securities | P/E, P/BV, P/Revenue, Op. Cash Flow M₮ |
| `insurance` | has `insurance_*` keys | P/E, P/BV, P/NPE, P/UWP, Op. Cash Flow M₮ |

**Metric definitions:**

| Key | Formula | Sector |
|-----|---------|--------|
| `ev_ebitda` | EV / EBIT (no D&A data available) | standard |
| `fcf` | (OCF + investing CF) scaled to M₮ | standard |
| `fcf_yield` | (OCF + investing CF) / MCap | standard |
| `ocf` | Operating Cash Flow scaled to M₮ | all sectors |
| `pe` | MCap / Net Income (positive only) | all |
| `pbv` | MCap / Equity (derived when parsed equity ≈ share capital only) | all |
| `ptbv` | MCap / (Equity − Intangibles) | commercial_bank |
| `p_ppop` | MCap / (Net Income + Loan Loss Provision) | commercial_bank, nbfi |
| `p_nii` | MCap / Net Interest Income | commercial_bank, nbfi |
| `p_inv_sec` | MCap / Investment Securities | holding |
| `p_revenue` | MCap / Total Revenue | securities |
| `p_npe` | MCap / Net Premiums Earned | insurance |
| `p_uwp` | MCap / Insurance Operating Profit | insurance |

**Why FCF vs OCF by sector:** FCF (OCF + investing CF) is meaningful for standard companies where investing CF is mostly capex. For banks, insurers, and NBFIs, investing CF is core business activity (loan deployment, securities portfolio); subtracting it produces a misleading number. Operating Cash Flow is shown instead — it captures cash from core operations without conflating business investment with capex.

**P/BV equity fallback:** if parsed `total_equity` < 1/5 of `total_assets − total_liabilities` (indicates parser captured only share capital), the derived value is used instead.

**Unit scaling:** MSE financial statements are typically denominated in thousands of MNT (мянган төгрөг), but market cap uses raw MNT (shares × price). `reporting_unit_multiplier` bridges this gap — all financial inputs are multiplied by this factor before any ratio is computed. Value is sourced from `metadata.reporting_unit_multiplier` in the parsed JSON (set by the parser); legacy files without the field fall back to a MCap/Assets heuristic in `state.py`.

---

### `portfolio_optimization.py` — Portfolio Analytics

| Function | Purpose |
|---|---|
| `load_price_returns(companies)` | Reads price JSONs → daily log returns per company |
| `align_returns(returns_map)` | Aligns all series to common date range |
| `compute_portfolio_returns(weights, matrix)` | Portfolio-level daily return series |
| `compute_risk_metrics(port_returns)` | Sortino, max drawdown, CVaR 95% |
| `mean_variance_optimize(matrix, names)` | SciPy minimize → max Sharpe weights (risk-free rate = 12% p.a.) |
| `sample_frontier(matrix, n=200)` | Efficient frontier scatter data |
| `compute_sector_breakdown(holdings)` | Sector weights for donut chart |
| `rebalance_weights(holdings, company, pct)` | Proportional rebalance after manual edit |

---

### `labels.py`

Provides label/color classification thresholds for composite scores (Green/Amber/Red bands).

---

## `components/`

| File | Purpose |
|---|---|
| `layout.py` | `page_layout(content)` — dark sidebar shell wrapping all pages |
| `sidebar.py` | Nav links: Home / Screener / Portfolio |
| `upload_zone.py` | `rx.upload` drag-drop zone + `selected_files_list()` |
| `file_list.py` | Table of uploaded files with delete buttons; reads `UploadState.uploaded_files` |

---

## `pages/`

| File | Route | Structure |
|---|---|---|
| `company.py` | `/company/[company]` | 5-tab layout: Ratios · Forensic · Valuation · DuPont · Red Flags. **Overview tab** shows `health_gauge()` (radial bar, `width="100%"`, `height=260`) + `radar_chart_panel()` (`width="100%"`, `height=320`, `outer_radius="65%"`, centred `cx/cy`) in a 2-column grid, then a **Key Metrics card** (9 rows: ROE, ROA, Net Margin, Gross Margin, Operating Margin, Debt/Equity, Current Ratio, Quick Ratio, Altman Z-Score; labels `text-sm`, values `text-lg font-mono`) alongside a **Risk Signals card**. **Red Flags tab** shows rule-based flags instantly, then replaces with Groq AI flags (spinner shown during AI call). Each flag rendered with severity badge (HIGH/MEDIUM/LOW/CLEAR) and matching border/icon color. Footer: "Powered by Groq AI". Sector-conditional ratio rendering: `ratios_tab_content()` branches on `company_is_bank` → `company_is_insurance` → `company_is_finance` → standard. **Forensic tab** shows Piotroski + Beneish for standard companies; shows `_sector_forensic_panel()` (criteria checklist + YoY bar chart) for Banking/Insurance/Finance. Hero card label switches from "Piotroski F-Score" → "Sector Forensic Score" for financial-sector companies. **Finance Asset Quality card** shows all 3 ratios: NPA Ratio, Receivables-to-Assets, Provision Coverage. **Valuation tab** renders one of 6 card grids based on `company_valuation_sector`: standard (5 cards: EV/EBIT · FCF Yield · Free Cash Flow M₮ · P/E · P/BV), commercial_bank (6 cards +Op. Cash Flow M₮), nbfi/holding/securities/insurance (4-5 cards each +Op. Cash Flow M₮). |
| `screener.py` | `/screener` | Sortable/filterable company table. Each row: health badge, ROE, sector; links to company page; "Add to Portfolio" button. Expandable **Methodology & Validation** panel documents scoring weights per sector (standard/CAMELS/IRIS/NBFI), universal adjustments (Beneish −10pt penalty, missing-data weight redistribution), and known limitations (Piotroski/Altman not applied to financial sectors, DEPI gap, thin dataset). |
| `portfolio.py` | `/portfolio` | 2-tab: Holdings (weight sliders, remove) + Analysis (frontier chart, optimization table, risk metrics, sector donut). **Analysis row 1** uses `grid(columns=2)`: sector donut pie chart (`width="100%"`, `height=300`) fills its column; Sortino Ratio and Max Drawdown risk cards use `flex-1` to fill the full column height. |

---

## `data/`

| File/Dir | Shape |
|---|---|
| `index.json` | `{"files": [{filename, company, year, sector, sheets_parsed, parsed_at}]}` |
| `company_registry.json` | `[{name, mse_id, tier, sector, sub_sector?, aliases?, english?}]` — 68 companies; all Finance entries have `sub_sector` ("Securities", "ББСБ (Lending NBFI)", "Investment/Holding") |
| `prices/{company}.json` | `{company, mse_id, scraped_at, shares_outstanding?, records:[{date,open,high,low,close,volume}]}` |
| `{Company}_{year}.json` | Full parsed dict with metadata wrapper from manual upload |

---

## Data Flow

```
User uploads .xls/.xlsx
        ↓
   excel_parser.py  ←── header_mappings.py (7 Mongolian→English dicts)
   (extracts rows)       registry_loader.py (sector detection)
        ↓
   json_store.py → data/{Company}_{year}.json
                 → data/index.json (manifest)
        ↓
   state.py (AnalysisState.load_company)
        ↓
   ratios.py            ← Standard sector
   bank_ratios.py       ← Banking sector
   insurance_ratios.py  ← Insurance sector
   finance_ratios.py    ← Finance / NBFI sector
   sector_forensics.py  ← Forensic scoring for Banking/Insurance/Finance
   valuation.py   ←── data/prices/{company}.json
   ai_red_flags.py ←── Groq API (llama-3.3-70b-versatile)
   portfolio_optimization.py
        ↓
   pages/company.py / screener.py / portfolio.py  (Reflex UI)

   Price refresh (separate):
   state.refresh_prices()
        ↓
   registry_loader.find_mse_id()
        ↓
   price_scraper.scrape_company_prices()  ← old.mse.mn
        ↓
   data/prices/{company}.json
```
