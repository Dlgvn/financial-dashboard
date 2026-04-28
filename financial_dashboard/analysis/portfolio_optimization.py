"""Portfolio optimization and risk math for MSE Analytica.

Pure Python module — NO Reflex imports. All computation uses numpy and scipy.
Follows the same style as valuation.py.

Exports:
    load_price_returns       Load price JSONs and compute log returns per company.
    align_returns            Align return arrays to equal length, return matrix.
    compute_portfolio_returns Weighted portfolio return series from returns matrix.
    compute_risk_metrics     Sortino, Max Drawdown, CVaR 95% from return series.
    mean_variance_optimize   Maximize Sharpe via SLSQP; returns weight dict.
    sample_frontier          Random frontier sample; returns list[dict[str,str]].
    rebalance_weights        Proportional weight rebalance after manual edit.
    compute_sector_breakdown Aggregate holdings weight by sector for pie chart.
"""

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRICES_DIR = Path(__file__).parent.parent.parent / "data" / "prices"

SECTOR_COLORS = {
    "Banking": "#60a5fa",
    "Insurance": "#f59e0b",
    "Standard": "#4ade80",
}

# Default color for unknown sectors
_DEFAULT_COLOR = "#94a3b8"

# ---------------------------------------------------------------------------
# 1. load_price_returns
# ---------------------------------------------------------------------------


def load_price_returns(company_names: list[str]) -> dict[str, np.ndarray]:
    """Load price JSON files and return log return arrays for each company.

    Args:
        company_names: List of company name strings (must match JSON file names).

    Returns:
        Dict mapping company name -> numpy array of log returns.
        Companies with missing files or fewer than 2 records are skipped.
    """
    result: dict[str, np.ndarray] = {}

    for name in company_names:
        path = PRICES_DIR / f"{name}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        records = data.get("records", [])
        if len(records) < 2:
            continue

        try:
            closes = np.array([float(r["close"]) for r in records], dtype=float)
        except (KeyError, ValueError):
            continue

        if len(closes) < 2:
            continue

        # Guard: zero or negative prices make log returns undefined
        if np.any(closes <= 0):
            continue

        # Log returns used instead of simple returns: log(P_t/P_{t-1}) is time-additive and approximately
        # normally distributed — required assumption for mean-variance optimization (log-normality).
        log_returns = np.log(closes[1:] / closes[:-1])
        result[name] = log_returns

    return result


# ---------------------------------------------------------------------------
# 2. align_returns
# ---------------------------------------------------------------------------


def align_returns(
    returns_map: dict[str, np.ndarray],
) -> tuple[list[str], np.ndarray]:
    """Align all return arrays to equal length and stack into a matrix.

    Uses the most recent `min_len` observations so all assets share the same
    time window.

    Args:
        returns_map: Dict from company name to 1-D log return array.

    Returns:
        Tuple of (names_list, matrix) where matrix has shape (n_obs, n_assets).
        n_obs is the minimum return array length across all companies.
    """
    if not returns_map:
        return [], np.empty((0, 0))

    names = list(returns_map.keys())
    min_len = min(len(arr) for arr in returns_map.values())

    # Truncate each array to the last min_len observations
    arrays = [returns_map[name][-min_len:] for name in names]
    matrix = np.column_stack(arrays)  # shape (min_len, n_assets)

    return names, matrix


# ---------------------------------------------------------------------------
# 3. compute_portfolio_returns
# ---------------------------------------------------------------------------


def compute_portfolio_returns(
    weights: np.ndarray, returns_matrix: np.ndarray
) -> np.ndarray:
    """Compute weighted portfolio return series.

    Args:
        weights: 1-D array of weights (should sum to 1.0).
        returns_matrix: 2-D array (n_obs, n_assets).

    Returns:
        1-D array of portfolio returns (n_obs,).
    """
    return returns_matrix @ weights


# ---------------------------------------------------------------------------
# 4. compute_risk_metrics
# ---------------------------------------------------------------------------


