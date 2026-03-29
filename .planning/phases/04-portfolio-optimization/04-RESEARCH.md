# Phase 4: Portfolio Optimization - Research

**Researched:** 2026-03-29
**Domain:** Mean-variance optimization, risk metrics, Reflex UI (tabs, recharts), scipy.optimize
**Confidence:** HIGH

## Summary

Phase 4 extends the existing portfolio page into a two-tab layout (Holdings | Analysis). The Holdings tab gains inline weight inputs; the Analysis tab adds a sector donut chart, three risk metric cards, an efficient frontier scatter plot, and a mean-variance optimization table. All math lives in a new `financial_dashboard/analysis/portfolio_optimization.py` module following the pattern already established by `valuation.py`.

The key dependencies are already present: scipy 1.16.2 and numpy 2.3.4 are installed. The Reflex tab pattern is proven in `company.py` (5-tab layout using `rx.tabs.root/list/trigger/content`). Recharts scatter and pie chart components are available in reflex 0.8.26. All chart data must be declared as `list[dict[str, str]]` state vars and never constructed inline.

The most significant implementation risk is the Reflex state var type constraint: all chart data and optimization results must be stored as `list[dict[str, str]]` (string-valued dicts). This means floats must be converted to strings before storage, and the rendering layer must format them back for display. Every computed value — weights, returns, risk — must round-trip through string conversion cleanly.

**Primary recommendation:** Build `portfolio_optimization.py` as a pure-Python module (no Reflex dependencies), test it independently with pytest, then wire it into `PortfolioState` via a single `_compute_portfolio_analysis()` event handler that populates all state vars at once.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Page Layout**
- D-01: Portfolio page gains two tabs: Holdings | Analysis. This replaces the current single-page layout.
- D-02: Holdings tab contains: the holdings table (with inline weight inputs) + blended health score header (existing).
- D-03: Analysis tab layout (top to bottom): (1) Top row: Sector donut chart (left) + 3 risk metric cards (right: Sortino, Max Drawdown, CVaR); (2) Middle: Efficient frontier scatter plot (full width); (3) Bottom: Optimization table — Company | Current | Optimal + "Apply Optimal Weights" button
- D-04: Analysis tab only renders when there are >=2 holdings with scraped price data. Otherwise shows a placeholder: "Add at least 2 companies with price history to see portfolio analysis."

**Weight Input UX**
- D-05: Each row in the Holdings tab table has an inline `rx.input` showing the current weight as a percentage (e.g., `25.0`). The weight column replaces the static `weight_str` display.
- D-06: When user edits a weight and presses Enter or Tab, the remaining holdings are proportionally rebalanced so all weights sum to 100%. The edited holding keeps its new value; all others scale to fill the remainder proportionally.
- D-07: Weights are stored as floats (0-100 range, not 0-1) in a new state var alongside existing `weight` (0-1). Display shows one decimal: `25.0%`.
- D-08: The existing equal-weight rebalancing (on add/remove) continues to work — Phase 4 adds manual override on top.

**Optimization Display**
- D-09: Optimization section shows a table: Company | Current Weight | Optimal Weight. Optimal weights show directional arrows (↑ if optimal > current, ↓ if optimal < current).
- D-10: An "Apply Optimal Weights" button below the table updates `PortfolioState.holdings` weights to the optimal values. This triggers recomputation of all metrics.
- D-11: Optimization runs automatically when the Analysis tab is active and portfolio changes. No manual "run optimization" button needed.

**Risk Metrics**
- D-12: Sortino Ratio, Maximum Drawdown, CVaR (95%) computed from daily portfolio returns derived from price history.
- D-13: Each metric displayed as a card (same `bg-slate-900 rounded-lg border border-slate-800` style) with label + value + brief description (e.g., "Sortino Ratio — 1.24").
- D-14: Metric cards show "N/A" when price data is insufficient.

**Efficient Frontier**
- D-15: Static scatter plot — ~200 randomly sampled portfolios (grey dots `#475569`) tracing the frontier shape, plus the current portfolio highlighted as a distinct green dot (`#4ade80`).
- D-16: Axes: X = annualized portfolio risk (std dev of returns), Y = annualized expected return. Both expressed as percentages (e.g., 12.5%).
- D-17: No hover tooltips. Clean static display using `rx.recharts.scatter_chart`.
- D-18: Current portfolio position updates reactively when weights change.

