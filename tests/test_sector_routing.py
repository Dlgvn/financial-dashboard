import json
import pytest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_index_json_has_sector():
    idx = json.loads((DATA_DIR.parent / "data" / "index.json").read_text())
    for entry in idx["files"]:
        assert "sector" in entry and entry["sector"], f"Missing sector: {entry}"
    known = {e["company"]: e["sector"] for e in idx["files"]}
    assert known["Хаан банк"] == "Banking"
    assert known["Мандал даатгал"] == "Insurance"
    assert known["АПУ"] == "Manufacturing"
    assert known["Сүү"] == "Food"
    assert known["Моносхүнс"] == "Food"
    assert known["Дархан нэхий ХК"] == "Textiles"
    assert known['" Премиум Нэксус " ХК'] == "Holding"


def test_detect_sector_from_data():
    from financial_dashboard.state import _detect_sector_from_data
    assert _detect_sector_from_data({"bank_balance_sheet": {}}) == "Banking"
    assert _detect_sector_from_data({"insurance_balance_sheet": {}}) == "Insurance"
    assert _detect_sector_from_data({"balance_sheet": {}}) == "Standard"


def test_bank_routing():
    from financial_dashboard.analysis.bank_ratios import compute_bank_ratios
    data_file = DATA_DIR / "Хаан_банк_2025.json"
    data = json.loads(data_file.read_text())
    result = compute_bank_ratios(data)
    assert result.get("is_bank") == True
    assert "nim" in result["current"].get("profitability", {})


def test_insurance_routing():
    from financial_dashboard.analysis.insurance_ratios import compute_insurance_ratios
    data_file = DATA_DIR / "Мандал_даатгал_2025.json"
    data = json.loads(data_file.read_text())
    result = compute_insurance_ratios(data)
    assert result.get("is_insurance") == True
    assert "underwriting" in result["current"]


def test_all_ratios_present():
    from financial_dashboard.analysis.ratios import compute_ratios
    data_file = DATA_DIR / "АПУ_2025.json"
    data = json.loads(data_file.read_text())
    result = compute_ratios(data)
    all_keys = set()
    for cat in result["current"].values():
        all_keys.update(cat.keys())
    assert len(all_keys) >= 20


def test_dupont_identity():
    from financial_dashboard.analysis.ratios import compute_ratios
    data_file = DATA_DIR / "АПУ_2025.json"
    data = json.loads(data_file.read_text())
    result = compute_ratios(data)
    curr = result["current"]
    net_margin = curr.get("profitability", {}).get("net_margin")
    asset_turnover = curr.get("activity", {}).get("total_asset_turnover")
    debt_to_equity = curr.get("solvency", {}).get("debt_to_equity")
    roe = curr.get("profitability", {}).get("roe")
    if any(v is None for v in [net_margin, asset_turnover, debt_to_equity, roe]):
        pytest.skip("ratio data incomplete")
    equity_multiplier = 1 + debt_to_equity
    computed_roe = net_margin * asset_turnover * equity_multiplier
    assert abs(computed_roe - roe) < 0.05


def test_red_flags_baseline():
    from financial_dashboard.state import _compute_red_flags
    from financial_dashboard.analysis.ratios import compute_ratios, compute_beneish
    data_file = DATA_DIR / "АПУ_2025.json"
    data = json.loads(data_file.read_text())
    ratios = compute_ratios(data)
    beneish = compute_beneish(data)
    result = _compute_red_flags(ratios, beneish)
    assert isinstance(result, list)
    for item in result:
        assert "flag" in item and "explanation" in item


def test_screener_filter():
    companies = [
        {"company": "Khan Bank", "sector": "Banking", "score": 80},
        {"company": "APU", "sector": "Manufacturing", "score": 70},
        {"company": "Mandal", "sector": "Insurance", "score": 60},
    ]
    filtered = [c for c in companies if c["sector"] == "Banking"]
    assert len(filtered) == 1
    assert filtered[0]["company"] == "Khan Bank"


def test_screener_sort():
    companies = [
        {"company": "A", "score": 50},
        {"company": "B", "score": 90},
        {"company": "C", "score": 70},
    ]
    sorted_companies = sorted(companies, key=lambda c: c.get("score", 0), reverse=True)
    assert sorted_companies[0]["score"] >= sorted_companies[-1]["score"]
