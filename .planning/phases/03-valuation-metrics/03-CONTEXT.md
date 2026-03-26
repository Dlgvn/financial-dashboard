# Phase 3: Valuation Metrics - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Fill the Valuation tab placeholder (created in Phase 2) with four computed valuation ratios and a historical price line chart with volume bars.

**In scope:** VAL-01, VAL-02, VAL-03
- Scrape shares outstanding from MSE website and store in price JSON
- Compute EV/EBITDA, FCF Yield, P/E, P/BV using scraped shares + last close price
- Display 4 ratio cards in a horizontal row above the price chart
- Historical Close price line chart + volume bars, with 1M/6M/1Y/All range toggle (default: 1Y)
- Manual shares outstanding override (edit icon on cards when shares unavailable)

**Not in scope:** Any other tab content, screener valuation filters (Phase 2 scope), portfolio metrics

</domain>

<decisions>
## Implementation Decisions

### Valuation Formulas
- **D-01:** All 4 ratios (EV/EBITDA, FCF Yield, P/E, P/BV) require shares outstanding. None are computable without it. The PROJECT.md claim that "EV/EBITDA and FCF yield computable from existing data" is superseded by this decision — user confirmed all 4 need shares.
- **D-02:** FCF Yield = FCF / Market Cap. FCF = Operating Cash Flow − CapEx. Market Cap = shares_outstanding × last_close_price.
- **D-03:** EV = Market Cap + Total Debt − Cash. EV/EBITDA = EV / EBITDA. EBITDA ≈ EBIT (MSE doesn't disclose depreciation separately — same approximation already used in ratios.py line 124–125).
- **D-04:** P/E = Market Cap / Net Income (or equivalently: last_close_price / EPS). P/BV = Market Cap / Book Value (Total Equity).
- **D-05:** Last close price = the most recent `close` value from `data/prices/{company}.json` records array.

### Shares Outstanding — Scraping
- **D-06:** Shares outstanding is scraped from `old.mse.mn/en/company/{mse_id}` alongside price data. The MSE website displays total shares outstanding on the company page.
- **D-07:** Shares outstanding stored as a `shares_outstanding` field in the price JSON file (`data/prices/{company}.json`) at the top level (alongside `company`, `mse_id`, `scraped_at`, `records`).
- **D-08:** The existing `scrape_company_prices()` function in `price_scraper.py` is extended (or a companion scrape function added) to also capture shares outstanding. The `save_price_data()` function is updated to persist this field.

### Shares Outstanding — Manual Fallback
- **D-09:** If `shares_outstanding` is missing from the price JSON (scrape failure, new company not yet in registry), all 4 ratio cards show "N/A" with a ✎ edit icon.
- **D-10:** Clicking the ✎ icon reveals an inline input field directly on the card. User enters the number and saves. The manual override is stored in the company's financial JSON (in `data/`), not in the price JSON.
- **D-11:** After saving manual shares, the 4 ratio cards update immediately (no page reload) — Reflex state update pattern.

### Price Chart
- **D-12:** Default range: 1 year. Toggle buttons: 1M / 6M / 1Y / All. Active range is tracked in state.
- **D-13:** Chart composition: Close price line chart (primary) + volume bars (secondary panel below). Uses `rx.recharts` only.
- **D-14:** Price data: `data/prices/{company}.json` → `records[]` array of `{date, open, high, low, close, volume}`. Date on x-axis, Close (MNT) on y-axis. Volume bars below.

### Metrics Layout
- **D-15:** 4 ratio cards arranged in a single horizontal row (`rx.hstack` or `rx.grid(columns="4")`) above the price chart. Card order: EV/EBITDA | FCF Yield | P/E | P/BV.
- **D-16:** Card style consistent with existing `score_card()` component in company.py (`bg-slate-900 rounded-lg border border-slate-800`).
- **D-17:** When shares are missing: card shows metric name, "N/A" as the value, and a ✎ edit icon. When shares are available: card shows the computed value.

### Claude's Discretion
- State var naming for valuation ratios — follow AnalysisState convention (`company_ev_ebitda: str = ""` etc.)
- Chart height, tooltip format (date, Close price, volume), axis label formatting
- Recharts `ComposedChart` or separate charts for price line + volume bars
- How the active range toggle button highlights (matching existing dark OLED button styles)
- Whether `shares_outstanding` input field accepts comma-formatted integers and normalizes to int

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Vision, constraints, tech stack, Reflex gotchas, key decisions
- `.planning/REQUIREMENTS.md` — VAL-01, VAL-02, VAL-03 acceptance criteria

### Existing Codebase
- `financial_dashboard/pages/company.py` — `valuation_placeholder()` function (line ~374) to be replaced; existing `score_card()`, `rx.recharts` patterns for gauge/radar/beneish charts
- `financial_dashboard/state.py` — `AnalysisState` state var patterns, `select_company()` event handler (must also load price data + compute valuation ratios), Reflex typing constraints
- `financial_dashboard/analysis/ratios.py` — EBIT computation (line 124–125), OCF at line 93 and 301 — reuse for FCF computation; existing ratio return structure
- `financial_dashboard/scraper/price_scraper.py` — `scrape_company_prices()` and `save_price_data()` — extend to scrape and persist `shares_outstanding`
- `data/prices/АПУ.json` — Confirmed price JSON structure: `{company, mse_id, scraped_at, records[{date, open, high, low, close, volume}]}`

### Reflex Constraints (from STATE.md)
- Charts: `rx.recharts` only
- State vars: `list[dict[str, str]]` typed — no raw dicts
- Tailwind v4: `class_name` strings only — no `rx.color()` calls
- Conditional rendering: `rx.cond()` required
- List iteration: `rx.foreach()` required
- Recharts data vars must be state vars — never construct inline in components

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `score_card()` in `company.py` — existing metric card component; reuse for the 4 valuation ratio cards (consistent styling with other tabs)
- `rx.recharts.line_chart` + `rx.recharts.bar_chart` patterns already in company.py — reuse for price line and volume bars
- `AnalysisState.select_company()` — already loads company data; extend to also load price data and compute valuation metrics
- `ratios.py` EBIT value and OCF value already computed per company — reuse directly

### Established Patterns
- Card style: `bg-slate-900 rounded-lg border border-slate-800 p-4`
- State vars for charts must be declared as `list[dict[str, str]]` on AnalysisState (e.g., `company_price_chart_data: list[dict[str, str]] = []`)
- Price file lookup: `data/prices/{company_name}.json` where `company_name` matches `index.json` `company` field (Mongolian name)

### Integration Points
- `valuation_placeholder()` in company.py → replace with `valuation_tab_content()` implementing D-15 layout
- `AnalysisState.select_company()` or a new `load_valuation_data()` event — must read price JSON, extract last close price, read shares_outstanding, compute 4 ratios, slice records by selected range
- New state vars needed: `company_ev_ebitda`, `company_fcf_yield`, `company_pe`, `company_pbv`, `company_shares_outstanding`, `company_price_chart_data`, `company_volume_chart_data`, `valuation_range` (enum: "1M"/"6M"/"1Y"/"All")
- Scraper: `save_price_data()` updated to persist `shares_outstanding` alongside records

</code_context>

<specifics>
## Specific Ideas

- User noted: "total share is displayed in MSE website" — scraping shares outstanding is feasible and preferred over manual input. The existing price scraper already fetches `old.mse.mn/en/company/{id}`, so shares can be captured in the same request.
- The Phase 2 Valuation tab already has a clean placeholder (`valuation_placeholder()`) — it just needs to be replaced, no structural changes to tabs needed.
- MSE is a thin-volume market — volume bars are explicitly wanted to provide trading volume context alongside the price line.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-valuation-metrics*
*Context gathered: 2026-03-26*
