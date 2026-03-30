"""Unit tests for financial_dashboard.analysis.portfolio_optimization.

TDD RED phase: all tests import from the module that does not exist yet.
All tests must FAIL until portfolio_optimization.py is implemented.

Covers PORT-03, PORT-05, PORT-06 requirements:
  PORT-03: Covariance matrix from price JSON
  PORT-04: Mean-variance optimization
  PORT-05: Sortino, Max Drawdown, CVaR 95%
  PORT-06: Efficient frontier sampling
  PORT-01: Manual weight rebalancing
  PORT-02: Sector breakdown chart data
"""

import numpy as np
import pytest

from financial_dashboard.analysis.portfolio_optimization import (
    align_returns,
    compute_portfolio_returns,
    compute_risk_metrics,
    compute_sector_breakdown,
    load_price_returns,
    mean_variance_optimize,
    rebalance_weights,
    sample_frontier,
)
import financial_dashboard.analysis.portfolio_optimization as portfolio_optimization


# ---------------------------------------------------------------------------
# Weight rebalancing tests (PORT-01)
# ---------------------------------------------------------------------------

def test_weight_rebalance():
    """rebalance_weights with 2 holdings: set A to 80 -> B becomes 20."""
    holdings = [
        {"company": "A", "weight_pct": "60.0", "weight": 0.6, "weight_str": "60.0%"},
        {"company": "B", "weight_pct": "40.0", "weight": 0.4, "weight_str": "40.0%"},
    ]
    result = rebalance_weights(holdings, "A", "80.0")
    result_map = {h["company"]: float(h["weight_pct"]) for h in result}
    assert abs(result_map["A"] - 80.0) < 0.01
    assert abs(result_map["B"] - 20.0) < 0.01
    total = sum(float(h["weight_pct"]) for h in result)
    assert abs(total - 100.0) < 0.1


def test_weight_rebalance_zero_others():
    """rebalance_weights: set one holding to 100 -> all others become 0."""
    holdings = [
        {"company": "A", "weight_pct": "50.0", "weight": 0.5, "weight_str": "50.0%"},
        {"company": "B", "weight_pct": "30.0", "weight": 0.3, "weight_str": "30.0%"},
        {"company": "C", "weight_pct": "20.0", "weight": 0.2, "weight_str": "20.0%"},
    ]
    result = rebalance_weights(holdings, "A", "100.0")
    result_map = {h["company"]: float(h["weight_pct"]) for h in result}
    assert abs(result_map["A"] - 100.0) < 0.01
    assert abs(result_map["B"]) < 0.01
    assert abs(result_map["C"]) < 0.01
    total = sum(float(h["weight_pct"]) for h in result)
    assert abs(total - 100.0) < 0.1


# ---------------------------------------------------------------------------
# Sector breakdown test (PORT-02)
# ---------------------------------------------------------------------------

def test_sector_chart_data():
    """compute_sector_breakdown aggregates weights by sector with correct colors."""
    holdings = [
        {"sector": "Banking", "weight_pct": "60.0"},
        {"sector": "Standard", "weight_pct": "40.0"},
    ]
    result = compute_sector_breakdown(holdings)
    # Result must be a list of dicts with name, value, fill
    assert isinstance(result, list)
    assert len(result) == 2
    result_map = {item["name"]: item for item in result}
    assert "Banking" in result_map
    assert "Standard" in result_map
    assert result_map["Banking"]["value"] == "60.0"
    assert result_map["Standard"]["value"] == "40.0"
    assert result_map["Banking"]["fill"] == "#60a5fa"
    assert result_map["Standard"]["fill"] == "#4ade80"


# ---------------------------------------------------------------------------
# Covariance matrix / return loading tests (PORT-03)
# ---------------------------------------------------------------------------

