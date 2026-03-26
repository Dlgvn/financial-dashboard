# Phase 4: Portfolio Optimization - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the portfolio page with manual portfolio weights, sector breakdown donut chart, mean-variance optimization with suggested optimal weights, PPMT risk metrics (Sortino Ratio, Max Drawdown, CVaR 95%), and an efficient frontier scatter plot.

**In scope:** PORT-01, PORT-02, PORT-03, PORT-04, PORT-05, PORT-06
- Manual weight input per holding with proportional rebalancing
- Sector breakdown donut chart
- Covariance matrix from scraped price history
- Mean-variance optimization → suggested optimal weights
- Sortino Ratio, Maximum Drawdown, CVaR (95%) from historical returns
- Efficient frontier scatter plot with current portfolio highlighted

**Not in scope:** Black-Litterman views, interactive weight sliders, screener improvements, any other page changes

</domain>

<decisions>
## Implementation Decisions

### Page Layout
- **D-01:** Portfolio page gains two tabs: **Holdings** | **Analysis**. This replaces the current single-page layout.
- **D-02:** Holdings tab contains: the holdings table (with inline weight inputs) + blended health score header (existing).
- **D-03:** Analysis tab layout (top to bottom):
  1. Top row: Sector donut chart (left) + 3 risk metric cards (right: Sortino, Max Drawdown, CVaR)
  2. Middle: Efficient frontier scatter plot (full width)
  3. Bottom: Optimization table — Company | Current | Optimal + "Apply Optimal Weights" button
- **D-04:** Analysis tab only renders when there are ≥2 holdings with scraped price data. Otherwise shows a placeholder: "Add at least 2 companies with price history to see portfolio analysis."

### Weight Input UX
- **D-05:** Each row in the Holdings tab table has an inline `rx.input` showing the current weight as a percentage (e.g., `25.0`). The weight column replaces the static `weight_str` display.
- **D-06:** When user edits a weight and presses Enter or Tab, the remaining holdings are proportionally rebalanced so all weights sum to 100%. The edited holding keeps its new value; all others scale to fill the remainder proportionally.
- **D-07:** Weights are stored as floats (0–100 range, not 0–1) in a new state var alongside existing `weight` (0–1). Display shows one decimal: `25.0%`.
- **D-08:** The existing equal-weight rebalancing (on add/remove) continues to work — Phase 4 adds manual override on top.

### Optimization Display
- **D-09:** Optimization section shows a table: Company | Current Weight | Optimal Weight. Optimal weights show directional arrows (↑ if optimal > current, ↓ if optimal < current).
- **D-10:** An "Apply Optimal Weights" button below the table updates `PortfolioState.holdings` weights to the optimal values. This triggers recomputation of all metrics.
- **D-11:** Optimization runs automatically when the Analysis tab is active and portfolio changes. No manual "run optimization" button needed.

### Risk Metrics
- **D-12:** Sortino Ratio, Maximum Drawdown, CVaR (95%) computed from daily portfolio returns derived from price history.
- **D-13:** Each metric displayed as a card (same `bg-slate-900 rounded-lg border border-slate-800` style) with label + value + brief description (e.g., "Sortino Ratio — 1.24").
- **D-14:** Metric cards show "N/A" when price data is insufficient.

### Efficient Frontier
- **D-15:** Static scatter plot — ~200 randomly sampled portfolios (grey dots `#475569`) tracing the frontier shape, plus the current portfolio highlighted as a distinct green dot (`#4ade80`).
- **D-16:** Axes: X = annualized portfolio risk (std dev of returns), Y = annualized expected return. Both expressed as percentages (e.g., 12.5%).
- **D-17:** No hover tooltips. Clean static display using `rx.recharts.scatter_chart`.
- **D-18:** Current portfolio position updates reactively when weights change.

### Sector Data
- **D-19:** Each holding in `PortfolioState.holdings` must include a `sector` field (values: "Banking", "Insurance", "Standard"). This field is already available in `all_companies` entries via the `sector` key. The `add_to_portfolio` event handler must be extended to include `sector` when building the holding dict.
- **D-20:** Sector donut uses `rx.recharts.pie_chart`. Segments: Banking / Insurance / Standard by total weight. Colors: Banking = blue (`#60a5fa`), Insurance = amber (`#f59e0b`), Standard = green (`#4ade80`).