**Sector Data**
- D-19: Each holding in `PortfolioState.holdings` must include a `sector` field (values: "Banking", "Insurance", "Standard"). This field is already available in `all_companies` entries via the `sector` key. The `add_to_portfolio` event handler must be extended to include `sector` when building the holding dict.
- D-20: Sector donut uses `rx.recharts.pie_chart`. Segments: Banking / Insurance / Standard by total weight. Colors: Banking = blue (`#60a5fa`), Insurance = amber (`#f59e0b`), Standard = green (`#4ade80`).

### Claude's Discretion
- Optimization library: scipy.optimize (minimize with SLSQP, equality constraint weights=1, bounds 0-1 per asset)
- Covariance matrix computation: use log returns from `close` prices in price JSON
- Efficient frontier sampling: random weight generation, filter to Pareto-efficient subset
- Sortino Ratio: target return = 0 (downside deviation from 0)
- CVaR 95%: historical simulation, 5th percentile tail average
- Tab component implementation: use `rx.tabs.root` / `rx.tabs.list` / `rx.tabs.content` (same pattern as company page tabs from Phase 2)
- Exact chart dimensions, tooltip format, axis label formatting

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PORT-01 | User can manually input portfolio weights per holding; weights auto-normalize to 100% | D-05/06/07: inline rx.input per row, Enter/Tab triggers proportional rebalance; holdings dict gains `weight_pct` float field |
| PORT-02 | Portfolio page shows sector breakdown as a donut/pie chart | D-19/20: sector field in holdings; rx.recharts.pie_chart; sector_chart_data state var as list[dict[str,str]] |
| PORT-03 | System computes a return covariance matrix from scraped historical price data | portfolio_optimization.py: load price JSONs, compute log returns, np.cov; confirmed scipy+numpy available |
| PORT-04 | System runs mean-variance optimization and displays suggested optimal weights alongside current weights | scipy.optimize.minimize with SLSQP; optimization_data state var; D-09/10/11 |
| PORT-05 | Portfolio page shows Sortino Ratio, Maximum Drawdown, CVaR (95%) | Three metric cards; pure numpy computation; sortino_str, max_drawdown_str, cvar_str state vars |
| PORT-06 | Efficient frontier scatter plot shown on portfolio page with current portfolio highlighted | rx.recharts.scatter_chart; frontier_data + current_point_data state vars; ~200 sampled portfolios |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scipy | 1.16.2 | mean-variance optimization via `scipy.optimize.minimize` (SLSQP) | Already installed; locked in CONTEXT.md; industry standard for constrained optimization |
| numpy | 2.3.4 | log returns, covariance matrix, portfolio math | Already installed; fundamental array math |
| reflex | 0.8.26 (pinned) | UI framework — tabs, recharts, state | Project constraint — cannot change |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | — | Load price JSONs from `data/prices/` | Reading price data in portfolio_optimization.py |
| pathlib (stdlib) | — | Locate price files | Use `Path` consistently with existing codebase patterns |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scipy SLSQP | PyPortfolioOpt | PyPortfolioOpt not installed; adds dependency; SLSQP sufficient for mean-variance |
| numpy log returns | pandas pct_change | pandas is available but adds overhead; numpy sufficient and consistent with optimization module |

**No additional installation needed.** scipy and numpy are already present. No changes to `requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure
```
financial_dashboard/
├── analysis/
│   ├── valuation.py              # Existing — pattern to follow
│   └── portfolio_optimization.py # NEW — pure Python, no Reflex imports
├── pages/
│   └── portfolio.py              # PRIMARY TARGET — full rewrite with tabs
└── state.py                      # Extend PortfolioState with new vars + handlers
```

### Pattern 1: Pure Python Analysis Module (follows valuation.py)
**What:** All math in a standalone module with typed function signatures, no Reflex imports, returns plain Python dicts/lists.
**When to use:** Any computation that needs testing independent of Reflex state.
**Example:**
```python
# financial_dashboard/analysis/portfolio_optimization.py
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

PRICES_DIR = Path(__file__).parent.parent.parent / "data" / "prices"


