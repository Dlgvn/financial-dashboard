"""Unit tests for financial_dashboard.scraper.registry_loader."""

import pytest

import financial_dashboard.scraper.registry_loader as rl


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