### Claude's Discretion
- Optimization library: scipy.optimize (minimize with SLSQP, equality constraint weights=1, bounds 0–1 per asset)
- Covariance matrix computation: use log returns from `close` prices in price JSON
- Efficient frontier sampling: random weight generation, filter to Pareto-efficient subset
- Sortino Ratio: target return = 0 (downside deviation from 0)
- CVaR 95%: historical simulation, 5th percentile tail average
- Tab component implementation: use `rx.tabs.root` / `rx.tabs.list` / `rx.tabs.content` (same pattern as company page tabs from Phase 2)
- Exact chart dimensions, tooltip format, axis label formatting

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Vision, constraints, tech stack, Reflex gotchas, key decisions
- `.planning/REQUIREMENTS.md` — PORT-01 through PORT-06 acceptance criteria

### Existing Codebase
- `financial_dashboard/pages/portfolio.py` — Current portfolio page (holdings table, PortfolioState bindings); this file is the primary target for Phase 4
- `financial_dashboard/state.py` — `PortfolioState` (line ~1037): `holdings` list structure `{company, filename, url, weight, weight_str, score, score_str, label, color}`, `add_to_portfolio`, `remove_from_portfolio`, `portfolio_health`, `in_portfolio`; also `_detect_sector_from_data()` and `all_companies` sector field
- `financial_dashboard/pages/company.py` — `rx.tabs.root` tab component pattern (from Phase 2) to replicate for portfolio page tabs
- `financial_dashboard/analysis/valuation.py` — Pattern for new analysis module (Phase 3); portfolio optimization module follows same structure
- `data/prices/АПУ.json` — Price JSON structure: `{company, mse_id, scraped_at, shares_outstanding, records[{date, open, high, low, close, volume}]}`

### Reflex Constraints (from STATE.md + Phase 3 context)
- Charts: `rx.recharts` only — `rx.recharts.scatter_chart` for efficient frontier, `rx.recharts.pie_chart` for sector donut
- State vars: `list[dict[str, str]]` typed — no raw dicts in state
- Tailwind v4: `class_name` strings only — no `rx.color()` calls
- Conditional rendering: `rx.cond()` required
- List iteration: `rx.foreach()` required
- Recharts data must be state vars — never construct inline in components

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PortfolioState` in `state.py` — extend with new state vars for optimization results, risk metrics, chart data; add weight-editing event handler
- `rx.tabs.root` pattern in `company.py` — copy tab structure for Holdings | Analysis tabs
- `score_card()` pattern in `company.py` — reuse for the 3 risk metric cards (Sortino, MaxDD, CVaR)
- `valuation.py` — pattern for a standalone analysis module; `portfolio_optimization.py` follows same structure

### Established Patterns
- Card style: `bg-slate-900 rounded-lg border border-slate-800 p-4`
- State vars for charts declared as `list[dict[str, str]]` on PortfolioState (e.g., `frontier_data: list[dict[str, str]] = []`)
- Event handler naming: `set_{thing}`, `toggle_{thing}`, `save_{thing}` (from Phase 3)
- Price file lookup: `data/prices/{company_name}.json` where name matches `index.json` `company` field (Mongolian name)

### Integration Points
- `PortfolioState.add_to_portfolio()` — must add `sector` field to holding dict (D-19)
- `PortfolioState.holdings` weight fields — extend with float weight (0–100) + inline input binding
- New module `financial_dashboard/analysis/portfolio_optimization.py` — covariance matrix, mean-variance optimization, risk metrics, frontier sampling
- New event handlers on `PortfolioState`: `set_holding_weight(company, value)`, `apply_optimal_weights()`, `_compute_portfolio_analysis()` (triggered when analysis tab is active + ≥2 price-data companies)

</code_context>

<specifics>
## Specific Ideas

- "Apply Optimal Weights" must propagate back to Holdings tab — changes the weight inputs there, not just the display
- The Analysis tab's fallback state (< 2 companies with price data) should be graceful — not an error, just a nudge to add more companies

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-portfolio-optimization*
*Context gathered: 2026-03-26*
