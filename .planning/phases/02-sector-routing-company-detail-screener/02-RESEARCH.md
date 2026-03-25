# Phase 2: Sector Routing, Company Detail & Screener - Research

**Researched:** 2026-03-25
**Domain:** Reflex 0.8.26 UI — rx.tabs, rx.recharts charts (RadialBarChart, RadarChart, BarChart), state extension for sector routing and full ratio display, screener filter/sort
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Sector is auto-detected from parsed data structure — no user input required. Logic: if parsed JSON has `bank_balance_sheet` or `bank_income_statement` keys → Banking; if it has insurance-specific keys → Insurance; otherwise → Standard. This works for all MSE companies, not just the 7 demo companies.
- **D-02:** For the 7 demo companies, `sector` field is added manually to `index.json` entries (already decided in PROJECT.md). For newly uploaded companies, sector is written to index.json at parse time using the auto-detection logic from D-01.
- **D-03:** Use Reflex's built-in `rx.tabs.root` + `rx.tabs.list` + `rx.tabs.content` for the 5-tab layout: **Ratios | Forensic | Valuation | DuPont | Red Flags**. Styled with `class_name` to match the dark OLED theme (`bg-slate-900`, `border-slate-800`). No custom tab state var needed.
- **D-04:** The Valuation tab exists in Phase 2 as a placeholder (empty panel or "Price data coming in Phase 3" message). Phase 3 populates it.
- **D-05:** Semicircle arc using `rx.recharts.radial_bar_chart` (or equivalent Recharts primitive). Three color zones: red (0–40), amber (40–70), green (70–100). Score number and label (Healthy/Caution/Distress) rendered in the center below the arc.
- **D-06:** Sector appears as both a **visible table column** and a **filter dropdown**. The sector column is also sortable (per SCREEN-02). Column order: Company | Year | Sector | Health Score | F-Score | ROE | Add.
- **D-07:** Sector filter dropdown values: All / Banking / Insurance / Manufacturing / Food / Textiles / Holding (as specified in SCREEN-01). When "All" is selected, all companies are shown.

### Claude's Discretion

- Beneish bar chart rendering details (bar colors, axis labels, threshold line style) — Claude decides using rx.recharts
- Radar chart normalization — use the 6 category subscores already computed by `compute_composite_score()` (already 0–100 scaled)
- Red Flags display style — Claude decides (warning list with icons + plain-language explanations per COMP-04)
- DuPont tab layout — follow COMP-03 spec: ROE = Net Profit Margin × Asset Turnover × Equity Multiplier, current and prior year side-by-side
- Rate at which `all_companies` state var is extended to include sector field
- Whether to use `selected_tab` state var fallback if `rx.tabs` has any Reflex 0.8.26 limitations

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SECTOR-01 | Add `sector` field to each entry in `index.json` | index.json structure confirmed; 7 entries, none have `sector` yet; field already read in `_load_all_companies()` (line 195 of state.py) — just not written |
| SECTOR-02 | Route Khan Bank to `bank_ratios.py` — NIM, NPL, CAR, LDR, Cost-to-Income | `compute_bank_ratios()` is complete and tested internally; detection key is `bank_balance_sheet` or `bank_income_statement` in parsed JSON |
| SECTOR-03 | Route Мандал даатгал to `insurance_ratios.py` — Loss Ratio, Combined Ratio, Solvency | `compute_insurance_ratios()` is complete; detection key is `insurance_balance_sheet` or `insurance_income_statement` |
| COMP-01 | Display all 26+ ratios organized by category | All ratios already computed by `compute_ratios()`; labels in `RATIO_LABELS` dict; currently only 9 are shown in company.py — need full 6-category layout |
| COMP-02 | 5-tab navigation: Ratios / Forensic / Valuation / DuPont / Red Flags | `rx.tabs.root` + `rx.tabs.list` + `rx.tabs.trigger` + `rx.tabs.content` confirmed available in Reflex 0.8.26 |
| COMP-03 | DuPont tab: ROE = Net Margin × Asset Turnover × Equity Multiplier, current + prior year | All three components are already computed: `net_margin` (profitability), `total_asset_turnover` (activity), `debt_to_equity` → equity multiplier derivable as `total_assets / total_equity` |
| COMP-04 | Red Flags tab: 5+ patterns with plain-language explanations | Patterns are computable from existing ratio data; no new computation engine needed |
| COMP-05 | Health score gauge (semicircle arc, 0–100, color zones) | `rx.recharts.radial_bar_chart` confirmed available; data must be a `list[dict]` state var |
| COMP-06 | Radar chart with 6 category axes | `rx.recharts.radar_chart` + `rx.recharts.radar` confirmed available; `compute_composite_score()` already returns `breakdown` dict with 6 category subscores |
| COMP-07 | Beneish M-Score horizontal bar chart with threshold line | `rx.recharts.bar_chart` with `layout="vertical"` + `rx.recharts.reference_line` confirmed available |
| SCREEN-01 | Sector filter dropdown | `screener_filter` state var already exists; `filtered_companies` computed var already implemented; dropdown UI is the only new piece |
| SCREEN-02 | Column sort (Health Score, F-Score, ROE, sector) | Requires new `screener_sort_col` + `screener_sort_asc` state vars and updated `filtered_companies` computed var |