def load_price_returns(company_names: list[str]) -> dict[str, np.ndarray]:
    """Load close prices from price JSONs and compute log returns.

    Returns: {company_name: log_return_array} — only companies with price files.
    """
    result = {}
    for name in company_names:
        path = PRICES_DIR / f"{name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data.get("records", [])
        if len(records) < 2:
            continue
        closes = np.array([float(r["close"]) for r in records])
        # Log returns: ln(p_t / p_{t-1})
        log_returns = np.log(closes[1:] / closes[:-1])
        result[name] = log_returns
    return result


def align_returns(returns_map: dict[str, np.ndarray]) -> tuple[list[str], np.ndarray]:
    """Align return series to shared minimum length.

    Returns: (company_names_list, returns_matrix [n_obs x n_assets])
    """
    names = list(returns_map.keys())
    min_len = min(len(r) for r in returns_map.values())
    # Use the LAST min_len observations (most recent data)
    matrix = np.column_stack([returns_map[n][-min_len:] for n in names])
    return names, matrix


def compute_portfolio_returns(weights: np.ndarray, returns_matrix: np.ndarray) -> np.ndarray:
    """Compute daily portfolio return series from weights and asset returns."""
    return returns_matrix @ weights


def compute_risk_metrics(portfolio_returns: np.ndarray) -> dict:
    """Compute Sortino Ratio, Maximum Drawdown, CVaR 95%.

    Returns: {sortino, max_drawdown, cvar_95} — all floats or None.
    """
    if len(portfolio_returns) < 10:
        return {"sortino": None, "max_drawdown": None, "cvar_95": None}

    # Sortino Ratio (annualized, target return = 0)
    downside = portfolio_returns[portfolio_returns < 0]
    if len(downside) == 0:
        sortino = None
    else:
        downside_std = np.std(downside, ddof=1) * np.sqrt(252)
        ann_return = np.mean(portfolio_returns) * 252
        sortino = ann_return / downside_std if downside_std > 0 else None

    # Maximum Drawdown
    cumulative = np.cumprod(1 + portfolio_returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = float(np.min(drawdowns))

    # CVaR 95% (historical simulation — average of worst 5% daily returns)
    threshold = np.percentile(portfolio_returns, 5)
    tail = portfolio_returns[portfolio_returns <= threshold]
    cvar_95 = float(np.mean(tail)) if len(tail) > 0 else None

    return {"sortino": sortino, "max_drawdown": max_drawdown, "cvar_95": cvar_95}


def mean_variance_optimize(
    returns_matrix: np.ndarray,
    names: list[str],
) -> dict:
    """Run mean-variance optimization (maximize Sharpe, risk-free = 0).

    Returns: {"weights": {name: float}, "success": bool}
    """
    n = len(names)
    mean_returns = np.mean(returns_matrix, axis=0) * 252
    cov_matrix = np.cov(returns_matrix.T) * 252

    def neg_sharpe(w):
        port_return = np.dot(w, mean_returns)
        port_vol = np.sqrt(w @ cov_matrix @ w)
        if port_vol < 1e-10:
            return 0.0
        return -(port_return / port_vol)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0.0, 1.0)] * n
    w0 = np.array([1 / n] * n)

    result = minimize(neg_sharpe, w0, method="SLSQP",
                      bounds=bounds, constraints=constraints,
                      options={"maxiter": 1000, "ftol": 1e-9})

    if result.success:
        weights = {names[i]: round(float(result.x[i]) * 100, 1) for i in range(n)}
    else:
        # Fallback: equal weights
        weights = {n: round(100 / len(names), 1) for n in names}

    return {"weights": weights, "success": result.success}


def sample_frontier(
    returns_matrix: np.ndarray,
    n_samples: int = 200,
) -> list[dict]:
    """Sample random portfolios to trace efficient frontier shape.

    Returns: list of {"risk": float_str, "return": float_str} — annualized %.
    """
    n_assets = returns_matrix.shape[1]
    mean_returns = np.mean(returns_matrix, axis=0) * 252
    cov_matrix = np.cov(returns_matrix.T) * 252

    rng = np.random.default_rng(seed=42)
    portfolios = []
    for _ in range(n_samples):
        w = rng.random(n_assets)
        w /= w.sum()
        port_return = float(np.dot(w, mean_returns) * 100)
        port_risk = float(np.sqrt(w @ cov_matrix @ w) * 100)
        portfolios.append({"risk": str(round(port_risk, 2)), "return": str(round(port_return, 2))})
    return portfolios
