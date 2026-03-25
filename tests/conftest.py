import json
from pathlib import Path

import pytest


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
