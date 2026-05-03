"""Unit tests for financial_dashboard.scraper.registry_loader."""

import json

import pytest

import financial_dashboard.scraper.registry_loader as rl
from financial_dashboard.state import _detect_finance_subsector


@pytest.fixture(autouse=True)
def reset_registry_cache():
    """Reset the module-level registry cache before each test."""
    rl._registry = None
    yield
    rl._registry = None


class TestFindMseId:
    def test_find_known_ids(self, sample_registry, monkeypatch):
        """find_mse_id returns correct IDs for known companies."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", sample_registry)

        assert rl.find_mse_id("АПУ") == 90
        assert rl.find_mse_id("Хаан банк") == 563

    def test_find_with_quotes_normalization(self, sample_registry, monkeypatch):
        """find_mse_id strips embedded quotes for lookup (index.json format)."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", sample_registry)

        # index.json stores this as '" Премиум Нэксус " ХК'
        assert rl.find_mse_id('" Премиум Нэксус " ХК') == 557

    def test_find_unknown_raises(self, sample_registry, monkeypatch):
        """find_mse_id raises KeyError for unrecognized company names."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", sample_registry)

        with pytest.raises(KeyError):
            rl.find_mse_id("NonExistent")


class TestAllCompanies:
    def test_all_companies(self, sample_registry, monkeypatch):
        """all_companies returns the full registry list."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", sample_registry)

        companies = rl.all_companies()
        assert len(companies) == 3


@pytest.fixture
def finance_registry(tmp_path):
    """Registry with one Finance/Securities company and one Finance company without sub_sector."""
    data = [
        {
            "name": "Бидисек",
            "mse_id": 522,
            "ticker": "BDS",
            "sector": "Finance",
            "sub_sector": "Securities",
        },
        {
            "name": "Монгол Финанс",
            "mse_id": 999,
            "ticker": "MFN",
            "sector": "Finance",
        },
    ]
    path = tmp_path / "company_registry.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class TestDetectFinanceSubsector:
    def test_registry_lookup_wins_for_securities(self, finance_registry, monkeypatch):
        """Securities company is classified via registry, not name heuristics."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", finance_registry)
        assert _detect_finance_subsector("Бидисек") == "Securities"

    def test_registry_lookup_wins_over_name_pattern(self, finance_registry, monkeypatch):
        """Registry sub_sector takes precedence even when the name would match a heuristic."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", finance_registry)
        # "Бидисек" contains "СЕК" — the old heuristic would return "Securities/Brokerage".
        # With registry lookup, the exact registry value "Securities" is returned instead.
        result = _detect_finance_subsector("Бидисек")
        assert result == "Securities"
        assert result != "Securities/Brokerage"

    def test_name_pattern_fallback_when_no_registry_entry(self, finance_registry, monkeypatch):
        """Unknown company falls through to name-pattern heuristics."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", finance_registry)
        assert _detect_finance_subsector("МОННАБ Бодлого") == "ББСБ (Lending NBFI)"

    def test_default_fallback_for_unrecognized_company(self, finance_registry, monkeypatch):
        """Completely unrecognized name returns the generic 'Finance' label."""
        monkeypatch.setattr(rl, "_REGISTRY_PATH", finance_registry)
        assert _detect_finance_subsector("Монгол Финанс") == "Finance"