```

### Pattern 2: State Var Types for Recharts (established project pattern)
**What:** All chart data vars typed as `list[dict[str, str]]` — floats converted to strings before storing.
**When to use:** Whenever a recharts component needs data fed from state.
**Example:**
```python
# In PortfolioState (state.py)
class PortfolioState(AnalysisState):
    # ... existing vars ...

    # Sector donut data
    sector_chart_data: list[dict[str, str]] = []
    # e.g., [{"name": "Banking", "value": "45.0"}, ...]

    # Efficient frontier scatter data
    frontier_data: list[dict[str, str]] = []
    # e.g., [{"risk": "12.3", "return": "8.5"}, ...]

    # Current portfolio point on frontier
    current_point_data: list[dict[str, str]] = []
    # e.g., [{"risk": "15.1", "return": "9.2"}]

    # Optimization table rows
    optimization_data: list[dict[str, str]] = []
    # e.g., [{"company": "АПУ", "current": "25.0", "optimal": "31.5", "arrow": "↑"}]

    # Risk metric display strings
    sortino_str: str = "N/A"
    max_drawdown_str: str = "N/A"
    cvar_str: str = "N/A"
```

### Pattern 3: rx.tabs with Holdings | Analysis
**What:** Two-tab layout using `rx.tabs.root/list/trigger/content`, default on "holdings".
**When to use:** This is the exact pattern from company.py to replicate.
**Example:**
```python
# In portfolio.py
rx.tabs.root(
    rx.tabs.list(
        rx.tabs.trigger(
            "Holdings", value="holdings",
            class_name="text-slate-400 data-[state=active]:text-green-400 "
                       "data-[state=active]:border-b-2 data-[state=active]:border-green-400 "
                       "px-4 py-2 text-sm font-medium",
        ),
        rx.tabs.trigger(
            "Analysis", value="analysis",
            class_name="text-slate-400 data-[state=active]:text-green-400 "
                       "data-[state=active]:border-b-2 data-[state=active]:border-green-400 "
                       "px-4 py-2 text-sm font-medium",
        ),
        class_name="border-b border-slate-800",
    ),
    rx.tabs.content(holdings_tab_content(), value="holdings"),
    rx.tabs.content(analysis_tab_content(), value="analysis"),
    default_value="holdings",
    width="100%",
    class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
)
```

### Pattern 4: Inline Weight Input with on_blur / on_key_down
**What:** `rx.input` in holding row for weight editing; triggers rebalance on Enter or blur.
**When to use:** D-05/D-06 — replace static `weight_str` cell.
**Example:**
```python
rx.input(
    value=holding["weight_pct"],
    on_blur=PortfolioState.set_holding_weight(holding["company"], holding["weight_pct"]),
    on_key_down=PortfolioState.handle_weight_key(holding["company"], holding["weight_pct"]),
    class_name="bg-transparent text-slate-300 text-sm font-mono w-16 text-right "
               "border border-slate-700 rounded px-1",
)
```
Note: Reflex `rx.input` binds `value` to a state var. The holding dict must include `weight_pct` as a string key. The event handler takes `(company: str, new_value: str)`.

### Pattern 5: Recharts Scatter Chart (efficient frontier)
**What:** Two-series scatter chart using state vars — one for frontier dots, one for current portfolio.
**When to use:** PORT-06 efficient frontier display.
**Example:**
```python
rx.recharts.scatter_chart(
    rx.recharts.scatter(
        data=PortfolioState.frontier_data,
        name="Frontier",
        fill="#475569",
    ),
    rx.recharts.scatter(
        data=PortfolioState.current_point_data,
        name="Current",
        fill="#4ade80",
    ),
    rx.recharts.x_axis(data_key="risk", name="Risk (%)"),
    rx.recharts.y_axis(data_key="return", name="Return (%)"),
    width=700,
    height=350,
)
```

### Pattern 6: Recharts Pie Chart (sector donut)
**What:** Pie chart driven by sector_chart_data state var.
**When to use:** PORT-02 sector breakdown.
**Example:**
```python
rx.recharts.pie_chart(
    rx.recharts.pie(
        data=PortfolioState.sector_chart_data,
        data_key="value",
        name_key="name",
        inner_radius="50%",
        outer_radius="80%",
        fill="#60a5fa",  # overridden per cell
    ),
    width=300,
    height=250,
)
```
Note: Per-segment colors require cell-level props or a fill function. Investigate recharts pie `cell` support in Reflex 0.8.26 before implementation.

### Pattern 7: `on_change` tab event for deferred analysis computation
**What:** When user switches to Analysis tab, trigger `_compute_portfolio_analysis()`.
**When to use:** D-11 — analysis runs automatically when tab is active.
**Example:**
```python
rx.tabs.root(
    ...
    on_change=PortfolioState.on_tab_change,
    ...
)
# In state:
@rx.event
def on_tab_change(self, tab: str):
    self.active_tab = tab
    if tab == "analysis":
        yield PortfolioState._compute_portfolio_analysis()