def compute_risk_metrics(portfolio_returns: np.ndarray) -> dict:
    """Compute Sortino Ratio, Maximum Drawdown, and CVaR 95%.

    Args:
        portfolio_returns: 1-D array of portfolio daily returns.

    Returns:
        Dict with keys: sortino (float|None), max_drawdown (float|None),
        cvar_95 (float|None). All None if fewer than 10 observations.
    """
    null_result = {"sortino": None, "max_drawdown": None, "cvar_95": None}

    if len(portfolio_returns) < 10:
        return null_result

    result: dict = {}

    # ------------------------------------------------------------------
    # Sortino Ratio
    # ------------------------------------------------------------------
    mean_return = float(np.mean(portfolio_returns))
    downside_returns = portfolio_returns[portfolio_returns < 0.0]
    if len(downside_returns) == 0:
        result["sortino"] = None
    else:
        downside_std = float(np.std(downside_returns, ddof=1))
        if downside_std == 0.0:
            result["sortino"] = None
        else:
            # Annualization convention: 252 trading days per year (standard for equities).
            # Returns scale linearly (× 252); volatility scales by square root (× √252) per i.i.d. returns assumption.
            ann_return = mean_return * 252
            ann_downside_std = downside_std * math.sqrt(252)
            result["sortino"] = ann_return / ann_downside_std

    # ------------------------------------------------------------------
    # Maximum Drawdown
    # ------------------------------------------------------------------
    cum_returns = np.cumprod(1.0 + portfolio_returns)
    peak = np.maximum.accumulate(cum_returns)
    drawdowns = (cum_returns - peak) / peak
    result["max_drawdown"] = float(np.min(drawdowns))

    # ------------------------------------------------------------------
    # CVaR (Conditional Value at Risk) at 95% = Expected Shortfall = mean of returns below the 5th percentile.
    # More conservative than VaR: captures the average magnitude of tail losses, not just the threshold.
    # Historical simulation used — no parametric distribution assumed.
    threshold = float(np.percentile(portfolio_returns, 5))
    tail = portfolio_returns[portfolio_returns <= threshold]
    if len(tail) == 0:
        result["cvar_95"] = float(threshold)
    else:
        result["cvar_95"] = float(np.mean(tail))

    return result


# ---------------------------------------------------------------------------
# 5. mean_variance_optimize
# ---------------------------------------------------------------------------


