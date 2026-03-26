"""Price scraper for MSE historical OHLCV data from old.mse.mn."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PRICES_DIR = DATA_DIR / "prices"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MSEAnalytica-Scraper/1.0)"}
BASE_URL = "http://old.mse.mn/en/company/{mse_id}"


def price_filename(company_name: str) -> str:
    """Sanitize company name for use as a filename.

    Strips leading/trailing whitespace and quote characters, then removes
    filesystem-unsafe characters.
    """
    name = company_name.strip().strip('"').strip()
    # Remove filesystem-unsafe chars
    name = re.sub(r'["/\\:*?<>|]', "", name)
    return f"{name}.json"


def price_file_exists(company_name: str) -> bool:
    """Check if the price file for a company already exists."""
    return (PRICES_DIR / price_filename(company_name)).exists()


def scrape_shares_outstanding(soup: BeautifulSoup) -> int | None:
    """Extract shares outstanding from the MSE company page HTML.

    Searches for a table row or element containing "share" (case-insensitive)
    in the company info section of old.mse.mn/en/company/{id}.

    Args:
        soup: Parsed BeautifulSoup of the company page.

    Returns:
        Total shares outstanding as an integer, or None if not found.
    """
    try:
        # Look for table rows with "share" in the label cell
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True).lower()
                if "share" in text and i + 1 < len(cells):
                    value_text = cells[i + 1].get_text(strip=True).replace(",", "").replace(" ", "")
                    try:
                        return int(value_text)
                    except ValueError:
                        pass

        # Fallback: search all text nodes near "share" keyword
        for tag in soup.find_all(string=re.compile(r"share", re.IGNORECASE)):
            parent = tag.parent
            if parent:
                next_sib = parent.find_next_sibling()
                if next_sib:
                    value_text = next_sib.get_text(strip=True).replace(",", "").replace(" ", "")
                    try:
                        return int(value_text)
                    except ValueError:
                        pass
    except Exception as e:
        logger.warning("Error extracting shares_outstanding: %s", e)

    return None


def scrape_company_prices(mse_id: int, company_name: str) -> tuple[list[dict], int | None]:
    """Fetch and parse historical OHLCV data for a company from old.mse.mn.

    Args:
        mse_id: The MSE company ID (used in the URL).
        company_name: The company's Mongolian name (used for logging).

    Returns:
        Tuple of (records, shares_outstanding) where records is a list of dicts
        with keys: date, open, high, low, close, volume (sorted ascending by date),
        and shares_outstanding is an int or None if not found on the page.

    Raises:
        ValueError: If no trade_history_result table is found on the page.
        requests.RequestException: On HTTP errors.
    """
    url = BASE_URL.format(mse_id=mse_id)
    logger.info("Fetching price data for %s (ID=%s) from %s", company_name, mse_id, url)

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract shares outstanding from the same page response (no extra HTTP request)
    shares_outstanding = scrape_shares_outstanding(soup)

    table = soup.find("table", class_="trade_history_result")

    if table is None:
        raise ValueError(
            f"No trade_history_result table found for company {company_name} (ID={mse_id})"
        )

    tbody = table.find("tbody")
    if tbody is None:
        raise ValueError(
            f"No tbody in trade_history_result table for company {company_name} (ID={mse_id})"
        )

    rows = tbody.find_all("tr")
    records = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 8:
            continue

        # Columns in order: No, High, Low, Open, Close, Volume, Value, Date
        def clean(val: str) -> str:
            return val.strip().replace(",", "")

        record = {
            "date": cells[7].get_text(strip=True),
            "open": clean(cells[3].get_text()),
            "high": clean(cells[1].get_text()),
            "low": clean(cells[2].get_text()),
            "close": clean(cells[4].get_text()),
            "volume": clean(cells[5].get_text()),
        }
        records.append(record)

    # Sort ascending by date
    records.sort(key=lambda r: r["date"])

    logger.info(
        "Scraped %d price records for %s (ID=%s)", len(records), company_name, mse_id
    )
    return records, shares_outstanding


def save_price_data(
    company_name: str,
    mse_id: int,
    records: list[dict],
    shares_outstanding: int | None = None,
) -> str:
    """Save price data to data/prices/{company_name}.json.

    Args:
        company_name: Mongolian company name (used as filename key).
        mse_id: The MSE company ID.
        records: List of OHLCV record dicts.
        shares_outstanding: Total shares outstanding scraped from MSE page (optional).

    Returns:
        The filename (without directory path) that was written.
    """
    PRICES_DIR.mkdir(parents=True, exist_ok=True)

    filename = price_filename(company_name)
    file_path = PRICES_DIR / filename

    # Sort records by date ascending before saving
    sorted_records = sorted(records, key=lambda r: r["date"])

    data = {
        "company": company_name,
        "mse_id": mse_id,
        "scraped_at": datetime.now().isoformat(),
        "records": sorted_records,
    }

    if shares_outstanding is not None:
        data["shares_outstanding"] = shares_outstanding

    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info("Saved %d records to %s", len(sorted_records), file_path)
    return filename