```

### Anti-Patterns to Avoid
- **Inline chart data construction:** Never build chart data dicts inside component functions — always declare as state vars. Recharts will not update reactively otherwise.
- **Python if/else in components:** Use `rx.cond()` for all conditional rendering in the UI.
- **Python for loops in components:** Use `rx.foreach()` for all list iteration in the UI.
- **Float values in list[dict[str,str]] state vars:** All numeric values must be converted to `str` before storing. `str(round(x, 2))` is the correct pattern.
- **rx.color() calls:** Tailwind v4 uses class_name strings only. No `rx.color()`.
- **Accessing dict keys with Python dot notation in foreach:** Use `holding["key"]` not `holding.key` in Reflex component expressions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Constrained optimization (weights sum to 1) | Custom gradient descent | `scipy.optimize.minimize(method="SLSQP")` | Handles bounds + equality constraints; numerically stable; already installed |
| Covariance matrix | Manual double loop | `np.cov(returns_matrix.T)` | Handles edge cases, numerical precision; one line |
| Efficient frontier sampling | Deterministic grid search | Random sampling with `np.random.default_rng(seed=42)` | Produces visually representative frontier with 200 points; deterministic seed for reproducibility |
| CVaR computation | Rolling window logic | `np.percentile` + boolean indexing | Three lines; exact historical simulation |

**Key insight:** The financial math is straightforward with scipy+numpy. The implementation complexity is entirely in Reflex state management and type constraints, not the math.

---

## Common Pitfalls

### Pitfall 1: Misaligned Return Series Lengths
**What goes wrong:** Different companies have different numbers of price records (some have 1,400+ rows, others fewer). Passing misaligned arrays to `np.cov()` raises a shape error.
**Why it happens:** The scraper fetches all available history per company; MSE listing dates differ.
**How to avoid:** `align_returns()` function truncates all series to the shortest length using the most recent `min_len` observations. Always call this before any covariance or optimization computation.
**Warning signs:** `ValueError: could not broadcast input array` from numpy; or `optimization_data` empty while holdings.length >= 2.

### Pitfall 2: Reflex State Var Type Mismatch (floats in list[dict[str,str]])
**What goes wrong:** Storing a Python `float` inside a `list[dict[str, str]]` state var causes a Reflex serialization error at runtime. The app crashes or silently drops the update.
**Why it happens:** Reflex 0.8.26 strictly enforces the declared type annotation for state vars. `list[dict[str, str]]` means every value must be a `str`.
**How to avoid:** Always convert: `{"risk": str(round(port_risk, 2)), "return": str(round(port_return, 2))}`. Do this in the analysis module before returning, not in the state handler.
**Warning signs:** Reflex console errors about type validation; chart data not rendering; state not updating.

### Pitfall 3: rx.input on_change on Every Keystroke
**What goes wrong:** Binding weight rebalancing logic to `on_change` (fires on every keystroke) causes continuous recalculation and optimization runs while the user is still typing, creating laggy/broken UX.
**Why it happens:** `on_change` is the default for interactive inputs, but rebalancing should only happen when editing is confirmed.
**How to avoid:** Bind rebalancing to `on_blur` (focus leaves input) and `on_key_down` filtered for Enter key. Use a separate `weight_input` state var that updates on_change but only triggers rebalance on confirm. Or simply store the raw string input and rebalance on blur.
**Warning signs:** Weight inputs jumping while typing; optimization running on each character.

### Pitfall 4: Optimization Fails with < 2 Companies Having Price Data
**What goes wrong:** `np.cov()` with a single column returns a scalar, not a 2D matrix. `minimize()` with n=1 returns trivial result (100% one asset). The UI shows spurious "optimal" weights.
**Why it happens:** The guard in D-04 is at the UI level (Analysis tab placeholder) but the state handler also needs a guard.
**How to avoid:** In `_compute_portfolio_analysis()`, count companies that have price files before calling optimization. If < 2, set all metric vars to `"N/A"` and clear chart data. The UI guard (D-04) and the state guard should both be present independently.
**Warning signs:** Optimization table shows 100% one company; errors in server logs about cov matrix shape.

### Pitfall 5: `weight_pct` Field Missing from holdings Dict Breaks foreach
**What goes wrong:** `rx.foreach(PortfolioState.holdings, holding_row)` renders each row, which accesses `holding["weight_pct"]` for the input. If the field was not added during `add_to_portfolio`, Reflex raises a key error.
**Why it happens:** The existing `add_to_portfolio` does not include `weight_pct`. Must extend both `add_to_portfolio` and `remove_from_portfolio` to include this field.
**How to avoid:** Add `"weight_pct": f"{new_weight * 100:.1f}"` (as string, not float) to every holding dict construction. Update both `add_to_portfolio` and `remove_from_portfolio`. Add `sector` at the same time (D-19).
**Warning signs:** `KeyError: 'weight_pct'` in server logs; holdings table not rendering.

### Pitfall 6: Recharts Scatter Requires Numeric-Parseable Strings
**What goes wrong:** Recharts renders `0` or blank points if `"risk"` and `"return"` values are not parseable as numbers. E.g., passing `"N/A"` as a value in frontier_data causes the point to not render.
**Why it happens:** Recharts internally calls `parseFloat()` on data_key values. `NaN` results in the point being dropped silently.
**How to avoid:** Never push `"N/A"` or empty strings into `frontier_data`. If data is insufficient, set `frontier_data = []` (empty list). Display the Analysis tab placeholder instead (D-04).
**Warning signs:** Scatter chart renders with fewer dots than expected; no error visible in UI.

### Pitfall 7: Pie Chart Per-Segment Colors in Reflex 0.8.26
**What goes wrong:** `rx.recharts.pie` may not support `rx.recharts.cell` subcomponents in the same way as raw Recharts. Per-segment color customization may require a different approach.
**Why it happens:** Reflex wraps Recharts but not all props are directly exposed. Cell-level customization needs verification against the Reflex 0.8.26 recharts API.
**How to avoid:** Encode the fill color as a field in `sector_chart_data` (e.g., `{"name": "Banking", "value": "45.0", "fill": "#60a5fa"}`). Test pie chart rendering early in Wave 1. If cells don't work, fall back to a single fill color or use the `fill` prop with a state var.
**Warning signs:** All pie segments same color; `rx.recharts.cell` prop not recognized.

---

## Code Examples

### Mean-Variance Optimization Wiring in State
```python
# Source: established project pattern (valuation.py integration in state.py)
@rx.event
def _compute_portfolio_analysis(self):
    """Compute all analysis tab data: optimization, risk metrics, frontier."""
    from .analysis.portfolio_optimization import (
        load_price_returns, align_returns, compute_portfolio_returns,
        compute_risk_metrics, mean_variance_optimize, sample_frontier,
    )

    company_names = [h["company"] for h in self.holdings]
    returns_map = load_price_returns(company_names)

    # Need >= 2 companies with price data
    if len(returns_map) < 2:
        self.sortino_str = "N/A"
        self.max_drawdown_str = "N/A"
        self.cvar_str = "N/A"
        self.frontier_data = []
        self.current_point_data = []
        self.optimization_data = []
        return

    names, matrix = align_returns(returns_map)

    # Current weights for companies with price data
    weights_dict = {h["company"]: float(h["weight"]) for h in self.holdings}
    current_weights = np.array([weights_dict.get(n, 0.0) for n in names])
    current_weights /= current_weights.sum()  # normalize

    # Risk metrics for current portfolio
    port_returns = compute_portfolio_returns(current_weights, matrix)
    metrics = compute_risk_metrics(port_returns)

    # Format for display
    self.sortino_str = f"{metrics['sortino']:.2f}" if metrics['sortino'] is not None else "N/A"
    self.max_drawdown_str = f"{metrics['max_drawdown'] * 100:.1f}%" if metrics['max_drawdown'] is not None else "N/A"
    self.cvar_str = f"{metrics['cvar_95'] * 100:.2f}%" if metrics['cvar_95'] is not None else "N/A"

    # Optimization
    opt = mean_variance_optimize(matrix, names)
    opt_weights = opt["weights"]

    # Build optimization table
    self.optimization_data = [
        {
            "company": n,
            "current": str(round(weights_dict.get(n, 0.0) * 100, 1)),
            "optimal": str(opt_weights.get(n, 0.0)),
            "arrow": "↑" if opt_weights.get(n, 0.0) > weights_dict.get(n, 0.0) * 100 else "↓",
        }
        for n in names
    ]

    # Frontier
    self.frontier_data = sample_frontier(matrix, n_samples=200)

    # Current portfolio point (annualized)
    mean_returns = np.mean(matrix, axis=0) * 252
    cov_matrix = np.cov(matrix.T) * 252
    current_return = float(np.dot(current_weights, mean_returns) * 100)
    current_risk = float(np.sqrt(current_weights @ cov_matrix @ current_weights) * 100)
    self.current_point_data = [{"risk": str(round(current_risk, 2)), "return": str(round(current_return, 2))}]