</phase_requirements>

---

## Summary

Phase 2 wires three pre-built ratio engines into the company page, expands the company detail page from 9 ratios to 26+ with 5-tab navigation and 3 Recharts visualizations, and upgrades the screener with sector filtering and column sort. All the heavy computation is already done — this phase is primarily UI wiring and state extension.

The biggest risk is not logic but **Reflex state var constraints**: charts require `list[dict[str, Any]]` typed state vars (not Python dicts), `rx.recharts.radial_bar_chart` for the health gauge requires a specific data shape, and computed vars like `filtered_companies` must return `list[dict]` (type annotation matters for Reflex's codegen). The sector routing in `load_company()` requires detecting which ratio engine to call based on the parsed JSON structure, then populating a materially different set of flat display vars.

**Primary recommendation:** Structure the implementation in four clean waves — (1) data layer: index.json sector field + sector detection in state, (2) company page tabs + full ratios, (3) three chart components, (4) screener filter/sort — each independently testable.

---

## Standard Stack

### Core (all already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| reflex | 0.8.26 | Framework, state, components | Locked — cannot change |
| rx.recharts | bundled with reflex 0.8.26 | Charts (RadialBarChart, RadarChart, BarChart) | Only chart lib available per project constraint |
| Python | 3.12 | Runtime | Locked |

### No New Packages Required

All packages for this phase are already installed. The ratio engines, labels, and UI framework are in place. No `pip install` steps needed.

---

## Architecture Patterns

### Recommended Project Structure Changes

```
financial_dashboard/
├── analysis/
│   ├── ratios.py           (unchanged)
│   ├── bank_ratios.py      (unchanged — wire in state.py)
│   ├── insurance_ratios.py (unchanged — wire in state.py)
│   └── labels.py           (unchanged)
├── pages/
│   ├── company.py          (REPLACE — 5-tab layout, sector-aware display)
│   └── screener.py         (EXTEND — sector column, filter dropdown, sort headers)
├── state.py                (EXTEND — sector detection, 40+ new flat vars, sort state)
data/
└── index.json              (PATCH — add sector field to 7 entries)
```

### Pattern 1: Sector Detection in `load_company()`

**What:** When loading a company, inspect the raw parsed JSON keys to determine which ratio engine to call. Set a `company_sector` state var. Route to `compute_bank_ratios()`, `compute_insurance_ratios()`, or `compute_ratios()` accordingly.

**When to use:** In `load_company()` (and `_load_all_companies()` for the screener).

**Example:**
```python
# In load_company(), after loading the data dict:
def _detect_sector(data: dict) -> str:
    if "bank_balance_sheet" in data or "bank_income_statement" in data:
        return "Banking"
    if "insurance_balance_sheet" in data or "insurance_income_statement" in data:
        return "Insurance"
    return "Standard"
```

Note: `_load_all_companies()` in state.py already reads `entry.get("sector", "")` from index.json (line 195) so the screener sector column will populate automatically once index.json is patched. No changes to `_load_all_companies()` are needed for SCREEN-01.

### Pattern 2: Flat Display Vars for Sector-Specific Ratios

**What:** Reflex requires flat typed state vars — no nested dicts in components. All sector-specific ratio values must be stored as `str` state vars (pre-formatted for display) just like the existing 9 ratio vars.

**Bank ratios to add as flat vars (19 ratios, 5 categories):**
```
# Profitability
company_bank_nim, company_bank_roa, company_bank_roe,
company_bank_net_margin, company_bank_interest_income_ratio
# Capital Adequacy
company_bank_car, company_bank_tier1_ratio,
company_bank_equity_multiplier, company_bank_equity_to_assets
# Asset Quality
company_bank_npl_ratio, company_bank_coverage_ratio,
company_bank_loan_loss_reserve_ratio, company_bank_provision_to_loans
# Liquidity
company_bank_ldr, company_bank_cash_to_deposits,
company_bank_loans_to_assets, company_bank_securities_to_assets
# Efficiency
company_bank_cost_to_income, company_bank_fee_income_ratio
```

**Insurance ratios to add as flat vars (15 ratios):**
```
# Underwriting
company_ins_loss_ratio, company_ins_expense_ratio, company_ins_combined_ratio
# Profitability
company_ins_roa, company_ins_roe, company_ins_net_margin,
company_ins_investment_income_ratio, company_ins_underwriting_margin
# Solvency
company_ins_solvency_ratio, company_ins_leverage_ratio,
company_ins_equity_to_liabilities, company_ins_reserve_coverage
# Liquidity
company_ins_ocf_ratio, company_ins_investment_ratio, company_ins_cash_to_liabilities
```

**Standard ratios to add (currently showing 9, need all 26):**
All keys in `RATIO_LABELS` that aren't yet flat vars must be added.

### Pattern 3: 5-Tab Layout with rx.tabs

**What:** `rx.tabs.root` wraps everything. `rx.tabs.list` contains `rx.tabs.trigger` items. `rx.tabs.content` renders each panel. No custom state var needed — Radix tabs manages active tab internally.

**Example:**
```python
# Source: Reflex 0.8.26 tabs component (verified in venv source)
rx.tabs.root(
    rx.tabs.list(
        rx.tabs.trigger("Ratios",    value="ratios"),
        rx.tabs.trigger("Forensic",  value="forensic"),
        rx.tabs.trigger("Valuation", value="valuation"),
        rx.tabs.trigger("DuPont",    value="dupont"),
        rx.tabs.trigger("Red Flags", value="redflags"),
        class_name="border-b border-slate-800",
    ),
    rx.tabs.content(ratios_tab_content(), value="ratios"),
    rx.tabs.content(forensic_tab_content(), value="forensic"),
    rx.tabs.content(valuation_placeholder(), value="valuation"),
    rx.tabs.content(dupont_tab_content(), value="dupont"),
    rx.tabs.content(red_flags_tab_content(), value="redflags"),
    default_value="ratios",
    width="100%",
)
```

The `on_change` event is available if a `selected_tab` fallback var is needed (D-03 discretion), but the Radix-internal state approach is simpler.

### Pattern 4: Health Gauge (RadialBarChart)

**What:** `rx.recharts.radial_bar_chart` renders a semicircle arc. Data must be a `list[dict[str, Any]]` state var — not computed inline in the component.

**State var needed:**
```python
company_gauge_data: list[dict] = []
# Populated in load_company() as:
# [{"name": "score", "value": score, "fill": "#22c55e"}]  # green/amber/red based on score
```

**Component pattern:**
```python
rx.recharts.radial_bar_chart(
    rx.recharts.radial_bar(
        data_key="value",
        min_angle=15,
        background=True,
    ),
    data=AnalysisState.company_gauge_data,
    start_angle=180,
    end_angle=0,
    inner_radius="60%",
    outer_radius="90%",
    width=280,
    height=160,
)
```

### Pattern 5: Radar Chart (RadarChart)

**What:** `rx.recharts.radar_chart` with `rx.recharts.radar` and `rx.recharts.polar_angle_axis`. Data must be a `list[dict[str, Any]]` state var.

**State var needed:**
```python
company_radar_data: list[dict] = []
# Populated in load_company() from composite["breakdown"]:
# [
#   {"category": "Profitability", "score": 72},
#   {"category": "Liquidity",     "score": 55},
#   {"category": "Solvency",      "score": 60},
#   {"category": "Activity",      "score": 40},
#   {"category": "Altman Z",      "score": 80},
#   {"category": "Piotroski",     "score": 66},
# ]
```

**Component pattern:**
```python
rx.recharts.radar_chart(
    rx.recharts.polar_grid(),
    rx.recharts.polar_angle_axis(data_key="category"),
    rx.recharts.radar(
        data_key="score",
        name="Health",
        fill="#22c55e",
        fill_opacity=0.3,
        stroke="#22c55e",
    ),
    data=AnalysisState.company_radar_data,
    width=300,
    height=300,
)
```

### Pattern 6: Beneish Bar Chart (BarChart, vertical)

**What:** Horizontal bar chart of the 7 Beneish indices with a reference line at the manipulation threshold. `layout="vertical"` turns BarChart sideways. `rx.recharts.reference_line` draws the threshold.

**State var needed:**
```python
company_beneish_chart_data: list[dict] = []
# [{"index": "DSRI", "value": 1.12, "fill": "#f59e0b"}, ...]
```

**Component pattern:**
```python
rx.recharts.bar_chart(
    rx.recharts.x_axis(type_="number"),
    rx.recharts.y_axis(data_key="index", type_="category"),
    rx.recharts.bar(data_key="value", fill="#60a5fa"),
    rx.recharts.reference_line(x=1.0, stroke="#ef4444", stroke_dasharray="4 4"),
    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
    data=AnalysisState.company_beneish_chart_data,
    layout="vertical",
    width="100%",
    height=240,
)
```

### Pattern 7: Screener Sort

**What:** Add `screener_sort_col: str` and `screener_sort_asc: bool` state vars. Update the `filtered_companies` computed var to apply sorting after filtering. Column headers become `rx.button` or `rx.text` with `on_click` handlers.

**State vars to add:**
```python
screener_sort_col: str = "score"   # default sort by health score
screener_sort_asc: bool = False    # default descending (best first)
```

**Updated `filtered_companies` computed var:**
```python
@rx.var
def filtered_companies(self) -> list[dict]:
    companies = self.all_companies if self.screener_filter == "All" \
        else [c for c in self.all_companies if c.get("sector") == self.screener_filter]
    col = self.screener_sort_col
    reverse = not self.screener_sort_asc
    try:
        return sorted(companies, key=lambda c: (c.get(col) or 0), reverse=reverse)
    except Exception:
        return companies
```

Note: `score` is already an `int` in the dict. `f_score_str` is a string like "6 / 8" — sort should use the raw `f_score` int from load, not the display string. Planner needs to ensure `f_score` (raw int) is included in the `all_companies` dict entries alongside `f_score_str`.

### Anti-Patterns to Avoid

- **Inline dict construction in components:** Never build `[{"value": score}]` inside a component function. It causes Reflex codegen errors. Always use a state var.
- **Using `rx.color()` for chart fills:** Pass hex color strings `"#22c55e"` directly to `fill` props. `rx.color()` is Tailwind-integrated and does not work in Recharts props in Reflex 0.8.26.
- **Python if/else in component bodies:** Use `rx.cond()` for all conditional rendering.
- **Accessing nested dict keys in components:** `company["scores"]["profitability"]` is invalid. Pre-flatten all values to state vars.
- **Using `all_companies` directly in screener foreach:** The screener must iterate `filtered_companies` (the computed var), not `all_companies` directly, so filtering and sorting work.
- **Tab content with heavy data loaded on every render:** Each tab content function should reference state vars already populated in `load_company()`. Do not trigger additional event handlers on tab switch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tab navigation with active state | Custom tab component with `selected_tab` var + conditional borders | `rx.tabs.root/list/trigger/content` | Radix tabs handles ARIA, keyboard nav, and active state internally |
| Horizontal bar chart | Custom SVG bars | `rx.recharts.bar_chart` with `layout="vertical"` | Edge cases in SVG scaling; Recharts handles responsive sizing |
| Radar chart polygon | Custom SVG polygon | `rx.recharts.radar_chart` + `rx.recharts.radar` | Axis scaling, label positioning, and responsive sizing are non-trivial |
| Semicircle gauge | Custom SVG arc with `d` path calculation | `rx.recharts.radial_bar_chart` with `start_angle=180, end_angle=0` | Arc math for responsive SVG is error-prone |
| Reference line on chart | `rx.box` overlay | `rx.recharts.reference_line` | Recharts reference_line aligns to data coordinates; overlay requires pixel math |
| Sort implementation | Custom sort state machine | Python `sorted()` in computed var | Recharts/Reflex has no built-in table sort; Python sort is sufficient and testable |
| Red flags detection | ML model | Rule-based comparisons on existing ratio vars | Current/prior year data is sufficient; patterns are threshold checks |

**Key insight:** This phase has zero new computation logic. Every engine is built. The work is entirely state var population and UI composition.

---

## Common Pitfalls

### Pitfall 1: Recharts Data Must Be a State Var, Not Inline Python

**What goes wrong:** Writing `data=[{"value": s.company_score}]` inside a component function raises a Reflex compilation error or silently renders empty.
**Why it happens:** Recharts data prop is serialized at compile time; Python list literals with Var references are not valid.
**How to avoid:** Always create a `list[dict]` state var (e.g., `company_gauge_data`), populate it in `load_company()`, and pass the state var to the `data` prop: `data=AnalysisState.company_gauge_data`.
**Warning signs:** Chart renders with no bars/lines but no Python error. Check if data prop is a state var.

### Pitfall 2: `filtered_companies` Type Annotation Required

**What goes wrong:** If `filtered_companies` computed var lacks a `-> list[dict]` return annotation, Reflex may infer the wrong type and `rx.foreach` over it fails silently.
**Why it happens:** Reflex 0.8.26 uses type annotations to generate the correct TypeScript type for SSE-synced state.
**How to avoid:** Always annotate computed vars: `def filtered_companies(self) -> list[dict]:`.
**Warning signs:** Screener table renders blank after adding filtering/sorting.

### Pitfall 3: Screener `company_row` Must Handle New `sector` Column

**What goes wrong:** The existing `company_row()` function does not render the sector column. Adding it to the table header but not the row body causes misaligned columns.
**Why it happens:** `rx.table.row` cells are positional — header and body must have the same count.
**How to avoid:** Update `company_row()` to add `rx.table.cell(company["sector"], ...)` at position 3 (after Year, before Health Score).
**Warning signs:** Columns shift sideways visually; sector header appears above ROE column value.

### Pitfall 4: Bank/Insurance Pages Must Not Show Standard Ratio Vars

**What goes wrong:** If `load_company()` calls `compute_ratios()` on a bank JSON, many ratios compute as N/A or nonsensical values (e.g., "inventory turnover" for a bank).
**Why it happens:** `compute_ratios()` uses `balance_sheet` key, banks use `bank_balance_sheet`.
**How to avoid:** Sector detection must happen before ratio computation. Only call the correct engine. Set `company_is_bank: bool`, `company_is_insurance: bool` state vars to control which tab content renders.
**Warning signs:** Bank company shows 9 N/A ratios instead of NIM/CAR/LDR.

### Pitfall 5: `rx.tabs` Default Value Must Match a `value` Prop

**What goes wrong:** If `default_value="ratios"` and no `rx.tabs.trigger` has `value="ratios"`, the first tab is blank.
**Why it happens:** Radix Tabs matches string values exactly.
**How to avoid:** Ensure `default_value` string matches exactly one `rx.tabs.trigger` value prop.

### Pitfall 6: Sort on String Display Values Gives Wrong Order

**What goes wrong:** Sorting `f_score_str` ("6 / 8") alphabetically places "7 / 8" before "6 / 8" correctly but "9 / 9" before "10 / 9" incorrectly (doesn't happen here since max is 9, but "N/A" sorts before numbers alphabetically).
**Why it happens:** Python string sort is lexicographic.
**How to avoid:** Store raw `f_score` (int) and `roe` (float) in the `all_companies` dict alongside the display strings. Sort computed var uses the raw numeric fields, not the display strings.

### Pitfall 7: DuPont Equity Multiplier Derivation

**What goes wrong:** `compute_ratios()` does not return `equity_multiplier` directly — it returns `debt_to_equity`. Equity Multiplier = Total Assets / Total Equity = 1 + Debt/Equity.
**Why it happens:** The bank engine has `equity_multiplier` but the standard engine uses `debt_to_equity`.
**How to avoid:** In `load_company()`, derive `equity_multiplier = 1 + debt_to_equity` when sector is Standard, or read it directly from bank ratios if Banking. Store as `company_equity_multiplier: str`.

---

## Code Examples

### Sector Detection (Pure Python — testable without Reflex)

```python
# Source: analysis of bank_ratios.py + insurance_ratios.py key structure (verified by reading source)
def _detect_sector_from_data(data: dict) -> str:
    """Detect sector from parsed JSON structure."""
    if "bank_balance_sheet" in data or "bank_income_statement" in data:
        return "Banking"
    if "insurance_balance_sheet" in data or "insurance_income_statement" in data:
        return "Insurance"
    return "Standard"
```

### index.json Sector Patch (7 companies confirmed from data/index.json)

```json
// Confirmed company names and their sectors:
// "Хаан банк"           → "Banking"
// "Мандал даатгал"      → "Insurance"
// "АПУ"                 → "Manufacturing"
// "Сүү"                 → "Food"   (dairy — maps to Food per D-07 values)
// "Моносхүнс"           → "Food"
// "Дархан нэхий ХК"     → "Textiles"
// "\" Премиум Нэксус \" ХК" → "Holding"
```

Note: Сүү (dairy) maps to "Food" — the SCREEN-01 spec lists Food not Dairy. Confirm with project intent but Food is the closest match in the D-07 dropdown list.

### Radar Chart State Var Population

```python
# Source: compute_composite_score() returns breakdown dict (verified in ratios.py lines 682-690)
breakdown = self.company_composite.get("breakdown", {})
self.company_radar_data = [
    {"category": "Profitability", "score": breakdown.get("profitability") or 0},
    {"category": "Liquidity",     "score": breakdown.get("liquidity") or 0},
    {"category": "Solvency",      "score": breakdown.get("solvency") or 0},
    {"category": "Activity",      "score": breakdown.get("activity") or 0},
    {"category": "Altman Z",      "score": breakdown.get("altman") or 0},
    {"category": "Piotroski",     "score": breakdown.get("piotroski") or 0},
]
```

### Beneish Chart State Var Population

```python
# Source: compute_beneish() returns indices dict (verified in ratios.py lines 455-527)
idx = self.company_beneish.get("indices", {})
# Color each bar: red if value > 1.0 (manipulation signal), blue otherwise
self.company_beneish_chart_data = [
    {"index": k.upper(), "value": round(v, 3) if v is not None else 0,
     "fill": "#ef4444" if (v is not None and v > 1.0) else "#60a5fa"}
    for k, v in idx.items() if k != "depi"  # depi is always None
]
```

### Health Gauge State Var Population

```python
# Determine fill color from score zone (D-05)
score = self.company_score
fill = "#22c55e" if score >= 70 else ("#f59e0b" if score >= 40 else "#ef4444")
self.company_gauge_data = [{"name": "score", "value": score, "fill": fill}]
```

### Sort Handler in AnalysisState

```python
@rx.event
def sort_screener(self, col: str):
    """Toggle sort direction if same column, else set new column ascending."""
    if self.screener_sort_col == col:
        self.screener_sort_asc = not self.screener_sort_asc
    else:
        self.screener_sort_col = col
        self.screener_sort_asc = True
```

### Red Flags Logic (Rule-Based)

```python
# Source: COMP-04 spec — 5 required patterns
def _compute_red_flags(ratios: dict, beneish: dict) -> list[dict[str, str]]:
    """Detect 5+ accounting red flag patterns. Returns list of {flag, explanation}."""
    flags = []
    curr = ratios.get("current", {})
    prev = ratios.get("prev", {})

    # 1. Receivables growing faster than revenue (DSRI > 1.1)
    dsri = beneish.get("indices", {}).get("dsri")
    if dsri is not None and dsri > 1.1:
        flags.append({
            "flag": "Receivables Outpacing Revenue",
            "explanation": f"DSRI = {dsri:.2f}. Receivables grew faster than sales — possible revenue front-loading or collection issues."
        })

    # 2. FCF diverging from net income (TATA > 0.05)
    tata = beneish.get("indices", {}).get("tata")
    if tata is not None and tata > 0.05:
        flags.append({
            "flag": "Earnings Quality Warning",
            "explanation": f"TATA = {tata:.2f}. Net income exceeds cash earnings — accruals are high relative to assets."
        })

    # 3. Sudden leverage spike
    d2e_curr = curr.get("solvency", {}).get("debt_to_equity")
    d2e_prev = prev.get("solvency", {}).get("debt_to_equity")
    if d2e_curr and d2e_prev and d2e_curr > d2e_prev * 1.25:
        flags.append({
            "flag": "Leverage Spike",
            "explanation": f"Debt/Equity rose from {d2e_prev:.2f}x to {d2e_curr:.2f}x — a 25%+ increase in one year."
        })

    # 4. M-Score above threshold
    m = beneish.get("m_score")
    if m is not None and beneish.get("reliable") and m > -1.78:
        flags.append({
            "flag": "Beneish Manipulation Signal",
            "explanation": f"M-Score = {m:.2f} (threshold -1.78). Accounting patterns resemble manipulated earnings."
        })

    # 5. Current ratio deterioration
    cr_curr = curr.get("liquidity", {}).get("current_ratio")
    cr_prev = prev.get("liquidity", {}).get("current_ratio")
    if cr_curr and cr_prev and cr_curr < 1.0 and cr_prev >= 1.0:
        flags.append({
            "flag": "Liquidity Deterioration",
            "explanation": f"Current Ratio dropped below 1.0 (now {cr_curr:.2f}x). Company may struggle to meet short-term obligations."
        })

    return flags if flags else [{"flag": "No Major Red Flags", "explanation": "No significant accounting anomalies detected."}]
```

---

## State Changes Summary

All new state vars to add to `AnalysisState`:

```python
# Sector identity
company_sector: str = ""
company_is_bank: bool = False
company_is_insurance: bool = False

# Chart data vars (must be list[dict] for Recharts)
company_gauge_data: list[dict] = []
company_radar_data: list[dict] = []
company_beneish_chart_data: list[dict] = []

# DuPont vars
company_net_margin_curr: str = ""
company_net_margin_prev: str = ""
company_asset_turnover_curr: str = ""
company_asset_turnover_prev: str = ""
company_equity_multiplier_curr: str = ""
company_equity_multiplier_prev: str = ""
company_roe_curr: str = ""   # redundant with company_roe but explicit for DuPont
company_roe_prev: str = ""

# Red flags
company_red_flags: list[dict] = []

# Standard ratios not yet shown (additional 17 beyond current 9)
company_gross_margin: str = ""
company_operating_margin: str = ""
company_ebit_margin: str = ""
company_cash_ratio: str = ""
company_working_capital: str = ""
company_debt_to_assets: str = ""
company_equity_ratio: str = ""
company_ocf_ratio: str = ""
company_cf_to_debt: str = ""
company_reinvestment_ratio: str = ""
company_fixed_asset_turnover: str = ""
company_inventory_turnover: str = ""
company_days_inventory: str = ""
company_receivables_turnover: str = ""
company_days_sales_outstanding: str = ""
company_payables_turnover: str = ""
company_days_payable_outstanding: str = ""
company_cash_conversion_cycle: str = ""
company_z_x1: str = ""
company_z_x2: str = ""
company_z_x3: str = ""
company_z_x4: str = ""
company_z_x5: str = ""

# Bank ratio flat vars (19)
company_bank_nim: str = ""
company_bank_car: str = ""
company_bank_npl_ratio: str = ""
company_bank_ldr: str = ""
company_bank_cost_to_income: str = ""
company_bank_roa: str = ""
company_bank_roe: str = ""
company_bank_net_margin: str = ""
company_bank_interest_income_ratio: str = ""
company_bank_tier1_ratio: str = ""
company_bank_equity_multiplier: str = ""
company_bank_equity_to_assets: str = ""
company_bank_coverage_ratio: str = ""
company_bank_loan_loss_reserve_ratio: str = ""
company_bank_provision_to_loans: str = ""
company_bank_cash_to_deposits: str = ""
company_bank_loans_to_assets: str = ""
company_bank_securities_to_assets: str = ""
company_bank_fee_income_ratio: str = ""

# Insurance ratio flat vars (15)
company_ins_loss_ratio: str = ""
company_ins_expense_ratio: str = ""
company_ins_combined_ratio: str = ""
company_ins_roa: str = ""
company_ins_roe: str = ""
company_ins_net_margin: str = ""
company_ins_investment_income_ratio: str = ""
company_ins_underwriting_margin: str = ""
company_ins_solvency_ratio: str = ""
company_ins_leverage_ratio: str = ""
company_ins_equity_to_liabilities: str = ""
company_ins_reserve_coverage: str = ""
company_ins_ocf_ratio: str = ""
company_ins_investment_ratio: str = ""
company_ins_cash_to_liabilities: str = ""

# Screener sort state
screener_sort_col: str = "score"
screener_sort_asc: bool = False
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline data in Recharts components | State var `list[dict]` fed to `data=` prop | Reflex 0.6+ | Breaking if not followed |
| `rx.color()` for chart colors | Hex strings in `fill=` props | Tailwind v4 migration | `rx.color()` does not resolve in Recharts props |
| Tabs via custom Python state var + `rx.cond()` | `rx.tabs.root/list/trigger/content` | Reflex 0.7+ | Radix Tabs is simpler and handles accessibility |

---

## Open Questions

1. **Сүү sector classification**
   - What we know: Сүү means "milk" — it is a dairy company. SCREEN-01 dropdown lists "Food" but not "Dairy".
   - What's unclear: Whether "Food" covers dairy or if a separate "Dairy" sector is needed.
   - Recommendation: Use "Food" for Сүү and Моносхүнс. This matches the D-07 dropdown values which do not include "Dairy".

2. **f_score sort field in all_companies**
   - What we know: `_load_all_companies()` already stores `f_score_str` ("6 / 8") but not the raw int `f_score`.
   - What's unclear: Whether sorting by F-Score in SCREEN-02 requires a raw numeric field.
   - Recommendation: Add `f_score` (int) and `roe` (float, not just `roe_str`) to the dict returned by `_load_all_companies()`. This requires a minor update to that function.

3. **Bank company on screener — which composite score?**
   - What we know: `_load_all_companies()` always calls `compute_ratios()` (standard). For Хаан банк, `compute_ratios()` will return mostly N/A because it uses `balance_sheet` not `bank_balance_sheet`.
   - What's unclear: Should the screener health score for banks use `compute_bank_ratios()` + a bank-specific composite, or fall back to whatever `compute_ratios()` produces?
   - Recommendation: For Phase 2 scope, update `_load_all_companies()` to call `compute_bank_ratios()` when sector is Banking, and use a simpler score (average of non-None bank ratios normalized 0–100). Alternatively, fall back to N/A display and note it. The simplest path: call the correct engine for the screener row, and display the composite score computed from whatever engine ran. The planner should decide the fallback score formula for banks in the screener.

---

## Environment Availability

Step 2.6: All dependencies are pure Python libraries already installed in the project venv. No external services, databases, or CLI tools beyond what Phase 1 installed.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| reflex | All UI components | Yes (in venv) | 0.8.26 | — |
| pytest | Test suite | Yes | 9.0.2 | — |
| Python 3.12 | Runtime | Yes | 3.12 | — |

No missing dependencies. No blocking items.

---

## Validation Architecture

`workflow.nyquist_validation` is not set to `false` in config.json — validation is enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None explicit — tests/ directory auto-discovered |
| Quick run command | `python -m pytest tests/test_sector_detection.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SECTOR-01 | index.json has `sector` field for all 7 companies | unit | `python -m pytest tests/test_sector_routing.py::test_index_json_has_sector -x` | Wave 0 |
| SECTOR-02 | Khan Bank data routes to bank_ratios and returns NIM/CAR | unit | `python -m pytest tests/test_sector_routing.py::test_bank_routing -x` | Wave 0 |
| SECTOR-03 | Мандал data routes to insurance_ratios and returns loss_ratio | unit | `python -m pytest tests/test_sector_routing.py::test_insurance_routing -x` | Wave 0 |
| COMP-01 | All 26+ RATIO_LABELS keys appear in ratio computation output | unit | `python -m pytest tests/test_sector_routing.py::test_all_ratios_present -x` | Wave 0 |
| COMP-03 | DuPont: product of margin × turnover × multiplier ≈ ROE | unit | `python -m pytest tests/test_sector_routing.py::test_dupont_identity -x` | Wave 0 |
| COMP-04 | Red flags returns list with at least "No Major Red Flags" entry | unit | `python -m pytest tests/test_sector_routing.py::test_red_flags_baseline -x` | Wave 0 |
| SCREEN-01 | filtered_companies returns only Banking companies when filter="Banking" | unit | `python -m pytest tests/test_sector_routing.py::test_screener_filter -x` | Wave 0 |
| SCREEN-02 | sorted companies by score desc have first entry >= last entry | unit | `python -m pytest tests/test_sector_routing.py::test_screener_sort -x` | Wave 0 |
| COMP-02, COMP-05, COMP-06, COMP-07 | Tab rendering, chart data shape | manual | Visual inspection in browser | manual only |

UI components (COMP-02 tabs, COMP-05 gauge, COMP-06 radar, COMP-07 bar chart) cannot be automated without a browser testing framework. These are marked manual-only and verified by human inspection during `/gsd:verify-work`.

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_sector_routing.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_sector_routing.py` — covers SECTOR-01, SECTOR-02, SECTOR-03, COMP-01, COMP-03, COMP-04, SCREEN-01, SCREEN-02
- [ ] No framework install needed — pytest 9.0.2 already available

---

## Sources

### Primary (HIGH confidence)

- Reflex 0.8.26 source in venv: `reflex/components/radix/themes/components/tabs.py` — `rx.tabs.root/list/trigger/content` API, `default_value`, `on_change` props verified
- Reflex 0.8.26 source in venv: `reflex/components/recharts/__init__.py` — confirmed `radar_chart`, `radial_bar_chart`, `bar_chart`, `reference_line`, `polar_angle_axis`, `polar_grid` all available
- Project source: `financial_dashboard/analysis/ratios.py` — `compute_composite_score()` breakdown keys confirmed: profitability, liquidity, solvency, activity, altman, piotroski
- Project source: `financial_dashboard/analysis/bank_ratios.py` — 19 ratios in 5 categories, detection via `bank_balance_sheet`/`bank_income_statement` keys confirmed
- Project source: `financial_dashboard/analysis/insurance_ratios.py` — 15+ ratios in 5 categories, detection via `insurance_balance_sheet`/`insurance_income_statement` keys confirmed
- Project source: `financial_dashboard/state.py` — existing `screener_filter`, `filtered_companies`, `load_company()` patterns confirmed; `_load_all_companies()` already reads `sector` from index.json
- Project source: `data/index.json` — 7 company entries confirmed, none have `sector` field yet

### Secondary (MEDIUM confidence)

- STATE.md Known Gotchas section — `list[dict[str,str]]` state var constraint, `rx.cond()`, `rx.foreach()`, `rx.recharts` only, Tailwind v4 `class_name` strings — documented project-level findings from Phase 1 experience

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed venv source
- Architecture: HIGH — based on actual source code analysis, not documentation assumptions
- Pitfalls: HIGH — derived from reading actual Reflex source + STATE.md accumulated gotchas from Phase 1

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (Reflex 0.8.26 is pinned; no version change expected within phase)
