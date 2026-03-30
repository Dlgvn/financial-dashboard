import json
import random
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Minimal reflex stub so state.py can be imported without the full Reflex
# package installed.  Only the symbols used at module / class definition
# time need to be present.
# ---------------------------------------------------------------------------
if "reflex" not in sys.modules:
    rx_mock = types.ModuleType("reflex")

    # rx.State base class
    class _StateBase:
        pass

    rx_mock.State = _StateBase

    # rx.var / rx.event decorators — pass-through
    def _passthrough(fn=None, **kwargs):
        if fn is not None:
            return fn
        def decorator(f):
            return f
        return decorator

    rx_mock.var = _passthrough
    rx_mock.event = _passthrough

    # rx.UploadFile stub
    rx_mock.UploadFile = MagicMock

    # rx.redirect stub
    rx_mock.redirect = MagicMock

    sys.modules["reflex"] = rx_mock


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    prices_dir = tmp_path / "prices"
    prices_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_registry(tmp_path):
    """Create a minimal test registry."""
    registry = [
        {"name": "АПУ", "mse_id": 90, "ticker": "APU", "tier": "I"},
        {"name": "Хаан банк", "mse_id": 563, "ticker": "KHAN", "tier": "I"},
        {"name": "Премиум Нэксус ХК", "mse_id": 557, "ticker": "PRMX", "tier": "I"},
    ]
    registry_path = tmp_path / "company_registry.json"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    return registry_path


@pytest.fixture
def sample_price_json(tmp_data_dir):
    """Create 2 mock price JSON files in tmp_data_dir/prices/ for portfolio tests.

    CompanyA: 100 records, close prices starting at 1000, seed=42.
    CompanyB: 100 records, close prices starting at 500, seed=99.
    All price values stored as STRINGS to match real MSE data format.
    Returns tmp_data_dir (parent of prices/).
    """
    prices_dir = tmp_data_dir / "prices"
    prices_dir.mkdir(exist_ok=True)

    def _make_records(start_price: int, seed: int) -> list[dict]:
        random.seed(seed)
        records = []
        price = float(start_price)
        for i in range(100):
            day = (i % 28) + 1
            month = (i // 28) + 1
            date_str = f"2025-{month:02d}-{day:02d}"
            step = random.randint(-20, 20)
            price = max(1.0, price + step)
            close_str = str(int(price))
            records.append({
                "date": date_str,
                "open": close_str,
                "high": close_str,
                "low": close_str,
                "close": close_str,
                "volume": "100",
            })
        return records

    for company_name, start_price, seed in [
        ("CompanyA", 1000, 42),
        ("CompanyB", 500, 99),
    ]:
        data = {
            "company": company_name,
            "mse_id": 1,
            "scraped_at": "2026-01-01",
            "shares_outstanding": None,
            "records": _make_records(start_price, seed),
        }
        (prices_dir / f"{company_name}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    return tmp_data_dir


@pytest.fixture
def sample_html_with_prices():
    """Return HTML containing a trade_history_result table."""
    return '''<html><body>
    <table class="trade_history_result">
    <thead><tr><th>No</th><th>High</th><th>Low</th><th>Open</th><th>Close</th><th>Volume</th><th>Value</th><th>Date</th></tr></thead>
    <tbody>
    <tr><td>1</td><td>3,700</td><td>3,650</td><td>3,655</td><td>3,700</td><td>510</td><td>1,883,250</td><td>2024-09-16</td></tr>
    <tr><td>2</td><td>3,600</td><td>3,500</td><td>3,550</td><td>3,600</td><td>200</td><td>710,000</td><td>2024-09-15</td></tr>
    </tbody>
    </table>
    </body></html>'''


@pytest.fixture
def sample_html_no_table():
    """Return HTML with no price table."""
    return '<html><body><h1>Company Profile</h1></body></html>'
