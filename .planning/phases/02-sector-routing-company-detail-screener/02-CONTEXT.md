# Phase 2: Sector Routing, Company Detail & Screener - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire bank/insurance sector-specific ratio engines into the company page, expand company detail page to full ratio coverage with 5-tab navigation and 3 chart visualizations (health gauge, radar chart, Beneish bar), and add sector filter dropdown + column sort to the screener — all interactions without page reload.

**In scope:** SECTOR-01, SECTOR-02, SECTOR-03, COMP-01 through COMP-07, SCREEN-01, SCREEN-02
**Not in scope:** Valuation tab content (Phase 3 fills it — Phase 2 creates the tab as a placeholder)

</domain>

<decisions>
## Implementation Decisions

### Sector Detection
- **D-01:** Sector is auto-detected from parsed data structure — no user input required. Logic: if parsed JSON has `bank_balance_sheet` or `bank_income_statement` keys → Banking; if it has insurance-specific keys → Insurance; otherwise → Standard. This works for all MSE companies, not just the 7 demo companies.
- **D-02:** For the 7 demo companies, `sector` field is added manually to `index.json` entries (already decided in PROJECT.md). For newly uploaded companies, sector is written to index.json at parse time using the auto-detection logic from D-01.

### Tab Navigation
- **D-03:** Use Reflex's built-in `rx.tabs.root` + `rx.tabs.list` + `rx.tabs.content` for the 5-tab layout: **Ratios | Forensic | Valuation | DuPont | Red Flags**. Styled with `class_name` to match the dark OLED theme (`bg-slate-900`, `border-slate-800`). No custom tab state var needed.
- **D-04:** The Valuation tab exists in Phase 2 as a placeholder (empty panel or "Price data coming in Phase 3" message). Phase 3 populates it.

### Health Gauge Visualization (COMP-05)
- **D-05:** Semicircle arc using `rx.recharts.radial_bar_chart` (or equivalent Recharts primitive). Three color zones: red (0–40), amber (40–70), green (70–100). Score number and label (Healthy/Caution/Distress) rendered in the center below the arc.

### Screener Layout
- **D-06:** Sector appears as both a **visible table column** and a **filter dropdown**. The sector column is also sortable (per SCREEN-02). Column order: Company | Year | Sector | Health Score | F-Score | ROE | Add.
- **D-07:** Sector filter dropdown values: All / Banking / Insurance / Manufacturing / Food / Textiles / Holding (as specified in SCREEN-01). When "All" is selected, all companies are shown.

### Claude's Discretion
- Beneish bar chart rendering details (bar colors, axis labels, threshold line style) — Claude decides using rx.recharts
- Radar chart normalization — use the 6 category subscores already computed by `compute_composite_score()` (already 0–100 scaled)
- Red Flags display style — Claude decides (warning list with icons + plain-language explanations per COMP-04)
- DuPont tab layout — follow COMP-03 spec: ROE = Net Profit Margin × Asset Turnover × Equity Multiplier, current and prior year side-by-side
- Rate at which `all_companies` state var is extended to include sector field
- Whether to use `selected_tab` state var fallback if `rx.tabs` has any Reflex 0.8.26 limitations

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Vision, constraints, tech stack, Reflex gotchas, key decisions
- `.planning/REQUIREMENTS.md` — SECTOR-01 through SCREEN-02 acceptance criteria (full spec for each requirement)

### Existing Codebase
- `financial_dashboard/pages/company.py` — Current company page (no tabs; 2-column layout with 9 ratios); must be replaced with 5-tab structure
- `financial_dashboard/pages/screener.py` — Current screener (no sector column, no sort); must be extended
- `financial_dashboard/state.py` — AnalysisState: current ratio state vars (9 vars); must be extended for sector routing and all 26+ ratios
- `financial_dashboard/analysis/bank_ratios.py` — Bank ratio engine (19 ratios, 5 categories) — built but NOT yet imported in state.py
- `financial_dashboard/analysis/insurance_ratios.py` — Insurance ratio engine (15+ ratios) — built but NOT yet imported in state.py
- `financial_dashboard/analysis/ratios.py` — Standard ratio engine (26 ratios, `compute_composite_score` returns 6 category subscores used for radar chart)
- `data/index.json` — 7-company manifest; `sector` field must be added to each entry

### Reflex Constraints (from STATE.md Known Gotchas)
- Charts: `rx.recharts` only — no other chart library
- State vars: `list[dict[str, str]]` typed — no raw dicts
- Tailwind v4: `class_name` strings only — no `rx.color()` calls
- Conditional rendering: `rx.cond()` required
- List iteration: `rx.foreach()` required

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `score_card()` in company.py — reusable metric card component; can be used in DuPont tab and top summary row
- `ratio_row()` in company.py — reusable table row; use in full 26-ratio Ratios tab
- `piotroski_criterion()` in company.py — reusable pass/fail row; move into Forensic tab
- `health_badge()` in screener.py — reusable colored badge; keep in screener table
- `compute_composite_score()` in ratios.py — already returns 6 category subscores (0–100 each) — use directly as radar chart data

### Established Patterns
- Card style: `bg-slate-900 rounded-lg border border-slate-800 p-4`
- Table style: `rx.table.root` with `variant="ghost"`, `rx.table.body` with `ratio_row()` helpers
- Responsive grid: `rx.grid(columns="2", spacing="4", width="100%")`
- State inheritance chain: `UploadState → AnalysisState → PortfolioState`

### Integration Points
- `AnalysisState.select_company()` (or equivalent) — must also run sector detection and route to correct ratio engine
- `all_companies` state var — must be extended to include `sector` field for screener filter and column
- `index.json` — must be updated to include `sector` field for all 7 demo companies; auto-populated for new uploads
- Screener's `rx.foreach(AnalysisState.all_companies, company_row)` — `company_row` must render the new Sector column

</code_context>

<specifics>
## Specific Ideas

- The auto-detect logic for sector is implicit in the parser already: MSE bank files produce `bank_balance_sheet` + `bank_income_statement` keys; insurance files produce insurance-specific keys. This means sector detection at parse time is straightforward — check which keys exist in the parsed dict.
- The 6 category subscores from `compute_composite_score()` (Profitability, Liquidity, Solvency, Activity, Altman Z, Piotroski) map directly to the radar chart axes required by COMP-06.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-sector-routing-company-detail-screener*
*Context gathered: 2026-03-25*