```

### Proportional Weight Rebalance on Manual Input
```python
# Source: D-06 decision
@rx.event
def set_holding_weight(self, company: str, new_value: str):
    """Rebalance: set company to new_value%, scale others proportionally."""
    try:
        new_pct = float(new_value)
        new_pct = max(0.0, min(100.0, new_pct))
    except ValueError:
        return  # ignore non-numeric input

    remainder = 100.0 - new_pct
    others = [h for h in self.holdings if h["company"] != company]
    other_total = sum(float(h["weight_pct"]) for h in others)

    holdings = []
    for h in self.holdings:
        if h["company"] == company:
            w_pct = new_pct
        else:
            if other_total > 0:
                w_pct = float(h["weight_pct"]) / other_total * remainder
            else:
                w_pct = remainder / len(others) if others else 0.0
        w_float = round(w_pct / 100, 4)
        holdings.append({
            **h,
            "weight": w_float,
            "weight_pct": str(round(w_pct, 1)),
            "weight_str": f"{w_pct:.1f}%",
        })
    self.holdings = holdings
```

### Sector Chart Data Computation
```python
# Source: D-20 decision; pure Python, called from _compute_sector_data()
@rx.event
def _compute_sector_data(self):
    """Build sector_chart_data from holdings."""
    sector_totals = {"Banking": 0.0, "Insurance": 0.0, "Standard": 0.0}
    for h in self.holdings:
        sector = h.get("sector", "Standard")
        sector_totals[sector] = sector_totals.get(sector, 0.0) + float(h.get("weight_pct", "0"))

    colors = {"Banking": "#60a5fa", "Insurance": "#f59e0b", "Standard": "#4ade80"}
    self.sector_chart_data = [
        {"name": sector, "value": str(round(pct, 1)), "fill": colors[sector]}
        for sector, pct in sector_totals.items()
        if pct > 0
    ]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyPortfolioOpt for mean-variance | scipy.optimize.minimize SLSQP | Project decision (CONTEXT.md) | No new dependency; scipy already installed |
