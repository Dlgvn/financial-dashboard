"""Registry loader for MSE company data from data/company_registry.json."""

import json
import re
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "company_registry.json"

_registry: list[dict] | None = None


def _load() -> list[dict]:
    """Lazy-load and cache the company registry from disk."""
    global _registry
    if _registry is None:
        _registry = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return _registry


def _normalize(name: str) -> str:
    """Normalize a company name for lookup: remove all quotes, collapse spaces, lowercase."""
    result = name.replace('"', "").replace("'", "")
    result = " ".join(result.split())
    return result.lower()


def _mse_id_from_filename(filename: str) -> int | None:
    """Extract MSE company ID from an MSE filename.

    Supports two formats from members.mse.mn downloads:
      _565 20244report.xls   → 565
      52220244report.xls     → 522
    """
    # Format 1: underscore prefix + space separator
    m = re.match(r"_(\d+)\s", filename)
    if m:
        return int(m.group(1))
    # Format 2: id directly concatenated with year (20XX) — strip year suffix
    m = re.match(r"^(\d+?)(20\d{2})", filename)
    if m:
        return int(m.group(1))
    return None


def find_mse_id(company_name: str) -> int:
    """Look up the MSE company ID by company name.

    Normalizes both the query and registry entries by stripping whitespace,
    embedded quote characters, and lowercasing before comparing.

    Args:
        company_name: The company's Mongolian name (may contain embedded quotes).

    Returns:
        The integer MSE company ID.

    Raises:
        KeyError: If no matching company is found in the registry.
    """
    registry = _load()
    query = _normalize(company_name)
    for entry in registry:
        if _normalize(entry["name"]) == query:
            return entry["mse_id"]
        for alias in entry.get("aliases", []):
            if _normalize(alias) == query:
                return entry["mse_id"]
    raise KeyError(
        f"Company not found in registry: {company_name!r} (normalized: {query!r})"
    )


def find_sector(company_name: str) -> str | None:
    """Look up the sector for a company by name (or alias).

    Returns the sector string, or None if not found.
    """
    if not company_name or company_name.lower() == "unknown":
        return None
    registry = _load()
    query = _normalize(company_name)
    for entry in registry:
        if _normalize(entry["name"]) == query:
            return entry.get("sector") or None
        for alias in entry.get("aliases", []):
            if _normalize(alias) == query:
                return entry.get("sector") or None
    return None


def find_sector_by_mse_id(mse_id: int) -> str | None:
    """Look up the sector for a company by its MSE numeric ID.

    Useful when the company name in the file doesn't match the registry name
    (e.g., Mongolian name in file vs English name in registry).
    """
    registry = _load()
    for entry in registry:
        if entry.get("mse_id") == mse_id:
            return entry.get("sector") or None
    return None


def find_sub_sector(company_name: str) -> str | None:
    """Look up the sub-sector for a company by name (or alias)."""
    if not company_name or company_name.lower() == "unknown":
        return None
    registry = _load()
    query = _normalize(company_name)
    for entry in registry:
        if _normalize(entry["name"]) == query:
            return entry.get("sub_sector") or None
        for alias in entry.get("aliases", []):
            if _normalize(alias) == query:
                return entry.get("sub_sector") or None
    return None


def find_sub_sector_by_mse_id(mse_id: int) -> str | None:
    """Look up the sub-sector for a company by its MSE numeric ID."""
    registry = _load()
    for entry in registry:
        if entry.get("mse_id") == mse_id:
            return entry.get("sub_sector") or None
    return None


def find_sector_from_filename(filename: str) -> str | None:
    """Extract sector by parsing the MSE ID from a filename.

    Fallback for when company name lookup returns None.
    """
    mse_id = _mse_id_from_filename(filename)
    if mse_id is not None:
        return find_sector_by_mse_id(mse_id)
    return None


def all_companies() -> list[dict]:
    """Return the full company registry as a list of dicts."""
    return _load()