def mean_variance_optimize(
    returns_matrix: np.ndarray, names: list[str]
) -> dict:
    """Find maximum-Sharpe weights using SLSQP.

    Args:
        returns_matrix: 2-D array (n_obs, n_assets).
        names: Asset names corresponding to columns.

    Returns:
        Dict with:
            weights: {name: weight_as_percent (float, 0-100)}, rounded to 1 dp.
            success: bool indicating whether optimizer converged.
    """
    n = returns_matrix.shape[1]
    equal_weights = {name: round(100.0 / n, 1) for name in names}

    if n == 0:
        return {"weights": {}, "success": False}

    # Annualize
    mean_returns = np.mean(returns_matrix, axis=0) * 252
    cov_matrix = np.cov(returns_matrix.T) * 252
    if cov_matrix.ndim == 0:
        # Single asset edge case
        cov_matrix = np.array([[float(cov_matrix)]])

    # Maximize Sharpe ratio by minimizing its negative (scipy.optimize.minimize minimizes by convention).
    # SLSQP (Sequential Least Squares Programming): gradient-based constrained optimizer.
    # Constraints: weights sum to exactly 1.0. Bounds: [0, 1] per asset enforces long-only (no shorting).
    def neg_sharpe(w: np.ndarray) -> float:
        port_return = float(w @ mean_returns)
        port_var = float(w @ cov_matrix @ w)
        if port_var <= 0:
            return 0.0
        return -(port_return / math.sqrt(port_var))

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0)] * n
    w0 = np.ones(n) / n

    opt_result = minimize(
        neg_sharpe,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if opt_result.success:
        raw_weights = opt_result.x
        # Ensure no tiny negative values due to floating point
        raw_weights = np.clip(raw_weights, 0.0, 1.0)
        # Renormalize
        total = raw_weights.sum()
        if total > 0:
            raw_weights = raw_weights / total
        weights = {name: round(float(w) * 100, 1) for name, w in zip(names, raw_weights)}
        return {"weights": weights, "success": True}
    else:
        # Fallback: equal weights
        return {"weights": equal_weights, "success": False}


# ---------------------------------------------------------------------------
# 6. sample_frontier
# ---------------------------------------------------------------------------


def sample_frontier(
    returns_matrix: np.ndarray, n_samples: int = 200
) -> list[dict]:
    """Sample random portfolio weights to approximate the efficient frontier.

    Args:
        returns_matrix: 2-D array (n_obs, n_assets).
        n_samples: Number of random portfolios to generate.

    Returns:
        List of n_samples dicts, each with string keys "risk" and "return".
        All values are strings (Reflex list[dict[str,str]] constraint per D-07).
    """
    n_assets = returns_matrix.shape[1]
    rng = np.random.default_rng(seed=42)  # Fixed seed: deterministic frontier scatter across page loads

    mean_returns = np.mean(returns_matrix, axis=0) * 252
    cov_matrix = np.cov(returns_matrix.T) * 252
    if cov_matrix.ndim == 0:
        cov_matrix = np.array([[float(cov_matrix)]])

    # Monte Carlo approximation of the efficient frontier: sample random normalized weight vectors,
    # compute (risk, return) for each. Not a true Markowitz parametric sweep — but sufficient to
    # visualize the frontier shape and locate the current portfolio relative to it.
    results = []
    for _ in range(n_samples):
        raw = rng.random(n_assets)
        w = raw / raw.sum()
        port_return = float(w @ mean_returns) * 100  # as percent
        port_var = float(w @ cov_matrix @ w)
        port_risk = math.sqrt(max(port_var, 0.0)) * 100  # as percent
        results.append({
            "risk": str(round(port_risk, 2)),
            "return": str(round(port_return, 2)),
        })

    return results


# ---------------------------------------------------------------------------
# 7. rebalance_weights
# ---------------------------------------------------------------------------


def rebalance_weights(
    holdings: list[dict], company: str, new_pct_str: str
) -> list[dict]:
    """Proportionally rebalance holdings after a manual weight edit.

    Args:
        holdings: Current holdings list. Each dict must have at least
                  'company' and 'weight_pct' (string representing 0-100).
        company: The company whose weight was edited.
        new_pct_str: New weight percentage as a string (e.g. "80.0").

    Returns:
        New holdings list (input is not mutated) with updated 'weight',
        'weight_pct', and 'weight_str' for each holding.
    """
    try:
        new_pct = float(new_pct_str)
    except (ValueError, TypeError):
        new_pct = 0.0
    new_pct = max(0.0, min(100.0, new_pct))

    remainder = 100.0 - new_pct

    # Separate target company and others
    others = [h for h in holdings if h["company"] != company]

    if not others:
        # Only one holding — clamp to 100
        new_pct = 100.0
        remainder = 0.0

    # Compute current total of other holdings
    other_total = sum(float(h.get("weight_pct", "0")) for h in others)

    new_holdings = []
    for h in holdings:
        h_copy = dict(h)
        if h_copy["company"] == company:
            pct = new_pct
        else:
            if other_total > 0:
                # Scale proportionally
                pct = float(h_copy.get("weight_pct", "0")) / other_total * remainder
            else:
                # Distribute equally
                pct = remainder / len(others) if others else 0.0

        h_copy["weight"] = round(pct / 100.0, 6)
        h_copy["weight_pct"] = str(round(pct, 1))
        h_copy["weight_str"] = f"{round(pct, 1)}%"
        new_holdings.append(h_copy)

    return new_holdings


# ---------------------------------------------------------------------------
# 8. compute_sector_breakdown
# ---------------------------------------------------------------------------


def compute_sector_breakdown(holdings: list[dict]) -> list[dict]:
    """Aggregate holdings weights by sector for pie chart rendering.

    Args:
        holdings: Holdings list. Each dict must have 'weight_pct' (string,
                  0-100) and optionally 'sector' (defaults to 'Standard').

    Returns:
        List of dicts with keys: name (str), value (str), fill (str).
        Only sectors with total weight > 0 are included.
        Values are strings (Reflex list[dict[str,str]] constraint).
    """
    sector_totals: dict[str, float] = {}

    for h in holdings:
        sector = h.get("sector", "Standard") or "Standard"
        try:
            pct = float(h.get("weight_pct", "0"))
        except (ValueError, TypeError):
            pct = 0.0
        sector_totals[sector] = sector_totals.get(sector, 0.0) + pct

    result = []
    for sector, total in sector_totals.items():
        if total <= 0:
            continue
        fill = SECTOR_COLORS.get(sector, _DEFAULT_COLOR)
        result.append({
            "name": sector,
            "value": str(round(total, 1)),
            "fill": fill,
        })

    return result