| Equal weights only in portfolio | Manual weight input + auto-normalize | Phase 4 | Requires extending holdings dict schema |

**Deprecated/outdated:**
- `weight_str` as a static display string: replaced by an `rx.input` in Phase 4. The field can remain for backward compatibility (other parts of state may use it) but the weight column in the Holdings tab no longer uses it for display.

---

## Open Questions

1. **Recharts `rx.recharts.cell` availability in Reflex 0.8.26**
   - What we know: Raw Recharts supports `<Cell fill={color} />` inside `<Pie>` for per-segment coloring
   - What's unclear: Whether Reflex 0.8.26's recharts wrapper exposes `rx.recharts.cell` as a component
   - Recommendation: Encode `fill` as a data field and test early. If cells don't work, use a colorScale prop or uniform color. Wave 1 should prototype the pie chart first.

2. **rx.input on_key_down event signature in Reflex 0.8.26**
   - What we know: `on_blur` takes a string value. `on_key_down` may take `(key: str)` not `(key: str, value: str)`
   - What's unclear: How to pass both key name and current input value to the handler
   - Recommendation: Use `on_blur` as primary trigger (sufficient for UX). For Enter key, use a local state var `weight_input_value` updated via `on_change`, then trigger rebalance when blur or a dedicated "confirm" event fires.

