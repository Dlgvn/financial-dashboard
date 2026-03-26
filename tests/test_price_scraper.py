"""Unit tests for financial_dashboard.scraper.price_scraper."""

from unittest.mock import MagicMock, patch

import pytest

import financial_dashboard.scraper.price_scraper as ps


class TestScrapeCompanyPrices:
    def test_parse_price_table(self, sample_html_with_prices):
        """Scraping returns correct OHLCV records sorted ascending by date."""
        mock_response = MagicMock()
        mock_response.text = sample_html_with_prices
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            records, shares = ps.scrape_company_prices(90, "АПУ")

        assert len(records) == 2

        # First record should be the earlier date (ascending sort)
        first = records[0]
        assert first["date"] == "2024-09-15"
        assert set(first.keys()) == {"date", "open", "high", "low", "close", "volume"}

        # Commas stripped from numeric values
        assert first["high"] == "3600"

    def test_no_price_table_raises(self, sample_html_no_table):
        """Raises ValueError when no trade_history_result table is present."""
        mock_response = MagicMock()
        mock_response.text = sample_html_no_table
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(ValueError):
                ps.scrape_company_prices(90, "АПУ")


class TestSaveAndExists:
    def test_save_and_exists(self, tmp_data_dir, monkeypatch):
        """save_price_data creates a file and price_file_exists returns True."""
        monkeypatch.setattr(ps, "PRICES_DIR", tmp_data_dir / "prices")

        records = [
            {
                "date": "2024-01-01",
                "open": "100",
                "high": "110",
                "low": "95",
                "close": "105",
                "volume": "500",
            }
        ]

        filename = ps.save_price_data("АПУ", 90, records)

        assert ps.price_file_exists("АПУ") is True

        # Verify file structure
        import json
        saved = json.loads((tmp_data_dir / "prices" / filename).read_text(encoding="utf-8"))
        assert "company" in saved
        assert "mse_id" in saved
        assert "scraped_at" in saved
        assert "records" in saved
        assert saved["records"][0]["date"] == "2024-01-01"

    def test_idempotency_check(self, tmp_data_dir, monkeypatch):
        """price_file_exists returns True after save, False for non-existent company."""
        monkeypatch.setattr(ps, "PRICES_DIR", tmp_data_dir / "prices")

        records = [{"date": "2024-01-01", "open": "100", "high": "110", "low": "95", "close": "105", "volume": "500"}]
        ps.save_price_data("АПУ", 90, records)

        assert ps.price_file_exists("АПУ") is True
        assert ps.price_file_exists("NonExistent") is False


class TestPriceFilename:
    def test_price_filename_sanitization(self):
        """Embedded quotes are stripped from filename."""
        result = ps.price_filename('" Премиум Нэксус " ХК')
        assert result == "Премиум Нэксус  ХК.json"