def test_covariance_matrix(sample_price_json, monkeypatch):
    """load_price_returns returns dict of log-return arrays for 2 companies.
    align_returns produces (names, matrix) where matrix.shape == (N, 2).
    """
    monkeypatch.setattr(
        portfolio_optimization, "PRICES_DIR", sample_price_json / "prices"
    )
    returns_map = load_price_returns(["CompanyA", "CompanyB"])
    assert "CompanyA" in returns_map
    assert "CompanyB" in returns_map
    assert isinstance(returns_map["CompanyA"], np.ndarray)
    assert isinstance(returns_map["CompanyB"], np.ndarray)
    assert len(returns_map["CompanyA"]) > 0

    names, matrix = align_returns(returns_map)
    assert isinstance(names, list)
    assert len(names) == 2
    assert matrix.shape == (len(returns_map["CompanyA"]), 2) or matrix.shape[1] == 2


# ---------------------------------------------------------------------------
# Optimization test (PORT-04)
# ---------------------------------------------------------------------------

def test_optimization(sample_price_json, monkeypatch):
    """mean_variance_optimize returns weights summing to ~100, all 0-100."""
    monkeypatch.setattr(
        portfolio_optimization, "PRICES_DIR", sample_price_json / "prices"
    )
    returns_map = load_price_returns(["CompanyA", "CompanyB"])
    names, matrix = align_returns(returns_map)
    result = mean_variance_optimize(matrix, names)
    assert "weights" in result
    assert "success" in result
    weights = result["weights"]
    assert isinstance(weights, dict)
    total = sum(weights.values())
    assert abs(total - 100.0) < 0.1
    for w in weights.values():
        assert 0.0 <= w <= 100.0 + 0.01


# ---------------------------------------------------------------------------
# Risk metrics tests (PORT-05)
# ---------------------------------------------------------------------------

def test_risk_metrics():
    """compute_risk_metrics with sufficient returns returns proper dict."""
    # 50 known returns: alternating small positive and negative values
    rng = np.random.default_rng(seed=7)
    returns = rng.normal(0.001, 0.02, size=50)
    result = compute_risk_metrics(returns)
    assert "sortino" in result
    assert "max_drawdown" in result
    assert "cvar_95" in result
    # max_drawdown should be <= 0 (drawdown is loss, expressed as negative or zero)
    if result["max_drawdown"] is not None:
        assert result["max_drawdown"] <= 0.0
    # cvar_95 should be <= 0 (tail loss)
    if result["cvar_95"] is not None:
        assert result["cvar_95"] <= 0.0


def test_risk_metrics_insufficient():
    """compute_risk_metrics with <10 returns returns all None."""
    returns = np.array([0.01, 0.02, -0.01, 0.005])
    result = compute_risk_metrics(returns)
    assert result["sortino"] is None
    assert result["max_drawdown"] is None
    assert result["cvar_95"] is None


# ---------------------------------------------------------------------------
# Frontier sampling test (PORT-06)
# ---------------------------------------------------------------------------

def test_frontier_sampling(sample_price_json, monkeypatch):
    """sample_frontier returns 50 dicts each with 'risk' and 'return' string keys."""
    monkeypatch.setattr(
        portfolio_optimization, "PRICES_DIR", sample_price_json / "prices"
    )
    returns_map = load_price_returns(["CompanyA", "CompanyB"])
    _, matrix = align_returns(returns_map)
    result = sample_frontier(matrix, n_samples=50)
    assert isinstance(result, list)
    assert len(result) == 50
    for item in result:
        assert "risk" in item
        assert "return" in item
        assert isinstance(item["risk"], str)
        assert isinstance(item["return"], str)


# ---------------------------------------------------------------------------
# Missing file handling
# ---------------------------------------------------------------------------

def test_load_price_returns_missing_file(sample_price_json, monkeypatch):
    """load_price_returns with a nonexistent company name returns empty result for it."""
    monkeypatch.setattr(
        portfolio_optimization, "PRICES_DIR", sample_price_json / "prices"
    )
    returns_map = load_price_returns(["CompanyA", "NonExistentCo"])
    assert "CompanyA" in returns_map
    assert "NonExistentCo" not in returns_map