3. **Efficient frontier Pareto filtering**
   - What we know: CONTEXT.md says "filter to Pareto-efficient subset" under Claude's Discretion
   - What's unclear: A strict Pareto filter may leave too few points for a visually coherent frontier with only 7 companies; random sampling already produces a banana-shaped cloud that approximates the frontier
   - Recommendation: Skip strict Pareto filtering for the MVP. Use 200 random portfolios with seed=42. The visual shape will be representative and deterministic.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| scipy | Mean-variance optimization | ✓ | 1.16.2 | — |
| numpy | Covariance matrix, risk metrics | ✓ | 2.3.4 | — |
| pandas | (not needed — numpy sufficient) | ✓ | 2.2.3 | n/a |
| Price JSON files | PORT-03, PORT-04, PORT-05, PORT-06 | ✓ | data/prices/ (7 companies scraped) | Analysis tab shows placeholder if < 2 |
| reflex 0.8.26 | All UI | ✓ (pinned) | 0.8.26 | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** Price data for individual companies — if a holding lacks a price JSON, it is excluded from optimization (but the UI shows a placeholder when < 2 companies have data).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing in project) |
| Config file | none — pytest discovers `tests/` automatically |
| Quick run command | `pytest tests/test_portfolio_optimization.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PORT-01 | Proportional weight rebalance on manual input | unit | `pytest tests/test_portfolio_optimization.py::test_weight_rebalance -x` | ❌ Wave 0 |
| PORT-02 | Sector chart data computed from holdings | unit | `pytest tests/test_portfolio_optimization.py::test_sector_chart_data -x` | ❌ Wave 0 |
| PORT-03 | Covariance matrix from price JSONs | unit | `pytest tests/test_portfolio_optimization.py::test_covariance_matrix -x` | ❌ Wave 0 |
| PORT-04 | Mean-variance optimization returns valid weights summing to 1 | unit | `pytest tests/test_portfolio_optimization.py::test_optimization -x` | ❌ Wave 0 |
| PORT-05 | Sortino/MaxDD/CVaR computed correctly from known return series | unit | `pytest tests/test_portfolio_optimization.py::test_risk_metrics -x` | ❌ Wave 0 |
| PORT-06 | Frontier sampling returns 200 dicts with risk/return string keys | unit | `pytest tests/test_portfolio_optimization.py::test_frontier_sampling -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_portfolio_optimization.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_portfolio_optimization.py` — covers PORT-01 through PORT-06
- [ ] The `conftest.py` already has `tmp_data_dir` fixture; extend it with a `sample_price_json` fixture returning mock price data (2 companies, 100 records each)

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection (`state.py`, `portfolio.py`, `company.py`, `valuation.py`) — holdings dict structure, Reflex tab pattern, recharts usage, established patterns
- `requirements.txt` + `pip show scipy/numpy` — confirmed installed versions
- `data/prices/АПУ.json` — confirmed price record schema `{date, open, high, low, close, volume}` (strings)
- `04-CONTEXT.md` — all locked decisions and discretion areas
- `PROJECT.md` — tech stack, constraints, Reflex version

### Secondary (MEDIUM confidence)
- scipy.optimize.minimize SLSQP documentation — industry standard for quadratic programming with linear constraints; behavior well-documented
- numpy.cov, numpy.random.default_rng — standard library; behavior verified by inspection

### Tertiary (LOW confidence)
- Recharts `rx.recharts.cell` availability in Reflex 0.8.26 — not directly verified against Reflex docs; flagged as Open Question

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed installed via pip show; versions verified
- Architecture: HIGH — follows established patterns directly copied from company.py and valuation.py
- Math (optimization/risk metrics): HIGH — standard implementations; scipy/numpy APIs stable
- Recharts pie cell colors: LOW — not verified against Reflex 0.8.26 API
- Pitfalls: HIGH — derived from existing codebase constraints documented in STATE.md and CONTEXT.md

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable libraries; Reflex 0.8.26 is pinned)
