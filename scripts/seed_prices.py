"""Seed script for scraping historical price data from old.mse.mn.

Usage:
    python scripts/seed_prices.py           # Skip companies with existing price files
    python scripts/seed_prices.py --force   # Re-scrape all companies

The script iterates over all 161 MSE-listed companies in data/company_registry.json,
scrapes OHLCV data for each one, and saves to data/prices/{company}.json.

Per-company errors are caught and logged without crashing the full run (idempotent).
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to sys.path so imports work when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_dashboard.scraper.price_scraper import (
    price_file_exists,
    save_price_data,
    scrape_company_prices,
)
from financial_dashboard.scraper.registry_loader import all_companies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

POLITENESS_DELAY = 0.5  # seconds between requests


def run_seed(force: bool = False) -> tuple[int, int, int]:
    """Run the price seed process for all companies in the registry.

    Args:
        force: If True, re-scrape companies that already have price files.

    Returns:
        Tuple of (ok_count, skipped_count, failed_count).
    """
    companies = all_companies()
    total = len(companies)
    ok = 0
    skipped = 0
    failed = 0

    logger.info("Starting price seed for %d companies (force=%s)", total, force)

    for i, entry in enumerate(companies, start=1):
        name = entry["name"]
        mse_id = entry["mse_id"]

        # Idempotency check: skip if file already exists (unless --force)
        if not force and price_file_exists(name):
            logger.debug("[%d/%d] SKIP %s (already scraped)", i, total, name)
            skipped += 1
            continue

        try:
            logger.info("[%d/%d] Scraping %s (ID=%s)...", i, total, name, mse_id)
            records = scrape_company_prices(mse_id, name)
            save_price_data(name, mse_id, records)
            logger.info(
                "[%d/%d] OK %s — %d records saved", i, total, name, len(records)
            )
            ok += 1
        except Exception as exc:
            logger.error(
                "[%d/%d] FAILED %s (ID=%s): %s", i, total, name, mse_id, exc
            )
            failed += 1

        # Politeness delay between requests
        time.sleep(POLITENESS_DELAY)

    logger.info("Seed complete: OK=%d SKIPPED=%d FAILED=%d", ok, skipped, failed)
    return ok, skipped, failed


def main() -> None:
    """Parse CLI arguments and run the seed."""
    parser = argparse.ArgumentParser(
        description="Seed historical price data from old.mse.mn for all MSE-listed companies."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-scrape companies that already have price files (override idempotency).",
    )
    args = parser.parse_args()
    run_seed(force=args.force)


if __name__ == "__main__":
    main()
